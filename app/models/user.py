# app/models/user.py

from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import uuid


class User(Base, TimestampMixin):
    """
    Enterprise User model for Mahavir AI HelpDesk system.
    Supports RBAC, departments, WhatsApp agents, audit logs.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), default="General")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    meta: Mapped[dict] = mapped_column(JSON, name="metadata", default=lambda: {})

    # ==============================
    # RBAC RELATIONSHIPS
    # ==============================
    user_roles = relationship(
    "UserRole",
    back_populates="user",
    cascade="all, delete-orphan"
)

    # ==============================
    # BUSINESS RELATIONSHIPS
    # ==============================
    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    conversations = relationship(
        "Conversation",
        foreign_keys="[Conversation.owner_id]",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    assigned_conversations = relationship(
        "Conversation",
        foreign_keys="[Conversation.assigned_user_id]",
        back_populates="assigned_user"
    )

    messages = relationship(
        "Message",
        foreign_keys="[Message.sender_id]",
        cascade="all, delete-orphan"
    )
