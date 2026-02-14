"""
User Model

Represents users in the system with authentication credentials, roles, and metadata.
"""

from datetime import datetime
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import uuid


class User(Base, TimestampMixin):
    """
    User model for authentication and authorization.
    
    Stores user account information, authentication credentials, roles, and metadata.
    """
    
    __tablename__ = "users"

    # Primary key and identity
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Basic information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), default="General")
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    roles: Mapped[list] = mapped_column(JSON, default=lambda: ["user"])  # List of role names
    # Avoid reserved attribute name 'metadata' on declarative classes
    meta: Mapped[dict] = mapped_column(JSON, name="metadata", default=lambda: {})
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email={self.email}, "
            f"full_name={self.full_name}, is_active={self.is_active})>"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "department": self.department,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "roles": self.roles,
            "metadata": self.meta,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

