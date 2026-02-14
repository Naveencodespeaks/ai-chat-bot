from sqlalchemy import Integer, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampMixin
from app.db.base import Base
from app.models.enums import TicketPriority


class SLAPolicy(Base, TimestampMixin):
    """
    SLA Policy per Department + Priority
    Used by Mahavir AI Helpdesk for response + resolution tracking
    """

    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --------------------------------------------
    # Department
    # --------------------------------------------
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    department = relationship("Department", lazy="joined")

    # --------------------------------------------
    # Priority Level
    # --------------------------------------------
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        nullable=False,
        index=True,
    )

    # --------------------------------------------
    # SLA Timings
    # --------------------------------------------
    first_response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    escalation_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Example:
    # IT + HIGH → response 15min, resolve 2hrs


# Prevent duplicate SLA rules
Index(
    "ix_unique_sla_policy",
    SLAPolicy.department_id,
    SLAPolicy.priority,
    unique=True,
)
