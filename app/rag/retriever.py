from typing import List
from app.auth.context import UserContext
from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embedding import embed_query


logger = get_logger(__name__)

from typing import List
from app.auth.context import UserContext
from app.core.logging import logger
from app.core.config import settings
from app.rag.embedding import embed_query


def retrieve_context(
    *,
    client,
    query: str,
    user_context: UserContext,
) -> List[dict]:
    """
    RBAC-aware, enterprise-safe vector retrieval.
    """

    # 1️⃣ Trust boundary
    if not user_context or not user_context.is_verified:
        raise PermissionError("Unverified user context")

    # 2️⃣ Generate embedding
    query_embedding = embed_query(query)

    # 3️⃣ Build RBAC filters
    filters = {
        "must": [
            {
                "key": "allowed_roles",
                "match": {"any": user_context.roles},
            },
            {
                "key": "visibility",
                "match": {"any": user_context.allowed_visibility},
            },
        ]
    }

    if user_context.department:
        filters["must"].append(
            {
                "key": "department",
                "match": {"value": user_context.department},
            }
        )

    logger.info(
        f"RAG search | user={user_context.user_id} "
        f"| roles={user_context.roles} "
        f"| dept={user_context.department}"
    )

    # 4️⃣ Vector search (RBAC enforced inside DB)
    results = client.search(
        collection_name=settings.RAG_COLLECTION,
        query_vector=query_embedding,
        limit=settings.RAG_TOP_K,
        query_filter=filters,
        with_payload=True,
    )

    return results
