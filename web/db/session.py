"""Database configuration and session management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class DatabaseSettings(BaseSettings):
    """Runtime settings governing database connectivity."""

    database_url: str = "sqlite:///data/app.db"
    echo: bool = False

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


Base = declarative_base()

_engine: Engine | None = None
_session_factory: sessionmaker | None = None


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Return cached database settings."""
    return DatabaseSettings()


def _ensure_sqlite_path(url: URL) -> None:
    """Create the parent directory for SQLite databases if needed."""
    if url.get_backend_name() != "sqlite":
        return
    database_path = url.database
    if database_path in (None, "", ":memory:"):
        return
    Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine instance."""
    global _engine
    if _engine is not None:
        return _engine

    settings = get_database_settings()
    url = make_url(settings.database_url)
    _ensure_sqlite_path(url)

    connect_args = {"check_same_thread": False} if url.get_backend_name() == "sqlite" else {}

    _engine = create_engine(
        url.render_as_string(hide_password=False),
        future=True,
        pool_pre_ping=True,
        echo=settings.echo,
        connect_args=connect_args,
    )
    return _engine


def get_session_factory() -> sessionmaker:
    """Return configured session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


def get_session() -> Generator[Session, None, None]:
    """Provide a database session for request lifecycle scopes."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    """Create database schema if it does not yet exist."""
    # Ensure models are registered with SQLAlchemy metadata before creation.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def reset_database_state() -> None:
    """Reset engine and settings caches (used by tests)."""
    global _engine, _session_factory
    if _session_factory is not None:
        _session_factory.close_all()
    _engine = None
    _session_factory = None
    get_database_settings.cache_clear()
