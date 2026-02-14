from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.message import Message
from app.models.ticket import Ticket
from app.models.enums import TicketPriority, TicketStatus, ConversationStatus
from app.models.conversation import Conversation

# OPTIONAL imports (only if models exist)
try:
    from app.models.audit_log import AuditLog  # adjust path if different
except Exception:  # noqa
    AuditLog = None  # type: ignore

try:
    from app.models.ticket_event import TicketEvent  # adjust path if different
except Exception:  # noqa
    TicketEvent = None  # type: ignore

try:
    from app.models.user import User  # adjust path if different
except Exception:  # noqa
    User = None  # type: ignore


# -----------------------------
# CONFIGURABLE THRESHOLDS
# -----------------------------
STRONG_NEGATIVE_THRESHOLD = -0.6
MODERATE_NEGATIVE_THRESHOLD = -0.4
REPEAT_WINDOW = 3

ESCALATION_KEYWORDS = [
    "complaint",
    "not resolved",
    "need manager",
    "frustrated",
    "escalate",
    "not happy",
    "system not working",
    "salary issue",
    "access denied",
    "data missing",
]


# -----------------------------
# HELPER: Check Keywords
# -----------------------------
def contains_escalation_keywords(text: str) -> bool:
    text_lower = (text or "").lower()
    return any(keyword in text_lower for keyword in ESCALATION_KEYWORDS)


# -----------------------------
# HELPER: Get Last N Messages
# -----------------------------
def get_recent_messages(
    db: Session,
    conversation_id: int,
    limit: int = REPEAT_WINDOW,
) -> List[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


# -----------------------------
# HELPER: Prevent duplicate ticket
# -----------------------------
def ticket_exists(db: Session, conversation_id: int) -> Optional[Ticket]:
    stmt = select(Ticket).where(Ticket.conversation_id == conversation_id)
    return db.scalars(stmt).first()


# -----------------------------
# HELPER: Assign agent (safe fallback)
# -----------------------------
def assign_agent(db: Session) -> Optional[object]:
    """
    Returns a User (agent) if User model exists.
    If you don't have User model or fields yet, returns None safely.
    """
    if User is None:
        return None

    # ✅ Adjust these filters to match your User model fields
    # common patterns:
    #   User.role == "AGENT"
    #   User.is_active == True
    #   User.status == UserStatus.ACTIVE
    conditions = []

    if hasattr(User, "is_active"):
        conditions.append(User.is_active == True)  # noqa: E712

    if hasattr(User, "role"):
        conditions.append(User.role == "AGENT")

    stmt = select(User)
    if conditions:
        stmt = stmt.where(*conditions)

    return db.scalars(stmt).first()


# -----------------------------
# MAIN ESCALATION ENGINE
# -----------------------------
def evaluate_escalation(
    db: Session,
    conversation: Conversation,
    latest_message: Message,
) -> Optional[Ticket]:
    """
    Balanced Enterprise Escalation Logic
    Returns Ticket if escalation triggered, else None
    """
    sentiment = latest_message.sentiment_score or 0

    # 1️⃣ Strong Negative
    if sentiment < STRONG_NEGATIVE_THRESHOLD:
        return create_ticket(
            db,
            conversation,
            reason="Strong negative sentiment detected",
            priority=TicketPriority.HIGH,
        )

    # 2️⃣ Repeated Moderate Negativity
    recent_messages = get_recent_messages(db, conversation.id)

    if len(recent_messages) >= REPEAT_WINDOW:
        avg_sentiment = (
            sum(msg.sentiment_score or 0 for msg in recent_messages) / len(recent_messages)
        )

        if avg_sentiment < MODERATE_NEGATIVE_THRESHOLD:
            return create_ticket(
                db,
                conversation,
                reason="Repeated moderate negative sentiment",
                priority=TicketPriority.MEDIUM,
            )

    # 3️⃣ Keyword Trigger
    if contains_escalation_keywords(latest_message.content):
        return create_ticket(
            db,
            conversation,
            reason="Escalation keyword detected",
            priority=TicketPriority.CRITICAL,
        )

    return None


# -----------------------------
# TICKET CREATION (Enterprise Safe)
# -----------------------------
def create_ticket(
    db: Session,
    conversation: Conversation,
    reason: str,
    priority: TicketPriority,
) -> Ticket:
    # 1️⃣ Prevent duplicate ticket
    existing = ticket_exists(db, conversation.id)
    if existing:
        return existing

    # 2️⃣ Assign agent automatically (if possible)
    agent = assign_agent(db)
    agent_id = getattr(agent, "id", None)

    # 3️⃣ Create ticket
    ticket = Ticket(
        id=uuid.uuid4(),  # if your Ticket.id is int, remove this line
        conversation_id=conversation.id,
        title=f"Auto-Escalated from Conversation {conversation.id}",
        description=reason,
        status=TicketStatus.OPEN,
        priority=priority,
        assigned_to_user_id=agent_id,  # if field doesn't exist, remove it
        sla_due_at=datetime.utcnow() + timedelta(hours=24),  # if field doesn't exist, remove it
        created_at=datetime.utcnow(),
    )

    db.add(ticket)

    # 4️⃣ Update conversation status
    conversation.status = ConversationStatus.ESCALATED

    # 5️⃣ Ticket event log (optional)
    if TicketEvent is not None:
        try:
            event = TicketEvent(
                ticket_id=ticket.id,
                event_type="ESCALATED",
                note=reason,
                created_at=datetime.utcnow(),
            )
            db.add(event)
        except Exception:
            # model exists but fields differ; don't crash startup
            pass

    # 6️⃣ Audit log (optional)
    if AuditLog is not None:
        try:
            audit = AuditLog(
                action="ESCALATE_TICKET",
                entity_type="ticket",
                entity_id=str(ticket.id),
                details={
                    "conversation_id": conversation.id,
                    "priority": getattr(priority, "name", str(priority)),
                    "reason": reason,
                },
                created_at=datetime.utcnow(),
            )
            db.add(audit)
        except Exception:
            pass

    db.commit()
    db.refresh(ticket)
    return ticket


# -----------------------------
# ESCALATE EXISTING TICKET
# -----------------------------
def escalate_ticket(db: Session, ticket: Ticket) -> Ticket:
    """
    Escalates an existing ticket by increasing its priority.
    Used when SLA breach or other escalation conditions are met.
    """
    # Increase priority
    if ticket.priority == TicketPriority.LOW:
        ticket.priority = TicketPriority.MEDIUM
    elif ticket.priority == TicketPriority.MEDIUM:
        ticket.priority = TicketPriority.HIGH
    elif ticket.priority == TicketPriority.HIGH:
        ticket.priority = TicketPriority.CRITICAL
    # CRITICAL stays CRITICAL
    
    # Update status if still open
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.OPEN
    
    db.add(ticket)
    
    # Log escalation event
    if TicketEvent is not None:
        try:
            event = TicketEvent(
                ticket_id=ticket.id,
                event_type="ESCALATED",
                note=f"Ticket escalated to {ticket.priority.name} priority",
                created_at=datetime.utcnow(),
            )
            db.add(event)
        except Exception:
            pass
    
    db.commit()
    db.refresh(ticket)
    return ticket
