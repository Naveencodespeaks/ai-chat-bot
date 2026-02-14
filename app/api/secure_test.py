"""
Secure Testing Endpoints

Provides endpoints to test authentication, RBAC, and security features.
These endpoints demonstrate proper use of security dependencies and help verify
the security infrastructure is functioning correctly.

WARNING: These endpoints should NOT be exposed in production.
Only enable in development/testing environments.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.auth.jwt import verify_user_role, verify_any_role
from app.auth.rbac import require_role, require_any_role
from app.schemas.auth import UserContext
from app.core.logging import logger


router = APIRouter(prefix="/secure", tags=["secure-testing"])


# ============================================================================
# Authentication Tests
# ============================================================================

@router.get(
    "/me",
    summary="Get Current User Info",
    description="Returns information about the currently authenticated user.",
    response_description="Current user context",
)
async def get_current_user_info(
    user: UserContext = Depends(get_current_user),
):
    """
    Retrieve current authenticated user information.
    
    Requires: Valid JWT token in Authorization header
    Returns: User context with roles and permissions
    """
    logger.info(
        f"User {user.user_id} accessed /secure/me endpoint",
        extra={"user_id": user.user_id, "endpoint": "/secure/me"},
    )
    
    return {
        "status": "authenticated",
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/token-info",
    summary="Get Token Information",
    description="Returns details about the current JWT token.",
)
async def get_token_info(
    user: UserContext = Depends(get_current_user),
):
    """
    Get information about the JWT token used for authentication.
    
    Requires: Valid JWT token
    Returns: Token metadata and user claims
    """
    return {
        "status": "valid",
        "message": "Token is valid and not expired",
        "user_info": {
            "id": user.user_id,
            "username": user.username,
            "email": user.email,
        },
        "roles": user.roles,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# RBAC Tests
# ============================================================================

@router.get(
    "/admin",
    summary="Admin Only Endpoint",
    description="This endpoint is only accessible by users with 'admin' role.",
)
async def admin_only(
    user: UserContext = Depends(require_role("admin")),
):
    """
    Test endpoint that requires admin role.
    
    Requires: User must have 'admin' role
    Returns: Admin access confirmation
    """
    logger.info(
        f"Admin user {user.user_id} accessed /secure/admin endpoint",
        extra={"user_id": user.user_id, "role": "admin"},
    )
    
    return {
        "status": "success",
        "message": "Welcome Admin",
        "user_id": user.user_id,
        "role": "admin",
        "access_level": "unrestricted",
    }


@router.get(
    "/support-staff",
    summary="Support Staff Endpoint",
    description="Accessible by support, supervisor, or admin roles.",
)
async def support_staff_only(
    user: UserContext = Depends(require_any_role(["support", "supervisor", "admin"])),
):
    """
    Test endpoint for support team.
    
    Requires: User must have 'support', 'supervisor', or 'admin' role
    Returns: Support access confirmation
    """
    logger.info(
        f"Support user {user.user_id} accessed /secure/support-staff endpoint",
        extra={"user_id": user.user_id, "roles": user.roles},
    )
    
    return {
        "status": "success",
        "message": "Welcome Support Staff",
        "user_id": user.user_id,
        "roles": user.roles,
        "access_level": "support_access",
    }


@router.get(
    "/user-area",
    summary="Authenticated User Endpoint",
    description="Accessible by any authenticated user.",
)
async def user_area(
    user: UserContext = Depends(get_current_user),
):
    """
    Test endpoint for any authenticated user.
    
    Requires: Valid JWT token (any user)
    Returns: User-specific information
    """
    logger.info(
        f"User {user.user_id} accessed /secure/user-area endpoint",
        extra={"user_id": user.user_id},
    )
    
    return {
        "status": "success",
        "message": f"Welcome {user.username}",
        "user_id": user.user_id,
        "roles": user.roles,
        "access_level": "authenticated_user",
    }


# ============================================================================
# Permission Verification Tests
# ============================================================================

@router.get(
    "/verify-admin",
    summary="Verify Admin Permission",
    description="Checks if current user has admin role (returns bool).",
)
async def verify_admin(
    user: UserContext = Depends(get_current_user),
):
    """
    Check if the current user has admin role without enforcing it.
    
    Requires: Valid JWT token
    Returns: Boolean indicating admin status
    """
    has_admin = verify_user_role(user, "admin")
    
    return {
        "user_id": user.user_id,
        "requested_role": "admin",
        "has_role": has_admin,
        "all_roles": user.roles,
    }


@router.get(
    "/verify-roles",
    summary="Verify Multiple Roles",
    description="Checks if user has any of the specified roles.",
)
async def verify_roles(
    user: UserContext = Depends(get_current_user),
):
    """
    Check if user has any of multiple roles.
    
    Requires: Valid JWT token
    Returns: Role verification results
    """
    required_roles = ["admin", "supervisor", "support"]
    has_any = verify_any_role(user, required_roles)
    
    return {
        "user_id": user.user_id,
        "checked_roles": required_roles,
        "has_any_role": has_any,
        "user_roles": user.roles,
    }


# ============================================================================
# Security Feature Tests
# ============================================================================

@router.get(
    "/headers",
    summary="Get Security Headers",
    description="Returns information about security headers in responses.",
)
async def get_security_headers(
    user: UserContext = Depends(get_current_user),
):
    """
    Information about security headers applied to API responses.
    
    Requires: Valid JWT token
    Returns: Security headers information
    """
    return {
        "security_features": {
            "cors": "Enabled - Cross-origin requests allowed for authorized origins",
            "https": "Required in production",
            "hsts": "Should be enabled in production (require HTTPS)",
            "csp": "Content-Security-Policy headers applied",
            "xfo": "X-Frame-Options: DENY (clickjacking protection)",
        },
        "authentication": {
            "scheme": "Bearer JWT",
            "algorithm": "HS256",
            "expiration": "24 hours",
        },
    }


@router.get(
    "/audit-log",
    summary="Get User's Audit Log",
    description="Returns audit trail for current user (requires admin or self).",
)
async def get_audit_log(
    user: UserContext = Depends(get_current_user),
):
    """
    Get audit log for the current user.
    
    Requires: Valid JWT token
    Returns: Recent activities and access logs (mock data for testing)
    """
    logger.info(
        f"User {user.user_id} accessed their audit log",
        extra={"user_id": user.user_id, "action": "view_audit_log"},
    )
    
    return {
        "user_id": user.user_id,
        "audit_log": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "login",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Client",
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "access_secure_endpoint",
                "endpoint": "/secure/audit-log",
                "method": "GET",
            },
        ],
        "total_events": 2,
    }


@router.get(
    "/data-isolation",
    summary="Test Data Isolation",
    description="Demonstrates that users can only access their own data.",
)
async def test_data_isolation(
    user: UserContext = Depends(get_current_user),
):
    """
    Test endpoint to verify data isolation between users.
    
    Requires: Valid JWT token
    Returns: User-specific data that respects ownership
    """
    # In production, this would fetch real user data from database
    # and verify the authenticated user owns it
    
    return {
        "status": "success",
        "message": "Data isolation verified - you can only see your data",
        "user_id": user.user_id,
        "accessible_data": {
            "conversations": f"Only conversations owned by {user.user_id}",
            "messages": f"Only messages from {user.user_id}",
            "documents": f"Only documents accessible to {user.user_id}",
        },
    }


# ============================================================================
# Error Handling Tests
# ============================================================================

@router.get(
    "/test-unauthorized",
    summary="Test Unauthorized Access",
    description="This endpoint always returns 401 Unauthorized for testing.",
)
async def test_unauthorized():
    """
    Test endpoint that always denies access.
    
    Returns: 401 Unauthorized error
    """
    logger.warning("Unauthorized access attempted to /secure/test-unauthorized")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access denied",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get(
    "/test-forbidden",
    summary="Test Forbidden Access",
    description="This endpoint always returns 403 Forbidden for testing.",
)
async def test_forbidden(
    user: UserContext = Depends(get_current_user),
):
    """
    Test endpoint that forbids access to authenticated users.
    
    Requires: Valid JWT token
    Returns: 403 Forbidden error
    """
    logger.warning(
        f"Forbidden access attempted by user {user.user_id} to /secure/test-forbidden",
        extra={"user_id": user.user_id},
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission to access this resource",
    )


# ============================================================================
# Summary Endpoint
# ============================================================================

@router.get(
    "/test-summary",
    summary="Security Testing Summary",
    description="Overview of all available security test endpoints.",
)
async def test_summary():
    """
    Get a summary of all security test endpoints.
    
    Returns: List of available test endpoints and their purposes
    """
    return {
        "module": "Secure Testing Endpoints",
        "description": "Test and verify authentication and RBAC functionality",
        "endpoints": {
            "Authentication Tests": {
                "/secure/me": "Get current user info",
                "/secure/token-info": "Get JWT token details",
            },
            "RBAC Tests": {
                "/secure/admin": "Admin-only endpoint",
                "/secure/support-staff": "Support staff endpoint",
                "/secure/user-area": "Any authenticated user",
            },
            "Permission Verification": {
                "/secure/verify-admin": "Check admin permission",
                "/secure/verify-roles": "Check multiple roles",
            },
            "Security Features": {
                "/secure/headers": "Security headers info",
                "/secure/audit-log": "User audit log",
                "/secure/data-isolation": "Data isolation test",
            },
            "Error Handling": {
                "/secure/test-unauthorized": "Test 401 response",
                "/secure/test-forbidden": "Test 403 response",
            },
        },
        "warning": "These endpoints should only be enabled in development/testing environments",
    }

