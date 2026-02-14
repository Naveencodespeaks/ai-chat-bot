from typing import Optional, List
from app.db.base import Base



class UserContext:
    """
    Domain-level authenticated user context.
    This object is TRUSTED and used across AI, RAG, and policy layers.
    """

    def __init__(
        self,
        user_id: str,
        role: str,
        department: Optional[str] = None,
    ):
        self.user_id = user_id
        self.roles: List[str] = [role]
        self.department = department

        self.allowed_visibility = self._resolve_visibility()
        self.is_verified = True

    def _resolve_visibility(self) -> List[str]:
        if "ADMIN" in self.roles:
            return ["PUBLIC", "INTERNAL", "CONFIDENTIAL"]
        if "HR" in self.roles:
            return ["PUBLIC", "INTERNAL"]
        return ["PUBLIC"]

    @property
    def primary_role(self) -> str:
        return self.roles[0]

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles