from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.actions.escalation import escalate_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/escalate")
def escalate(
    conversation_id: str,
    message_id: str,
    reason: str = "User requested escalation",
    sentiment_score: float | None = None,
    db: Session = Depends(get_db),
):
    ticket, created_new = escalate_ticket(
        db,
        conversation_id=conversation_id,
        message_id=message_id,
        reason=reason,
        sentiment_score=sentiment_score,
    )
    return {
        "created_new": created_new,
        "ticket_id": ticket.id,
        "status": getattr(ticket, "status", None),
        "priority": getattr(ticket, "priority", None),
        "assigned_user_id": getattr(ticket, "assigned_user_id", None),
    }