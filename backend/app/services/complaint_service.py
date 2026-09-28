"""Complaint & Grievance Management Service for CampusPulse PulseRecord subsystem.

Implements:
- Formal grievance intake from students and external reporters.
- Anonymous filing with identity accountability and subject redaction.
- Reviewer assignment, information requests, and multi-stage adjudication.
- Appeals, evidence storage, and administrative file closure.
- Invariant A: Zero connection or impact to PulseWatch or PulseRisk.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import get_storage_provider
from app.models.academic import Department, Institution, StudentProfile
from app.models.audit_log import AuditLog
from app.models.pulserecord import Complaint, ComplaintAppeal, ComplaintEvidence
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas.pulserecord import (
    ComplaintAdjudicateRequest,
    ComplaintAppealCreate,
    ComplaintAppealResolve,
    ComplaintAppealResponse,
    ComplaintCreate,
    ComplaintDetailResponse,
    ComplaintEvidenceResponse,
    ComplaintResponse,
)


class ComplaintService:
    """Core domain service governing formal institutional complaints, evidence, and appeals."""

    @staticmethod
    def _resolve_caller_institution_id(
        db: Session,
        current_user: User,
        requested_inst_id: Optional[str] = None,
    ) -> str:
        """Resolve institution ID for user or enforce SUPER_ADMIN delegation."""
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
    def create_complaint(
        cls,
        db: Session,
        caller_user: User,
        payload: ComplaintCreate,
    ) -> Complaint:
        """Submit a new formal institutional grievance."""
        institution_id = cls._resolve_caller_institution_id(db, caller_user)
        complaint_code = ComplaintRepository.generate_next_code(db, institution_id)
        role = caller_user.role_names[0] if caller_user.role_names else "OTHER"

        # Validate target student exists if specified
        if payload.target_student_id:
            target_student = AcademicRepository.get_student_profile_by_id(db, payload.target_student_id)
            if not target_student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target student profile not found.",
                )

        complaint = Complaint(
            institution_id=institution_id,
            complaint_code=complaint_code,
            complainant_user_id=str(caller_user.id),
            complainant_role=role,
            is_anonymous=payload.is_anonymous,
            category=payload.category.value,
            target_type=payload.target_type.value,
            target_student_id=payload.target_student_id,
            target_department_id=payload.target_department_id,
            title=payload.title,
            description=payload.description,
            status="SUBMITTED",
        )
        created = ComplaintRepository.create(db, complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_SUBMITTED",
                entity_type="Complaint",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=role,
                details=f"Complaint {created.complaint_code} ({created.category}) filed. Anonymous: {created.is_anonymous}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def get_own_complaints(
        cls,
        db: Session,
        caller_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Complaint]:
        """List complaints submitted by the authenticated caller."""
        return ComplaintRepository.list_for_complainant(
            db, complainant_user_id=str(caller_user.id), skip=skip, limit=limit
        )

    @classmethod
    def get_assigned_complaints(
        cls,
        db: Session,
        caller_user: User,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Complaint]:
        """List complaints explicitly assigned to the authenticated reviewer."""
        return ComplaintRepository.list_for_assigned_reviewer(
            db, reviewer_user_id=str(caller_user.id), status=status_filter, skip=skip, limit=limit
        )

    @classmethod
    def get_institutional_complaints(
        cls,
        db: Session,
        caller_user: User,
        institution_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Complaint]:
        """List all institutional complaints (Admin oversight)."""
        target_inst = cls._resolve_caller_institution_id(db, caller_user, requested_inst_id=institution_id)
        return ComplaintRepository.list_for_institution(
            db,
            institution_id=target_inst,
            status=status_filter,
            category=category_filter,
            skip=skip,
            limit=limit,
        )

    @classmethod
    def get_complaint_by_id(
        cls,
        db: Session,
        complaint_id: str,
        caller_user: User,
    ) -> Complaint:
        """Fetch complaint by ID enforcing authorization and tenant scoping."""
        complaint = ComplaintRepository.get_by_id(db, complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint '{complaint_id}' not found.",
            )

        caller_roles = set(caller_user.role_names)
        caller_inst = cls._resolve_caller_institution_id(db, caller_user)
        if "SUPER_ADMIN" not in caller_roles and complaint.institution_id != caller_inst:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden.",
            )

        # Authorized if: Admin, SuperAdmin, Complainant, or Assigned Reviewer
        if "SUPER_ADMIN" in caller_roles or "ADMIN" in caller_roles:
            return complaint

        if complaint.complainant_user_id == str(caller_user.id):
            return complaint

        if complaint.assigned_reviewer_id == str(caller_user.id):
            return complaint

        # If caller is target student (and complaint is in an adjudicated state where notification occurred)
        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        if student and complaint.target_student_id == student.id and complaint.status in [
            "VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME", "APPEALED", "RESOLVED", "CLOSED"
        ]:
            return complaint

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this complaint.",
        )

    @classmethod
    def assign_reviewer(
        cls,
        db: Session,
        complaint_id: str,
        reviewer_user_id: str,
        caller_user: User,
    ) -> Complaint:
        """Assign an administrative or faculty reviewer to investigate the complaint."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        caller_roles = set(caller_user.role_names)
        if not caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can assign reviewers.",
            )

        reviewer = db.query(User).filter(User.id == reviewer_user_id).first()
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reviewer user '{reviewer_user_id}' not found.",
            )

        complaint.assigned_reviewer_id = str(reviewer.id)
        complaint.assigned_at = datetime.now(timezone.utc)
        if complaint.status == "SUBMITTED":
            complaint.status = "UNDER_REVIEW"

        db.commit()
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_ASSIGNED",
                entity_type="Complaint",
                entity_id=complaint.id,
                actor_id=str(caller_user.id),
                actor_role=list(caller_roles)[0],
                details=f"Reviewer {reviewer.full_name} ({reviewer.id}) assigned to complaint {complaint.complaint_code}.",
            )
        )
        db.commit()
        return complaint

    @classmethod
    def request_information(
        cls,
        db: Session,
        complaint_id: str,
        details: str,
        caller_user: User,
    ) -> Complaint:
        """Reviewer requests additional information from the complainant."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        caller_roles = set(caller_user.role_names)
        is_assigned = complaint.assigned_reviewer_id == str(caller_user.id)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))

        if not (is_assigned or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned reviewer or an administrator can request information.",
            )

        if complaint.status != "UNDER_REVIEW":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Information can only be requested while in 'UNDER_REVIEW' status. Current: '{complaint.status}'.",
            )

        complaint.status = "NEEDS_INFORMATION"
        complaint.info_request_details = details

        db.commit()
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_NEEDS_INFO",
                entity_type="Complaint",
                entity_id=complaint.id,
                actor_id=str(caller_user.id),
                actor_role=list(caller_roles)[0],
                details=f"Information requested: {details}",
            )
        )
        db.commit()
        return complaint

    @classmethod
    def provide_information(
        cls,
        db: Session,
        complaint_id: str,
        response: str,
        caller_user: User,
    ) -> Complaint:
        """Complainant provides requested clarification, resuming review."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        if complaint.complainant_user_id != str(caller_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the complainant can respond to an information request.",
            )

        if complaint.status != "NEEDS_INFORMATION":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Can only respond when in 'NEEDS_INFORMATION' status. Current: '{complaint.status}'.",
            )

        complaint.status = "UNDER_REVIEW"
        complaint.info_response_details = response

        db.commit()
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_INFO_SUBMITTED",
                entity_type="Complaint",
                entity_id=complaint.id,
                actor_id=str(caller_user.id),
                actor_role=complaint.complainant_role,
                details="Complainant provided requested clarification.",
            )
        )
        db.commit()
        return complaint

    @classmethod
    def adjudicate_complaint(
        cls,
        db: Session,
        complaint_id: str,
        payload: ComplaintAdjudicateRequest,
        caller_user: User,
    ) -> Complaint:
        """Adjudicate complaint finding (VERIFIED, DISMISSED, or OTHER_AUTHORIZED_OUTCOME)."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        caller_roles = set(caller_user.role_names)
        is_assigned = complaint.assigned_reviewer_id == str(caller_user.id)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))

        if not (is_assigned or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned reviewer or an administrator can adjudicate this complaint.",
            )

        if complaint.status not in ["UNDER_REVIEW", "NEEDS_INFORMATION"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot adjudicate complaint from status '{complaint.status}'.",
            )

        target_status = payload.status.value
        complaint.status = target_status
        complaint.adjudication_outcome = payload.adjudication_outcome
        complaint.adjudication_summary = payload.adjudication_summary
        complaint.internal_reviewer_notes = payload.internal_reviewer_notes

        db.commit()
        db.refresh(complaint)

        action = (
            "COMPLAINT_VERIFIED"
            if target_status == "VERIFIED"
            else ("COMPLAINT_DISMISSED" if target_status == "DISMISSED" else "COMPLAINT_RESOLVED")
        )
        db.add(
            AuditLog(
                action=action,
                entity_type="Complaint",
                entity_id=complaint.id,
                actor_id=str(caller_user.id),
                actor_role=list(caller_roles)[0],
                details=f"Adjudicated as {target_status} ({complaint.adjudication_outcome}). Summary: {complaint.adjudication_summary}",
            )
        )
        db.commit()
        return complaint

    @classmethod
    def appeal_complaint(
        cls,
        db: Session,
        complaint_id: str,
        reason: str,
        caller_user: User,
    ) -> ComplaintAppeal:
        """File a formal appeal contesting an adjudication finding."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        is_complainant = complaint.complainant_user_id == str(caller_user.id)
        is_target_student = student and complaint.target_student_id == student.id

        if not (is_complainant or is_target_student):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the complainant or the subject student can appeal this adjudication.",
            )

        # Permitted from VERIFIED, DISMISSED, OTHER_AUTHORIZED_OUTCOME
        if complaint.status not in ["VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Appeals can only be submitted against an adjudicated finding. Current status: '{complaint.status}'.",
            )

        appeal_number = ComplaintRepository.get_next_appeal_number(db, complaint.id)

        appeal = ComplaintAppeal(
            institution_id=complaint.institution_id,
            complaint_id=complaint.id,
            appellant_user_id=str(caller_user.id),
            appeal_number=appeal_number,
            reason=reason,
            status="SUBMITTED",
        )
        created_appeal = ComplaintRepository.create_appeal(db, appeal)

        # Single persistent canonical state for contestation: APPEALED
        complaint.status = "APPEALED"
        db.commit()
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_APPEALED",
                entity_type="ComplaintAppeal",
                entity_id=created_appeal.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "USER",
                details=f"Appeal #{appeal_number} submitted against {complaint.complaint_code}. Reason: {reason}",
            )
        )
        db.commit()
        return created_appeal

    @classmethod
    def resolve_appeal(
        cls,
        db: Session,
        complaint_id: str,
        appeal_id: str,
        payload: ComplaintAppealResolve,
        caller_user: User,
    ) -> ComplaintAppeal:
        """Resolve a formal appeal (Admin / appellate reviewer)."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)
        caller_roles = set(caller_user.role_names)

        if not caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only institutional administrators can resolve formal appeals.",
            )

        appeal = ComplaintRepository.get_appeal_by_id(db, appeal_id)
        if not appeal or appeal.complaint_id != complaint.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appeal not found for this complaint.",
            )

        if appeal.status in ["UPHELD", "OVERTURNED", "MODIFIED", "DISMISSED"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Appeal has already been resolved with disposition '{appeal.status}'.",
            )

        appeal.status = payload.status
        appeal.disposition_summary = payload.disposition_summary
        appeal.reviewer_notes = payload.reviewer_notes
        appeal.reviewer_user_id = str(caller_user.id)
        appeal.decided_at = datetime.now(timezone.utc)

        # Transition complaint status to RESOLVED
        complaint.status = "RESOLVED"
        complaint.adjudication_summary = f"[APPEAL RESOLUTION - {payload.status}]: {payload.disposition_summary}"

        db.commit()
        db.refresh(appeal)
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_RESOLVED",
                entity_type="ComplaintAppeal",
                entity_id=appeal.id,
                actor_id=str(caller_user.id),
                actor_role=list(caller_roles)[0],
                details=f"Appeal #{appeal.appeal_number} resolved as {appeal.status}. Summary: {appeal.disposition_summary}",
            )
        )
        db.commit()
        return appeal

    @classmethod
    def close_complaint(
        cls,
        db: Session,
        complaint_id: str,
        caller_user: User,
    ) -> Complaint:
        """Close complaint file and seal all evidence."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)
        caller_roles = set(caller_user.role_names)

        if not caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only institutional administrators can formally close complaint files.",
            )

        if complaint.status not in ["VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME", "RESOLVED"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot close complaint in status '{complaint.status}'. Must be adjudicated or resolved.",
            )

        complaint.status = "CLOSED"
        complaint.closed_by_user_id = str(caller_user.id)
        complaint.closed_at = datetime.now(timezone.utc)

        # Seal all evidence records
        for ev in complaint.evidence:
            ev.is_sealed = True

        db.commit()
        db.refresh(complaint)

        db.add(
            AuditLog(
                action="COMPLAINT_CLOSED",
                entity_type="Complaint",
                entity_id=complaint.id,
                actor_id=str(caller_user.id),
                actor_role=list(caller_roles)[0],
                details=f"Complaint {complaint.complaint_code} closed and evidence sealed.",
            )
        )
        db.commit()
        return complaint

    @classmethod
    def upload_evidence(
        cls,
        db: Session,
        complaint_id: str,
        caller_user: User,
        file_name: str,
        mime_type: str,
        file_bytes: bytes,
        description: Optional[str] = None,
        is_confidential: bool = False,
    ) -> ComplaintEvidence:
        """Upload supporting evidence file."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)

        caller_roles = set(caller_user.role_names)
        is_complainant = complaint.complainant_user_id == str(caller_user.id)
        is_reviewer = complaint.assigned_reviewer_id == str(caller_user.id)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))

        if not (is_complainant or is_reviewer or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to upload evidence to this complaint.",
            )

        if complaint.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload evidence to a CLOSED complaint file.",
            )

        # Complainant can only upload during active input states
        if is_complainant and not is_admin and not is_reviewer:
            if complaint.status not in ["SUBMITTED", "UNDER_REVIEW", "NEEDS_INFORMATION", "APPEALED"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Complainant cannot upload evidence in status '{complaint.status}'.",
                )

        if len(complaint.evidence) >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 5 evidence files allowed per complaint.",
            )

        if len(file_bytes) == 0 or len(file_bytes) > 20971520:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence file size must be between 1 byte and 20 MiB.",
            )

        allowed_mimes = {"application/pdf", "image/jpeg", "image/png", "text/plain"}
        if mime_type.lower() not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MIME type '{mime_type}'. Allowed: PDF, JPEG, PNG, TXT.",
            )

        storage = get_storage_provider()
        storage_key, sha256_hash = storage.store_file(
            institution_id=complaint.institution_id,
            partition=f"complaints/{complaint.id}",
            file_name=file_name,
            data=file_bytes,
        )

        role = caller_user.role_names[0] if caller_user.role_names else "USER"
        evidence = ComplaintEvidence(
            institution_id=complaint.institution_id,
            complaint_id=complaint.id,
            uploader_user_id=str(caller_user.id),
            uploader_role=role,
            file_name=storage.sanitize_filename(file_name),
            file_size_bytes=len(file_bytes),
            mime_type=mime_type.lower(),
            sha256_hash=sha256_hash,
            storage_key=storage_key,
            description=description,
            is_confidential=is_confidential,
        )
        created = ComplaintRepository.create_evidence(db, evidence)

        db.add(
            AuditLog(
                action="COMPLAINT_EVIDENCE_UPLOADED",
                entity_type="ComplaintEvidence",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role=role,
                details=f"Evidence '{created.file_name}' ({created.file_size_bytes} bytes) attached. Confidential: {created.is_confidential}.",
            )
        )
        db.commit()
        return created

    @classmethod
    def get_evidence_file(
        cls,
        db: Session,
        complaint_id: str,
        evidence_id: str,
        caller_user: User,
    ) -> Tuple[bytes, str, str]:
        """Download evidence file enforcing confidentiality and role authorization."""
        complaint = cls.get_complaint_by_id(db, complaint_id, caller_user)
        evidence = ComplaintRepository.get_evidence_by_id(db, evidence_id)
        if not evidence or evidence.complaint_id != complaint.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence file not found.",
            )

        caller_roles = set(caller_user.role_names)
        is_reviewer = complaint.assigned_reviewer_id == str(caller_user.id)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))

        # Confidential evidence visible ONLY to reviewer and admin
        if evidence.is_confidential and not (is_reviewer or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Confidential evidence can only be accessed by assigned reviewers or administrators.",
            )

        storage = get_storage_provider()
        try:
            data = storage.retrieve_file(evidence.storage_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence file data could not be retrieved: {str(e)}",
            )

        db.add(
            AuditLog(
                action="COMPLAINT_EVIDENCE_ACCESSED",
                entity_type="ComplaintEvidence",
                entity_id=evidence.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "USER",
                details=f"Evidence '{evidence.file_name}' accessed.",
            )
        )
        db.commit()
        return data, evidence.mime_type, evidence.file_name

    # =========================================================================
    # Projection & Privacy Redaction Helpers
    # =========================================================================

    @staticmethod
    def project_complaint_response(
        complaint: Complaint,
        caller_user: User,
    ) -> ComplaintResponse:
        """Project Complaint into Response schema with strict anonymity and note redaction."""
        caller_roles = set(caller_user.role_names)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))
        is_reviewer = complaint.assigned_reviewer_id == str(caller_user.id)

        # Redact complainant identity if anonymous unless caller is authorized for institutional accountability
        # Authorized roles: ADMIN and SUPER_ADMIN (or complainant on self-read)
        # Unauthorized roles: Assigned faculty/advisor reviewers, target subjects, general users
        complainant_user_id = complaint.complainant_user_id
        complainant_role = complaint.complainant_role
        if complaint.is_anonymous:
            if not (is_admin or str(caller_user.id) == complaint.complainant_user_id):
                complainant_user_id = None
                complainant_role = None

        # Redact internal reviewer notes unless reviewer or admin
        internal_notes = complaint.internal_reviewer_notes
        if not (is_reviewer or is_admin):
            internal_notes = None

        reviewer_name = None
        if complaint.assigned_reviewer:
            reviewer_name = complaint.assigned_reviewer.full_name

        return ComplaintResponse(
            id=complaint.id,
            institution_id=complaint.institution_id,
            complaint_code=complaint.complaint_code,
            complainant_user_id=complainant_user_id,
            complainant_role=complainant_role,
            is_anonymous=complaint.is_anonymous,
            category=complaint.category,
            target_type=complaint.target_type,
            target_student_id=complaint.target_student_id,
            target_department_id=complaint.target_department_id,
            title=complaint.title,
            description=complaint.description,
            status=complaint.status,
            assigned_reviewer_id=complaint.assigned_reviewer_id,
            assigned_reviewer_name=reviewer_name,
            assigned_at=complaint.assigned_at,
            adjudication_outcome=complaint.adjudication_outcome,
            adjudication_summary=complaint.adjudication_summary,
            internal_reviewer_notes=internal_notes,
            info_request_details=complaint.info_request_details,
            info_response_details=complaint.info_response_details,
            evidence_count=len(complaint.evidence),
            appeal_count=len(complaint.appeals),
            closed_at=complaint.closed_at,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
        )

    @classmethod
    def project_complaint_detail_response(
        cls,
        complaint: Complaint,
        caller_user: User,
    ) -> ComplaintDetailResponse:
        """Project complete Complaint Detail with redacted evidence and appeals."""
        base_resp = cls.project_complaint_response(complaint, caller_user)
        caller_roles = set(caller_user.role_names)
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))
        is_reviewer = complaint.assigned_reviewer_id == str(caller_user.id)

        evidence_list = []
        for ev in complaint.evidence:
            # If confidential, skip unless reviewer or admin
            if ev.is_confidential and not (is_reviewer or is_admin):
                continue

            uploader_id = ev.uploader_user_id
            if complaint.is_anonymous and not (is_admin or str(caller_user.id) == ev.uploader_user_id):
                uploader_id = None

            evidence_list.append(
                ComplaintEvidenceResponse(
                    id=ev.id,
                    complaint_id=ev.complaint_id,
                    uploader_user_id=uploader_id,
                    uploader_role=ev.uploader_role,
                    file_name=ev.file_name,
                    file_size_bytes=ev.file_size_bytes,
                    mime_type=ev.mime_type,
                    sha256_hash=ev.sha256_hash,
                    description=ev.description,
                    is_confidential=ev.is_confidential,
                    is_sealed=ev.is_sealed,
                    created_at=ev.created_at,
                )
            )

        appeals_list = []
        for app in complaint.appeals:
            reviewer_notes = app.reviewer_notes if (is_reviewer or is_admin) else None
            appeals_list.append(
                ComplaintAppealResponse(
                    id=app.id,
                    complaint_id=app.complaint_id,
                    appellant_user_id=app.appellant_user_id,
                    appeal_number=app.appeal_number,
                    reason=app.reason,
                    status=app.status,
                    reviewer_user_id=app.reviewer_user_id,
                    reviewer_notes=reviewer_notes,
                    disposition_summary=app.disposition_summary,
                    decided_at=app.decided_at,
                    created_at=app.created_at,
                    updated_at=app.updated_at,
                )
            )

        return ComplaintDetailResponse(
            **base_resp.model_dump(),
            evidence=evidence_list,
            appeals=appeals_list,
        )
