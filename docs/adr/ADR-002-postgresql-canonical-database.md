# ADR-002: PostgreSQL as Canonical Relational Database & Alembic Migrations

## Status
Accepted

## Date
2026-09-17

## Context
CampusPulse manages relational institutional entities (users, academic records, attendance, cases, leaves) requiring ACID guarantees, transactional consistency, and complex indexing. The project requires reproducible, auditable database schema versioning across development, testing, and production environments.

## Decision
We select:
- **Canonical Database**: PostgreSQL 16.
- **Migration Framework**: Alembic.
- **ORM**: SQLAlchemy 2.0 with DeclarativeBase.
- **Testing Rule**: All integration tests target an isolated PostgreSQL test database (`TEST_DATABASE_URL`), never the development or production database.

## Alternatives Considered
- **MongoDB / Document Store**: Flexible for ad-hoc records, but poor fit for strictly relational academic enrollments, attendance ledgers, and foreign-key referential integrity required for audit compliance.
- **SQLite for Production**: Insufficient concurrency, lacks native network connection pooling, and does not support PostgreSQL-specific advanced data types (e.g. JSONB, array fields) needed for future multi-signal storage.
- **Manual SQL Scripts / No Migrations**: High risk of schema drift and deployment regressions.

## Consequences
- Strict referential integrity, strong relational data modeling, and robust concurrency.
- Every schema modification requires a tracked, bidirectional Alembic revision script (`upgrade` and `downgrade`).
- Local developers require PostgreSQL (via service or container), and CI requires a PostgreSQL service container.
