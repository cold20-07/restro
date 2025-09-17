"""Authentication middleware and dependencies"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Tuple, Optional

from app.models.auth import User
from app.services.auth_service import get_auth_service, AuthenticationError, AuthorizationError


# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Tuple[User, str]:
    """
    Dependency to get current authenticated user and their restaurant_id
    Returns tuple of (User, restaurant_id)
    """
    try:
        token = credentials.credentials
        user, restaurant_id = await get_auth_service().get_current_user(token)
        return user, restaurant_id
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


async def get_current_user_id(
    current_user: Tuple[User, str] = Depends(get_current_user)
) -> str:
    """Dependency to get just the current user ID"""
    user, _ = current_user
    return user.id


async def get_current_restaurant_id(
    current_user: Tuple[User, str] = Depends(get_current_user)
) -> str:
    """Dependency to get just the current restaurant ID"""
    _, restaurant_id = current_user
    return restaurant_id


async def verify_restaurant_ownership(
    restaurant_id: str,
    current_user: Tuple[User, str] = Depends(get_current_user)
) -> str:
    """
    Dependency to verify that the current user owns the specified restaurant
    Returns the restaurant_id if valid
    """
    user, user_restaurant_id = current_user
    
    # Check if the user is trying to access their own restaurant
    if restaurant_id != user_restaurant_id:
        # Double-check with the database
        has_access = await get_auth_service().verify_restaurant_access(user.id, restaurant_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this restaurant"
            )
    
    return restaurant_id


class RestaurantAccessChecker:
    """Class-based dependency for checking restaurant access with path parameters"""
    
    def __init__(self, restaurant_id_param: str = "restaurant_id"):
        self.restaurant_id_param = restaurant_id_param
    
    async def __call__(
        self,
        restaurant_id: str,
        current_user: Tuple[User, str] = Depends(get_current_user)
    ) -> str:
        """Verify restaurant access for path parameter"""
        return await verify_restaurant_ownership(restaurant_id, current_user)


# Common dependency instances
check_restaurant_access = RestaurantAccessChecker()


async def get_current_user_from_token(token: str) -> User:
    """
    Get current user from JWT token string
    Used for WebSocket authentication where we can't use FastAPI dependencies
    """
    try:
        user, _ = await get_auth_service().get_current_user(token)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Tuple[User, str]]:
    """
    Optional authentication dependency for public endpoints that can benefit from auth
    Returns None if no authentication provided, otherwise returns (User, restaurant_id)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user, restaurant_id = await get_auth_service().get_current_user(token)
        return user, restaurant_id
    except (AuthenticationError, AuthorizationError):
        # For optional auth, we don't raise errors, just return None
        return None