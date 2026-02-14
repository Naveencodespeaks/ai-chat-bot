"""
Role-Based Access Control (RBAC) Module

Provides role checking dependencies for FastAPI endpoints.
Supports single role requirements, multiple role requirements (any), and custom permissions.
"""

from typing import Callable, List, Optional
from functools import wraps
from fastapi import Depends, HTTPException, status

from app.schemas.auth import UserContext
from app.auth.dependencies import get_current_user
from app.core.logging import logger


# ============================================================================
# Role Definitions
# ============================================================================

# Standard application roles
ROLES = {
    "admin": "Administrator - Full system access",
    "supervisor": "Supervisor - Manage support team and escalations",
    "support": "Support Agent - Handle customer conversations",
    "user": "Regular User - Standard access",
    "guest": "Guest - Limited read-only access",
}

# Role hierarchies (higher level includes lower level permissions)
ROLE_HIERARCHY = {
    "admin": ["admin", "supervisor", "support", "user", "guest"],
    "supervisor": ["supervisor", "support", "user", "guest"],
    "support": ["support", "user", "guest"],
    "user": ["user", "guest"],
    "guest": ["guest"],
}

# Permission definitions per role
ROLE_PERMISSIONS = {
    "admin": {
        "user_management",
        "role_assignment",
        "system_configuration",
        "audit_logs",
        "document_management",
        "escalation_handling",
        "sla_management",
        "conversation_management",
        "sentiment_analysis",
    },
    "supervisor": {
        "team_management",
        "escalation_handling",
        "conversation_management",
        "sentiment_analysis",
        "audit_logs_team",
    },
    "support": {
        "conversation_management",
        "sentiment_analysis",
        "document_access",
        "escalation_request",
    },
    "user": {
        "conversation_management",
        "sentiment_analysis",
        "document_access",
    },
    "guest": {
        "read_public_documents",
        "view_status",
    },
}


# ============================================================================
# RBAC Dependency Functions
# ============================================================================

def require_role(required_role: str) -> Callable:
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Single role required for access
    
    Returns:
        Dependency function that validates user has the required role
    
    Example:
        @router.get("/admin")
        async def admin_endpoint(user: UserContext = Depends(require_role("admin"))):
            return {"message": f"Welcome {user.username}"}
    """
    async def role_checker(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if required_role not in user.roles:
            logger.warning(
                f"Access denied: User {user.user_id} lacks required role {required_role}",
                extra={
                    "user_id": user.user_id,
                    "required_role": required_role,
                    "user_roles": user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This resource requires '{required_role}' role",
            )
        return user
    
    return role_checker


def require_any_role(allowed_roles: List[str]) -> Callable:
    """
    Create a dependency that requires any of the specified roles.
    
    Args:
        allowed_roles: List of roles, user must have at least one
    
    Returns:
        Dependency function that validates user has any required role
    
    Example:
        @router.get("/support")
        async def support_endpoint(
            user: UserContext = Depends(require_any_role(["admin", "supervisor", "support"]))
        ):
            return {"message": f"Welcome {user.username}"}
    """
    async def role_checker(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if not any(role in user.roles for role in allowed_roles):
            logger.warning(
                f"Access denied: User {user.user_id} lacks any of required roles {allowed_roles}",
                extra={
                    "user_id": user.user_id,
                    "allowed_roles": allowed_roles,
                    "user_roles": user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This resource requires one of these roles: {', '.join(allowed_roles)}",
            )
        return user
    
    return role_checker


def require_admin() -> Callable:
    """
    Create a dependency that requires admin role.
    
    Convenience function for require_role("admin").
    
    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(user: UserContext = Depends(require_admin())):
            return {"message": f"User deleted by {user.username}"}
    """
    return require_role("admin")


def require_supervisor_or_admin() -> Callable:
    """
    Create a dependency that requires supervisor or admin role.
    
    Convenience function for require_any_role(["supervisor", "admin"]).
    """
    return require_any_role(["supervisor", "admin"])


def require_support_or_higher() -> Callable:
    """
    Create a dependency that requires support role or higher.
    
    Includes: support, supervisor, admin
    """
    return require_any_role(["support", "supervisor", "admin"])


# ============================================================================
# RBAC Utility Functions
# ============================================================================

def has_role(user: UserContext, role: str) -> bool:
    """
    Check if user has a specific role.
    
    Args:
        user: User context
        role: Role to check
    
    Returns:
        True if user has the role, False otherwise
    """
    return role in user.roles


def has_any_role(user: UserContext, roles: List[str]) -> bool:
    """
    Check if user has any of the specified roles.
    
    Args:
        user: User context
        roles: List of roles to check
    
    Returns:
        True if user has at least one role, False otherwise
    """
    return any(role in user.roles for role in roles)


def has_all_roles(user: UserContext, roles: List[str]) -> bool:
    """
    Check if user has all of the specified roles.
    
    Args:
        user: User context
        roles: List of roles user must have
    
    Returns:
        True if user has all roles, False otherwise
    """
    return all(role in user.roles for role in roles)


def is_admin(user: UserContext) -> bool:
    """
    Convenience function to check if user is admin.
    
    Args:
        user: User context
    
    Returns:
        True if user is admin, False otherwise
    """
    return has_role(user, "admin")


def is_support_or_higher(user: UserContext) -> bool:
    """
    Check if user has support role or higher (support, supervisor, admin).
    
    Args:
        user: User context
    
    Returns:
        True if user qualifies, False otherwise
    """
    return has_any_role(user, ["support", "supervisor", "admin"])


def get_highest_role(user: UserContext) -> Optional[str]:
    """
    Get the highest role from user's role list using role hierarchy.
    
    Args:
        user: User context
    
    Returns:
        Highest role or None if user has no roles
    
    Example:
        highest = get_highest_role(user)  # Returns "admin" if user has admin role
    """
    role_priority = {"admin": 5, "supervisor": 4, "support": 3, "user": 2, "guest": 1}
    
    if not user.roles:
        return None
    
    highest = max(user.roles, key=lambda r: role_priority.get(r, 0))
    return highest


def get_user_permissions(user: UserContext) -> set:
    """
    Get all permissions for a user based on their roles.
    
    Args:
        user: User context
    
    Returns:
        Set of permission strings user has
    
    Example:
        perms = get_user_permissions(user)
        if "user_management" in perms:
            # User can manage other users
    """
    permissions = set()
    
    for role in user.roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    
    return permissions


def has_permission(user: UserContext, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User context
        permission: Permission name to check
    
    Returns:
        True if user has permission, False otherwise
    
    Example:
        if has_permission(user, "user_management"):
            # User can manage users
    """
    return permission in get_user_permissions(user)


def check_resource_ownership(
    user: UserContext,
    resource_owner_id: str,
    allow_admin_override: bool = True,
) -> bool:
    """
    Check if user owns a resource or is admin.
    
    Args:
        user: User context
        resource_owner_id: ID of resource owner
        allow_admin_override: If True, admins can access any resource
    
    Returns:
        True if user owns resource or is allowed override, False otherwise
    
    Example:
        if not check_resource_ownership(user, conversation.owner_id):
            raise HTTPException(status_code=403, detail="Not your conversation")
    """
    if not allow_admin_override:
        return user.user_id == resource_owner_id
    
    return user.user_id == resource_owner_id or is_admin(user)


# ============================================================================
# Deprecated/Legacy Support
# ============================================================================

# Note: The old name is supported for backward compatibility but logs a warning
def require_admin_role() -> Callable:
    """
    Deprecated: Use require_admin() instead.
    
    This function is kept for backward compatibility.
    """
    logger.warning("require_admin_role() is deprecated. Use require_admin() instead.")
    return require_admin()

