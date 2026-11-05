
"""SQLAlchemy database engine, session management, and table initialization."""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Base

logger = get_logger("database")

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database_url


def _create_engine() -> Engine:
    connect_args = {}

    # SQLite-specific configuration
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=settings.db_echo,
    )


engine: Engine = _create_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db() -> None:
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
