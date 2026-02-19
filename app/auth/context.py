from typing import Optional, List


class UserContext:
    """
    Domain-level authenticated user context.
    Used across AI, RAG, and policy layers.
    """

    def __init__(
        self,
        user_id: str,
        role: Optional[str] = None,
        roles: Optional[List[str]] = None,
        department: Optional[str] = None,
        is_verified: bool = True,
    ):
        if not user_id:
            raise ValueError("user_id is required")

        # support role or roles
        if roles:
            self.roles: List[str] = [r.upper() for r in roles]
        elif role:
            self.roles: List[str] = [role.upper()]
        else:
            self.roles = ["USER"]

        self.user_id = user_id
        self.department = (department or "GENERAL").upper()
        self.is_verified = is_verified

        self.allowed_visibility = self._resolve_visibility()

    def _resolve_visibility(self) -> List[str]:
        if "ADMIN" in self.roles:
            return ["PUBLIC", "INTERNAL", "CONFIDENTIAL"]

        if any(r.startswith("HR") for r in self.roles):
            return ["PUBLIC", "INTERNAL"]

        return ["PUBLIC"]

    @property
    def primary_role(self) -> str:
        return self.roles[0]

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles

    def has_role(self, role: str) -> bool:
        return role.upper() in self.roles

    def __repr__(self) -> str:
        return (
            f"UserContext(user_id={self.user_id}, "
            f"roles={self.roles}, "
            f"department={self.department})"
        )
