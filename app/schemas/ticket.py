from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    conversation_id: int = Field(..., description="Associated conversation id")
    title: Optional[str] = Field(None, description="Ticket title")
    description: Optional[str] = Field(None, description="Detailed description")
    priority: Optional[str] = Field(None, description="Priority: LOW/MEDIUM/HIGH/CRITICAL")
    category: Optional[str] = Field(None, description="Issue category")

    model_config = {"from_attributes": True}


class TicketUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[int] = None

    model_config = {"from_attributes": True}


class TicketResponse(BaseModel):
    id: int
    conversation_id: int
    department_id: Optional[int]
    assigned_agent_id: Optional[int]
    status: Optional[str]
    priority: Optional[str]
    resolution_notes: Optional[str]
    sla_due_at: Optional[datetime]
    first_response_at: Optional[datetime]
    closed_at: Optional[datetime]
    sla_breached: Optional[bool]
    escalation_level: Optional[int]
    reassigned_count: Optional[int]
    assigned_at: Optional[datetime]
    routing_method: Optional[str]
    ai_confidence: Optional[float]
    ai_predicted_department: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
