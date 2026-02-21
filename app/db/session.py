from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.base import Base
import logging

# --------------------------------------------------
# SAFE SETTINGS
# --------------------------------------------------

DATABASE_URL = settings.DATABASE_URL

# If DEBUG not present in config → default False
DEBUG = getattr(settings, "DEBUG", False)

# --------------------------------------------------
# DATABASE ENGINE
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    future=True,
    pool_pre_ping=True,      # avoid stale connections
    pool_recycle=1800,       # recycle every 30 min
)

# --------------------------------------------------
# SESSION FACTORY
# --------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)

# --------------------------------------------------
# FASTAPI DEPENDENCY
# --------------------------------------------------

def get_db():
    """
    FastAPI dependency.
    Safe DB session handling.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logging.exception("DB Session Error")
        raise
    finally:
        db.close()

# --------------------------------------------------
# OPTIONAL: CREATE TABLES (DEV ONLY)
# --------------------------------------------------

def init_db():
    """
    Create tables manually (DEV only).
    Production → use Alembic.
    """
    Base.metadata.create_all(bind=engine)