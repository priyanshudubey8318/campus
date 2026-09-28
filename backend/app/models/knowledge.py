"""Knowledge and document models for Phase 5 PulseAssist subsystem.

Includes KnowledgeDocument, DocumentVersionSchedule, and KnowledgeChunk.
Supports strict version immutability, date-range effective scheduling,
and hybrid vector/sparse retrieval.
"""

from datetime import date, datetime, timezone
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    types,
)
from sqlalchemy.dialects.postgresql import DATERANGE, JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql.base import ischema_names
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VectorType(types.UserDefinedType):
    """SQLAlchemy UserDefinedType for PostgreSQL pgvector vector(N)."""

    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__()
        self.dim = dim

    def get_col_spec(self, **kw):
        return f"vector({self.dim})"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return "[" + ",".join(str(float(x)) for x in value) + "]"
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                val_str = value.strip("[] \t\r\n")
                if not val_str:
                    return []
                return [float(x.strip()) for x in val_str.split(",")]
            if isinstance(value, (list, tuple)):
                return list(value)
            return value
        return process


# Register vector type in PostgreSQL dialect schema map for Alembic reflection
ischema_names["vector"] = VectorType


class KnowledgeDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional knowledge document version record.
    
    Status machine: DRAFT -> PUBLISHED -> ARCHIVED.
    PUBLISHED and ARCHIVED documents are permanently immutable and protected
    from direct SQL deletion at the database trigger level.
    """

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "document_code",
            "version",
            name="uq_knowledge_doc_code_version_inst",
        ),
        UniqueConstraint(
            "id",
            "institution_id",
            name="uq_knowledge_documents_id_institution",
        ),
        UniqueConstraint(
            "id",
            "institution_id",
            "document_code",
            "version",
            name="uq_knowledge_doc_composite_id_inst_code_ver",
        ),
        Index("ix_knowledge_docs_inst_status", "institution_id", "status"),
        Index("ix_knowledge_docs_category", "institution_id", "category"),
        Index("ix_knowledge_docs_audience", "institution_id", "audience"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="RESTRICT", name="fk_knowledge_docs_institution"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    audience: Mapped[str] = mapped_column(String(32), nullable=False, default="ALL")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_knowledge_docs_creator"),
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    creator = relationship("User", foreign_keys=[created_by_user_id])
    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index",
    )
    schedules = relationship(
        "DocumentVersionSchedule",
        back_populates="document",
        order_by="DocumentVersionSchedule.effective_from.desc()",
    )


class DocumentVersionSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Effective timeline schedule for published knowledge documents.
    
    Decouples scheduling from document versions, guaranteeing that future versions
    can be published without mutating existing published documents.
    Non-overlap is enforced by database triggers and GiST exclusion constraints.
    """

    __tablename__ = "document_version_schedules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "institution_id", "document_code", "version"],
            ["knowledge_documents.id", "knowledge_documents.institution_id", "knowledge_documents.document_code", "knowledge_documents.version"],
            name="fk_doc_schedules_doc_composite",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "institution_id",
            "document_code",
            "effective_from",
            name="uq_doc_schedules_inst_code_effective_from",
        ),
        Index("ix_doc_schedules_inst_code", "institution_id", "document_code"),
        Index("ix_doc_schedules_effective_range", "institution_id", "document_code", "effective_from", "effective_to"),
        Index(
            "uq_doc_schedules_indefinite_head",
            "institution_id",
            "document_code",
            unique=True,
            postgresql_where=sa.text("effective_to IS NULL AND is_active = TRUE"),
        ),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="RESTRICT", name="fk_doc_schedules_institution"),
        nullable=False,
    )
    document_code: Mapped[str] = mapped_column(String(64), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_range: Mapped[Optional[str]] = mapped_column(
        DATERANGE,
        sa.Computed(
            "daterange(effective_from, CASE WHEN effective_to IS NULL THEN NULL ELSE effective_to + 1 END, '[)')"
        ),
        nullable=True,
    )

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id], overlaps="schedules")
    document = relationship(
        "KnowledgeDocument",
        back_populates="schedules",
        foreign_keys=[document_id],
    )


class KnowledgeChunk(Base, UUIDPrimaryKeyMixin):
    """Semantic chunk with dense vector embedding and tsvector sparse tokens.
    
    Composite foreign key enforces tenant matching with the parent document.
    Chunks of PUBLISHED/ARCHIVED documents cannot be mutated or deleted.
    """

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "institution_id"],
            ["knowledge_documents.id", "knowledge_documents.institution_id"],
            name="fk_knowledge_chunks_doc_institution",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunk_doc_index",
        ),
        Index("ix_knowledge_chunks_doc_id", "document_id"),
        Index("ix_knowledge_chunks_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="RESTRICT", name="fk_knowledge_chunks_institution"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tsv: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        sa.Computed("to_tsvector('english', content)"),
        nullable=True,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(VectorType(768), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    document = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
        foreign_keys=[document_id],
    )
    institution = relationship("Institution", foreign_keys=[institution_id], overlaps="chunks")
