"""
Chunk Model
Used for RAG document splitting and vector embedding mapping
Mahavir AI HelpDesk Enterprise Version
"""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampMixin
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.documents import Document


class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"

    # ✅ UUID primary key
    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ✅ MUST match documents.id type
    document_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Optional for Qdrant mapping
    embedding_id: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks"
    )


# Useful index for fast retrieval
Index("ix_chunks_doc_index", Chunk.document_id, Chunk.chunk_index)
