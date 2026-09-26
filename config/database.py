"""
config/database.py
==================
SQLAlchemy engine and session factory with automatic PostgreSQL / SQLite
fallback support.

Provides:
    - ``engine``          — the SQLAlchemy Engine
    - ``SessionLocal``    — scoped sessionmaker
    - ``get_session()``   — context-manager for a single unit of work
    - ``init_database()`` — runs Alembic migrations and returns True on success
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

def get_db_path() -> str:
    """Resolve the absolute path to the SQLite database to prevent data loss."""
    if getattr(sys, 'frozen', False):
        # Running as compiled PyInstaller executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running in IDE
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "hamza_travels.db")

# ---------------------------------------------------------------------------
# Late import to avoid circular imports (settings → database → settings)
# ---------------------------------------------------------------------------
_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily create and cache the SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    from config.settings import settings

    db_url = settings.active_db_url

    connect_args = {}
    engine_kwargs = {
        "echo": settings.db.echo,
        "future": True,
    }

    if db_url.startswith("sqlite"):
        # Dynamically resolve absolute path so we don't save in PyInstaller's temp folder
        db_path = get_db_path()
        db_url = f"sqlite:///{Path(db_path).as_posix()}"
        
        # SQLite-specific settings
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = 15.0  # Prevent database is locked errors
        engine_kwargs["connect_args"] = connect_args
        logger.info("Database engine: SQLite @ %s (timeout: 15s)", db_path)
    else:
        # PostgreSQL-specific settings
        engine_kwargs["pool_size"] = settings.db.pool_size
        engine_kwargs["max_overflow"] = settings.db.max_overflow
        engine_kwargs["pool_timeout"] = settings.db.pool_timeout
        engine_kwargs["pool_pre_ping"] = True
        logger.info(
            "Database engine: PostgreSQL @ %s:%s/%s",
            settings.db.host,
            settings.db.port,
            settings.db.name,
        )

    _engine = create_engine(db_url, **engine_kwargs)

    # Enable WAL mode for SQLite (better concurrency)
    if db_url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def _get_session_factory():
    """Lazily create and cache the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session.

    Automatically commits on success and rolls back on any exception.
    Always closes the session when done.

    Usage::

        with get_session() as session:
            customer = session.get(Customer, customer_id)
    """
    factory = _get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_factory() -> sessionmaker:
    """Return the session factory (useful for dependency injection)."""
    return _get_session_factory()


def init_database() -> bool:
    """
    Initialise the database by running Alembic migrations.

    Returns True on success, False on failure.
    This is called once during application startup.
    """
    try:
        engine = _get_engine()

        # Test connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified.")

        # Run Alembic migrations
        _run_migrations()
        logger.info("Database initialised successfully.")
        return True

    except OperationalError as exc:
        from config.settings import settings
        if not settings.sqlite.enabled:
            logger.warning(
                "PostgreSQL unavailable (%s). Attempting SQLite fallback...", exc
            )
            return _fallback_to_sqlite()
        logger.error("Database connection failed: %s", exc)
        return False
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Database initialisation failed: %s", exc, exc_info=True)
        return False


def _fallback_to_sqlite() -> bool:
    """Switch to SQLite and reinitialise."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None

    import os
    os.environ["USE_SQLITE_FALLBACK"] = "true"

    # Reload settings singleton (reset it)
    from config import settings as settings_module
    settings_module.settings._load()  # type: ignore[attr-defined]

    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("SQLite fallback activated successfully.")
        _run_migrations()
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("SQLite fallback also failed: %s", exc, exc_info=True)
        return False


def _run_migrations() -> None:
    """Run Alembic migrations programmatically."""
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        from pathlib import Path

        alembic_cfg = AlembicConfig(str(Path(__file__).parent.parent / "alembic.ini"))
        alembic_cfg.set_main_option(
            "sqlalchemy.url", _get_engine().url.render_as_string(hide_password=False)
        )
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied.")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Alembic migration failed (%s) — creating tables directly.", exc)
        _create_tables_directly()


def _create_tables_directly() -> None:
    """
    Fallback: create all tables directly from SQLAlchemy metadata.
    Used when Alembic is not configured yet (first run).
    """
    from core.base_model import Base
    # Import all models so they register with Base.metadata
    import models  # noqa: F401
    Base.metadata.create_all(_get_engine())
    logger.info("All database tables created directly from metadata.")
