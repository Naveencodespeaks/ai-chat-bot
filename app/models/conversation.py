# app/models/conversation.py

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import uuid


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    owner_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    assigned_user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="conversations"
    )

    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_user_id],
        back_populates="assigned_conversations"
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
