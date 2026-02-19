# # app/actions/ai_orchestrator.py

# from __future__ import annotations

# from app.auth.context import UserContext


# from dataclasses import dataclass
# from typing import Any, Dict, List, Optional
# from datetime import datetime, timezone

# from sqlalchemy.orm import Session

# from app.core.logging import get_logger
# from app.core.policies import PolicyEngine

# from app.sentiment.analyzer import analyze_sentiment
# from app.rag.retriever import retrieve_context
# from app.rag.prompt_builder import build_prompt

# # ✅ FIX: use your real client entrypoint + prompts
# from app.llm.client import get_llm_client, SYSTEM_PROMPTS, BaseLLMClient
# from app.llm.guardrails import enforce_guardrails

# from app.actions.audit import audit_event
# from app.actions.ticketing import create_ticket_if_needed
# from app.actions.escalation import escalate_ticket_if_needed

# from app.models.chat_log import ChatLog
# from app.models.ticket import Ticket

# logger = get_logger(__name__)


# # -----------------------------
# # INPUT / OUTPUT DTOs
# # -----------------------------
# @dataclass
# class OrchestratorInput:
#     user_id: str
#     user_email: str
#     user_roles: List[str]
#     department: str
#     message: str
#     conversation_id: Optional[str] = None
#     channel: str = "web"  # web / whatsapp / api / etc.
#     metadata: Optional[Dict[str, Any]] = None


# @dataclass
# class OrchestratorOutput:
#     reply: str
#     sentiment_score: float
#     sentiment_label: str
#     retrieved_chunks: int
#     policy_flags: List[str]
#     ticket_id: Optional[int] = None
#     escalated: bool = False


# # -----------------------------
# # ORCHESTRATOR
# # -----------------------------
# class AIOrchestrator:
#     """
#     Central brain of the AI system.
#     Pipeline:
#       1) Policy checks
#       2) Sentiment analysis
#       3) Role-based RAG retrieval
#       4) Prompt build
#       5) LLM call (+ guardrails)
#       6) Ticketing / escalation
#       7) Audit + DB chat logging
#     """

#     def __init__(
#         self,
#         llm_client: Optional[BaseLLMClient] = None,
#         policy_engine: Optional[PolicyEngine] = None,
#         system_prompt_name: str = "support",  # support/technical/assistant/sales
#     ) -> None:
#         self.llm = llm_client or get_llm_client()
#         self.policy = policy_engine or PolicyEngine()
#         self.system_prompt_name = system_prompt_name

#     def run(self, db: Session, data: OrchestratorInput) -> OrchestratorOutput:
#         started_at = datetime.now(timezone.utc)

#         meta = data.metadata or {}
#         meta.setdefault("channel", data.channel)
#         meta.setdefault("conversation_id", data.conversation_id)

#         user_ctx = {
#             "user_id": data.user_id,
#             "email": data.user_email,
#             "roles": data.user_roles or [],
#             "department": data.department or "General",
#             "conversation_id": data.conversation_id,
#             "channel": data.channel,
#         }

#         text = (data.message or "").strip()
#         if not text:
#             return OrchestratorOutput(
#                 reply="Please type your question so I can help you.",
#                 sentiment_score=0.0,
#                 sentiment_label="neutral",
#                 retrieved_chunks=0,
#                 policy_flags=["empty_message"],
#             )

#         # 1) POLICY
#         policy_flags = self.policy.evaluate_input(text=text, user_context=user_ctx)

#         if "blocked" in policy_flags:
#             reply = "Sorry, I can’t help with that request."
#             self._safe_audit_and_log(
#                 db=db,
#                 user_ctx=user_ctx,
#                 user_text=text,
#                 assistant_text=reply,
#                 policy_flags=policy_flags,
#                 sentiment={"score": 0.0, "label": "neutral"},
#                 retrieved=[],
#                 meta=meta,
#                 started_at=started_at,
#                 error=None,
#             )
#             return OrchestratorOutput(
#                 reply=reply,
#                 sentiment_score=0.0,
#                 sentiment_label="neutral",
#                 retrieved_chunks=0,
#                 policy_flags=policy_flags,
#             )

#         # 2) SENTIMENT
#         sentiment = analyze_sentiment(text)
#         sentiment_score = float(sentiment.get("score", 0.0))
#         sentiment_label = str(sentiment.get("label", "neutral"))

#         # 3) ROLE-BASED RAG RETRIEVAL
#         retrieved: List[Dict[str, Any]] = []
#         try:
#             client = get_qdrant_client()
#             user_context = UserContext(
#                 user_id=user_ctx["user_id"],
#                 roles=user_ctx["roles"],
#                 department=user_ctx["department"],
#                 allowed_visibility=["internal"],  # change if needed
#                 is_verified=True,
#             )
#             retrieved = retrieve_context(
#                 client=client,
#                 query=text,
#                 user_context=user_context,
#                 ticket_id=user_ctx.get("conversation_id"),
#                 top_k=6,
#             )
#             #     user_id=user_ctx["user_id"],
#             # retrieved = retrieve_context(
#             #     db=db,
#             #     query=text,
#             #     user_roles=user_ctx["roles"],
#             #     department=user_ctx["department"],
#             #     top_k=6,
#             # )
#         except Exception:
#             logger.exception("RAG retrieval failed")
#             policy_flags.append("rag_retrieval_failed")
#             retrieved = []

#         # 4) PROMPT BUILD
#         prompt = build_prompt(
#             user_message=text,
#             retrieved=retrieved,
#             user_context=user_ctx,
#             sentiment=sentiment,
#         )

#         # 5) LLM CALL (✅ aligned to your client.py)
#         system_prompt = SYSTEM_PROMPTS.get(self.system_prompt_name, SYSTEM_PROMPTS["assistant"])

#         try:
#             raw_reply = self.llm.generate(
#                 prompt,
#                 system_prompt=system_prompt,
#                 use_cache=True,
#             )
#         except Exception:
#             logger.exception("LLM generation failed")
#             raw_reply = (
#                 "I’m facing a temporary issue while generating a response. "
#                 "Please try again in a minute."
#             )
#             policy_flags.append("llm_failed")

#         # Guardrails
#         safe_reply, guardrail_flags = enforce_guardrails(
#             user_message=text,
#             assistant_message=raw_reply,
#             user_context=user_ctx,
#         )
#         policy_flags.extend(list(set(guardrail_flags)))

#         # 6) Ticket + Escalation
#         ticket_id: Optional[str] = None
#         escalated = False

#         try:
#             ticket: Optional[Ticket] = create_ticket_if_needed(
#                 db=db,
#                 user_id=user_ctx["user_id"],
#                 user_message=text,
#                 assistant_message=safe_reply,
#                 sentiment_score=sentiment_score,
#                 sentiment_label=sentiment_label,
#                 conversation_id=user_ctx["conversation_id"],
#                 policy_flags=policy_flags,
#             )
#             ticket_id: Optional[int] = None
#             if ticket:
#                 ticket_id = ticket.id

#             escalated = escalate_ticket_if_needed(
#                 db=db,
#                 user_id=user_ctx["user_id"],
#                 user_message=text,
#                 sentiment_score=sentiment_score,
#                 policy_flags=policy_flags,
#                 conversation_id=user_ctx["conversation_id"],
#                 ticket_id=ticket_id,
#             )
#         except Exception:
#             logger.exception("Ticket/escalation action failed")
#             policy_flags.append("action_failed")

#         # 7) AUDIT + CHAT LOG
#         self._safe_audit_and_log(
#             db=db,
#             user_ctx=user_ctx,
#             user_text=text,
#             assistant_text=safe_reply,
#             policy_flags=policy_flags,
#             sentiment={"score": sentiment_score, "label": sentiment_label},
#             retrieved=retrieved,
#             meta=meta,
#             started_at=started_at,
#             error=None,
#             ticket_id=ticket_id,
#             escalated=escalated,
#         )

#         return OrchestratorOutput(
#             reply=safe_reply,
#             sentiment_score=sentiment_score,
#             sentiment_label=sentiment_label,
#             retrieved_chunks=len(retrieved or []),
#             policy_flags=sorted(list(set(policy_flags))),
#             ticket_id=ticket_id,
#             escalated=escalated,
#         )



#     def _safe_audit_and_log(
#         self,
#         db: Session,
#         user_ctx: Dict[str, Any],
#         user_text: str,
#         assistant_text: str,
#         policy_flags: List[str],
#         sentiment: Dict[str, Any],
#         retrieved: List[Dict[str, Any]],
#         meta: Dict[str, Any],
#         started_at: datetime,
#         error: Optional[str],
#         ticket_id: Optional[str] = None,
#         escalated: bool = False,
#     ) -> None:
#         try:
#             # ====================================================
#             # 1️⃣ AUDIT LOG  (match your audit.py signature)
#             # ====================================================
#             audit_event(
#                 event_type="ai_chat",
#                 user_id=user_ctx["user_id"],
#                 role=",".join(user_ctx.get("roles", [])),
#                 sentiment=sentiment.get("label"),
#                 rag_used=len(retrieved or []) > 0,
#                 retrieved_docs=[r.get("source") for r in retrieved] if retrieved else [],
#             )

#             # ====================================================
#             # 2️⃣ CHAT LOG  (match your ChatLog model exactly)
#             # ====================================================
#             chat_row = ChatLog(
#                 user_id=user_ctx["user_id"],
#                 ticket_id=int(ticket_id) if ticket_id else 0,   # ⚠️ see note below
#                 message=user_text,
#                 response=assistant_text,
#             )

#             db.add(chat_row)
#             db.commit()

#         except Exception:
#             db.rollback()
#             logger.exception("Audit/chat logging failed")




# app/actions/ai_orchestrator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import concurrent.futures
import inspect

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.policies import PolicyEngine

from app.sentiment.analyzer import analyze_sentiment
from app.rag.retriever import retrieve_context
from app.rag.prompt_builder import build_prompt

# LLM + guardrails
from app.llm.client import get_llm_client, SYSTEM_PROMPTS, BaseLLMClient
from app.llm.guardrails import enforce_guardrails

# Actions
from app.actions.audit import audit_event
from app.actions.ticketing import create_ticket_if_needed
from app.actions.escalation import escalate_ticket_if_needed

# Models
from app.models.chat_log import ChatLog
from app.models.ticket import Ticket

# Auth
from app.auth.context import UserContext

logger = get_logger(__name__)


# -----------------------------
# INPUT / OUTPUT DTOs
# -----------------------------
@dataclass
class OrchestratorInput:
    user_id: str
    user_email: str
    user_roles: List[str]
    department: str
    message: str
    conversation_id: Optional[str] = None
    channel: str = "web"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OrchestratorOutput:
    reply: str
    sentiment_score: float
    sentiment_label: str
    retrieved_chunks: int
    policy_flags: List[str]
    ticket_id: Optional[int] = None
    escalated: bool = False


# -----------------------------
# ORCHESTRATOR
# -----------------------------
class AIOrchestrator:
    """
    Central brain of the AI system.

    Pipeline:
      1) Policy checks
      2) Sentiment analysis
      3) Role-based RAG retrieval
      4) Prompt build
      5) LLM call (+ guardrails)
      6) Ticketing / escalation
      7) Audit + DB chat logging
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        policy_engine: Optional[PolicyEngine] = None,
        system_prompt_name: str = "support",
        llm_timeout_seconds: int = 30,
        rag_top_k: int = 6,
    ) -> None:
        self.llm = llm_client or get_llm_client()
        self.policy = policy_engine or PolicyEngine()
        self.system_prompt_name = system_prompt_name
        self.llm_timeout_seconds = llm_timeout_seconds
        self.rag_top_k = rag_top_k

    def run(self, db: Session, data: OrchestratorInput) -> OrchestratorOutput:
        started_at = datetime.now(timezone.utc)

        meta = dict(data.metadata or {})
        meta.setdefault("channel", data.channel)
        meta.setdefault("conversation_id", data.conversation_id)

        user_ctx: Dict[str, Any] = {
            "user_id": data.user_id,
            "email": data.user_email,
            "roles": data.user_roles or [],
            "department": (data.department or "GENERAL"),
            "conversation_id": data.conversation_id,
            "channel": data.channel,
        }

        text = (data.message or "").strip()
        if not text:
            return OrchestratorOutput(
                reply="Please type your question so I can help you.",
                sentiment_score=0.0,
                sentiment_label="neutral",
                retrieved_chunks=0,
                policy_flags=["empty_message"],
            )

        # 1) POLICY
        policy_flags = self._safe_policy_evaluate(text=text, user_ctx=user_ctx)
        if "blocked" in policy_flags:
            reply = "Sorry, I can’t help with that request."
            self._safe_audit_and_log(
                db=db,
                user_ctx=user_ctx,
                user_text=text,
                assistant_text=reply,
                policy_flags=policy_flags,
                sentiment={"score": 0.0, "label": "neutral"},
                retrieved=[],
                meta=meta,
                started_at=started_at,
                error=None,
                ticket_id=None,
                escalated=False,
            )
            return OrchestratorOutput(
                reply=reply,
                sentiment_score=0.0,
                sentiment_label="neutral",
                retrieved_chunks=0,
                policy_flags=sorted(list(set(policy_flags))),
            )

        # 2) SENTIMENT
        sentiment = self._safe_sentiment(text)
        sentiment_score = float(sentiment.get("score", 0.0))
        sentiment_label = str(sentiment.get("label", "neutral"))

        # 3) ROLE-BASED RAG RETRIEVAL
        retrieved: List[Dict[str, Any]] = []
        try:
            user_context = UserContext(
                user_id=user_ctx["user_id"],
                roles=[str(r).upper() for r in (user_ctx.get("roles") or [])],
                department=str(user_ctx.get("department") or "GENERAL").upper(),
                allowed_visibility=["INTERNAL"],  # must match ingest payload casing
                is_verified=True,
            )

            retrieved = self._call_retrieve_context(
                query=text,
                user_context=user_context,
                ticket_id=user_ctx.get("conversation_id"),
                top_k=self.rag_top_k,
            )
        except Exception:
            logger.exception("RAG retrieval failed")
            policy_flags.append("rag_retrieval_failed")
            retrieved = []

        # 4) PROMPT BUILD (signature-safe)
        prompt = self._call_build_prompt(
            user_message=text,
            retrieved=retrieved,
            user_context=user_ctx,
            sentiment={"score": sentiment_score, "label": sentiment_label},
        )

        # 5) LLM CALL
        system_prompt = SYSTEM_PROMPTS.get(
            self.system_prompt_name,
            SYSTEM_PROMPTS.get("assistant", ""),
        )

        raw_reply = self._safe_llm_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            policy_flags=policy_flags,
        )

        # Guardrails
        safe_reply, guardrail_flags = enforce_guardrails(
            user_message=text,
            assistant_message=raw_reply,
            user_context=user_ctx,
        )
        policy_flags.extend(list(set(guardrail_flags or [])))

        # 6) Ticket + Escalation
        ticket_id: Optional[int] = None
        escalated = False

        try:
            ticket: Optional[Ticket] = create_ticket_if_needed(
                db=db,
                user_id=user_ctx["user_id"],
                user_message=text,
                assistant_message=safe_reply,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                conversation_id=user_ctx.get("conversation_id"),
                policy_flags=policy_flags,
            )

            if ticket is not None and getattr(ticket, "id", None) is not None:
                ticket_id = int(ticket.id)

            escalated = bool(
                escalate_ticket_if_needed(
                    db=db,
                    user_id=user_ctx["user_id"],
                    user_message=text,
                    sentiment_score=sentiment_score,
                    policy_flags=policy_flags,
                    conversation_id=user_ctx.get("conversation_id"),
                    ticket_id=ticket_id,
                )
            )
        except Exception:
            logger.exception("Ticket/escalation action failed")
            policy_flags.append("action_failed")

        # 7) AUDIT + CHAT LOG
        self._safe_audit_and_log(
            db=db,
            user_ctx=user_ctx,
            user_text=text,
            assistant_text=safe_reply,
            policy_flags=policy_flags,
            sentiment={"score": sentiment_score, "label": sentiment_label},
            retrieved=retrieved,
            meta=meta,
            started_at=started_at,
            error=None,
            ticket_id=ticket_id,
            escalated=escalated,
        )

        return OrchestratorOutput(
            reply=safe_reply,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            retrieved_chunks=len(retrieved or []),
            policy_flags=sorted(list(set(policy_flags))),
            ticket_id=ticket_id,
            escalated=escalated,
        )

    # -----------------------------
    # INTERNAL HELPERS
    # -----------------------------
    def _safe_policy_evaluate(self, *, text: str, user_ctx: Dict[str, Any]) -> List[str]:
        try:
            flags = self.policy.evaluate_input(text=text, user_context=user_ctx)
            if not isinstance(flags, list):
                return []
            return [str(f) for f in flags]
        except Exception:
            logger.exception("Policy engine failed")
            return ["policy_engine_failed"]

    def _safe_sentiment(self, text: str) -> Dict[str, Any]:
        try:
            s = analyze_sentiment(text)
            return s if isinstance(s, dict) else {"score": 0.0, "label": "neutral"}
        except Exception:
            logger.exception("Sentiment failed")
            return {"score": 0.0, "label": "neutral"}

    def _safe_llm_generate(self, *, prompt: str, system_prompt: str, policy_flags: List[str]) -> str:
        """
        Calls llm.generate safely with timeout.
        Handles common generate() signatures.
        """
        def _call() -> str:
            sig = inspect.signature(self.llm.generate)
            kwargs: Dict[str, Any] = {}
            if "system_prompt" in sig.parameters:
                kwargs["system_prompt"] = system_prompt
            if "use_cache" in sig.parameters:
                kwargs["use_cache"] = True
            return self.llm.generate(prompt, **kwargs)  # type: ignore[arg-type]

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_call)
                return fut.result(timeout=self.llm_timeout_seconds)
        except Exception:
            logger.exception("LLM generation failed/timeout")
            policy_flags.append("llm_failed")
            return (
                "I’m facing a temporary issue while generating a response. "
                "Please try again in a minute."
            )

    def _call_retrieve_context(
        self,
        *,
        query: str,
        user_context: UserContext,
        ticket_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Supports both retriever signatures:
          retrieve_context(query=..., user_context=..., ticket_id=..., top_k=...)
          retrieve_context(client=..., query=..., user_context=..., ticket_id=..., top_k=...)
        """
        sig = inspect.signature(retrieve_context)
        kwargs: Dict[str, Any] = {
            "query": query,
            "user_context": user_context,
            "ticket_id": ticket_id,
            "top_k": top_k,
        }

        if "client" in sig.parameters:
            from app.db.vector import get_qdrant_client
            kwargs["client"] = get_qdrant_client()

        return retrieve_context(**kwargs)  # type: ignore[misc]

    def _call_build_prompt(
        self,
        *,
        user_message: str,
        retrieved: List[Dict[str, Any]],
        user_context: Dict[str, Any],
        sentiment: Dict[str, Any],
    ) -> str:
        """
        Signature-safe prompt builder call (prevents runtime errors if build_prompt changes).
        """
        try:
            sig = inspect.signature(build_prompt)
            kwargs: Dict[str, Any] = {}

            if "user_message" in sig.parameters:
                kwargs["user_message"] = user_message
            if "retrieved" in sig.parameters:
                kwargs["retrieved"] = retrieved
            if "user_context" in sig.parameters:
                kwargs["user_context"] = user_context
            if "sentiment" in sig.parameters:
                kwargs["sentiment"] = sentiment

            # If build_prompt has fewer params, this will still work
            return build_prompt(**kwargs)  # type: ignore[misc]
        except Exception:
            logger.exception("Prompt build failed; using fallback prompt")
            # Safe fallback prompt (no hallucinations; uses only retrieved text)
            context_text = "\n\n".join([(r.get("text") or "") for r in (retrieved or [])]).strip()
            return (
                "You are Mahavir Group HelpDesk AI.\n"
                "Answer using ONLY the provided CONTEXT. If context is missing, say you don’t know.\n\n"
                f"CONTEXT:\n{context_text}\n\n"
                f"QUESTION:\n{user_message}\n"
            )

    def _safe_audit_and_log(
        self,
        *,
        db: Session,
        user_ctx: Dict[str, Any],
        user_text: str,
        assistant_text: str,
        policy_flags: List[str],
        sentiment: Dict[str, Any],
        retrieved: List[Dict[str, Any]],
        meta: Dict[str, Any],
        started_at: datetime,
        error: Optional[str],
        ticket_id: Optional[int],
        escalated: bool,
    ) -> None:
        """
        Best-effort audit + chat logging. Never breaks the main request.
        """

        # 1) AUDIT (signature-safe)
        try:
            sig = inspect.signature(audit_event)
            kwargs: Dict[str, Any] = {}

            # Fill only what audit_event supports in YOUR code
            if "event_type" in sig.parameters:
                kwargs["event_type"] = "ai_chat"
            if "user_id" in sig.parameters:
                kwargs["user_id"] = user_ctx.get("user_id")
            if "role" in sig.parameters:
                kwargs["role"] = ",".join([str(r) for r in (user_ctx.get("roles") or [])])
            if "sentiment" in sig.parameters:
                kwargs["sentiment"] = str(sentiment.get("label", "neutral"))
            if "rag_used" in sig.parameters:
                kwargs["rag_used"] = bool(len(retrieved or []) > 0)
            if "retrieved_docs" in sig.parameters:
                kwargs["retrieved_docs"] = [r.get("source") for r in retrieved] if retrieved else []

            audit_event(**kwargs)  # type: ignore[misc]
        except Exception:
            logger.exception("Audit event failed")

        # 2) CHAT LOG (best effort)
        try:
            chat_kwargs: Dict[str, Any] = {}

            # Build kwargs only for fields that exist in ChatLog model
            cols = getattr(ChatLog, "__table__").columns  # type: ignore[attr-defined]

            if "user_id" in cols:
                chat_kwargs["user_id"] = user_ctx.get("user_id")
            if "ticket_id" in cols:
                chat_kwargs["ticket_id"] = ticket_id  # keep None if nullable
            if "message" in cols:
                chat_kwargs["message"] = user_text
            if "response" in cols:
                chat_kwargs["response"] = assistant_text

            # Optional extra columns if you have them
            if "created_at" in cols:
                chat_kwargs["created_at"] = datetime.now(timezone.utc)
            if "meta" in cols:
                chat_kwargs["meta"] = meta

            chat_row = ChatLog(**chat_kwargs)
            db.add(chat_row)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Chat logging failed")
