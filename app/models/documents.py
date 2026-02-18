"""
Document Model for RAG System
Enterprise Version – Mahavir AI HelpDesk
"""

from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chunk import Chunk


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    # ✅ UUID primary key
    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ✅ FK must match users.id type (String 255)
    owner_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="documents"
    )

    # -----------------------------
    # DOCUMENT METADATA
    # -----------------------------
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), default="text")

    # -----------------------------
    # FILE INFO
    # -----------------------------
    file_path: Mapped[Optional[str]] = mapped_column(String(512))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(100), default="text/plain")

    # -----------------------------
    # PROCESSING INFO
    # -----------------------------
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # -----------------------------
    # TAGGING & METADATA
    # -----------------------------
    tags: Mapped[list] = mapped_column(JSON, default=lambda: [])
    meta: Mapped[dict] = mapped_column(JSON, name="metadata", default=lambda: {})

    # -----------------------------
    # RELATIONSHIPS
    # -----------------------------
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title}>"
