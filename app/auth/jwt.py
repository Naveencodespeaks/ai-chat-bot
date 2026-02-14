"""
JWT Token Management Module

Provides token creation, validation, and user context extraction.
Supports configurable algorithms, secrets, and expiration times.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError
from passlib.context import CryptContext
import os

from app.core.logging import logger
from app.schemas.auth import UserContext


# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


# Configuration from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Warning if using default secret
if JWT_SECRET_KEY == "your-secret-key-change-in-production":
    logger.warning(
        "JWT_SECRET_KEY not configured in environment. Using default key. "
        "Change JWT_SECRET_KEY in production!"
    )


# ============================================================================
# Password Hashing Functions
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Hashed password string
    
    Raises:
        ValueError: If password is invalid or hashing fails
    """
    try:
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        hashed = pwd_context.hash(password)
        return hashed
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise ValueError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password
    
    Returns:
        True if password matches, False otherwise
    
    Raises:
        ValueError: If inputs are invalid
    """
    try:
        if not plain_password or not hashed_password:
            return False
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


class TokenData:
    """Token payload data structure."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        username: str,
        roles: list[str],
        exp: Optional[int] = None,
        iat: Optional[int] = None,
        jti: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.username = username
        self.roles = roles
        self.exp = exp
        self.iat = iat
        self.jti = jti  # JWT ID for token revocation tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT payload."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "roles": self.roles,
            "exp": self.exp,
            "iat": self.iat,
            "jti": self.jti,
        }


def create_access_token(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
    token_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.
    
    Supports two calling styles:
    1. New style: create_access_token(user_id, email, username, roles, expires_delta)
    2. Old style: create_access_token(data={"sub": user_id}, expires_delta=expires_delta)
    
    Args:
        user_id: User identifier (new style)
        email: User email address (new style)
        username: Username (new style)
        roles: List of user roles (new style)
        expires_delta: Custom expiration time (default: JWT_EXPIRATION_HOURS)
        token_id: Optional token ID for revocation tracking
        data: Legacy dict-based payload (old style)
    
    Returns:
        Encoded JWT token string
    
    Raises:
        ValueError: If configuration is invalid
    """
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "your-secret-key-change-in-production":
        raise ValueError(
            "JWT_SECRET_KEY must be configured in environment before creating tokens"
        )
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Handle old-style data dict (backward compatibility)
    if data is not None:
        to_encode = data.copy()
        to_encode["exp"] = expire
        to_encode["iat"] = datetime.utcnow()
    else:
        # New style with structured data
        to_encode = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "roles": roles or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": token_id,
        }
    
    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.debug(
            f"Token created for user {user_id or to_encode.get('sub')}",
            extra={"user_id": user_id, "expires_at": expire.isoformat()},
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise


def create_refresh_token(
    user_id: str,
    email: str,
    username: str,
    roles: list[str],
    token_id: Optional[str] = None,
) -> str:
    """
    Create a refresh token with longer expiration.
    
    Args:
        user_id: User identifier
        email: User email
        username: Username
        roles: User roles
        token_id: Optional token ID
    
    Returns:
        Encoded refresh token
    """
    expires_delta = timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)
    return create_access_token(
        user_id=user_id,
        email=email,
        username=username,
        roles=roles,
        expires_delta=expires_delta,
        token_id=token_id,
    )


def decode_jwt(token: str) -> TokenData:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData object with decoded claims
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract required fields
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        username: str = payload.get("username")
        roles: list[str] = payload.get("roles", [])
        exp = payload.get("exp")
        iat = payload.get("iat")
        jti = payload.get("jti")
        
        # Validate required fields
        if not all([user_id, email, username]):
            logger.warning("Missing required fields in JWT payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            username=username,
            roles=roles,
            exp=exp,
            iat=iat,
            jti=jti,
        )
    
    except JWTError as e:
        logger.warning(f"JWT decoding failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_context_from_token(token: str) -> UserContext:
    """
    Extract UserContext from JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        UserContext object for use in requests
    
    Raises:
        HTTPException: If token is invalid
    """
    token_data = decode_jwt(token)
    
    try:
        user_context = UserContext(
            user_id=token_data.user_id,
            username=token_data.username,
            email=token_data.email,
            roles=token_data.roles,
        )
        return user_context
    except ValidationError as e:
        logger.error(f"Failed to create UserContext from token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_expiration(token_data: TokenData) -> bool:
    """
    Check if token is expired.
    
    Args:
        token_data: Decoded token data
    
    Returns:
        True if valid, False if expired
    """
    if token_data.exp is None:
        return True
    
    exp_datetime = datetime.utcfromtimestamp(token_data.exp)
    is_valid = datetime.utcnow() < exp_datetime
    
    if not is_valid:
        logger.info(f"Token expired at {exp_datetime.isoformat()}")
    
    return is_valid


def verify_user_role(user_context: UserContext, required_role: str) -> bool:
    """
    Check if user has required role.
    
    Args:
        user_context: User context from token
        required_role: Required role name
    
    Returns:
        True if user has role, False otherwise
    """
    has_role = required_role in user_context.roles
    
    if not has_role:
        logger.warning(
            f"User {user_context.user_id} lacks required role: {required_role}",
            extra={"user_id": user_context.user_id, "required_role": required_role},
        )
    
    return has_role


def verify_any_role(user_context: UserContext, required_roles: list[str]) -> bool:
    """
    Check if user has any of the required roles.
    
    Args:
        user_context: User context from token
        required_roles: List of allowed roles
    
    Returns:
        True if user has at least one role, False otherwise
    """
    has_role = any(role in user_context.roles for role in required_roles)
    
    if not has_role:
        logger.warning(
            f"User {user_context.user_id} lacks any required roles: {required_roles}",
            extra={"user_id": user_context.user_id, "required_roles": required_roles},
        )
    
    return has_role
