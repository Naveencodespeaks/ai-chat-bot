from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ticket import Ticket
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.sentiment_log import SentimentLog
from app.models.routing_rule import RoutingRule
from app.models.department import Department
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.models.chat_log import ChatLog

from app.models.enums import TicketPriority, TicketStatus

from app.core.logging import get_logger

logger = get_logger(__name__)

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_REPEAT_WINDOW_HOURS = 3


def _pick_priority(sentiment_score: Optional[float]) -> TicketPriority:
    """
    Adjust thresholds based on your policy.
    """
    if sentiment_score is None:
        return TicketPriority.MEDIUM
    if sentiment_score <= -0.6:
        return TicketPriority.HIGH
    if sentiment_score <= -0.4:
        return TicketPriority.MEDIUM
    return TicketPriority.LOW


def _resolve_department(
    db: Session,
    conversation: Conversation,
    message_text: str,
) -> Optional[Department]:
    """
    Uses routing_rules to decide which department should get the ticket.

    RoutingRule expected idea:
      - keyword / pattern -> department_id
      - or conversation.department_id if present
    """
    # 1) If your Conversation already tracks department, prefer it
    dept_id = getattr(conversation, "department_id", None)
    if dept_id:
        return db.query(Department).filter(Department.id == dept_id).first()

    # 2) Keyword routing
    text = (message_text or "").lower()
    try:
        rules = db.query(RoutingRule).all()
    except Exception:
        rules = []

    for rule in rules:
        keyword = getattr(rule, "keyword", None) or getattr(rule, "pattern", None)
        if keyword and keyword.lower() in text:
            return db.query(Department).filter(Department.id == rule.department_id).first()

    return None


def _pick_agent_for_department(db: Session, department_id: Optional[str]) -> Optional[str]:
    """
    Picks an agent user_id for a department.
    Strategy: least OPEN tickets assigned to that agent.
    If department_id is None -> pick any agent.
    """
    try:
        agent_role = db.query(Role).filter(func.lower(Role.name) == "agent").first()
        if not agent_role:
            return None

        q = (
            db.query(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .filter(UserRole.role_id == agent_role.id)
        )

        if hasattr(User, "is_active"):
            q = q.filter(User.is_active.is_(True))

        # If your User has department_id, filter by it
        if department_id and hasattr(User, "department_id"):
            q = q.filter(User.department_id == department_id)

        agent_ids = [row[0] for row in q.all()]
        if not agent_ids:
            return None

        # Count open tickets per agent and pick least
        if hasattr(Ticket, "assigned_user_id"):
            counts = (
                db.query(Ticket.assigned_user_id, func.count(Ticket.id))
                .filter(Ticket.status == TicketStatus.OPEN)
                .filter(Ticket.assigned_user_id.in_(agent_ids))
                .group_by(Ticket.assigned_user_id)
                .all()
            )
            count_map = {aid: cnt for aid, cnt in counts}
            agent_ids.sort(key=lambda aid: count_map.get(aid, 0))

        return agent_ids[0]
    except Exception:
        logger.exception("Agent pick failed")
        return None


def _create_chat_log(db: Session, conversation_id: str, event: str, meta: Dict[str, Any]) -> None:
    """
    Writes to chat_logs table (safe).
    """
    try:
        log = ChatLog(
            conversation_id=conversation_id,
            event=event,
            meta=meta,
            created_at=datetime.utcnow(),
        )
        db.add(log)
    except Exception:
        # Schema mismatch? Do not crash.
        logger.exception("Failed to write chat_log (schema mismatch).")


def _get_message_text(message: Message) -> str:
    """
    Supports either `content` or `text` fields.
    """
    return (getattr(message, "content", None) or getattr(message, "text", None) or "").strip()


def evaluate_escalation(db, conversation, message):
    """
    Wrapper used by AI Orchestrator.
    Calls escalate_ticket if needed.
    """
    return escalate_ticket(
        db,
        conversation_id=conversation.id,
        message_id=message.id,
        reason="AI escalation",
        sentiment_score=getattr(message, "sentiment_score", None),
    )



def escalate_ticket(
    db: Session,
    *,
    conversation_id: str,
    message_id: str,
    reason: str = "Auto escalation",
    sentiment_score: Optional[float] = None,
    repeat_window_hours: int = DEFAULT_REPEAT_WINDOW_HOURS,
) -> Tuple[Ticket, bool]:
    """
    Returns (ticket, created_new)

    Prevent duplicate escalation:
      - If an OPEN ticket already exists for this conversation within repeat_window, reuse it.
      - Else create new ticket.
    """

    # ---------- Validate conversation ----------
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise ValueError(f"Conversation not found: {conversation_id}")

    # ---------- Validate message ----------
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise ValueError(f"Message not found: {message_id}")

    now = datetime.utcnow()
    window_start = now - timedelta(hours=repeat_window_hours)

    # ---------- Log sentiment (safe) ----------
    try:
        s = SentimentLog(
            conversation_id=conversation_id,
            message_id=message_id,
            score=sentiment_score,
            label="negative" if (sentiment_score is not None and sentiment_score < 0) else "neutral",
            created_at=now,
        )
        db.add(s)
    except Exception:
        logger.exception("Failed to write sentiment_log (schema mismatch).")

    # ---------- Existing ticket reuse ----------
    existing = (
        db.query(Ticket)
        .filter(Ticket.conversation_id == conversation_id)
        .filter(Ticket.status == TicketStatus.OPEN)
        .filter(Ticket.created_at >= window_start)
        .order_by(Ticket.created_at.desc())
        .first()
    )

    if existing:
        # Update fields safely
        try:
            if hasattr(existing, "priority"):
                existing.priority = _pick_priority(sentiment_score)
            if hasattr(existing, "updated_at"):
                existing.updated_at = now

            if hasattr(existing, "last_message_id"):
                existing.last_message_id = message_id
            if hasattr(existing, "message_id"):
                existing.message_id = message_id

            if hasattr(existing, "reason"):
                prev = getattr(existing, "reason", "") or ""
                existing.reason = f"{prev}; {reason}".strip("; ").strip()

            _create_chat_log(
                db,
                conversation_id,
                "ticket_escalation_reused",
                {"ticket_id": existing.id, "reason": reason},
            )

            db.commit()
            db.refresh(existing)
        except Exception:
            db.rollback()
            logger.exception("Failed to update existing ticket")

        return existing, False

    # ---------- Decide department ----------
    message_text = _get_message_text(message)
    dept = _resolve_department(db, conversation, message_text)

    # ---------- Assign agent ----------
    assigned_user_id = _pick_agent_for_department(db, dept.id if dept else None)

    # ---------- Create new ticket (safe fields) ----------
    ticket = Ticket(
        conversation_id=conversation_id,
        status=TicketStatus.OPEN,
        priority=_pick_priority(sentiment_score),
        created_at=now,
        updated_at=now,
    )

    # Optional fields (only if they exist)
    if hasattr(ticket, "assigned_user_id"):
        ticket.assigned_user_id = assigned_user_id

    if hasattr(ticket, "department_id") and dept:
        ticket.department_id = dept.id

    if hasattr(ticket, "message_id"):
        ticket.message_id = message_id

    if hasattr(ticket, "title"):
        ticket.title = "Auto Escalation"

    if hasattr(ticket, "reason"):
        ticket.reason = reason

    if hasattr(ticket, "source"):
        ticket.source = "chatbot"

    db.add(ticket)

    # ---------- Add chat log ----------
    _create_chat_log(
        db,
        conversation_id,
        "ticket_escalated",
        {"reason": reason, "assigned_user_id": assigned_user_id, "department_id": getattr(dept, "id", None)},
    )

    # ---------- Commit ----------
    try:
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        logger.exception("Failed to create ticket")
        raise

    return ticket, True