# app/db/vector.py

from __future__ import annotations

from qdrant_client import QdrantClient
from app.core.config import settings
from app.core.logging import get_logger
from typing import Optional
from threading import Lock

logger = get_logger(__name__)

_vector_client: Optional[QdrantClient] = None
_lock = Lock()


# -----------------------------
# MAIN CLIENT
# -----------------------------
def get_qdrant_client() -> QdrantClient:
    """
    Thread-safe Singleton Qdrant client.
    Used by RAG Retriever + Ingest + AI Orchestrator.
    """

    global _vector_client

    if _vector_client:
        return _vector_client

    with _lock:
        if _vector_client:
            return _vector_client

        try:
            if settings.QDRANT_URL:
                logger.info(f"[QDRANT] Connecting to remote {settings.QDRANT_URL}")
                _vector_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY or None,
                    timeout=settings.QDRANT_TIMEOUT or 60,
                )
            else:
                logger.info("[QDRANT] Using local storage ./qdrant_data")
                _vector_client = QdrantClient(path="./qdrant_data")

            # Test connection
            _vector_client.get_collections()
            logger.info("[QDRANT] Connection successful")

            return _vector_client

        except Exception as e:
            logger.error(f"[QDRANT] Initialization failed: {e}")
            raise


# -----------------------------
# HEALTH CHECK
# -----------------------------
def qdrant_health_check() -> bool:
    try:
        get_qdrant_client().get_collections()
        return True
    except Exception:
        return False


# -----------------------------
# COLLECTION HELPER
# -----------------------------
def ensure_collection(
    collection_name: str,
    vector_size: int,
    distance: str = "COSINE",
):
    client = get_qdrant_client()

    from qdrant_client.http import models as qmodels

    collections = client.get_collections().collections
    names = {c.name for c in collections}

    if collection_name in names:
        return

    distance_map = {
        "COSINE": qmodels.Distance.COSINE,
        "DOT": qmodels.Distance.DOT,
        "EUCLID": qmodels.Distance.EUCLID,
    }

    client.create_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(
            size=vector_size,
            distance=distance_map.get(distance.upper(), qmodels.Distance.COSINE),
        ),
    )
