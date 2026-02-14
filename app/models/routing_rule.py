from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampMixin
from app.db.base import Base


class RoutingRule(Base, TimestampMixin):
    __tablename__ = "routing_rules"

    id: Mapped[int] = mapped_column(primary_key=True)

    keyword: Mapped[str] = mapped_column(String(100), index=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id")
    )

    department = relationship("Department")
