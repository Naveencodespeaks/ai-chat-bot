# app/models/message.py

from sqlalchemy import String, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import SenderType


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    conversation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, name="sender_type"),
        nullable=False,
        index=True
    )

    sender_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column(Float)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
