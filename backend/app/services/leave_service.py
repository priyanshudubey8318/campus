"""Leave Management Service for CampusPulse PulseRecord subsystem.

Implements:
- Leave request submission and days calculation.
- Reviewer adjudication (approve/reject) and cancellation.
- Secure attachment metadata, storage, and retrieval.
- Read-only analytics contract: get_approved_leave_intervals.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import get_storage_provider
from app.models.academic import Department, Enrollment, FacultyCourseAssignment, Institution, StudentProfile
from app.models.audit_log import AuditLog
from app.models.pulserecord import LeaveAttachment, LeaveRequest
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.leave_repo import LeaveRepository
from app.schemas.pulserecord import LeaveCancelRequest, LeaveRequestCreate, LeaveReviewRequest


class LeaveService:
    """Core domain service governing student leave requests and attachments."""

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
    def create_leave_request(
        cls,
        db: Session,
        caller_user: User,
        payload: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request for the authenticated student."""
        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only enrolled students with an academic profile can submit leave requests.",
            )

        if payload.end_date < payload.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Leave end_date must be on or after start_date.",
            )

        institution_id = cls._resolve_caller_institution_id(db, caller_user)
        days_count = (payload.end_date - payload.start_date).days + 1

        leave = LeaveRequest(
            institution_id=institution_id,
            student_id=student.id,
            leave_type=payload.leave_type.value,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days_count=days_count,
            reason=payload.reason,
            status="SUBMITTED",
        )
        created = LeaveRepository.create(db, leave)

        # Audit log
        db.add(
            AuditLog(
                action="LEAVE_SUBMITTED",
                entity_type="LeaveRequest",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role="STUDENT",
                details=f"Leave {created.leave_type} ({created.start_date} to {created.end_date}) submitted.",
            )
        )
        db.commit()
        return created

    @classmethod
    def get_own_leaves(
        cls,
        db: Session,
        caller_user: User,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LeaveRequest]:
        """Fetch leave requests submitted by the authenticated student."""
        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        if not student:
            return []
        return LeaveRepository.list_for_student(
            db, student_id=student.id, status=status_filter, skip=skip, limit=limit
        )

    @classmethod
    def get_assigned_leaves(
        cls,
        db: Session,
        caller_user: User,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LeaveRequest]:
        """Fetch leave requests for students assigned to this faculty member or advisor."""
        user_roles = set(caller_user.role_names)
        student_ids: List[str] = []

        if "FACULTY" in user_roles and caller_user.faculty_profile:
            # Students enrolled in courses assigned to this faculty
            assignments = (
                db.query(FacultyCourseAssignment)
                .filter(FacultyCourseAssignment.faculty_id == caller_user.faculty_profile.id)
                .all()
            )
            course_ids = [a.course_id for a in assignments]
            if course_ids:
                enrollments = (
                    db.query(Enrollment.student_id)
                    .filter(Enrollment.course_id.in_(course_ids))
                    .distinct()
                    .all()
                )
                student_ids = [e[0] for e in enrollments]

        elif "ADVISOR" in user_roles:
            # If advisor, fetch advisees from department or cohort
            inst_id = cls._resolve_caller_institution_id(db, caller_user)
            students = (
                db.query(StudentProfile.id)
                .join(Department, StudentProfile.program_id == Department.id, isouter=True)
                .filter(StudentProfile.academic_status == "ENROLLED")
                .all()
            )
            student_ids = [s[0] for s in students]

        return LeaveRepository.list_for_assigned_students(
            db, student_ids=student_ids, status=status_filter, skip=skip, limit=limit
        )

    @classmethod
    def get_all_leaves(
        cls,
        db: Session,
        caller_user: User,
        institution_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LeaveRequest]:
        """Fetch all leave requests for the institution (Admin oversight)."""
        target_inst = cls._resolve_caller_institution_id(db, caller_user, requested_inst_id=institution_id)
        return LeaveRepository.list_for_institution(
            db, institution_id=target_inst, status=status_filter, skip=skip, limit=limit
        )

    @classmethod
    def get_leave_by_id(
        cls,
        db: Session,
        leave_id: str,
        caller_user: User,
    ) -> LeaveRequest:
        """Fetch leave request by ID enforcing strict authorization and tenant scoping."""
        leave = LeaveRepository.get_by_id(db, leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request '{leave_id}' not found.",
            )

        # Scoping check
        caller_roles = set(caller_user.role_names)
        caller_inst = cls._resolve_caller_institution_id(db, caller_user)
        if "SUPER_ADMIN" not in caller_roles and leave.institution_id != caller_inst:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden.",
            )

        if "SUPER_ADMIN" in caller_roles or "ADMIN" in caller_roles:
            return leave

        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        if student and leave.student_id == student.id:
            return leave

        if "FACULTY" in caller_roles and caller_user.faculty_profile:
            # Check if student is enrolled in faculty's assigned courses
            assignments = (
                db.query(FacultyCourseAssignment.course_id)
                .filter(FacultyCourseAssignment.faculty_id == caller_user.faculty_profile.id)
                .all()
            )
            course_ids = [a[0] for a in assignments]
            is_enrolled = (
                db.query(Enrollment)
                .filter(
                    Enrollment.student_id == leave.student_id,
                    Enrollment.course_id.in_(course_ids),
                )
                .first()
            )
            if is_enrolled:
                return leave

        if "ADVISOR" in caller_roles:
            return leave

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this leave request.",
        )

    @classmethod
    def review_leave(
        cls,
        db: Session,
        leave_id: str,
        caller_user: User,
        payload: LeaveReviewRequest,
    ) -> LeaveRequest:
        """Adjudicate (approve or reject) a leave request with notes."""
        leave = cls.get_leave_by_id(db, leave_id, caller_user)

        user_roles = set(caller_user.role_names)
        if not (user_roles.intersection({"FACULTY", "ADVISOR", "ADMIN", "SUPER_ADMIN"})):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Caller is not authorized to review leave requests.",
            )

        if leave.status not in ["SUBMITTED", "UNDER_REVIEW"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot review leave in terminal status '{leave.status}'.",
            )

        if payload.status == "REJECTED" and not (payload.reviewer_notes and payload.reviewer_notes.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reviewer notes are mandatory when rejecting a leave request.",
            )

        leave.status = payload.status.value
        leave.reviewed_by_user_id = str(caller_user.id)
        leave.reviewed_at = datetime.now(timezone.utc)
        leave.reviewer_notes = payload.reviewer_notes

        db.commit()
        db.refresh(leave)

        # Audit
        action = "LEAVE_APPROVED" if leave.status == "APPROVED" else "LEAVE_REJECTED"
        db.add(
            AuditLog(
                action=action,
                entity_type="LeaveRequest",
                entity_id=leave.id,
                actor_id=str(caller_user.id),
                actor_role=list(user_roles)[0] if user_roles else "STAFF",
                details=f"Leave {leave.status} by {caller_user.full_name}. Notes: {leave.reviewer_notes}",
            )
        )
        db.commit()
        return leave

    @classmethod
    def cancel_leave(
        cls,
        db: Session,
        leave_id: str,
        caller_user: User,
        payload: LeaveCancelRequest,
    ) -> LeaveRequest:
        """Cancel a pending leave request."""
        leave = cls.get_leave_by_id(db, leave_id, caller_user)

        caller_roles = set(caller_user.role_names)
        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        is_owner = student and leave.student_id == student.id
        is_admin = bool(caller_roles.intersection({"ADMIN", "SUPER_ADMIN"}))

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owning student or an administrator can cancel this leave request.",
            )

        if leave.status not in ["SUBMITTED", "UNDER_REVIEW"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave in status '{leave.status}' cannot be cancelled.",
            )

        leave.status = "CANCELLED"
        leave.cancellation_reason = payload.cancellation_reason
        leave.cancelled_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(leave)

        db.add(
            AuditLog(
                action="LEAVE_CANCELLED",
                entity_type="LeaveRequest",
                entity_id=leave.id,
                actor_id=str(caller_user.id),
                actor_role="STUDENT" if is_owner else "ADMIN",
                details=f"Leave cancelled. Reason: {leave.cancellation_reason}",
            )
        )
        db.commit()
        return leave

    @classmethod
    def attach_document(
        cls,
        db: Session,
        leave_id: str,
        caller_user: User,
        file_name: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> LeaveAttachment:
        """Attach a supporting verification file to a leave request."""
        leave = cls.get_leave_by_id(db, leave_id, caller_user)

        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        is_owner = student and leave.student_id == student.id
        is_admin = bool(set(caller_user.role_names).intersection({"ADMIN", "SUPER_ADMIN"}))

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owning student can upload attachments to this leave request.",
            )

        if leave.status not in ["SUBMITTED", "UNDER_REVIEW"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload attachments to leave in status '{leave.status}'.",
            )

        # Limits: max 3 attachments
        if len(leave.attachments) >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 3 attachments allowed per leave request.",
            )

        # File size: max 10MB
        if len(file_bytes) == 0 or len(file_bytes) > 10485760:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be greater than 0 and not exceed 10 MiB.",
            )

        # MIME check
        allowed_mimes = {"application/pdf", "image/jpeg", "image/png"}
        if mime_type.lower() not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MIME type '{mime_type}'. Allowed: PDF, JPEG, PNG.",
            )

        storage = get_storage_provider()
        storage_key, sha256_hash = storage.store_file(
            institution_id=leave.institution_id,
            partition=f"leaves/{leave.id}",
            file_name=file_name,
            data=file_bytes,
        )

        attachment = LeaveAttachment(
            institution_id=leave.institution_id,
            leave_request_id=leave.id,
            uploader_user_id=str(caller_user.id),
            file_name=storage.sanitize_filename(file_name),
            file_size_bytes=len(file_bytes),
            mime_type=mime_type.lower(),
            sha256_hash=sha256_hash,
            storage_key=storage_key,
        )
        created = LeaveRepository.create_attachment(db, attachment)

        db.add(
            AuditLog(
                action="LEAVE_ATTACHMENT_UPLOADED",
                entity_type="LeaveAttachment",
                entity_id=created.id,
                actor_id=str(caller_user.id),
                actor_role="STUDENT" if is_owner else "ADMIN",
                details=f"Attachment '{created.file_name}' ({created.file_size_bytes} bytes) uploaded.",
            )
        )
        db.commit()
        return created

    @classmethod
    def delete_attachment(
        cls,
        db: Session,
        leave_id: str,
        attachment_id: str,
        caller_user: User,
    ) -> None:
        """Delete an attachment, allowed ONLY while leave is in SUBMITTED state."""
        leave = cls.get_leave_by_id(db, leave_id, caller_user)

        student = AcademicRepository.get_student_profile_by_user_id(db, caller_user.id)
        is_owner = student and leave.student_id == student.id
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owning student can delete attachments.",
            )

        if leave.status != "SUBMITTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attachments can only be deleted while in 'SUBMITTED' status. Current: '{leave.status}'.",
            )

        attachment = LeaveRepository.get_attachment_by_id(db, attachment_id)
        if not attachment or attachment.leave_request_id != leave.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found.",
            )

        # Remove file from storage
        storage = get_storage_provider()
        storage.delete_file(attachment.storage_key)
        LeaveRepository.delete_attachment(db, attachment)

        db.add(
            AuditLog(
                action="LEAVE_ATTACHMENT_DELETED",
                entity_type="LeaveAttachment",
                entity_id=attachment_id,
                actor_id=str(caller_user.id),
                actor_role="STUDENT",
                details=f"Attachment '{attachment.file_name}' deleted.",
            )
        )
        db.commit()

    @classmethod
    def get_attachment_file(
        cls,
        db: Session,
        leave_id: str,
        attachment_id: str,
        caller_user: User,
    ) -> Tuple[bytes, str, str]:
        """Retrieve attachment binary bytes, mime type, and filename enforcing authorization."""
        leave = cls.get_leave_by_id(db, leave_id, caller_user)
        attachment = LeaveRepository.get_attachment_by_id(db, attachment_id)
        if not attachment or attachment.leave_request_id != leave.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found.",
            )

        storage = get_storage_provider()
        try:
            data = storage.retrieve_file(attachment.storage_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment file data could not be retrieved: {str(e)}",
            )

        db.add(
            AuditLog(
                action="LEAVE_ATTACHMENT_DOWNLOADED",
                entity_type="LeaveAttachment",
                entity_id=attachment.id,
                actor_id=str(caller_user.id),
                actor_role=caller_user.role_names[0] if caller_user.role_names else "USER",
                details=f"Attachment '{attachment.file_name}' downloaded.",
            )
        )
        db.commit()
        return data, attachment.mime_type, attachment.file_name

    # =========================================================================
    # Master Spec / Invariant B: Analytics Read-Only Integration Contract
    # =========================================================================

    @staticmethod
    def get_approved_leave_intervals(
        db: Session,
        student_id: str,
        date_range: Tuple[date, date],
    ) -> List[Tuple[date, date]]:
        """Query verified, approved leave date intervals.
        
        Invariants:
        1. Returns closed intervals (start_date, end_date) inclusive.
        2. Strictly filters by status == 'APPROVED'.
        3. Merges contiguous or overlapping intervals.
        4. Completely excludes CANCELLED, REJECTED, and SUBMITTED requests.
        5. Pure read-only query contract. Zero modification to PulseWatch.
        """
        start_bound, end_bound = date_range
        approved_leaves = LeaveRepository.get_approved_in_range(
            db, student_id=student_id, start_date=start_bound, end_date=end_bound
        )

        if not approved_leaves:
            return []

        # Merge overlapping or contiguous date ranges
        merged: List[Tuple[date, date]] = []
        for leave in approved_leaves:
            cur_start, cur_end = leave.start_date, leave.end_date
            if not merged:
                merged.append((cur_start, cur_end))
            else:
                prev_start, prev_end = merged[-1]
                # If current start <= previous end + 1 day, intervals touch or overlap
                if cur_start <= prev_end + timedelta(days=1):
                    merged[-1] = (prev_start, max(prev_end, cur_end))
                else:
                    merged.append((cur_start, cur_end))
        return merged
