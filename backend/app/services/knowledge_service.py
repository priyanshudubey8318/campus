"""Knowledge document management and lifecycle service for Phase 5 PulseAssist."""

import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge import (
    DocumentVersionSchedule,
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.protocols import AIProviderProtocol


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB
CHUNK_TARGET_CHARS = 1800
CHUNK_OVERLAP_CHARS = 200


def _extract_text_from_bytes(file_name: str, content: bytes) -> str:
    """Extract clean text content from file bytes."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _chunk_text(text: str) -> List[Tuple[str, Optional[str]]]:
    """Split text into semantic chunks with section titles and character overlap."""
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

    chunks: List[Tuple[str, Optional[str]]] = []
    current_chunk = ""
    current_title: Optional[str] = None

    for para in paragraphs:
        first_line = para.split("\n")[0].strip()
        is_header = (
            first_line.startswith("#")
            or first_line.upper().startswith("SECTION")
            or first_line.upper().startswith("ITEM")
            or first_line.upper().startswith("RULE")
            or first_line.upper().startswith("GUIDELINE")
            or first_line.upper().startswith("POLICY")
            or first_line.upper().startswith("ARTICLE")
        )
        if is_header:
            if current_chunk:
                chunks.append((current_chunk, current_title))
                current_chunk = ""
            current_title = first_line.lstrip("#").strip()

        if current_chunk:
            if len(current_chunk) + len(para) + 2 <= CHUNK_TARGET_CHARS:
                current_chunk += "\n\n" + para
            else:
                chunks.append((current_chunk, current_title))
                overlap = current_chunk[-CHUNK_OVERLAP_CHARS:] if len(current_chunk) > CHUNK_OVERLAP_CHARS else ""
                current_chunk = (overlap + "\n\n" + para).strip()
        else:
            current_chunk = para

    if current_chunk:
        chunks.append((current_chunk, current_title))

    return chunks if chunks else [("Empty document content", None)]


class KnowledgeDocumentService:
    """Manages knowledge document uploads, chunking, version scheduling, and lifecycles."""

    def __init__(self, ai_provider: Optional[AIProviderProtocol] = None):
        self.ai_provider = ai_provider or MockAIProvider()

    def create_draft_document(
        self,
        db: Session,
        institution_id: str,
        user_id: str,
        title: str,
        document_code: str,
        category: str,
        file_name: str,
        file_content: bytes,
        version: str = "v1.0",
        audience: str = "ALL",
        summary: Optional[str] = None,
    ) -> KnowledgeDocument:
        """Upload and parse an institutional document into DRAFT status with chunks."""
        # 1. Validate file extension and size
        ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {sorted(list(ALLOWED_EXTENSIONS))}",
            )

        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File exceeds maximum allowed size of 25MB ({len(file_content)} bytes).",
            )

        # 2. Check for duplicate version in this institution
        existing = db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.institution_id == institution_id,
                KnowledgeDocument.document_code == document_code,
                KnowledgeDocument.version == version,
            )
        ).scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document '{document_code}' version '{version}' already exists in this institution.",
            )

        # 3. Compute file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # 4. Extract text and generate chunks
        text_content = _extract_text_from_bytes(file_name, file_content)
        chunk_tuples = _chunk_text(text_content)

        # 5. Create draft document record
        doc = KnowledgeDocument(
            institution_id=institution_id,
            title=title,
            document_code=document_code,
            category=category,
            version=version,
            status="DRAFT",
            audience=audience,
            summary=summary,
            file_name=file_name,
            file_hash=file_hash,
            file_size_bytes=len(file_content),
            created_by_user_id=user_id,
        )
        db.add(doc)
        db.flush()

        # 6. Create chunks with dense embeddings and hashes
        for idx, (content_chunk, sec_title) in enumerate(chunk_tuples):
            chunk_hash = hashlib.sha256(content_chunk.encode("utf-8")).hexdigest()
            token_count = max(1, len(content_chunk.split()))
            embedding = self.ai_provider.generate_embedding(content_chunk)

            chunk = KnowledgeChunk(
                document_id=doc.id,
                institution_id=institution_id,
                chunk_index=idx,
                section_title=sec_title,
                content=content_chunk,
                content_hash=chunk_hash,
                token_count=token_count,
                embedding=embedding,
                metadata_json={
                    "document_code": document_code,
                    "title": title,
                    "category": category,
                    "audience": audience,
                    "version": version,
                },
            )
            db.add(chunk)

        db.commit()
        db.refresh(doc)
        return doc

    def publish_document(
        self,
        db: Session,
        institution_id: str,
        document_id: str,
        effective_from: date,
        effective_to: Optional[date] = None,
    ) -> KnowledgeDocument:
        """Publish a DRAFT document and schedule its effective timeline."""
        doc = db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.institution_id == institution_id,
            )
        ).scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document '{document_id}' not found.",
            )

        if doc.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot publish document with status '{doc.status}'. Only DRAFT documents can be published.",
            )

        # Ensure document has chunks
        chunk_count = db.execute(
            select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == doc.id)
        ).scalar() or 0

        if chunk_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot publish a document with 0 chunks.",
            )

        # Validate effective range dates
        if effective_to is not None and effective_to < effective_from:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"effective_to ({effective_to}) cannot precede effective_from ({effective_from}).",
            )

        # Check existing active schedules for this document_code
        active_head = db.execute(
            select(DocumentVersionSchedule).where(
                DocumentVersionSchedule.institution_id == institution_id,
                DocumentVersionSchedule.document_code == doc.document_code,
                DocumentVersionSchedule.is_active == True,
                DocumentVersionSchedule.effective_to.is_(None),
            )
        ).scalar_one_or_none()

        if active_head:
            if effective_from <= active_head.effective_from:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"New schedule effective_from ({effective_from}) must be strictly after "
                        f"existing active head effective_from ({active_head.effective_from})."
                    ),
                )
            # Update existing head's effective_to to cut over cleanly without overlap
            active_head.effective_to = effective_from - timedelta(days=1)
            db.flush()

        # Update document status to PUBLISHED
        doc.status = "PUBLISHED"
        db.flush()

        # Create schedule entry
        schedule = DocumentVersionSchedule(
            institution_id=institution_id,
            document_code=doc.document_code,
            document_id=doc.id,
            version=doc.version,
            effective_from=effective_from,
            effective_to=effective_to,
            is_active=True,
        )
        db.add(schedule)
        db.commit()
        db.refresh(doc)
        return doc

    def archive_document(
        self,
        db: Session,
        institution_id: str,
        document_id: str,
    ) -> KnowledgeDocument:
        """Retire and archive an active PUBLISHED document version."""
        doc = db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.institution_id == institution_id,
            )
        ).scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document '{document_id}' not found.",
            )

        if doc.status != "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot archive document with status '{doc.status}'. Only PUBLISHED documents can be archived.",
            )

        # Deactivate associated active schedules
        schedules = db.execute(
            select(DocumentVersionSchedule).where(
                DocumentVersionSchedule.institution_id == institution_id,
                DocumentVersionSchedule.document_id == doc.id,
                DocumentVersionSchedule.is_active == True,
            )
        ).scalars().all()

        for s in schedules:
            s.is_active = False

        doc.status = "ARCHIVED"
        db.commit()
        db.refresh(doc)
        return doc

    def delete_draft_document(
        self,
        db: Session,
        institution_id: str,
        document_id: str,
    ) -> bool:
        """Delete an unapproved DRAFT document. Published/Archived docs are protected."""
        doc = db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.institution_id == institution_id,
            )
        ).scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document '{document_id}' not found.",
            )

        if doc.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot delete document with status '{doc.status}'. Only DRAFT documents can be deleted.",
            )

        db.delete(doc)
        db.commit()
        return True

    def get_document(
        self,
        db: Session,
        institution_id: str,
        document_id: str,
    ) -> KnowledgeDocument:
        """Retrieve single document with chunks count and schedules."""
        doc = db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.institution_id == institution_id,
            )
        ).scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document '{document_id}' not found.",
            )
        return doc

    def get_document_chunks(
        self,
        db: Session,
        institution_id: str,
        document_id: str,
    ) -> List[KnowledgeChunk]:
        """Retrieve all semantic chunks for a document."""
        chunks = db.execute(
            select(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.institution_id == institution_id,
            ).order_by(KnowledgeChunk.chunk_index.asc())
        ).scalars().all()
        return list(chunks)

    def list_documents(
        self,
        db: Session,
        institution_id: str,
        status_filter: Optional[str] = None,
        category: Optional[str] = None,
        audience: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[KnowledgeDocument], int]:
        """List documents matching filters with pagination."""
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.institution_id == institution_id)

        if status_filter:
            stmt = stmt.where(KnowledgeDocument.status == status_filter)
        if category:
            stmt = stmt.where(KnowledgeDocument.category == category)
        if audience:
            stmt = stmt.where(KnowledgeDocument.audience == audience)

        total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        docs = db.execute(stmt.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit)).scalars().all()
        return list(docs), total
