# app/db/vector.py

from __future__ import annotations

from qdrant_client import QdrantClient
from app.core.config import settings
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)

_vector_client: Optional[QdrantClient] = None


# -----------------------------
# MAIN CLIENT
# -----------------------------
def get_qdrant_client() -> QdrantClient:
    """
    Singleton Qdrant client for Mahavir AI RAG system.
    Safe for high-load enterprise usage.
    """

    global _vector_client

    if _vector_client is not None:
        return _vector_client

    try:
        if settings.QDRANT_URL:
            logger.info(f"[QDRANT] Connecting to remote: {settings.QDRANT_URL}")
            _vector_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=60,
            )
        else:
            # Local dev mode
            logger.info("[QDRANT] Using local storage ./qdrant_data")
            _vector_client = QdrantClient(path="./qdrant_data")

        # Test connection
        try:
            _vector_client.get_collections()
            logger.info("[QDRANT] Connection successful")
        except Exception as e:
            logger.warning(f"[QDRANT] Connection test failed: {e}")

        return _vector_client

    except Exception as e:
        logger.error(f"[QDRANT] Failed to initialize client: {e}")
        raise


# -----------------------------
# COLLECTION HELPER
# -----------------------------
def ensure_collection(collection_name: str, vector_size: int):
    """
    Ensure collection exists.
    Used by rag/ingest.py
    """

    client = get_qdrant_client()

    try:
        collections = client.get_collections().collections
        names = {c.name for c in collections}

        if collection_name in names:
            return

        from qdrant_client.http import models as qmodels

        logger.info(
            f"[QDRANT] Creating collection={collection_name} vector_size={vector_size}"
        )

        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )

    except Exception as e:
        logger.error(f"[QDRANT] Error ensuring collection: {e}")
        raise
