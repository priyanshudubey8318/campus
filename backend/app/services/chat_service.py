"""PulseAssist interactive chat and RAG orchestration service."""

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic import (
    AttendanceRecord,
    Course,
    Department,
    Enrollment,
    FacultyCourseAssignment,
    FacultyProfile,
    Institution,
    Program,
    StudentProfile,
)
from app.models.ai_log import AIInteractionLog
from app.models.pulserisk import StudentRiskSnapshot
from app.models.user import User
from app.schemas.knowledge import (
    PulseAssistCitation,
    PulseAssistMetricEvidence,
    PulseAssistQueryRequest,
    PulseAssistQueryResponse,
)
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.protocols import AIProviderProtocol
from app.services.grounding_service import (
    CitationVerificationService,
    NumericalGroundingValidator,
)
from app.services.retrieval_service import PulseAssistRetrievalService

logger = logging.getLogger(__name__)

# System Prompt enforcing institutional knowledge invariants
SYSTEM_PROMPT = """You are CampusPulse PulseAssist, an institutional AI assistant for higher education operations.
Your job is to provide accurate, grounded answers regarding institutional policies and verified student metrics.

STRICT OPERATIONAL SAFETY INVARIANTS:
1. ONLY make claims supported by the provided institutional policy documents.
2. CITE all policy sources inline using the format [Doc: <DOCUMENT_CODE>].
3. NEVER fabricate or hallucinate document codes, policy provisions, or deadlines.
4. If the provided documents do not contain the answer, explicitly state that no official policy was found and advise contacting an advisor.
5. NEVER calculate, derive, or modify student risk scores or Support Priority Indexes.
6. NEVER diagnose mental health, emotional state, or psychological conditions.
7. Treat all student performance data as confidential and only reference the exact verified figures provided in the prompt.
8. Maintain a professional, empathetic, and objective tone.
"""


class RateLimiter:
    """In-memory sliding window rate limiter for user queries."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, user_id: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds
        # Clean expired timestamps
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if t > window_start]

        if len(self.user_requests[user_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {self.max_requests} queries per minute.",
            )
        self.user_requests[user_id].append(now)


_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


class PulseAssistChatService:
    """Orchestrates query authorization, context assembly, LLM completion, grounding, and audit logging."""

    def __init__(
        self,
        ai_provider: Optional[AIProviderProtocol] = None,
        retrieval_service: Optional[PulseAssistRetrievalService] = None,
    ):
        self.ai_provider = ai_provider or MockAIProvider()
        self.retrieval_service = retrieval_service or PulseAssistRetrievalService(ai_provider=self.ai_provider)
        self.citation_verifier = CitationVerificationService()
        self.numerical_validator = NumericalGroundingValidator()

    def _resolve_user_audience(self, current_user: User) -> str:
        """Derive the primary audience scope based on user's active role."""
        roles = [r.name for r in current_user.roles]
        if "SUPER_ADMIN" in roles:
            return "SUPER_ADMIN"
        if "ADMIN" in roles:
            return "ADMIN"
        if "ADVISOR" in roles:
            return "ADVISOR"
        if "FACULTY" in roles:
            return "FACULTY"
        if "STUDENT" in roles:
            return "STUDENT"
        return "ALL"

    def _resolve_caller_institution_id(
        self,
        db: Session,
        current_user: User,
        requested_inst_id: Optional[str] = None,
    ) -> str:
        """Resolve institution ID for the caller or enforce SUPER_ADMIN scope rules."""
        role_names = set(current_user.role_names)
        user_inst_id = None
        if current_user.student_profile and current_user.student_profile.program:
            dept = current_user.student_profile.program.department
            if dept:
                user_inst_id = dept.institution_id
        elif current_user.faculty_profile and current_user.faculty_profile.department:
            user_inst_id = current_user.faculty_profile.department.institution_id

        if "SUPER_ADMIN" in role_names:
            if requested_inst_id:
                inst = db.query(Institution).filter(Institution.id == requested_inst_id).first()
                if not inst:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Target institution '{requested_inst_id}' not found.",
                    )
                return requested_inst_id
            if user_inst_id:
                return user_inst_id
            first_inst = db.query(Institution).filter(Institution.is_active).first()
            return first_inst.id if first_inst else "default_inst"

        # Non-SUPER_ADMIN users cannot override target institution
        if requested_inst_id:
            if user_inst_id and requested_inst_id != user_inst_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non-SUPER_ADMIN users cannot override target institution.",
                )
            inst = db.query(Institution).filter(Institution.id == requested_inst_id).first()
            if not inst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target institution '{requested_inst_id}' not found.",
                )
            return requested_inst_id

        if user_inst_id:
            return user_inst_id

        first_inst = db.query(Institution).filter(Institution.is_active).first()
        return first_inst.id if first_inst else "default_inst"

    def _validate_student_access(
        self,
        db: Session,
        current_user: User,
        student_id: Optional[str],
        scoped_institution_id: Optional[str] = None,
    ) -> Optional[StudentProfile]:
        """Validate RBAC scoping rules for accessing student data."""
        if not student_id:
            return None

        # Resolve student profile joining program & department
        query = (
            select(StudentProfile)
            .outerjoin(Program, StudentProfile.program_id == Program.id)
            .outerjoin(Department, Program.department_id == Department.id)
            .where(StudentProfile.id == student_id)
        )
        if scoped_institution_id:
            query = query.where(Department.institution_id == scoped_institution_id)

        student = db.execute(query).scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student profile '{student_id}' not found in institution.",
            )

        roles = set(current_user.role_names)

        # 1. Student self-scoping
        if "STUDENT" in roles and "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
            if student.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-student access forbidden: Students may only access their own profile metrics.",
                )
            return student

        # 2. Faculty scoping
        if "FACULTY" in roles and "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
            fac_prof = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
            if not fac_prof:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Faculty profile required.",
                )

            faculty_assignment = db.execute(
                select(Enrollment.id)
                .join(FacultyCourseAssignment, FacultyCourseAssignment.course_id == Enrollment.course_id)
                .where(
                    FacultyCourseAssignment.faculty_id == fac_prof.id,
                    Enrollment.student_id == student.id,
                )
            ).scalars().first()

            if not faculty_assignment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Faculty may only query metrics for students enrolled in their assigned courses.",
                )
            return student

        # 3. Admin / Advisor / Super Admin
        return student

    def _gather_student_metrics(
        self,
        db: Session,
        student: StudentProfile,
    ) -> List[PulseAssistMetricEvidence]:
        """Gather verified ground truth student performance data from Phase 2–4 models."""
        metrics: List[PulseAssistMetricEvidence] = []

        # 1. CGPA
        cgpa_val = getattr(student, "cgpa", None)
        if cgpa_val is not None:
            metrics.append(
                PulseAssistMetricEvidence(
                    metric_name="cumulative_gpa",
                    observed_value=str(cgpa_val),
                    source_entity="student_profiles",
                    timestamp=student.updated_at,
                )
            )

        # 2. Overall attendance calculation
        total_att = db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.student_id == student.id
            )
        ).scalar() or 0

        if total_att > 0:
            present_att = db.execute(
                select(func.count(AttendanceRecord.id)).where(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.status.in_(["PRESENT", "LATE"]),
                )
            ).scalar() or 0
            att_pct = round((present_att / total_att) * 100.0, 1)
            metrics.append(
                PulseAssistMetricEvidence(
                    metric_name="attendance_percentage",
                    observed_value=f"{att_pct}%",
                    source_entity="attendance_records",
                    timestamp=datetime.now(timezone.utc),
                )
            )

        # 3. Read-only latest risk snapshot (if available)
        snapshot = db.execute(
            select(StudentRiskSnapshot)
            .where(StudentRiskSnapshot.student_id == student.id)
            .order_by(StudentRiskSnapshot.evaluation_date.desc(), StudentRiskSnapshot.created_at.desc())
        ).scalars().first()

        if snapshot:
            metrics.append(
                PulseAssistMetricEvidence(
                    metric_name="support_priority_tier",
                    observed_value=snapshot.priority_tier,
                    source_entity="student_risk_snapshots",
                    timestamp=snapshot.created_at,
                )
            )
            metrics.append(
                PulseAssistMetricEvidence(
                    metric_name="support_priority_index",
                    observed_value=str(snapshot.support_priority_index),
                    source_entity="student_risk_snapshots",
                    timestamp=snapshot.created_at,
                )
            )

        return metrics

    def process_query(
        self,
        db: Session,
        current_user: User,
        query_request: PulseAssistQueryRequest,
    ) -> PulseAssistQueryResponse:
        """Process an interactive student/staff inquiry through the verified RAG pipeline."""
        # 1. Check rate limits (10 req/min)
        _rate_limiter.check_rate_limit(current_user.id)

        # 2. Resolve audience & tenant institution scope
        audience = self._resolve_user_audience(current_user)
        scoped_institution_id = self._resolve_caller_institution_id(
            db, current_user, query_request.institution_id
        )

        # 3. Validate student data access
        student = self._validate_student_access(
            db, current_user, query_request.student_id, scoped_institution_id
        )

        # 4. Gather verified student metrics if requested and authorized
        ground_truth_metrics: List[PulseAssistMetricEvidence] = []
        if query_request.include_student_metrics and student:
            ground_truth_metrics = self._gather_student_metrics(db, student)

        # 5. Perform hybrid retrieval
        retrieved_chunks = self.retrieval_service.hybrid_search(
            db=db,
            query_text=query_request.query,
            institution_id=scoped_institution_id,
            audience=audience,
            top_k=5,
        )

        # 6. Build prompt
        context_blocks = []
        for c in retrieved_chunks:
            sec_str = f", Sec: {c.section_title}" if c.section_title else ""
            p_str = f", Page: {c.page_number}" if c.page_number else ""
            context_blocks.append(f"[Doc: {c.document_code}{sec_str}{p_str}]\n{c.content}")

        context_text = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant institutional documents found."

        metrics_blocks = []
        for m in ground_truth_metrics:
            metrics_blocks.append(f"{m.metric_name}: {m.observed_value} (Source: {m.source_entity})")

        metrics_text = "\n".join(metrics_blocks) if metrics_blocks else "None provided."

        prompt = f"""CONTEXT POLICY DOCUMENTS:
{context_text}

VERIFIED STUDENT METRICS:
{metrics_text}

USER INQUIRY:
{query_request.query}

Please answer the user inquiry strictly adhering to the institutional documents and verified metrics above."""

        # 7. Generate AI response
        ai_resp = self.ai_provider.generate_response(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1024,
        )

        # 8. Verify citations
        sanitized_text, verified_citations, has_hallucination = self.citation_verifier.verify_and_align_citations(
            ai_resp.text,
            retrieved_chunks,
        )

        # 9. Validate numerical assertions
        is_num_valid, ungrounded_numbers = self.numerical_validator.validate_grounding(
            sanitized_text,
            retrieved_chunks,
            ground_truth_metrics,
        )

        if not is_num_valid:
            logger.warning("Ungrounded numerical assertions detected: %s", ungrounded_numbers)

        # 10. Audit log interaction
        cited_ids = [vc.chunk_id for vc in verified_citations]
        audit_log = AIInteractionLog(
            institution_id=scoped_institution_id,
            user_id=current_user.id,
            student_context_id=student.id if student else None,
            interaction_type="POLICY_QA" if not student else "STUDENT_ASSIST",
            query_text=query_request.query,
            response_text=sanitized_text,
            chunks_cited_ids=cited_ids,
            verified_data_included=len(ground_truth_metrics) > 0,
            prompt_tokens=ai_resp.prompt_tokens,
            completion_tokens=ai_resp.completion_tokens,
            latency_ms=ai_resp.latency_ms,
            ai_provider=ai_resp.provider_name,
            model_name=ai_resp.model_name,
        )
        db.add(audit_log)
        db.commit()

        return PulseAssistQueryResponse(
            query=query_request.query,
            response=sanitized_text,
            citations=verified_citations,
            ground_truth_metrics=ground_truth_metrics,
            verified_data_included=len(ground_truth_metrics) > 0,
            tokens_used=ai_resp.prompt_tokens + ai_resp.completion_tokens,
            latency_ms=ai_resp.latency_ms,
            ai_provider=ai_resp.provider_name,
            model_name=ai_resp.model_name,
        )
