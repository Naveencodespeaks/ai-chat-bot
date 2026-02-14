from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from app.db.session import Base
from sqlalchemy import (
    Enum,
    ForeignKey,
    Text,
    String,
    Float,
    DateTime,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampMixin
from app.models.enums import TicketStatus, TicketPriority

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User
    from app.models.department import Department


class Ticket(Base, TimestampMixin):
    """
    Enterprise Ticket Model
    Used for Mahavir AI Helpdesk + WhatsApp Support
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --------------------------------------------------
    # CORE RELATIONS
    # --------------------------------------------------
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 🔥 FIXED → must be STRING because users.id is STRING
    created_by_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_agent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --------------------------------------------------
    # BASIC INFO
    # --------------------------------------------------
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )

    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    # --------------------------------------------------
    # SLA TRACKING
    # --------------------------------------------------
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_response_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    escalation_level: Mapped[int] = mapped_column(default=0)
    reassigned_count: Mapped[int] = mapped_column(default=0)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # --------------------------------------------------
    # ROUTING ANALYTICS
    # --------------------------------------------------
    routing_method: Mapped[Optional[str]] = mapped_column(String(20))
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float)
    ai_predicted_department: Mapped[Optional[str]] = mapped_column(String(100))

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------
    conversation: Mapped["Conversation"] = relationship("Conversation", lazy="joined")

    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="joined",
    )

    assigned_agent: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_agent_id],
        lazy="joined",
    )

    department: Mapped[Optional["Department"]] = relationship("Department", lazy="joined")

    # --------------------------------------------------
    # HELPER PROPERTY
    # --------------------------------------------------
    @property
    def assigned_to_id(self) -> Optional[str]:
        return self.assigned_agent_id

    @assigned_to_id.setter
    def assigned_to_id(self, value: Optional[str]):
        self.assigned_agent_id = value


# --------------------------------------------------
# INDEXES
# --------------------------------------------------
Index("ix_tickets_status_priority", Ticket.status, Ticket.priority)
Index("ix_tickets_agent_status", Ticket.assigned_agent_id, Ticket.status)
Index("ix_tickets_sla_due", Ticket.sla_due_at)
