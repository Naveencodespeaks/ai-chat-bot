from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampMixin
from app.db.base import Base


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Optional future extension
    manager_id: Mapped[int] = mapped_column(nullable=True)

    tickets = relationship("Ticket", back_populates="department")
    agents = relationship("User", back_populates="department")