"""
JWT Token Management Module

Provides token creation, validation, and user context extraction.
Supports configurable algorithms, secrets, and expiration times.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
load_dotenv()

from app.core.logging import logger
from app.schemas.auth import UserContext


# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


# ============================================================================
# JWT Configuration
# ============================================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# -----------------------------
# Validate JWT Secret
# -----------------------------
if not JWT_SECRET_KEY:
    logger.critical(
        "JWT_SECRET_KEY not found in environment variables. "
        "Application cannot start securely."
    )
    raise RuntimeError("JWT_SECRET_KEY must be set in environment")

if len(JWT_SECRET_KEY) < 32:
    logger.warning(
        "JWT_SECRET_KEY is too short. Use at least 32 characters "
        "for enterprise security."
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
    Create JWT access token with enterprise logging and error handling.
    """

    try:
        # -----------------------------
        # Validate configuration
        # -----------------------------
        if not JWT_SECRET_KEY:
            logger.critical("JWT_SECRET_KEY missing")
            raise ValueError("JWT_SECRET_KEY not configured")

        if data is None and not all([user_id, email, username]):
            logger.error(
                "Token creation failed: missing user fields",
                extra={"user_id": user_id, "email": email, "username": username},
            )
            raise ValueError("user_id, email, username required")

        expire = datetime.utcnow() + (
            expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS)
        )

        if not token_id:
            token_id = str(uuid.uuid4())

        if data is not None:
            to_encode = data.copy()
            to_encode["exp"] = expire
            to_encode["iat"] = datetime.utcnow()
            to_encode["jti"] = token_id
            to_encode.setdefault("type", "access")
        else:
            to_encode = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "roles": roles or [],
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": token_id,
                "type": "access",
            }

        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        logger.info("JWT created", extra={"user_id": user_id})

        return encoded_jwt

        # -----------------------------
        # Set expiration
        # -----------------------------
        expire = datetime.utcnow() + (
            expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS)
        )

        # -----------------------------
        # Generate token id
        # -----------------------------
        if not token_id:
            token_id = str(uuid.uuid4())

        # -----------------------------
        # Prepare payload
        # -----------------------------
        if data is not None:
            to_encode = data.copy()
            to_encode["exp"] = expire
            to_encode["iat"] = datetime.utcnow()
            to_encode["jti"] = token_id
            to_encode.setdefault("type", "access")
        else:
            to_encode = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "roles": roles or [],
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": token_id,
                "type": "access",
            }

        # -----------------------------
        # Encode token
        # -----------------------------
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        logger.info(
            "JWT created successfully",
            extra={
                "user_id": user_id,
                "token_id": token_id,
                "expires_at": expire.isoformat(),
            },
        )

        return encoded_jwt

    except ValueError as ve:
        logger.error(f"Token validation error: {ve}")
        raise

    except Exception as e:
        logger.exception("Unexpected error during JWT creation")
        raise RuntimeError("Failed to create JWT token") from e


def create_refresh_token(
    user_id: str,
    email: str,
    username: str,
    roles: list[str],
    token_id: Optional[str] = None,
) -> str:
    """
    Create refresh token with enterprise logging and error handling.
    """

    try:
        # -----------------------------
        # Validate configuration
        # -----------------------------
        if not JWT_SECRET_KEY:
            logger.critical("JWT_SECRET_KEY missing in environment")
            raise ValueError("JWT_SECRET_KEY must be configured")

        if not user_id or not email or not username:
            logger.error(
                "Refresh token creation failed: missing required user fields",
                extra={"user_id": user_id, "email": email, "username": username},
            )
            raise ValueError("user_id, email, and username are required")
        
        if not all([user_id, email, username]):
            logger.error(
                "Refresh token failed: missing user fields",
                extra={"user_id": user_id, "email": email, "username": username},
            )
            raise ValueError("user_id, email, username required")

        # -----------------------------
        # Expiration time
        # -----------------------------
        expires_delta = timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)

        # -----------------------------
        # Generate refresh token
        # -----------------------------
        token = create_access_token(
            user_id=user_id,
            email=email,
            username=username,
            roles=roles,
            expires_delta=expires_delta,
            token_id=token_id,
            data={"type": "refresh"},
        )

        logger.info(
            "Refresh token created successfully",
            extra={
                "user_id": user_id,
                "expires_days": JWT_REFRESH_EXPIRATION_DAYS,
            },
        )

        return token

    except ValueError as ve:
        logger.error(f"Refresh token validation error: {ve}")
        raise

    except Exception as e:
        logger.exception("Unexpected error during refresh token creation")
        raise RuntimeError("Failed to create refresh token") from e


def decode_jwt(token: str) -> TokenData:
    """
    Decode and validate JWT token.
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
            logger.warning(
                "JWT missing required fields",
                extra={"user_id": user_id, "email": email},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # -----------------------------
        # Expiration Check
        # -----------------------------
        try:
            if exp:
                # exp may be timestamp or datetime
                if isinstance(exp, (int, float)):
                    exp_time = datetime.utcfromtimestamp(exp)
                else:
                    exp_time = exp

                if datetime.utcnow() > exp_time:
                    logger.warning(
                        "JWT expired",
                        extra={"user_id": user_id, "expired_at": str(exp_time)},
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        except Exception as e:
            logger.error(f"JWT expiration validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token expiration",
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
