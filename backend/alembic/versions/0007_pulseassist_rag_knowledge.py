"""0007 PulseAssist RAG Knowledge Subsystem

Revision ID: 0007_pulseassist_rag_knowledge
Revises: 0006_pulserisk_support_prioritization
Create Date: 2026-09-23 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0007_pulseassist_rag_knowledge"
down_revision: Union[str, None] = "0006_pulserisk_support_prioritization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Ensure vector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Safely check if btree_gist is available in PostgreSQL extensions catalog
    conn = op.get_bind()
    has_btree_gist = bool(
        conn.execute(
            sa.text("SELECT 1 FROM pg_available_extensions WHERE name = :name"),
            {"name": "btree_gist"},
        ).scalar()
    )
    if has_btree_gist:
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 1. knowledge_documents table
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_code", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="v1.0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("audience", sa.String(length=32), nullable=False, server_default="ALL"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], name="fk_knowledge_docs_institution", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_knowledge_docs_creator", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "document_code", "version", name="uq_knowledge_doc_code_version_inst"),
        sa.UniqueConstraint("id", "institution_id", name="uq_knowledge_documents_id_institution"),
        sa.UniqueConstraint("id", "institution_id", "document_code", "version", name="uq_knowledge_doc_composite_id_inst_code_ver"),
    )
    op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"], unique=False)
    op.create_index("ix_knowledge_docs_inst_status", "knowledge_documents", ["institution_id", "status"], unique=False)
    op.create_index("ix_knowledge_docs_category", "knowledge_documents", ["institution_id", "category"], unique=False)
    op.create_index("ix_knowledge_docs_audience", "knowledge_documents", ["institution_id", "audience"], unique=False)

    # Trigger: Delete protection on knowledge_documents
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_prevent_published_document_delete()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.status IN ('PUBLISHED', 'ARCHIVED') THEN
            RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Cannot delete % documents. Document history is permanently immutable.', OLD.status;
        END IF;
        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_knowledge_documents_delete_guard
    BEFORE DELETE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_document_delete();
    """)

    # Trigger: Immutability and state machine enforcement on knowledge_documents
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_prevent_published_document_mutation()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.status = 'DRAFT' THEN
            IF NEW.status <> 'DRAFT' AND NEW.status <> 'PUBLISHED' THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Invalid status transition from DRAFT to %. Only PUBLISHED is permitted.', NEW.status;
            END IF;
            IF NEW.status = 'PUBLISHED' THEN
                NEW.published_at := CURRENT_TIMESTAMP;
            END IF;
        ELSIF OLD.status = 'PUBLISHED' THEN
            IF (
                NEW.institution_id <> OLD.institution_id OR
                NEW.title <> OLD.title OR
                NEW.document_code <> OLD.document_code OR
                NEW.category <> OLD.category OR
                NEW.audience <> OLD.audience OR
                (NEW.summary IS DISTINCT FROM OLD.summary) OR
                NEW.file_name <> OLD.file_name OR
                NEW.file_hash <> OLD.file_hash OR
                NEW.file_size_bytes <> OLD.file_size_bytes OR
                NEW.version <> OLD.version OR
                NEW.published_at IS DISTINCT FROM OLD.published_at OR
                NEW.created_by_user_id <> OLD.created_by_user_id OR
                NEW.created_at <> OLD.created_at
            ) THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Published document fields are strictly immutable. Create a new version.';
            END IF;

            IF NEW.status <> OLD.status AND NEW.status <> 'ARCHIVED' THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Invalid status transition from PUBLISHED to %. Only ARCHIVED is permitted.', NEW.status;
            END IF;
            IF NEW.status = 'ARCHIVED' THEN
                NEW.archived_at := CURRENT_TIMESTAMP;
            END IF;
        ELSIF OLD.status = 'ARCHIVED' THEN
            IF (
                NEW.institution_id <> OLD.institution_id OR
                NEW.title <> OLD.title OR
                NEW.document_code <> OLD.document_code OR
                NEW.category <> OLD.category OR
                NEW.audience <> OLD.audience OR
                (NEW.summary IS DISTINCT FROM OLD.summary) OR
                NEW.file_name <> OLD.file_name OR
                NEW.file_hash <> OLD.file_hash OR
                NEW.file_size_bytes <> OLD.file_size_bytes OR
                NEW.version <> OLD.version OR
                NEW.published_at IS DISTINCT FROM OLD.published_at OR
                NEW.archived_at IS DISTINCT FROM OLD.archived_at OR
                NEW.status <> OLD.status
            ) THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Archived documents are permanently immutable and cannot be resurrected or modified.';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_knowledge_documents_immutable
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_document_mutation();
    """)

    # 2. document_version_schedules table
    op.execute("""
    CREATE TABLE document_version_schedules (
        id VARCHAR(36) PRIMARY KEY,
        institution_id VARCHAR(36) NOT NULL,
        document_code VARCHAR(64) NOT NULL,
        document_id VARCHAR(36) NOT NULL,
        version VARCHAR(32) NOT NULL,
        effective_from DATE NOT NULL,
        effective_to DATE NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        effective_range daterange GENERATED ALWAYS AS (
            daterange(effective_from, CASE WHEN effective_to IS NULL THEN NULL ELSE effective_to + 1 END, '[)')
        ) STORED,
        CONSTRAINT fk_doc_schedules_institution FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE RESTRICT,
        CONSTRAINT fk_doc_schedules_doc_composite FOREIGN KEY (document_id, institution_id, document_code, version)
            REFERENCES knowledge_documents(id, institution_id, document_code, version) ON DELETE RESTRICT,
        CONSTRAINT uq_doc_schedules_inst_code_effective_from UNIQUE (institution_id, document_code, effective_from)
    );
    """)

    op.create_index(op.f("ix_document_version_schedules_id"), "document_version_schedules", ["id"], unique=False)
    op.create_index("ix_doc_schedules_inst_code", "document_version_schedules", ["institution_id", "document_code"], unique=False)
    op.create_index(
        "ix_doc_schedules_effective_range",
        "document_version_schedules",
        ["institution_id", "document_code", "effective_from", "effective_to"],
        unique=False,
    )
    op.create_index(
        "uq_doc_schedules_indefinite_head",
        "document_version_schedules",
        ["institution_id", "document_code"],
        unique=True,
        postgresql_where=sa.text("effective_to IS NULL AND is_active = TRUE"),
    )

    if has_btree_gist:
        try:
            op.execute("""
            ALTER TABLE document_version_schedules
            ADD CONSTRAINT ex_doc_schedules_no_overlap EXCLUDE USING gist (
                institution_id WITH =,
                document_code WITH =,
                effective_range WITH &&
            ) WHERE (is_active = TRUE);
            """)
        except Exception:
            pass

    # Trigger: Schedule non-overlap defense-in-depth guard
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_check_schedule_no_overlap()
    RETURNS TRIGGER AS $$
    DECLARE
        overlap_count INTEGER;
    BEGIN
        IF NEW.is_active = TRUE THEN
            SELECT COUNT(*) INTO overlap_count
            FROM document_version_schedules
            WHERE institution_id = NEW.institution_id
              AND document_code = NEW.document_code
              AND is_active = TRUE
              AND id <> COALESCE(NEW.id, '')
              AND daterange(effective_from, CASE WHEN effective_to IS NULL THEN NULL ELSE effective_to + 1 END, '[)') &&
                  daterange(NEW.effective_from, CASE WHEN NEW.effective_to IS NULL THEN NULL ELSE NEW.effective_to + 1 END, '[)');
            IF overlap_count > 0 THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Schedule overlap detected for institution %, document_code %', NEW.institution_id, NEW.document_code;
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_doc_schedules_overlap_guard
    BEFORE INSERT OR UPDATE ON document_version_schedules
    FOR EACH ROW EXECUTE FUNCTION trg_check_schedule_no_overlap();
    """)

    # Trigger: Validate schedule references PUBLISHED document only
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_validate_schedule_document_published()
    RETURNS TRIGGER AS $$
    DECLARE
        doc_status VARCHAR(32);
    BEGIN
        SELECT status INTO doc_status 
        FROM knowledge_documents 
        WHERE id = NEW.document_id AND institution_id = NEW.institution_id;

        IF doc_status IS NULL THEN
            RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Referenced document % does not exist in institution %.', NEW.document_id, NEW.institution_id;
        END IF;

        IF NEW.is_active = TRUE AND doc_status <> 'PUBLISHED' THEN
            RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Cannot schedule document with status %. Only PUBLISHED documents can have active schedules.', doc_status;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_doc_schedules_publish_guard
    BEFORE INSERT OR UPDATE ON document_version_schedules
    FOR EACH ROW EXECUTE FUNCTION trg_validate_schedule_document_published();
    """)

    # 3. knowledge_chunks table
    op.execute("""
    CREATE TABLE knowledge_chunks (
        id VARCHAR(36) PRIMARY KEY,
        document_id VARCHAR(36) NOT NULL,
        institution_id VARCHAR(36) NOT NULL,
        chunk_index INTEGER NOT NULL,
        section_title VARCHAR(255) NULL,
        page_number INTEGER NULL,
        content TEXT NOT NULL,
        content_hash VARCHAR(64) NOT NULL,
        token_count INTEGER NOT NULL,
        tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
        embedding vector(768) NULL,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        CONSTRAINT fk_knowledge_chunks_doc_institution FOREIGN KEY (document_id, institution_id)
            REFERENCES knowledge_documents(id, institution_id) ON DELETE CASCADE,
        CONSTRAINT fk_knowledge_chunks_institution FOREIGN KEY (institution_id)
            REFERENCES institutions(id) ON DELETE RESTRICT,
        CONSTRAINT uq_knowledge_chunk_doc_index UNIQUE (document_id, chunk_index)
    );
    """)

    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_doc_id"), "knowledge_chunks", ["document_id"], unique=False)
    op.execute("CREATE INDEX ix_knowledge_chunks_tsv ON knowledge_chunks USING GIN(tsv);")
    op.execute("CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);")

    # Trigger: Immutability enforcement for chunks of published or archived documents
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_prevent_published_chunk_mutation()
    RETURNS TRIGGER AS $$
    DECLARE
        target_doc_id VARCHAR(36);
        doc_status VARCHAR(32);
    BEGIN
        IF TG_OP = 'INSERT' THEN
            target_doc_id := NEW.document_id;
        ELSE
            target_doc_id := OLD.document_id;
        END IF;

        SELECT status INTO doc_status FROM knowledge_documents WHERE id = target_doc_id;
        
        IF doc_status = 'PUBLISHED' THEN
            IF TG_OP = 'INSERT' THEN
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Cannot insert chunks into an already-PUBLISHED document. Chunks must be created prior to publication.';
            ELSE
                RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Chunks belonging to published documents are strictly immutable and cannot be updated or deleted.';
            END IF;
        ELSIF doc_status = 'ARCHIVED' THEN
            RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Chunks belonging to archived documents are permanently immutable.';
        END IF;

        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_knowledge_chunks_immutable
    BEFORE INSERT OR UPDATE OR DELETE ON knowledge_chunks
    FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_chunk_mutation();
    """)

    # 4. ai_interaction_logs table
    op.create_table(
        "ai_interaction_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("student_context_id", sa.String(length=36), nullable=True),
        sa.Column("interaction_type", sa.String(length=64), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("chunks_cited_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("verified_data_included", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("ai_provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], name="fk_ai_logs_institution", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_logs_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_context_id"], ["student_profiles.id"], name="fk_ai_logs_student", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_interaction_logs_id"), "ai_interaction_logs", ["id"], unique=False)
    op.create_index("ix_ai_logs_inst_user", "ai_interaction_logs", ["institution_id", "user_id"], unique=False)
    op.create_index("ix_ai_logs_student", "ai_interaction_logs", ["student_context_id"], unique=False)
    op.create_index("ix_ai_logs_created", "ai_interaction_logs", ["created_at"], unique=False)


def downgrade() -> None:
    # 4. Drop ai_interaction_logs
    op.drop_index("ix_ai_logs_created", table_name="ai_interaction_logs")
    op.drop_index("ix_ai_logs_student", table_name="ai_interaction_logs")
    op.drop_index("ix_ai_logs_inst_user", table_name="ai_interaction_logs")
    op.drop_index(op.f("ix_ai_interaction_logs_id"), table_name="ai_interaction_logs")
    op.drop_table("ai_interaction_logs")

    # 3. Drop knowledge_chunks
    op.execute("DROP TRIGGER IF EXISTS trg_knowledge_chunks_immutable ON knowledge_chunks;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_published_chunk_mutation();")
    op.drop_table("knowledge_chunks")

    # 2. Drop document_version_schedules
    op.execute("DROP TRIGGER IF EXISTS trg_doc_schedules_publish_guard ON document_version_schedules;")
    op.execute("DROP FUNCTION IF EXISTS trg_validate_schedule_document_published();")
    op.execute("DROP TRIGGER IF EXISTS trg_doc_schedules_overlap_guard ON document_version_schedules;")
    op.execute("DROP FUNCTION IF EXISTS trg_check_schedule_no_overlap();")
    op.drop_index(op.f("ix_document_version_schedules_id"), table_name="document_version_schedules")
    op.drop_table("document_version_schedules")

    # 1. Drop knowledge_documents
    op.execute("DROP TRIGGER IF EXISTS trg_knowledge_documents_immutable ON knowledge_documents;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_published_document_mutation();")
    op.execute("DROP TRIGGER IF EXISTS trg_knowledge_documents_delete_guard ON knowledge_documents;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_published_document_delete();")
    op.drop_index(op.f("ix_knowledge_documents_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
