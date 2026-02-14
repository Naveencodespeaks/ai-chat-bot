# app/actions/audit.py

from app.core.logging import logger
from typing import List, Optional


def audit_event(
    *,
    event_type: str,
    user_id: str,
    role: str,
    sentiment: Optional[str] = None,
    rag_used: bool = False,
    retrieved_docs: Optional[List[str]] = None,
):
    """
    Minimal audit hook.

    For now:
    - logs structured audit information
    Later:
    - can be extended to DB / SIEM / analytics
    """

    logger.info(
        f"AUDIT | event={event_type} "
        f"| user={user_id} "
        f"| role={role} "
        f"| sentiment={sentiment} "
        f"| rag_used={rag_used} "
        f"| docs={retrieved_docs or []}"
    )
