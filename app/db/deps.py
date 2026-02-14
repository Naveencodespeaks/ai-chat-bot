from app.db.session import SessionLocal, Base, engine
from app.core.logging import logger
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
    finally:
        db.close()