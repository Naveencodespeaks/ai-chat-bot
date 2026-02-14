from qdrant_client import QdrantClient
from app.core.config import settings
from app.db.base import Base

def get_vector_client():
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

vector_client = get_vector_client()
