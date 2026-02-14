# app/actions/ai_orchestrator.py

import json
from typing import Any, List, Tuple

from app.core.logging import get_logger
from app.core.policies import PolicyEngine
from app.sentiment.analyzer import analyze_sentiment
from app.rag.retriever import retrieve_context
from app.rag.prompt_builder import build_prompt
from app.llm.client import LLMClient
from app.actions.audit import audit_event

logger = get_logger(__name__)


class AIOrchestrator:
    """
    Central brain of the AI system.
    Handles:
    - RBAC
    - RAG
    - Sentiment
    - LLM
    - Classification
    """

    def __init__(self, llm_client: LLMClient, vector_client):
        self.llm = llm_client
        self.vector_client = vector_client

    # --------------------------------------------------
    # MAIN CHAT FLOW
    # --------------------------------------------------
    async def handle_query(
        self,
        *,
        user_context,
        query: str,
        use_rag: bool = True,
    ) -> str:

        if not user_context or not getattr(user_context, "is_verified", False):
            raise PermissionError("Invalid user")

        PolicyEngine.check_ai_access(user_context)

        sentiment = analyze_sentiment(query)

        context_chunks = []
        if use_rag and PolicyEngine.can_use_rag(user_context):
            context_chunks = retrieve_context(
                client=self.vector_client,
                query=query,
                user_context=user_context,
            )

        prompt = build_prompt(
            query=query,
            context_chunks=context_chunks,
            sentiment=sentiment,
        )

        response = await self.llm.generate(prompt)

        audit_event(
            event_type="AI_QUERY",
            user_id=user_context.user_id,
            role=getattr(user_context, "primary_role", "UNKNOWN"),
            sentiment=str(getattr(sentiment, "label", sentiment)),
            rag_used=bool(context_chunks),
        )

        return response

    # --------------------------------------------------
    # ENTERPRISE CLASSIFIER
    # --------------------------------------------------
    async def classify_department(
        self,
        message: str
    ) -> Tuple[str | None, float]:

        departments = [
            "HR",
            "IT",
            "Finance",
            "Admin",
            "Operations",
            "General"
        ]

        prompt = f"""
You are an enterprise helpdesk classifier.

Classify this message into ONE department:
{departments}

Return STRICT JSON:
{{ "department": "...", "confidence": 0.0 }}

Message:
{message}
"""

        try:
            response = await self.llm.generate(prompt)
            data = json.loads(response)

            dept = data.get("department")
            conf = float(data.get("confidence", 0.0))

            if dept not in departments:
                return None, 0.0

            return dept, max(0.0, min(1.0, conf))

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return None, 0.0
