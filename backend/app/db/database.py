"""SQLite database engine, session management, and table initialization."""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.db.models import Base

logger = get_logger("database")

# SQLite for development
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"


def _create_engine() -> Engine:
    # check_same_thread=False is required for SQLite when using FastAPI with threads
    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


engine: Engine = _create_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not exist (dev convenience)."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized", extra={"db_url": SQLALCHEMY_DATABASE_URL})


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
