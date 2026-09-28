"""Complaint & Grievance Management API endpoints for CampusPulse."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.pulserecord import (
    ComplaintAdjudicateRequest,
    ComplaintAppealCreate,
    ComplaintAppealResolve,
    ComplaintAppealResponse,
    ComplaintAssignRequest,
    ComplaintCreate,
    ComplaintDetailResponse,
    ComplaintEvidenceResponse,
    ComplaintProvideInfo,
    ComplaintRequestInfo,
    ComplaintResponse,
)
from app.services.complaint_service import ComplaintService

router = APIRouter()


@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(require_permission("complaints:create")),
    db: Session = Depends(get_db),
):
    """File a formal institutional grievance."""
    complaint = ComplaintService.create_complaint(db, current_user, payload)
    return ComplaintService.project_complaint_response(complaint, current_user)


@router.get("/mine", response_model=List[ComplaintResponse])
def get_own_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("complaints:read_own")),
    db: Session = Depends(get_db),
):
    """List grievances filed by authenticated caller."""
    complaints = ComplaintService.get_own_complaints(db, current_user, skip=skip, limit=limit)
    return [ComplaintService.project_complaint_response(c, current_user) for c in complaints]


@router.get("/assigned", response_model=List[ComplaintResponse])
def get_assigned_complaints(
    status: Optional[str] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("complaints:read_assigned")),
    db: Session = Depends(get_db),
):
    """List grievances explicitly assigned to caller for review."""
    complaints = ComplaintService.get_assigned_complaints(
        db, current_user, status_filter=status, skip=skip, limit=limit
    )
    return [ComplaintService.project_complaint_response(c, current_user) for c in complaints]


@router.get("/", response_model=List[ComplaintResponse])
def get_institutional_complaints(
    institution_id: Optional[str] = Query(None, description="Target institution (SuperAdmin only)"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(require_permission("complaints:read_all")),
    db: Session = Depends(get_db),
):
    """List all institutional grievances (Administrative oversight)."""
    complaints = ComplaintService.get_institutional_complaints(
        db,
        current_user,
        institution_id=institution_id,
        status_filter=status,
        category_filter=category,
        skip=skip,
        limit=limit,
    )
    return [ComplaintService.project_complaint_response(c, current_user) for c in complaints]


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
def get_complaint_detail(
    complaint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete complaint details with redacted internal notes and anonymous projection."""
    complaint = ComplaintService.get_complaint_by_id(db, complaint_id, current_user)
    return ComplaintService.project_complaint_detail_response(complaint, current_user)


@router.post("/{complaint_id}/assign", response_model=ComplaintResponse)
def assign_reviewer(
    complaint_id: str,
    payload: ComplaintAssignRequest,
    current_user: User = Depends(require_permission("complaints:read_all")),
    db: Session = Depends(get_db),
):
    """Assign an administrative reviewer to investigate the grievance."""
    assigned = ComplaintService.assign_reviewer(db, complaint_id, payload.reviewer_user_id, current_user)
    return ComplaintService.project_complaint_response(assigned, current_user)


@router.post("/{complaint_id}/request-information", response_model=ComplaintResponse)
def request_information(
    complaint_id: str,
    payload: ComplaintRequestInfo,
    current_user: User = Depends(require_permission("complaints:review")),
    db: Session = Depends(get_db),
):
    """Reviewer requests additional information from the complainant."""
    updated = ComplaintService.request_information(db, complaint_id, payload.details, current_user)
    return ComplaintService.project_complaint_response(updated, current_user)


@router.post("/{complaint_id}/respond", response_model=ComplaintResponse)
def provide_information(
    complaint_id: str,
    payload: ComplaintProvideInfo,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complainant provides requested clarification, resuming review."""
    updated = ComplaintService.provide_information(db, complaint_id, payload.response, current_user)
    return ComplaintService.project_complaint_response(updated, current_user)


@router.post("/{complaint_id}/adjudicate", response_model=ComplaintResponse)
def adjudicate_complaint(
    complaint_id: str,
    payload: ComplaintAdjudicateRequest,
    current_user: User = Depends(require_permission("complaints:review")),
    db: Session = Depends(get_db),
):
    """Adjudicate formal complaint outcome (VERIFIED, DISMISSED, or OTHER_AUTHORIZED_OUTCOME)."""
    adjudicated = ComplaintService.adjudicate_complaint(db, complaint_id, payload, current_user)
    return ComplaintService.project_complaint_response(adjudicated, current_user)


@router.post("/{complaint_id}/appeal", response_model=ComplaintAppealResponse, status_code=status.HTTP_201_CREATED)
def appeal_complaint(
    complaint_id: str,
    payload: ComplaintAppealCreate,
    current_user: User = Depends(require_permission("complaints:appeal")),
    db: Session = Depends(get_db),
):
    """File a formal appeal contesting an adjudication finding."""
    appeal = ComplaintService.appeal_complaint(db, complaint_id, payload.reason, current_user)
    return ComplaintAppealResponse.model_validate(appeal)


@router.post("/{complaint_id}/resolve-appeal", response_model=ComplaintAppealResponse)
def resolve_appeal(
    complaint_id: str,
    appeal_id: str = Query(..., description="ID of appeal to resolve"),
    payload: ComplaintAppealResolve = ...,
    current_user: User = Depends(require_permission("complaints:read_all")),
    db: Session = Depends(get_db),
):
    """Resolve an appeal with formal disposition (Admin only)."""
    resolved = ComplaintService.resolve_appeal(db, complaint_id, appeal_id, payload, current_user)
    return ComplaintAppealResponse.model_validate(resolved)


@router.post("/{complaint_id}/close", response_model=ComplaintResponse)
def close_complaint(
    complaint_id: str,
    current_user: User = Depends(require_permission("complaints:read_all")),
    db: Session = Depends(get_db),
):
    """Formally close a complaint file and seal evidence."""
    closed = ComplaintService.close_complaint(db, complaint_id, current_user)
    return ComplaintService.project_complaint_response(closed, current_user)


@router.post("/{complaint_id}/evidence", response_model=ComplaintEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    complaint_id: str,
    description: Optional[str] = Form(None),
    is_confidential: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload supporting evidence file."""
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    evidence = ComplaintService.upload_evidence(
        db,
        complaint_id=complaint_id,
        caller_user=current_user,
        file_name=file.filename or "evidence",
        mime_type=mime,
        file_bytes=content,
        description=description,
        is_confidential=is_confidential,
    )
    return ComplaintEvidenceResponse(
        id=evidence.id,
        complaint_id=evidence.complaint_id,
        uploader_user_id=evidence.uploader_user_id,
        uploader_role=evidence.uploader_role,
        file_name=evidence.file_name,
        file_size_bytes=evidence.file_size_bytes,
        mime_type=evidence.mime_type,
        sha256_hash=evidence.sha256_hash,
        description=evidence.description,
        is_confidential=evidence.is_confidential,
        is_sealed=evidence.is_sealed,
        created_at=evidence.created_at,
    )


@router.get("/{complaint_id}/evidence/{evidence_id}/download")
def download_evidence(
    complaint_id: str,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download evidence file with authenticated proxy streaming."""
    data, mime_type, file_name = ComplaintService.get_evidence_file(db, complaint_id, evidence_id, current_user)
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
