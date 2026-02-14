from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin
from app.models.enums import ConversationStatus

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class Conversation(Base, TimestampMixin):
    """
    Conversation = chat thread/session
    Used in Mahavir AI Helpdesk + WhatsApp system
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 🔥 MUST MATCH users.id TYPE (String UUID)
    user_id: Mapped[str] = mapped_column(
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

    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        nullable=False,
        default=ConversationStatus.OPEN,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined",
    )

    assigned_agent: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_agent_id],
        lazy="joined",
    )

    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.id",
    )


Index("ix_conversations_user_status", Conversation.user_id, Conversation.status)
Index("ix_conversations_agent_status", Conversation.assigned_agent_id, Conversation.status)
