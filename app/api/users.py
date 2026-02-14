from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.deps import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.schemas.auth import UserResponse
from app.auth.jwt import hash_password


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List users",
    description="Retrieve all users (admin only)"
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all users with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50)
    
    Returns:
        List[UserResponse]: List of users
    """
    try:
        # Check if user has admin role
        is_admin = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
        ).first()
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can list users"
            )
        
        users = db.query(User).offset(skip).limit(limit).all()
        
        logger.info(f"Listed {len(users)} users by admin: {current_user.id}")
        
        return [UserResponse.from_orm(u) for u in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get(
    "/search",
    response_model=List[UserResponse],
    summary="Search users",
    description="Search for users by email or name"
)
def search_users(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search for users by email or full name.
    
    Query Parameters:
        query: Search query string
    
    Returns:
        List[UserResponse]: Matching users
    """
    try:
        users = db.query(User).filter(
            (User.email.ilike(f"%{query}%")) |
            (User.full_name.ilike(f"%{query}%"))
        ).all()
        
        logger.info(
            f"Search performed by user: {current_user.id}, "
            f"query: {query}, matches: {len(users)}"
        )
        
        return [UserResponse.from_orm(u) for u in users]
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    description="Retrieve specific user information"
)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specific user information.
    
    Path Parameters:
        user_id: ID of the user to retrieve
    
    Returns:
        UserResponse: User information
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Users can only view their own profile unless they're admin
        if current_user.id != user_id:
            is_admin = db.query(UserRole).filter(
                UserRole.user_id == current_user.id,
                UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
            ).first()
            
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own profile"
                )
        
        logger.info(f"Retrieved user: {user_id} by user: {current_user.id}")
        
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information (admin only)"
)
def update_user(
    user_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user information.
    
    Path Parameters:
        user_id: ID of the user to update
    
    Request Body:
        full_name: Updated full name (optional)
        email: Updated email (optional)
        is_active: Active status (optional, admin only)
    
    Returns:
        UserResponse: Updated user
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Only admins can update other users
        if current_user.id != user_id:
            is_admin = db.query(UserRole).filter(
                UserRole.user_id == current_user.id,
                UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
            ).first()
            
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update your own profile"
                )
        
        # Update allowed fields
        if "full_name" in update_data:
            user.full_name = update_data["full_name"]
        
        if "email" in update_data and update_data["email"] != user.email:
            existing = db.query(User).filter(User.email == update_data["email"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = update_data["email"]
        
        # Only admins can update is_active
        if "is_active" in update_data:
            is_admin = db.query(UserRole).filter(
                UserRole.user_id == current_user.id,
                UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
            ).first()
            
            if is_admin:
                user.is_active = update_data["is_active"]
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated user: {user_id} by user: {current_user.id}")
        
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user account (admin only)"
)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a user account.
    
    Path Parameters:
        user_id: ID of the user to delete
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Only admins can delete users
        is_admin = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
        ).first()
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete users"
            )
        
        # Prevent self-deletion
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        db.delete(user)
        db.commit()
        
        logger.info(f"Deleted user: {user_id} by admin: {current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign role",
    description="Assign a role to a user (admin only)"
)
def assign_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Assign a role to a user.
    
    Path Parameters:
        user_id: ID of the user
        role_id: ID of the role
    
    Returns:
        dict: Success message
    """
    try:
        # Check admin permission
        is_admin = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
        ).first()
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can assign roles"
            )
        
        # Verify user and role exist
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.id == role_id).first()
        
        if not user or not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User or role not found"
            )
        
        # Check if already assigned
        existing = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already assigned"
            )
        
        # Assign role
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        db.commit()
        
        logger.info(
            f"Role {role_id} assigned to user {user_id} by admin: {current_user.id}"
        )
        
        return {"message": "Role assigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove role",
    description="Remove a role from a user (admin only)"
)
def remove_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a role from a user.
    
    Path Parameters:
        user_id: ID of the user
        role_id: ID of the role
    """
    try:
        # Check admin permission
        is_admin = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.role_id == db.query(Role).filter(Role.name == "admin").first().id
        ).first()
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can remove roles"
            )
        
        # Find and delete role assignment
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not assigned to user"
            )
        
        db.delete(user_role)
        db.commit()
        
        logger.info(
            f"Role {role_id} removed from user {user_id} by admin: {current_user.id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role"
        )
