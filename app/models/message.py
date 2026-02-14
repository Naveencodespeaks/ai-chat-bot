from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Text, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin
from app.models.enums import SenderType

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User


class Message(Base, TimestampMixin):
    """
    Represents a single message within a conversation.
    Can be sent by USER, BOT, AGENT, or SYSTEM.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, name="sender_type"),
        nullable=False,
        index=True,
    )

    # Nullable because BOT/SYSTEM may not have a user ID
    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Sentiment analysis score (-1 to 1 typically)
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
        lazy="joined",
    )

    sender: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[sender_id],
        lazy="joined",
    )


# Useful indexes
Index("ix_messages_conversation_sender", Message.conversation_id, Message.sender_type)
