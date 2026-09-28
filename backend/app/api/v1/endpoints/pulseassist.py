"""PulseAssist API endpoints for institutional knowledge RAG and interactive assistance."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_role
from app.core.config import get_settings
from app.core.database import get_db
from app.models.academic import Institution
from app.models.ai_log import AIInteractionLog
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    DocumentScheduleResponse,
    KnowledgeChunkResponse,
    KnowledgeDocumentPublish,
    KnowledgeDocumentResponse,
    PulseAssistQueryRequest,
    PulseAssistQueryResponse,
)
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.chat_service import PulseAssistChatService
from app.services.knowledge_service import KnowledgeDocumentService

router = APIRouter()
settings = get_settings()


def _get_ai_provider():
    if settings.AI_PROVIDER.lower() == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
            embedding_model=settings.GEMINI_EMBEDDING_MODEL,
        )
    return MockAIProvider()


def _map_doc_to_response(doc: KnowledgeDocument, db: Session) -> KnowledgeDocumentResponse:
    chunk_count = db.execute(
        select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == doc.id)
    ).scalar() or 0

    schedules_data = [
        DocumentScheduleResponse(
            id=s.id,
            institution_id=s.institution_id,
            document_code=s.document_code,
            document_id=s.document_id,
            version=s.version,
            effective_from=s.effective_from,
            effective_to=s.effective_to,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in doc.schedules
    ]

    return KnowledgeDocumentResponse(
        id=doc.id,
        institution_id=doc.institution_id,
        title=doc.title,
        document_code=doc.document_code,
        category=doc.category,
        version=doc.version,
        status=doc.status,
        audience=doc.audience,
        summary=doc.summary,
        file_name=doc.file_name,
        file_hash=doc.file_hash,
        file_size_bytes=doc.file_size_bytes,
        created_by_user_id=doc.created_by_user_id,
        published_at=doc.published_at,
        archived_at=doc.archived_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks_count=chunk_count,
        schedules=schedules_data,
    )


def _resolve_caller_institution_id(
    db: Session,
    current_user: User,
    explicit_institution_id: Optional[str] = None,
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
        if explicit_institution_id:
            inst = db.query(Institution).filter(Institution.id == explicit_institution_id).first()
            if not inst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target institution '{explicit_institution_id}' not found.",
                )
            return explicit_institution_id
        if user_inst_id:
            return user_inst_id
        first_inst = db.query(Institution).filter(Institution.is_active).first()
        return first_inst.id if first_inst else "default_inst"

    # Non-SUPER_ADMIN users cannot override target institution
    if explicit_institution_id:
        if user_inst_id and explicit_institution_id != user_inst_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non-SUPER_ADMIN users cannot override target institution.",
            )
        inst = db.query(Institution).filter(Institution.id == explicit_institution_id).first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target institution '{explicit_institution_id}' not found.",
            )
        return explicit_institution_id

    if user_inst_id:
        return user_inst_id

    first_inst = db.query(Institution).filter(Institution.is_active).first()
    return first_inst.id if first_inst else "default_inst"


# --------------------------------------------------------------------------
# Document Ingestion & Lifecycle Management (Admin / Super Admin)
# --------------------------------------------------------------------------

@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload draft institutional document",
)
async def upload_draft_document(
    title: str = Form(...),
    document_code: str = Form(...),
    category: str = Form(...),
    version: str = Form("v1.0"),
    audience: str = Form("ALL"),
    summary: Optional[str] = Form(None),
    institution_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Upload and parse an institutional document into DRAFT status."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    content = await file.read()
    ai_provider = _get_ai_provider()
    service = KnowledgeDocumentService(ai_provider=ai_provider)

    doc = service.create_draft_document(
        db=db,
        institution_id=scoped_institution_id,
        user_id=current_user.id,
        title=title,
        document_code=document_code,
        category=category,
        file_name=file.filename or "uploaded_file.txt",
        file_content=content,
        version=version,
        audience=audience,
        summary=summary,
    )
    return _map_doc_to_response(doc, db)


@router.get(
    "/documents",
    response_model=List[KnowledgeDocumentResponse],
    summary="List institutional documents",
)
def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    audience: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents for the institution."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    docs, _ = service.list_documents(
        db=db,
        institution_id=scoped_institution_id,
        status_filter=status_filter,
        category=category,
        audience=audience,
        skip=skip,
        limit=limit,
    )
    return [_map_doc_to_response(d, db) for d in docs]


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
    summary="Get single document details",
)
def get_document(
    document_id: str,
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details, status, and timeline schedules of a knowledge document."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    doc = service.get_document(db, scoped_institution_id, document_id)
    return _map_doc_to_response(doc, db)


@router.get(
    "/documents/{document_id}/chunks",
    response_model=List[KnowledgeChunkResponse],
    summary="Get document chunks",
)
def get_document_chunks(
    document_id: str,
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all parsed semantic chunks for a document."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    chunks = service.get_document_chunks(db, scoped_institution_id, document_id)
    return [
        KnowledgeChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            section_title=c.section_title,
            page_number=c.page_number,
            content=c.content,
            token_count=c.token_count,
            metadata_json=c.metadata_json,
            created_at=c.created_at,
        )
        for c in chunks
    ]


@router.post(
    "/documents/{document_id}/publish",
    response_model=KnowledgeDocumentResponse,
    summary="Publish draft document version",
)
def publish_document(
    document_id: str,
    payload: KnowledgeDocumentPublish,
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Publish a draft document and schedule its effective range."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    doc = service.publish_document(
        db=db,
        institution_id=scoped_institution_id,
        document_id=document_id,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )
    return _map_doc_to_response(doc, db)


@router.post(
    "/documents/{document_id}/archive",
    response_model=KnowledgeDocumentResponse,
    summary="Archive published document version",
)
def archive_document(
    document_id: str,
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Archive an active document version."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    doc = service.archive_document(db, scoped_institution_id, document_id)
    return _map_doc_to_response(doc, db)


@router.delete(
    "/documents/{document_id}",
    summary="Delete unapproved draft document",
)
def delete_draft_document(
    document_id: str,
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Delete a DRAFT document. Published and archived documents cannot be deleted."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    service = KnowledgeDocumentService()
    service.delete_draft_document(db, scoped_institution_id, document_id)
    return {"detail": "Draft document deleted successfully"}


# --------------------------------------------------------------------------
# PulseAssist Interactive Query Endpoint
# --------------------------------------------------------------------------

@router.post(
    "/query",
    response_model=PulseAssistQueryResponse,
    summary="Submit query to PulseAssist RAG",
)
def query_pulseassist(
    payload: PulseAssistQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process an interactive student or advisor query through the grounded RAG pipeline."""
    ai_provider = _get_ai_provider()
    chat_service = PulseAssistChatService(ai_provider=ai_provider)
    return chat_service.process_query(db, current_user, payload)


# --------------------------------------------------------------------------
# Audit Logging / Telemetry Endpoint
# --------------------------------------------------------------------------

@router.get(
    "/audit-logs",
    summary="List PulseAssist interaction audit logs",
)
def list_ai_audit_logs(
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN", "ADVISOR"])),
):
    """List administrative audit logs for AI interactions."""
    scoped_institution_id = _resolve_caller_institution_id(db, current_user, institution_id)
    logs = db.execute(
        select(AIInteractionLog)
        .where(AIInteractionLog.institution_id == scoped_institution_id)
        .order_by(AIInteractionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "student_context_id": l.student_context_id,
            "interaction_type": l.interaction_type,
            "query_text": l.query_text,
            "response_text": l.response_text,
            "chunks_cited_ids": l.chunks_cited_ids,
            "verified_data_included": l.verified_data_included,
            "prompt_tokens": l.prompt_tokens,
            "completion_tokens": l.completion_tokens,
            "latency_ms": l.latency_ms,
            "ai_provider": l.ai_provider,
            "model_name": l.model_name,
            "created_at": l.created_at,
        }
        for l in logs
    ]
