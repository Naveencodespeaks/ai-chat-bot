from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.ticket import Ticket
from app.models.enums import TicketStatus
from app.actions.notifications import notify_manager
from app.actions.escalation import escalate_ticket
from app.actions.notifications import notify_manager




def check_sla_breach(db: Session):

    now = datetime.utcnow()

    tickets = db.scalars(
        select(Ticket).where(
            Ticket.sla_due_at != None,
            Ticket.status == TicketStatus.OPEN,
            Ticket.sla_due_at < now
        )
    ).all()

    for ticket in tickets:

        ticket.sla_breached = True

        escalate_ticket(db, ticket)
        notify_manager(db, ticket)

    db.commit()

    return len(tickets)
