"""Authentication utilities for agent APIs."""

import jwt
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config.settings import settings
from ..utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": False,
                "verify_iss": False
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = await verify_jwt_token(token)
        
        # Extract user ID from token
        user_id = (
            payload.get("sub") or
            payload.get("id") or
            payload.get("user_id")
        )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        # Verify user exists in database
        user_exists = await supabase_client.verify_user_exists(user_id)
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in system"
            )
        
        # Get user profile
        user_profile = await supabase_client.get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found"
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "profile": user_profile,
            "token_payload": payload
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def require_super_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require super admin role."""
    try:
        user_id = current_user["user_id"]
        
        is_super_admin = await supabase_client.check_super_admin_role(user_id)
        if not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin role required"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking super admin role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization check failed"
        )


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """Get current user optionally (for endpoints that work with or without auth)."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
    except Exception:
        return None


class RoleChecker:
    """Role-based access control checker."""
    
    def __init__(self, allowed_roles: list):
        """Initialize with allowed roles."""
        self.allowed_roles = allowed_roles
    
    async def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Check if user has required role."""
        try:
            user_id = current_user["user_id"]
            
            # Always allow super admin
            is_super_admin = await supabase_client.check_super_admin_role(user_id)
            if is_super_admin:
                return current_user
            
            # Check specific roles
            user_profile = current_user.get("profile", {})
            active_role = user_profile.get("active_role")
            
            if active_role in self.allowed_roles:
                return current_user
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' or '.join(self.allowed_roles)}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role check failed"
            )


# Pre-defined role checkers
require_teacher = RoleChecker(["teacher", "organization_admin"])
require_admin = RoleChecker(["organization_admin"])


async def verify_resource_ownership(
    resource_user_id: str,
    current_user: Dict[str, Any],
    allow_super_admin: bool = True
) -> bool:
    """Verify if user owns the resource or has admin privileges."""
    try:
        user_id = current_user["user_id"]
        
        # Check if user owns the resource
        if resource_user_id == user_id:
            return True
        
        # Check if user is super admin
        if allow_super_admin:
            is_super_admin = await supabase_client.check_super_admin_role(user_id)
            if is_super_admin:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error verifying resource ownership: {str(e)}")
        return False


async def check_rate_limit(user_id: str, operation: str, limit: int, window_seconds: int) -> bool:
    """Check rate limiting for user operations."""
    try:
        # This is a placeholder implementation
        # In production, you would use Redis or another cache
        # to track rate limits per user per operation
        
        # For now, always allow
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        return True


def create_access_token(data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """Create access token (utility function)."""
    try:
        to_encode = data.copy()
        
        if expires_delta:
            from datetime import datetime, timedelta
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
            to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise


def validate_file_permissions(
    file_data: Dict[str, Any],
    current_user: Dict[str, Any]
) -> bool:
    """Validate file access permissions."""
    try:
        user_id = current_user["user_id"]
        file_owner = file_data.get("uploaded_by")
        
        # Check ownership
        if file_owner == user_id:
            return True
        
        # Check if file is attached to a course assistant the user created
        assistant_id = file_data.get("assistant_id")
        if assistant_id:
            # This would require checking if the user owns the assistant
            # For now, allow access if user is super admin
            return supabase_client.check_super_admin_role(user_id)
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating file permissions: {str(e)}")
        return False


async def log_user_activity(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log user activity for audit trails."""
    try:
        # This is a placeholder for activity logging
        # In production, you would store this in a separate audit table
        logger.info(
            f"User Activity: {user_id} performed '{action}' on {resource_type}"
            f"{f' ({resource_id})' if resource_id else ''}"
        )
        
    except Exception as e:
        logger.error(f"Error logging user activity: {str(e)}")


async def validate_api_quota(user_id: str, operation: str) -> bool:
    """Validate API usage quota for user."""
    try:
        # This is a placeholder for quota validation
        # In production, you would track API usage per user
        # and enforce limits based on their subscription tier
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating API quota: {str(e)}")
        return True
