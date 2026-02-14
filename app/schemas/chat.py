from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------


class ChatMessageRequest(BaseModel):
    """User message input in a chat"""
    content: str = Field(..., min_length=1, max_length=5000)


class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation"""
    title: Optional[str] = None


# -------------------------------------------------
# RESPONSE MODELS
# -------------------------------------------------


class MessageBase(BaseModel):
    """Base message information"""
    id: int
    content: str
    sender_type: str
    created_at: datetime


class MessageResponse(MessageBase):
    """Single message response"""
    sentiment_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """User message + bot response pair"""
    user_message: MessageResponse
    bot_response: Optional[MessageResponse] = None
    sentiment_score: Optional[float] = None
    requires_escalation: bool = False
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Complete conversation response"""
    id: int
    user_id: int
    assigned_agent_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
 
