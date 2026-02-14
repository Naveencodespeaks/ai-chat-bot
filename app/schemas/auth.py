from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class PasswordChangeRequest(BaseModel):
    """Change password request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


# -------------------------------------------------
# RESPONSE MODELS
# -------------------------------------------------


class UserResponse(BaseModel):
    """User information response"""
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str
    user: UserResponse


class UserContext:
    def __init__(self, user_id: str, role: str, department: Optional[str] = None,):
        self.user_id = user_id
        self.role = role
        self.department = department
        self.allowed_visibility = self._determine_visibility()
        self.isverified = True  # In a real implementation, this would be determined by your auth system


    def _resolve_visibility(self)-> List[str]:
        if "ADMIN" in self.role:
            return ["PUBLIC", "INTERNAL", "CONFIDENTIAL"]
        if "HR" in self.role:
            return ["PUBLIC", "INTERNAL"]
        return ["PUBLIC"]
    @property
    def primary_role(self):
        return self.roles[0]