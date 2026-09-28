"""Pytest fixtures for CampusPulse backend integration tests.

PostgreSQL is the canonical database. All integration tests target the isolated
TEST_DATABASE_URL (e.g. postgresql://postgres:postgres@localhost:5432/campuspulse_test).
Accidental execution against the normal development or production database is strictly guarded against.
"""

import os
import pathlib
import pytest
from typing import Generator
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

# Configure test environment
os.environ["APP_ENV"] = "test"
env_local = pathlib.Path(__file__).resolve().parent.parent.parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)

if "TEST_DATABASE_URL" not in os.environ:
    os.environ["TEST_DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/campuspulse_test"

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.seed import seed_roles_and_permissions
from app.main import app

test_settings = get_settings()
test_settings.validate_test_database_safety()

_embedded_server = None
test_engine = create_engine(
    test_settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _ensure_postgres_engine():
    """Ensure a valid, reachable PostgreSQL test engine is available."""
    global test_engine, TestingSessionLocal, _embedded_server

    # 1. Check if configured TEST_DATABASE_URL is already reachable (e.g. CI or running service)
    try:
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return test_engine
    except Exception:
        pass

    # 2. Automatically launch embedded PostgreSQL if available locally
    try:
        import tempfile
        import pathlib
        import psycopg2
        from pgembed import get_server

        temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="campuspulse_test_pg_"))
        _embedded_server = get_server(temp_dir)
        _embedded_server.ensure_postgres_running()

        admin_uri = _embedded_server.get_uri("postgres")
        conn = psycopg2.connect(admin_uri)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'campuspulse_test';")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE campuspulse_test;")
        cur.close()
        conn.close()

        test_uri = _embedded_server.get_uri("campuspulse_test")
        test_settings.TEST_DATABASE_URL = test_uri
        test_settings.validate_test_database_safety()

        test_engine = create_engine(test_uri, pool_pre_ping=True, echo=False)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        return test_engine
    except Exception as e:
        return test_engine


def is_postgres_available() -> bool:
    """Check whether a PostgreSQL test instance is reachable."""
    try:
        engine = _ensure_postgres_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except (OperationalError, Exception):
        return False


def get_test_session() -> Session:
    """Return a fresh database session targeting the test database."""
    _ensure_postgres_engine()
    return TestingSessionLocal()


@pytest.fixture(scope="session")
def postgres_available() -> bool:
    """Session-level check for PostgreSQL reachability."""
    return is_postgres_available()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(postgres_available: bool):
    """Set up and tear down tables in the PostgreSQL test database."""
    global _embedded_server
    if not postgres_available:
        yield
        return

    # Ensure required PostgreSQL extensions exist in the isolated test database
    try:
        with test_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
    except Exception:
        pass

    # Create tables in the isolated test database
    Base.metadata.create_all(bind=test_engine)

    # Apply Phase 5 triggers and functions for database-level lifecycle & immutability enforcement
    try:
        with test_engine.connect() as conn:
            conn.execute(text("""
            CREATE OR REPLACE FUNCTION trg_prevent_published_document_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.status IN ('PUBLISHED', 'ARCHIVED') THEN
                    RAISE EXCEPTION 'DATABASE INTEGRITY VIOLATION: Cannot delete % documents. Document history is permanently immutable.', OLD.status;
                END IF;
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_knowledge_documents_delete_guard ON knowledge_documents;
            CREATE TRIGGER trg_knowledge_documents_delete_guard
            BEFORE DELETE ON knowledge_documents
            FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_document_delete();

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

            DROP TRIGGER IF EXISTS trg_knowledge_documents_immutable ON knowledge_documents;
            CREATE TRIGGER trg_knowledge_documents_immutable
            BEFORE UPDATE ON knowledge_documents
            FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_document_mutation();

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

            DROP TRIGGER IF EXISTS trg_doc_schedules_overlap_guard ON document_version_schedules;
            CREATE TRIGGER trg_doc_schedules_overlap_guard
            BEFORE INSERT OR UPDATE ON document_version_schedules
            FOR EACH ROW EXECUTE FUNCTION trg_check_schedule_no_overlap();

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

            DROP TRIGGER IF EXISTS trg_doc_schedules_publish_guard ON document_version_schedules;
            CREATE TRIGGER trg_doc_schedules_publish_guard
            BEFORE INSERT OR UPDATE ON document_version_schedules
            FOR EACH ROW EXECUTE FUNCTION trg_validate_schedule_document_published();

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

            DROP TRIGGER IF EXISTS trg_knowledge_chunks_immutable ON knowledge_chunks;
            CREATE TRIGGER trg_knowledge_chunks_immutable
            BEFORE INSERT OR UPDATE OR DELETE ON knowledge_chunks
            FOR EACH ROW EXECUTE FUNCTION trg_prevent_published_chunk_mutation();
            """))
            conn.commit()
    except Exception as e:
        print("Warning applying Phase 5 triggers:", e)

    with TestingSessionLocal() as session:
        seed_roles_and_permissions(session)
    yield
    # Clean up test database
    try:
        Base.metadata.drop_all(bind=test_engine)
    except Exception:
        pass

    if _embedded_server is not None:
        try:
            _embedded_server.cleanup()
        except Exception:
            pass


@pytest.fixture
def db_session(postgres_available: bool) -> Generator[Session, None, None]:
    """Provide an isolated, transactional database session for each test."""
    if not postgres_available:
        pytest.skip(
            f"PostgreSQL test database not reachable at {test_settings.TEST_DATABASE_URL}. "
            "To run integration tests, start PostgreSQL and ensure TEST_DATABASE_URL is accessible."
        )

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(postgres_available: bool) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with database session wired to the test database."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

