"""PulseCase business logic and orchestration service for CampusPulse.

Implements:
- Direct case creation by authorized advisors and admins.
- Faculty advising referral intake.
- Case assignment with strict role-matching validation (ADVISOR vs. COUNSELOR).
- Complete deterministic lifecycle state machine:
  OPEN -> IN_PROGRESS -> WAITING_FOR_STUDENT / FOLLOW_UP_SCHEDULED -> RESOLVED -> CLOSED.
- Case notes with COUNSELOR_CONFIDENTIAL access restrictions and zero leakage.
- Interventions, commitments, and scheduled follow-up evaluation workflows.
- Immutable CLOSED state protection.
- Atomic audit recording for all state mutations.
- Pure read-only analytics contract: has_active_intervention.
"""

from datetime import datetime, timezone
from typing import List, Optional, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic import Institution, StudentProfile
from app.models.audit_log import AuditLog
from app.models.pulsecase import (
    CaseFollowUp,
    CaseIntervention,
    CaseNote,
    SupportCase,
)
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulsecase_repo import PulseCaseRepository
from app.repositories.user_repo import UserRepository
from app.schemas.pulsecase import (
    CaseAssignRequest,
    CaseCloseRequest,
    CaseCreateRequest,
    CaseFollowUpCreateRequest,
    CaseFollowUpResponse,
    CaseFollowUpUpdateRequest,
    CaseInterventionCreateRequest,
    CaseInterventionResponse,
    CaseInterventionUpdateRequest,
    CaseNoteCreateRequest,
    CaseNoteResponse,
    CaseResolveRequest,
    CaseStatusUpdateRequest,
    FacultyReferralCreateRequest,
    FacultyReferralReceiptResponse,
    StudentSupportItemResponse,
    StudentSupportSummaryResponse,
    StudentUpcomingFollowUpResponse,
    SupportCaseDetailResponse,
    SupportCaseResponse,
)


class PulseCaseService:
    """Core domain service for PulseCase support cases and interventions."""

    VALID_TRANSITIONS = {
        "OPEN": {"IN_PROGRESS"},
        "IN_PROGRESS": {"WAITING_FOR_STUDENT", "FOLLOW_UP_SCHEDULED", "RESOLVED"},
        "WAITING_FOR_STUDENT": {"IN_PROGRESS", "FOLLOW_UP_SCHEDULED"},
        "FOLLOW_UP_SCHEDULED": {"IN_PROGRESS", "RESOLVED"},
        "RESOLVED": {"IN_PROGRESS", "CLOSED"},
        "CLOSED": set(),  # Terminal state
    }

    @classmethod
    def _resolve_institution_id(
        cls,
        db: Session,
        current_user: User,
        requested_inst_id: Optional[str] = None,
    ) -> str:
        """Deterministically resolve the institution context for the caller."""
        user_roles = set(current_user.role_names)
        user_inst_id = None
        if current_user.student_profile and current_user.student_profile.program:
            dept = current_user.student_profile.program.department
            if dept:
                user_inst_id = dept.institution_id
        elif current_user.faculty_profile and current_user.faculty_profile.department:
            user_inst_id = current_user.faculty_profile.department.institution_id

        if "SUPER_ADMIN" in user_roles:
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

        if requested_inst_id:
            if user_inst_id and requested_inst_id != user_inst_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non-SUPER_ADMIN users cannot override target institution.",
                )
            return requested_inst_id

        if user_inst_id:
            return user_inst_id

        first_inst = db.query(Institution).filter(Institution.is_active).first()
        return first_inst.id if first_inst else "default_inst"

    @classmethod
    def create_case(
        cls,
        db: Session,
        caller_user: User,
        payload: CaseCreateRequest,
    ) -> SupportCase:
        """Directly open an intervention case (Advisor or Admin)."""
        inst_id = cls._resolve_institution_id(db, caller_user)

        # 1. Validate student exists in this institution
        student = db.query(StudentProfile).filter(StudentProfile.id == payload.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student profile '{payload.student_id}' not found.",
            )

        # Validate student belongs to institution
        student_inst_id = None
        if student.program and student.program.department:
            student_inst_id = student.program.department.institution_id
        if student_inst_id and student_inst_id != inst_id and "SUPER_ADMIN" not in caller_user.role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student does not belong to your institution.",
            )

        # 2. Staff assignment validation
        assigned_staff_role = None
        initial_status = "OPEN"
        if payload.assigned_staff_id:
            staff_user = UserRepository.get_by_id(db, payload.assigned_staff_id)
            if not staff_user or not staff_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assigned staff user '{payload.assigned_staff_id}' not found or inactive.",
                )
            assigned_roles = set(staff_user.role_names)

            if payload.case_type == "WELLBEING_REFERRAL":
                if "COUNSELOR" not in assigned_roles:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Wellbeing referral cases must be assigned to a staff member with the COUNSELOR role.",
                    )
                assigned_staff_role = "COUNSELOR"
            elif payload.case_type == "ACADEMIC_SUPPORT":
                if "ADVISOR" not in assigned_roles and "ADMIN" not in assigned_roles and "SUPER_ADMIN" not in assigned_roles:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Academic support cases must be assigned to a staff member with the ADVISOR role.",
                    )
                assigned_staff_role = "ADVISOR" if "ADVISOR" in assigned_roles else "ADVISOR"
            else:
                if "COUNSELOR" in assigned_roles:
                    assigned_staff_role = "COUNSELOR"
                elif "ADVISOR" in assigned_roles:
                    assigned_staff_role = "ADVISOR"
                else:
                    assigned_staff_role = "ADVISOR"

            initial_status = "IN_PROGRESS"

        case_number = PulseCaseRepository.generate_next_case_number(db, inst_id)

        case = SupportCase(
            institution_id=inst_id,
            case_number=case_number,
            student_id=payload.student_id,
            case_type=payload.case_type,
            status=initial_status,
            priority=payload.priority,
            trigger_source=payload.trigger_source,
            reason=payload.reason,
            evidence_references=payload.evidence_references,
            assigned_staff_id=payload.assigned_staff_id,
            assigned_staff_role=assigned_staff_role,
            referred_by_user_id=caller_user.id,
        )
        created = PulseCaseRepository.create_case(db, case)

        # Audit
        db.add(
            AuditLog(
                action="CASE_CREATED",
                entity_type="SupportCase",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Case {created.case_number} ({created.case_type}) opened. Priority: {created.priority}. Trigger: {created.trigger_source}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def create_referral(
        cls,
        db: Session,
        caller_user: User,
        payload: FacultyReferralCreateRequest,
    ) -> SupportCase:
        """Submit an academic advising referral (Faculty)."""
        inst_id = cls._resolve_institution_id(db, caller_user)

        # Validate student exists
        student = db.query(StudentProfile).filter(StudentProfile.id == payload.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student profile '{payload.student_id}' not found.",
            )

        case_number = PulseCaseRepository.generate_next_case_number(db, inst_id)

        evidence = {}
        if payload.course_id:
            evidence["course_id"] = payload.course_id

        case = SupportCase(
            institution_id=inst_id,
            case_number=case_number,
            student_id=payload.student_id,
            case_type="ACADEMIC_SUPPORT",
            status="OPEN",
            priority=payload.priority,
            trigger_source="FACULTY_REFERRAL",
            reason=payload.reason,
            evidence_references=evidence if evidence else None,
            assigned_staff_id=None,
            assigned_staff_role=None,
            referred_by_user_id=caller_user.id,
        )
        created = PulseCaseRepository.create_case(db, case)

        # Audit
        db.add(
            AuditLog(
                action="CASE_REFERRAL_SUBMITTED",
                entity_type="SupportCase",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role="FACULTY",
                details=f"Faculty referral submitted for student {created.student_id}. Case {created.case_number}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def assign_case(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseAssignRequest,
    ) -> SupportCase:
        """Assign or reassign staff handler to a case."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reassign a CLOSED case. Closed cases are permanently archived.",
            )

        staff_user = UserRepository.get_by_id(db, payload.assigned_staff_id)
        if not staff_user or not staff_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target staff user '{payload.assigned_staff_id}' not found or inactive.",
            )

        assigned_roles = set(staff_user.role_names)
        if case.case_type == "WELLBEING_REFERRAL":
            if "COUNSELOR" not in assigned_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Wellbeing referral cases must be assigned to a staff member with the COUNSELOR role.",
                )
            assigned_role = "COUNSELOR"
        elif case.case_type == "ACADEMIC_SUPPORT":
            if "ADVISOR" not in assigned_roles and "ADMIN" not in assigned_roles and "SUPER_ADMIN" not in assigned_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Academic support cases must be assigned to a staff member with the ADVISOR role.",
                )
            assigned_role = "ADVISOR"
        else:
            if "COUNSELOR" in assigned_roles:
                assigned_role = "COUNSELOR"
            else:
                assigned_role = "ADVISOR"

        old_staff_id = case.assigned_staff_id
        case.assigned_staff_id = payload.assigned_staff_id
        case.assigned_staff_role = assigned_role

        if case.status == "OPEN":
            case.status = "IN_PROGRESS"

        db.add(
            AuditLog(
                action="CASE_ASSIGNED",
                entity_type="SupportCase",
                entity_id=case.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Case {case.case_number} assigned to {staff_user.full_name} ({assigned_role}). Previous staff: {old_staff_id}.",
            )
        )
        db.commit()
        db.refresh(case)
        return case

    @classmethod
    def transition_case(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseStatusUpdateRequest,
    ) -> SupportCase:
        """Advance case lifecycle status according to canonical state machine."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a CLOSED case. Closed cases are permanently archived.",
            )

        target_status = payload.status
        allowed = cls.VALID_TRANSITIONS.get(case.status, set())
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {case.status} to {target_status}. Allowed: {sorted(list(allowed))}.",
            )

        old_status = case.status
        case.status = target_status

        db.add(
            AuditLog(
                action="CASE_STATUS_CHANGED",
                entity_type="SupportCase",
                entity_id=case.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Case {case.case_number} status changed from {old_status} to {target_status}. Note: {payload.notes or 'None'}.",
            )
        )
        db.commit()
        db.refresh(case)
        return case

    @classmethod
    def resolve_case(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseResolveRequest,
    ) -> SupportCase:
        """Resolve case with documented outcome."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot resolve a CLOSED case. Closed cases are permanently archived.",
            )

        if case.status not in ("IN_PROGRESS", "FOLLOW_UP_SCHEDULED", "RESOLVED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case in status '{case.status}' cannot be resolved. Must be IN_PROGRESS or FOLLOW_UP_SCHEDULED.",
            )

        case.status = "RESOLVED"
        case.resolution_outcome = payload.resolution_outcome
        case.resolution_summary = payload.resolution_summary
        case.resolved_at = datetime.now(timezone.utc)

        db.add(
            AuditLog(
                action="CASE_RESOLVED",
                entity_type="SupportCase",
                entity_id=case.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Case {case.case_number} resolved with outcome {case.resolution_outcome}.",
            )
        )
        db.commit()
        db.refresh(case)
        return case

    @classmethod
    def close_case(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseCloseRequest,
    ) -> SupportCase:
        """Permanently close and archive a resolved case."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            return case

        if case.status != "RESOLVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only cases in RESOLVED status can be closed. Current status: '{case.status}'.",
            )

        case.status = "CLOSED"
        case.closed_at = datetime.now(timezone.utc)
        case.closed_by_user_id = caller_user.id

        db.add(
            AuditLog(
                action="CASE_CLOSED",
                entity_type="SupportCase",
                entity_id=case.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Case {case.case_number} closed by {caller_user.full_name}. Closing note: {payload.closing_notes or 'None'}.",
            )
        )
        db.commit()
        db.refresh(case)
        return case

    # =========================================================================
    # Notes & Confidentiality
    # =========================================================================

    @classmethod
    def add_note(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseNoteCreateRequest,
    ) -> CaseNote:
        """Add timestamped note to case with confidentiality enforcement."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add notes to a CLOSED case.",
            )

        caller_roles = set(caller_user.role_names)

        # Confidentiality rule: Only COUNSELOR or SUPER_ADMIN can post COUNSELOR_CONFIDENTIAL
        if payload.confidentiality_level == "COUNSELOR_CONFIDENTIAL":
            if "COUNSELOR" not in caller_roles and "SUPER_ADMIN" not in caller_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only staff with the COUNSELOR role or SUPER_ADMIN may record counselor confidential notes.",
                )

        note = CaseNote(
            institution_id=case.institution_id,
            case_id=case.id,
            author_user_id=caller_user.id,
            note_type=payload.note_type,
            confidentiality_level=payload.confidentiality_level,
            content=payload.content,
        )
        created = PulseCaseRepository.create_note(db, note)

        # Audit metadata ONLY - NEVER log confidential note content!
        db.add(
            AuditLog(
                action="CASE_NOTE_ADDED",
                entity_type="CaseNote",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Note added to case {case.case_number}. Type: {created.note_type}. Confidentiality: {created.confidentiality_level}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def get_case_notes(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
    ) -> List[CaseNote]:
        """Fetch notes for a case, strictly redacting COUNSELOR_CONFIDENTIAL notes from unauthorized callers."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        caller_roles = set(caller_user.role_names)

        # Students and faculty are barred from reading internal case notes
        if "STUDENT" in caller_roles or "FACULTY" in caller_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view internal case notes.",
            )

        raw_notes = PulseCaseRepository.get_notes_by_case(db, case_id)
        filtered_notes: List[CaseNote] = []

        is_super_admin = "SUPER_ADMIN" in caller_roles
        is_assigned_counselor = "COUNSELOR" in caller_roles and case.assigned_staff_id == caller_user.id

        for note in raw_notes:
            if note.confidentiality_level == "COUNSELOR_CONFIDENTIAL":
                is_author_counselor = "COUNSELOR" in caller_roles and note.author_user_id == caller_user.id
                # Only author counselor, assigned counselor, or SUPER_ADMIN
                if is_super_admin or is_author_counselor or is_assigned_counselor:
                    filtered_notes.append(note)
                else:
                    continue  # Strict redaction
            else:
                filtered_notes.append(note)

        return filtered_notes

    # =========================================================================
    # Interventions & Follow-ups
    # =========================================================================

    @classmethod
    def add_intervention(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseInterventionCreateRequest,
    ) -> CaseIntervention:
        """Add action item or commitment to intervention case."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add interventions to a CLOSED case.",
            )

        intervention = CaseIntervention(
            institution_id=case.institution_id,
            case_id=case.id,
            intervention_type=payload.intervention_type,
            title=payload.title,
            description=payload.description,
            assigned_to_user_id=payload.assigned_to_user_id or case.assigned_staff_id,
            target_completion_date=payload.target_completion_date,
            status="PLANNED",
        )
        created = PulseCaseRepository.create_intervention(db, intervention)

        db.add(
            AuditLog(
                action="CASE_INTERVENTION_CREATED",
                entity_type="CaseIntervention",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Intervention '{created.title}' ({created.intervention_type}) added to case {case.case_number}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def update_intervention(
        cls,
        db: Session,
        caller_user: User,
        intervention_id: str,
        payload: CaseInterventionUpdateRequest,
    ) -> CaseIntervention:
        """Update intervention progress or completion."""
        intervention = PulseCaseRepository.get_intervention_by_id(db, intervention_id)
        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention '{intervention_id}' not found.",
            )

        intervention.status = payload.status
        if payload.status == "COMPLETED":
            intervention.completed_at = datetime.now(timezone.utc)
        if payload.outcome_notes:
            intervention.outcome_notes = payload.outcome_notes

        db.add(
            AuditLog(
                action="CASE_INTERVENTION_UPDATED",
                entity_type="CaseIntervention",
                entity_id=intervention.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Intervention {intervention.id} status updated to {intervention.status}.",
            )
        )
        db.commit()
        db.refresh(intervention)
        return intervention

    @classmethod
    def add_follow_up(
        cls,
        db: Session,
        caller_user: User,
        case_id: str,
        payload: CaseFollowUpCreateRequest,
    ) -> CaseFollowUp:
        """Schedule evaluation check-in meeting."""
        case = PulseCaseRepository.get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )

        if case.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot schedule follow-up on a CLOSED case.",
            )

        staff_id = payload.assigned_staff_id or case.assigned_staff_id or caller_user.id

        follow_up = CaseFollowUp(
            institution_id=case.institution_id,
            case_id=case.id,
            scheduled_date=payload.scheduled_date,
            scheduled_time=payload.scheduled_time,
            follow_up_type=payload.follow_up_type,
            assigned_staff_id=staff_id,
            status="SCHEDULED",
            notes=payload.notes,
        )
        created = PulseCaseRepository.create_follow_up(db, follow_up)

        # Transition case to FOLLOW_UP_SCHEDULED if currently IN_PROGRESS
        if case.status == "IN_PROGRESS":
            case.status = "FOLLOW_UP_SCHEDULED"

        db.add(
            AuditLog(
                action="CASE_FOLLOW_UP_SCHEDULED",
                entity_type="CaseFollowUp",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Follow-up scheduled for case {case.case_number} on {created.scheduled_date}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def update_follow_up(
        cls,
        db: Session,
        caller_user: User,
        follow_up_id: str,
        payload: CaseFollowUpUpdateRequest,
    ) -> CaseFollowUp:
        """Record follow-up session outcome."""
        follow_up = PulseCaseRepository.get_follow_up_by_id(db, follow_up_id)
        if not follow_up:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Follow-up session '{follow_up_id}' not found.",
            )

        follow_up.status = payload.status
        if payload.status == "COMPLETED":
            follow_up.completed_at = datetime.now(timezone.utc)
        if payload.notes:
            follow_up.notes = payload.notes

        db.add(
            AuditLog(
                action="CASE_FOLLOW_UP_COMPLETED",
                entity_type="CaseFollowUp",
                entity_id=follow_up.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "STAFF",
                details=f"Follow-up {follow_up.id} marked {follow_up.status}.",
            )
        )
        db.commit()
        db.refresh(follow_up)
        return follow_up

    # =========================================================================
    # Projections & Read Contracts
    # =========================================================================

    @classmethod
    def project_case_response(
        cls,
        case: SupportCase,
        caller_user: User,
    ) -> SupportCaseResponse:
        """Transform SupportCase to summary response."""
        student_name = case.student.user.full_name if case.student and case.student.user else None
        student_enrollment = case.student.enrollment_number if case.student else None
        assigned_name = case.assigned_staff.full_name if case.assigned_staff else None
        referred_name = case.referred_by.full_name if case.referred_by else None

        return SupportCaseResponse(
            id=case.id,
            institution_id=case.institution_id,
            case_number=case.case_number,
            student_id=case.student_id,
            student_name=student_name,
            student_enrollment_number=student_enrollment,
            case_type=case.case_type,
            status=case.status,
            priority=case.priority,
            trigger_source=case.trigger_source,
            reason=case.reason,
            evidence_references=case.evidence_references,
            assigned_staff_id=case.assigned_staff_id,
            assigned_advisor_id=case.assigned_staff_id,
            assigned_staff_name=assigned_name,
            assigned_staff_role=case.assigned_staff_role,
            referred_by_user_id=case.referred_by_user_id,
            referred_by_name=referred_name,
            resolution_outcome=case.resolution_outcome,
            resolution_summary=case.resolution_summary,
            resolved_at=case.resolved_at,
            closed_by_user_id=case.closed_by_user_id,
            closed_at=case.closed_at,
            created_at=case.created_at,
            updated_at=case.updated_at,
            interventions_count=len(case.interventions) if case.interventions else 0,
            follow_ups_count=len(case.follow_ups) if case.follow_ups else 0,
            notes_count=len(case.notes) if case.notes else 0,
        )

    @classmethod
    def project_case_detail_response(
        cls,
        db: Session,
        case: SupportCase,
        caller_user: User,
    ) -> SupportCaseDetailResponse:
        """Transform SupportCase to detail response with notes filtered by caller authorization."""
        base = cls.project_case_response(case, caller_user)

        # Filter notes
        filtered_notes = cls.get_case_notes(db, caller_user, case.id)
        note_responses = [
            CaseNoteResponse(
                id=n.id,
                case_id=n.case_id,
                author_user_id=n.author_user_id,
                author_name=n.author.full_name if n.author else None,
                note_type=n.note_type,
                confidentiality_level=n.confidentiality_level,
                content=n.content,
                created_at=n.created_at,
            )
            for n in filtered_notes
        ]

        intervention_responses = [
            CaseInterventionResponse(
                id=i.id,
                case_id=i.case_id,
                intervention_type=i.intervention_type,
                title=i.title,
                description=i.description,
                assigned_to_user_id=i.assigned_to_user_id,
                target_completion_date=i.target_completion_date,
                status=i.status,
                completed_at=i.completed_at,
                outcome_notes=i.outcome_notes,
                created_at=i.created_at,
            )
            for i in (case.interventions or [])
        ]

        follow_up_responses = [
            CaseFollowUpResponse(
                id=f.id,
                case_id=f.case_id,
                scheduled_date=f.scheduled_date,
                scheduled_time=f.scheduled_time,
                follow_up_type=f.follow_up_type,
                assigned_staff_id=f.assigned_staff_id,
                assigned_staff_name=f.assigned_staff.full_name if f.assigned_staff else None,
                status=f.status,
                notes=f.notes,
                completed_at=f.completed_at,
                created_at=f.created_at,
            )
            for f in (case.follow_ups or [])
        ]

        return SupportCaseDetailResponse(
            **base.model_dump(),
            notes=note_responses,
            interventions=intervention_responses,
            follow_ups=follow_up_responses,
        )

    @classmethod
    def student_support_projection(
        cls,
        db: Session,
        caller_user: User,
    ) -> StudentSupportSummaryResponse:
        """Student self-service overview: action items and upcoming appointments only."""
        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Caller does not have an active student profile.",
            )

        active_cases = (
            db.query(SupportCase)
            .filter(
                SupportCase.student_id == student.id,
                SupportCase.status.in_(["OPEN", "IN_PROGRESS", "WAITING_FOR_STUDENT", "FOLLOW_UP_SCHEDULED"]),
            )
            .all()
        )

        advisor_name = None
        action_items: List[StudentSupportItemResponse] = []
        upcoming_follow_ups: List[StudentUpcomingFollowUpResponse] = []

        for c in active_cases:
            if not advisor_name and c.assigned_staff:
                advisor_name = c.assigned_staff.full_name

            for i in c.interventions or []:
                if i.status in ("PLANNED", "IN_PROGRESS"):
                    action_items.append(
                        StudentSupportItemResponse(
                            id=i.id,
                            title=i.title,
                            description=i.description,
                            intervention_type=i.intervention_type,
                            target_date=i.target_completion_date,
                            status=i.status,
                        )
                    )

            for f in c.follow_ups or []:
                if f.status == "SCHEDULED":
                    upcoming_follow_ups.append(
                        StudentUpcomingFollowUpResponse(
                            id=f.id,
                            scheduled_date=f.scheduled_date,
                            scheduled_time=f.scheduled_time,
                            follow_up_type=f.follow_up_type,
                            status=f.status,
                        )
                    )

        return StudentSupportSummaryResponse(
            active_cases_count=len(active_cases),
            assigned_advisor_name=advisor_name,
            support_action_items=action_items,
            upcoming_follow_ups=upcoming_follow_ups,
        )

    @classmethod
    def faculty_referral_projection(
        cls,
        db: Session,
        caller_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FacultyReferralReceiptResponse]:
        """Sanitized referral receipts for faculty."""
        cases = PulseCaseRepository.list_referrals_by_referrer(db, caller_user.id, skip=skip, limit=limit)
        return [
            FacultyReferralReceiptResponse(
                id=c.id,
                case_number=c.case_number,
                student_id=c.student_id,
                student_name=c.student.user.full_name if c.student and c.student.user else None,
                case_type=c.case_type,
                status=c.status,
                priority=c.priority,
                created_at=c.created_at,
                closed_at=c.closed_at,
                resolution_outcome=c.resolution_outcome,
            )
            for c in cases
        ]

    @classmethod
    def get_student_case_history(
        cls,
        db: Session,
        caller_user: User,
        student_id: str,
    ) -> List[SupportCaseResponse]:
        """Fetch prior intervention cases for recurrence tracking."""
        cases = PulseCaseRepository.get_student_history(db, student_id)
        return [cls.project_case_response(c, caller_user) for c in cases]

    @classmethod
    def has_active_intervention(
        cls,
        db: Session,
        student_id: str,
    ) -> bool:
        """Pure read-only contract for PulseWatch / PulseRisk integration."""
        return PulseCaseRepository.has_active_intervention(db, student_id)
