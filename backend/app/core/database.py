"""SQLAlchemy engine, session factory, and database dependency."""

from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .config import get_settings
from .logging import logger
from ..models.base import Base

settings = get_settings()

# Engine creation with sqlite fallback support for tests/local dev
connect_args: Dict[str, Any] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for injecting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Dict[str, Any]:
    """Execute a lightweight query to verify database connectivity."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            return {
                "connected": result == 1,
                "dialect": engine.dialect.name,
                "message": "Database is operational",
            }
    except Exception as exc:
        logger.warning(f"Database connectivity check failed: {exc}")
        return {
            "connected": False,
            "dialect": engine.dialect.name if hasattr(engine, "dialect") else "unknown",
            "message": str(exc),
        }
