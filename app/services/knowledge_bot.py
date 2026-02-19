# app/services/knowledge_bot.py

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.actions.ai_orchestrator import AIOrchestrator, OrchestratorInput
from app.auth.context import UserContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class CompanyKnowledgeBot:
    """
    Role-Based Company Knowledge Bot

    Uses:
    - RBAC
    - RAG Retrieval
    - AI Orchestrator
    - Sentiment + Ticket escalation
    """

    def __init__(self):
        self.orchestrator = AIOrchestrator(system_prompt_name="support")

    def ask(
        self,
        db: Session,
        user: UserContext,
        message: str,
        conversation_id: Optional[str] = None,
        channel: str = "web",
    ) -> Dict[str, Any]:

        logger.info(
            f"[KNOWLEDGE BOT] user={user.user_id} "
            f"roles={user.roles} dept={user.department}"
        )

        data = OrchestratorInput(
            user_id=user.user_id,
            user_email=f"{user.user_id}@mahavir.local",
            user_roles=user.roles,
            department=user.department,
            message=message,
            conversation_id=conversation_id,
            channel=channel,
        )

        result = self.orchestrator.run(db=db, data=data)

        return {
            "reply": result.reply,
            "sentiment": result.sentiment_label,
            "retrieved_chunks": result.retrieved_chunks,
            "ticket_id": result.ticket_id,
            "escalated": result.escalated,
        }
