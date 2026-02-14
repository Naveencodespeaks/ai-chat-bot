# app/actions/routing.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.routing_rule import RoutingRule
from app.models.department import Department
from app.models.sla_policy import SLAPolicy
from app.models.ticket import Ticket
from app.models.enums import TicketPriority
from app.actions.ai_orchestrator import AIOrchestrator


AI_CONFIDENCE_THRESHOLD = 0.75


# --------------------------------------------------
# FALLBACK KEYWORD ROUTING
# --------------------------------------------------
def detect_department(db: Session, message_content: str):

    message_lower = message_content.lower()
    rules = db.scalars(select(RoutingRule)).all()

    for rule in rules:
        if rule.keyword.lower() in message_lower:
            return rule.department

    return None


# --------------------------------------------------
# SLA POLICY
# --------------------------------------------------
def apply_sla_policy(db: Session, department_id: int, priority: TicketPriority):

    policy = db.scalar(
        select(SLAPolicy).where(
            SLAPolicy.department_id == department_id,
            SLAPolicy.priority == priority,
        )
    )

    if not policy:
        return None

    return datetime.utcnow() + timedelta(minutes=policy.response_time_minutes)


# --------------------------------------------------
# HYBRID ROUTING ENGINE
# --------------------------------------------------
async def route_ticket(
    db: Session,
    ticket: Ticket,
    message_content: str,
    orchestrator: AIOrchestrator
) -> Ticket:

    chosen_department = None
    routing_method = None
    ai_confidence_value = None
    ai_predicted = None

    # -------------------------------
    # 1️⃣ AI Classification
    # -------------------------------
    ai_department_name, ai_confidence = await orchestrator.classify_department(
        message_content
    )

    ai_predicted = ai_department_name
    ai_confidence_value = ai_confidence

    if ai_department_name and ai_confidence >= AI_CONFIDENCE_THRESHOLD:
        chosen_department = db.scalar(
            select(Department).where(
                Department.name == ai_department_name
            )
        )
        routing_method = "AI"

    # -------------------------------
    # 2️⃣ FALLBACK
    # -------------------------------
    if not chosen_department:
        chosen_department = detect_department(db, message_content)
        if chosen_department:
            routing_method = "FALLBACK"

    # -------------------------------
    # 3️⃣ APPLY SLA
    # -------------------------------
    if chosen_department:
        ticket.department_id = chosen_department.id
        ticket.sla_due_at = apply_sla_policy(
            db,
            chosen_department.id,
            ticket.priority,
        )

    # -------------------------------
    # 4️⃣ ANALYTICS LOGGING
    # -------------------------------
    ticket.routing_method = routing_method
    ticket.ai_confidence = ai_confidence_value
    ticket.ai_predicted_department = ai_predicted

    db.commit()
    db.refresh(ticket)

    return ticket


def apply_sla_policy(db, department_id, priority):

    policy = db.scalar(
        select(SLAPolicy).where(
            SLAPolicy.department_id == department_id,
            SLAPolicy.priority == priority,
        )
    )

    if not policy:
        return None

    return {
        "first_response_due":
            datetime.utcnow() + timedelta(minutes=policy.first_response_minutes),
        "resolution_due":
            datetime.utcnow() + timedelta(minutes=policy.resolution_minutes),
    }
