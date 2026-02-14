from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token, verify_password, hash_password
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    RegisterRequest,
)
from app.core.config import settings


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account"
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    Request Body:
        email: User email (must be unique)
        password: Account password (min 8 characters)
        full_name: User's full name
    
    Returns:
        UserResponse: Created user information
    """
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(request.password)
        user = User(
            email=request.email,
            full_name=request.full_name,
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and get access token"
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.
    
    Request Body:
        email: User email
        password: User password
    
    Returns:
        TokenResponse: Access token and user information
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve authenticated user information"
)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get the authenticated user's profile information.
    
    Returns:
        UserResponse: Current user's details
    """
    logger.info(f"Retrieved user info for: {current_user.email}")
    return UserResponse.from_orm(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update authenticated user's profile information"
)
def update_user(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the authenticated user's profile.
    
    Request Body:
        full_name: Updated full name (optional)
        email: Updated email (optional, must be unique)
    
    Returns:
        UserResponse: Updated user information
    """
    try:
        # Check if email is already in use
        if "email" in request and request["email"] != current_user.email:
            existing = db.query(User).filter(User.email == request["email"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            current_user.email = request["email"]
        
        if "full_name" in request:
            current_user.full_name = request["full_name"]
        
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User updated: {current_user.email}")
        
        return UserResponse.from_orm(current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the authenticated user's password"
)
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the password for the authenticated user.
    
    Request Body:
        old_password: Current password
        new_password: New password (min 8 characters)
    
    Returns:
        dict: Success message
    """
    try:
        # Verify old password
        if not verify_password(old_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password"
            )
        
        # Update password
        current_user.hashed_password = hash_password(new_password)
        db.add(current_user)
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
