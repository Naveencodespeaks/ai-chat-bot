"""
RAG Retriever Module
Enterprise-ready retrieval with RBAC filtering
"""

from typing import List, Dict, Any, Optional
from app.db.vector import get_qdrant_client
from app.auth.context import UserContext
from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embedding import embed_query

from qdrant_client.http import models as qmodels

logger = get_logger(__name__)


# -------------------------------------------------
# MAIN RETRIEVER
# -------------------------------------------------
def retrieve_context(
    *,
    query: str,
    user_context: UserContext,
    ticket_id: Optional[str] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Enterprise RAG retrieval with RBAC filtering.
    """

    if not user_context or not user_context.is_verified:
        raise PermissionError("Unverified user")

    client = get_qdrant_client()
    top_k = top_k or settings.RAG_TOP_K

    # -------------------------------------------------
    # Embed Query
    # -------------------------------------------------
    query_embedding = embed_query(query)

    # -------------------------------------------------
    # RBAC FILTER
    # -------------------------------------------------
    user_roles = [r.upper() for r in (user_context.roles or [])]
    user_department = getattr(user_context, "department", None)

    is_admin = "ADMIN" in user_roles or "SUPERADMIN" in user_roles

    if is_admin:
        q_filter = None
    else:
        must_conditions = [
            qmodels.FieldCondition(
                key="allowed_roles",
                match=qmodels.MatchAny(any=user_roles),
            ),
            qmodels.FieldCondition(
                key="visibility",
                match=qmodels.MatchAny(any=user_context.allowed_visibility),
            ),
        ]

        if user_department:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="department",
                    match=qmodels.MatchValue(value=user_department),
                )
            )

        should_conditions = []
        if ticket_id:
            should_conditions.append(
                qmodels.FieldCondition(
                    key="ticket_id",
                    match=qmodels.MatchValue(value=ticket_id),
                )
            )

        q_filter = qmodels.Filter(
            must=must_conditions,
            should=should_conditions if should_conditions else None,
        )

    # -------------------------------------------------
    # VECTOR SEARCH
    # -------------------------------------------------
    try:
        response = client.search(
            collection_name=settings.RAG_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=q_filter,
            with_payload=True,
        )

    except Exception as e:
        logger.exception("[RAG] Qdrant search failed")
        raise RuntimeError("Vector search failed") from e

    # -------------------------------------------------
    # Logging
    # -------------------------------------------------
    logger.info(
        f"[RAG SEARCH] user={user_context.user_id} "
        f"roles={user_roles} "
        f"dept={user_department} "
        f"results={len(response)}"
    )

    # -------------------------------------------------
    # Return Payloads
    # -------------------------------------------------
    return [
        {
            "text": r.payload.get("text"),
            "source": r.payload.get("source"),
            "department": r.payload.get("department"),
            "allowed_roles": r.payload.get("allowed_roles"),
            "score": r.score,
        }
        for r in response
    ]
