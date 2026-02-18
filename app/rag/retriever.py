from typing import List
from app.auth.context import UserContext
from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embedding import embed_query

logger = get_logger(__name__)


def retrieve_context(
    *,
    client,
    query: str,
    user_context: UserContext,
    ticket_id: str | None = None,
    top_k: int | None = None,
) -> List[dict]:
    """
    Enterprise RBAC-aware vector retrieval for Mahavir AI HelpDesk.
    """

    if not user_context or not user_context.is_verified:
        raise PermissionError("Unverified user context")

    top_k = top_k or settings.RAG_TOP_K

    # 1️⃣ Embed query
    query_embedding = embed_query(query)

    # 2️⃣ Build RBAC Filters
    filters = {
        "must": [
            {"key": "allowed_roles", "match": {"any": user_context.roles}},
            {"key": "visibility", "match": {"any": user_context.allowed_visibility}},
        ]
    }

    # Department filter (Mahavir HR/IT/Sales/Service separation)
    if user_context.department:
        filters["must"].append(
            {"key": "department", "match": {"value": user_context.department}}
        )

    # Ticket-specific knowledge (VERY IMPORTANT for HelpDesk)
    if ticket_id:
        filters["should"] = [
            {"key": "ticket_id", "match": {"value": ticket_id}}
        ]

    logger.info(
        f"[RAG SEARCH] user={user_context.user_id} "
        f"roles={user_context.roles} "
        f"dept={user_context.department} "
        f"ticket={ticket_id}"
    )

    # 3️⃣ Search Vector DB
    results = client.search(
        collection_name=settings.RAG_COLLECTION,
        query_vector=query_embedding,
        limit=top_k,
        query_filter=filters,
        with_payload=True,
        with_vectors=False,
    )

    logger.info(f"[RAG RESULTS] found={len(results)}")

    return [r.payload for r in results]
