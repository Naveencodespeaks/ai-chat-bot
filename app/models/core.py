# app/db/models/core.py
import uuid
from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Text, Integer, Float,
    Enum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import (
    UserStatus, ConversationStatus, SenderType,
    TicketStatus, TicketPriority, IngestionStatus
)

# class Department(Base):
#     __tablename__ = "departments"

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
#     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, name="user_status"), default=UserStatus.ACTIVE)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    department: Mapped["Department | None"] = relationship()

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conv_participant"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    role_in_conversation: Mapped[str] = mapped_column(String(30), default="VIEWER")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# class Message(Base):
#     __tablename__ = "messages"
#     __table_args__ = (
#         Index("ix_messages_conversation_time", "conversation_id", "created_at"),
#     )

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
#     conversation: Mapped["Conversation"] = relationship(back_populates="messages")

#     sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType, name="sender_type"), nullable=False)
#     sender_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
#     content: Mapped[str] = mapped_column(Text, nullable=False)
#     content_format: Mapped[str] = mapped_column(String(30), default="plain")
#     reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))

#     message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
#     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SentimentEvent(Base):
    __tablename__ = "sentiment_events"
    __table_args__ = (
        Index("ix_sentiment_message", "message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)

    label: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    model_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class LLMCall(Base):
    __tablename__ = "llm_calls"
    __table_args__ = (
        Index("ix_llm_calls_conversation_time", "conversation_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    request_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))
    response_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))

    provider: Mapped[str] = mapped_column(String(50), default="openai")
    model: Mapped[str] = mapped_column(String(120), nullable=False)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    temperature: Mapped[float | None] = mapped_column(Float)
    top_p: Mapped[float | None] = mapped_column(Float)
    prompt_hash: Mapped[str | None] = mapped_column(String(128))

    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RagContext(Base):
    __tablename__ = "rag_contexts"
    __table_args__ = (
        UniqueConstraint("llm_call_id", "rank", name="uq_rag_context_rank"),
        Index("ix_rag_llm", "llm_call_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    llm_call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("llm_calls.id"), nullable=False)

    document_chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("document_chunks.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class KbSource(Base):
    __tablename__ = "kb_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # UPLOAD/URL/DRIVE/SHAREPOINT/API
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_source", "source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("kb_sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(1024))

    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    access_tags: Mapped[list] = mapped_column(JSONB, default=list)

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_doc_version_no"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)

    checksum: Mapped[str | None] = mapped_column(String(128))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str | None] = mapped_column(String(1024))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_version_id", "chunk_index", name="uq_doc_chunk_idx"),
        Index("ix_doc_chunks_version", "document_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("document_versions.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str | None] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    document_chunks_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    qdrant_point_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("ix_ingestion_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("kb_sources.id"), nullable=False)

    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus, name="ingestion_status"), default=IngestionStatus.QUEUED)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    documents_total: Mapped[int] = mapped_column(Integer, default=0)
    documents_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0)

    error_summary: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# class Ticket(Base):
#     __tablename__ = "tickets"
#     __table_args__ = (
#         Index("ix_tickets_status_priority", "status", "priority"),
#     )

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), unique=True)

#     created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
#     assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

#     status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus, name="ticket_status"), default=TicketStatus.OPEN)
#     priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority, name="ticket_priority"), default=TicketPriority.MEDIUM)

#     category: Mapped[str | None] = mapped_column(String(50))
#     subject: Mapped[str] = mapped_column(String(255), nullable=False)
#     description: Mapped[str | None] = mapped_column(Text)

#     sla_due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

#     created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
#     updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TicketEvent(Base):
    __tablename__ = "ticket_events"
    __table_args__ = (
        Index("ix_ticket_events_ticket_time", "ticket_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[dict] = mapped_column(JSONB, default=dict)
    new_value: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_time", "created_at"),
        Index("ix_audit_actor_time", "actor_user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
