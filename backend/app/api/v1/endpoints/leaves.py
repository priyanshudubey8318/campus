"""Leave Management API endpoints for CampusPulse."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_permission
from app.core.database import get_db
from app.models.pulserecord import LeaveRequest
from app.models.user import User
from app.schemas.pulserecord import (
    LeaveAttachmentResponse,
    LeaveCancelRequest,
    LeaveRequestCreate,
    LeaveRequestDetailResponse,
    LeaveRequestResponse,
    LeaveReviewRequest,
)
from app.services.leave_service import LeaveService

router = APIRouter()


def _map_leave_to_response(leave: LeaveRequest) -> LeaveRequestResponse:
    student_name = None
    enrollment_number = None
    if leave.student and leave.student.user:
        student_name = leave.student.user.full_name
        enrollment_number = leave.student.enrollment_number

    reviewer_name = None
    if leave.reviewer:
        reviewer_name = leave.reviewer.full_name

    return LeaveRequestResponse(
        id=leave.id,
        institution_id=leave.institution_id,
        student_id=leave.student_id,
        student_name=student_name,
        enrollment_number=enrollment_number,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        days_count=leave.days_count,
        reason=leave.reason,
        status=leave.status,
        reviewed_by_user_id=leave.reviewed_by_user_id,
        reviewer_name=reviewer_name,
        reviewed_at=leave.reviewed_at,
        reviewer_notes=leave.reviewer_notes,
        cancellation_reason=leave.cancellation_reason,
        cancelled_at=leave.cancelled_at,
        attachment_count=len(leave.attachments),
        created_at=leave.created_at,
        updated_at=leave.updated_at,
    )


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_leave_request(
    payload: LeaveRequestCreate,
    current_user: User = Depends(require_permission("leaves:create")),
    db: Session = Depends(get_db),
):
    """Submit a formal student leave application."""
    created = LeaveService.create_leave_request(db, current_user, payload)
    return _map_leave_to_response(created)


@router.get("/mine", response_model=List[LeaveRequestResponse])
def get_own_leaves(
    status: Optional[str] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("leaves:read_own")),
    db: Session = Depends(get_db),
):
    """List leave requests submitted by the authenticated student."""
    leaves = LeaveService.get_own_leaves(db, current_user, status_filter=status, skip=skip, limit=limit)
    return [_map_leave_to_response(l) for l in leaves]


@router.get("/assigned", response_model=List[LeaveRequestResponse])
def get_assigned_leaves(
    status: Optional[str] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("leaves:read_assigned")),
    db: Session = Depends(get_db),
):
    """List leave requests for assigned students (Faculty or Advisor)."""
    leaves = LeaveService.get_assigned_leaves(db, current_user, status_filter=status, skip=skip, limit=limit)
    return [_map_leave_to_response(l) for l in leaves]


@router.get("/", response_model=List[LeaveRequestResponse])
def get_all_leaves(
    institution_id: Optional[str] = Query(None, description="Target institution (SuperAdmin only)"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(require_permission("leaves:read_all")),
    db: Session = Depends(get_db),
):
    """List all institutional leave requests (Admin oversight)."""
    leaves = LeaveService.get_all_leaves(
        db, current_user, institution_id=institution_id, status_filter=status, skip=skip, limit=limit
    )
    return [_map_leave_to_response(l) for l in leaves]


@router.get("/{leave_id}", response_model=LeaveRequestDetailResponse)
def get_leave_detail(
    leave_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete leave details including attachment metadata."""
    leave = LeaveService.get_leave_by_id(db, leave_id, current_user)
    base = _map_leave_to_response(leave)

    attachments = [
        LeaveAttachmentResponse(
            id=a.id,
            leave_request_id=a.leave_request_id,
            file_name=a.file_name,
            file_size_bytes=a.file_size_bytes,
            mime_type=a.mime_type,
            sha256_hash=a.sha256_hash,
            created_at=a.created_at,
        )
        for a in leave.attachments
        if not a.is_deleted
    ]

    return LeaveRequestDetailResponse(**base.model_dump(), attachments=attachments)


@router.post("/{leave_id}/cancel", response_model=LeaveRequestResponse)
def cancel_leave(
    leave_id: str,
    payload: LeaveCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending leave request."""
    cancelled = LeaveService.cancel_leave(db, leave_id, current_user, payload)
    return _map_leave_to_response(cancelled)


@router.post("/{leave_id}/review", response_model=LeaveRequestResponse)
def review_leave(
    leave_id: str,
    payload: LeaveReviewRequest,
    current_user: User = Depends(require_permission("leaves:review")),
    db: Session = Depends(get_db),
):
    """Approve or reject a student leave request with notes."""
    reviewed = LeaveService.review_leave(db, leave_id, current_user, payload)
    return _map_leave_to_response(reviewed)


@router.post("/{leave_id}/attachments", response_model=LeaveAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_leave_attachment(
    leave_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload supporting verification document to a leave request."""
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    attached = LeaveService.attach_document(
        db,
        leave_id=leave_id,
        caller_user=current_user,
        file_name=file.filename or "attachment",
        mime_type=mime,
        file_bytes=content,
    )
    return LeaveAttachmentResponse(
        id=attached.id,
        leave_request_id=attached.leave_request_id,
        file_name=attached.file_name,
        file_size_bytes=attached.file_size_bytes,
        mime_type=attached.mime_type,
        sha256_hash=attached.sha256_hash,
        created_at=attached.created_at,
    )


@router.get("/{leave_id}/attachments/{attachment_id}/download")
def download_leave_attachment(
    leave_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download attachment file with authenticated proxy streaming."""
    data, mime_type, file_name = LeaveService.get_attachment_file(db, leave_id, attachment_id, current_user)
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.delete("/{leave_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_attachment(
    leave_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete attachment from leave request, permitted only while in SUBMITTED state."""
    LeaveService.delete_attachment(db, leave_id, attachment_id, current_user)
    return None
