"""
Import all SQLAlchemy models here so Alembic can detect them.
"""

from .user import User
from .role import Role
from .user_role import UserRole
from .documents import Document
from .chunk import Chunk
from .chat_log import ChatLog
from .sentiment_log import SentimentLog
# Note: avoid using wildcard import from core to prevent duplicate model
# definitions when models are split across multiple files. Import specific
# models explicitly above instead.
from .conversation import Conversation
from .message import Message
from .ticket import Ticket
from .department import Department
from .sla_policy import SLAPolicy
from .routing_rule import RoutingRule

__all__ = [
    "User",
    "Role",
    "UserRole",
    "Document",
    "Chunk",
    "ChatLog",
    "SentimentLog",
    "Conversation",
    "Message",
    "Ticket",
    "Department",
    "SLAPolicy",
    "RoutingRule",
]
