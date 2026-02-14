from sqlalchemy.orm import Session
from app.models.ticket import Ticket


def notify_manager(db: Session, ticket: Ticket):
    """
    Temporary manager notification.
    Later integrate WhatsApp / Email / Slack.
    """
    print(f"[SLA ALERT] Ticket {ticket.id} breached SLA")
