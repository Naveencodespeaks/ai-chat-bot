"""
Document Model for RAG System

Stores metadata about documents that have been ingested into the RAG system.
Includes references to file storage, vector embeddings, and processing status.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin
from app.models.user import User


class Document(Base, TimestampMixin):
    """
    Document model for RAG ingestion.
    
    Stores document metadata including file references, processing status,
    and metadata for retrieval and analysis.
    """
    
    __tablename__ = "documents"
    
    # Primary key and relationships
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    
    # Document metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # Original filename
    document_type: Mapped[str] = mapped_column(String(50), default="text")  # pdf, txt, markdown, etc.
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Size in bytes
    content_type: Mapped[str] = mapped_column(String(100), default="text/plain")
    
    # Processing information
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Organization and retrieval
    tags: Mapped[list] = mapped_column(JSON, default=lambda: [])
    # Use 'meta' as attribute name to avoid conflict with SQLAlchemy's reserved
    # 'metadata' attribute on declarative classes. Database column name remains
    # 'metadata' for compatibility.
    meta: Mapped[dict] = mapped_column(JSON, name="metadata", default=lambda: {})
    
    # Timestamps (inherited from TimestampMixin)
    # created_at: Mapped[datetime]
    # updated_at: Mapped[datetime]
    
    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, title={self.title}, "
            f"owner_id={self.owner_id}, processed={self.is_processed})>"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "name": self.name,
            "file_path": self.file_path,
            "document_type": self.document_type,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "tags": self.tags,
            "metadata": self.meta,
            "is_processed": self.is_processed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

