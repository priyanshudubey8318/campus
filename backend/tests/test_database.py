"""Tests for database connectivity and foundational models."""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def test_audit_log_crud(db_session: Session):
    """Verify that foundational AuditLog model can be written and read from DB."""
    entry = AuditLog(
        action="SYSTEM_INITIALIZE",
        entity_type="SYSTEM",
        entity_id="phase-0",
        actor_id="admin-1",
        actor_role="SUPER_ADMIN",
        details="Phase 0 foundational database initialization.",
        ip_address="127.0.0.1",
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    assert entry.id is not None
    assert len(entry.id) == 36
    assert entry.action == "SYSTEM_INITIALIZE"
    assert entry.actor_role == "SUPER_ADMIN"
    assert entry.created_at is not None
    assert entry.updated_at is not None

    # Query back
    fetched = db_session.query(AuditLog).filter_by(action="SYSTEM_INITIALIZE").first()
    assert fetched is not None
    assert fetched.id == entry.id
    assert fetched.actor_id == "admin-1"
