"""SQLAlchemy database engine, session management, and table initialization."""

from __future__ import annotations

from typing import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
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
    # check_same_thread=False is required for SQLite when using FastAPI with threads
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, echo=settings.db_echo)


def _ensure_mysql_database_exists() -> None:
    """Create the configured MySQL database if it does not exist yet."""
    if not settings.auto_create_database:
        return
    if not SQLALCHEMY_DATABASE_URL.startswith("mysql"):
        return

    parsed = urlparse(SQLALCHEMY_DATABASE_URL)
    db_name = (parsed.path or "").lstrip("/")
    if not db_name:
        return

    admin_db_url = SQLALCHEMY_DATABASE_URL.replace(f"/{db_name}", "/mysql", 1)
    admin_engine = create_engine(admin_db_url, pool_pre_ping=True, echo=settings.db_echo)
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        logger.info("Ensured MySQL database exists", extra={"database": db_name})
    finally:
        admin_engine.dispose()


engine: Engine = _create_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not exist (dev convenience)."""
    _ensure_mysql_database_exists()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized", extra={"db_url": SQLALCHEMY_DATABASE_URL})


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
