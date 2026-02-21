# app/models/conversation.py

from sqlalchemy import String, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import uuid

from app.models.base import Base, TimestampMixin
from app.models.enums import ConversationStatus


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    __table_args__ = (
        Index("idx_conversation_owner", "owner_id"),
        Index("idx_conversation_assigned", "assigned_user_id"),
        Index("idx_conversation_status", "status"),
        Index("idx_conversation_last_message", "last_message_at"),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =============================
    # USER RELATIONS
    # =============================
    owner_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    assigned_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # =============================
    # STATUS
    # =============================
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.OPEN,
        nullable=False,
        index=True
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        default="WHATSAPP"
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    # =============================
    # RELATIONSHIPS
    # =============================
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

    ticket = relationship(
        "Ticket",
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan"
    )