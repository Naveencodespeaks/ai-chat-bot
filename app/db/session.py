from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# Use the single Base declared in app.db.base

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Enable echo for debugging purposes
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


