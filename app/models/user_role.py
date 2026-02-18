# app/models/user_role.py

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import uuid


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role_name: Mapped[str] = mapped_column(String(100), nullable=False)

    user = relationship("User", back_populates="user_roles")
