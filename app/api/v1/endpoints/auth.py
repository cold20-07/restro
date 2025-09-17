"""Authentication API endpoints"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Tuple
import traceback

from app.models.auth import UserRegister, UserLogin, AuthResponse, User
from app.services.auth_service import get_auth_service, AuthenticationError, AuthorizationError
from app.core.auth import get_current_user
from app.core.input_validation import validate_request_body, validate_input
from app.core.exceptions import ValidationError, raise_validation_error
from app.core.error_monitoring import record_error
from app.core.logging_config import get_logger

logger = get_logger("auth_endpoints")


router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@validate_request_body(UserRegister)
async def register(user_data: UserRegister, request: Request):
    """
    Register a new restaurant owner account
    
    Creates a new user account and associated restaurant in the system.
    Returns authentication token for immediate login.
    
    - **email**: Valid email address for the account
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **restaurant_name**: Name of the restaurant to create
    """
    try:
        # Additional business logic validation
        if not user_data.email or not user_data.password or not user_data.restaurant_name:
            raise_validation_error(
                "All fields are required",
                {
                    "email": ["Email is required"] if not user_data.email else [],
                    "password": ["Password is required"] if not user_data.password else [],
                    "restaurant_name": ["Restaurant name is required"] if not user_data.restaurant_name else []
                }
            )
        
        auth_response = await get_auth_service().register_user(user_data)
        
        logger.info(
            "User registration successful",
            extra={
                "email": user_data.email,
                "restaurant_name": user_data.restaurant_name,
                "endpoint": "/api/auth/register"
            }
        )
        
        return auth_response
        
    except ValidationError:
        raise
    except AuthenticationError as e:
        logger.warning(
            f"Registration failed: {str(e)}",
            extra={
                "email": user_data.email,
                "endpoint": "/api/auth/register",
                "error_type": "AuthenticationError"
            }
        )
        record_error(e, endpoint="/api/auth/register", request_data={"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Registration failed with unexpected error: {str(e)}",
            extra={
                "email": user_data.email,
                "endpoint": "/api/auth/register",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        record_error(e, endpoint="/api/auth/register", request_data={"email": user_data.email}, stack_trace=traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.post("/login", response_model=AuthResponse)
@validate_request_body(UserLogin)
async def login(login_data: UserLogin, request: Request):
    """
    Authenticate restaurant owner and get access token
    
    Validates credentials and returns JWT token for accessing protected endpoints.
    Token includes restaurant context for multi-tenant isolation.
    
    - **email**: Registered email address
    - **password**: Account password
    """
    try:
        # Additional validation
        if not login_data.email or not login_data.password:
            raise_validation_error(
                "Email and password are required",
                {
                    "email": ["Email is required"] if not login_data.email else [],
                    "password": ["Password is required"] if not login_data.password else []
                }
            )
        
        auth_response = await get_auth_service().login_user(login_data)
        
        logger.info(
            "User login successful",
            extra={
                "email": login_data.email,
                "endpoint": "/api/auth/login"
            }
        )
        
        return auth_response
        
    except ValidationError:
        raise
    except AuthenticationError as e:
        logger.warning(
            f"Login failed: {str(e)}",
            extra={
                "email": login_data.email,
                "endpoint": "/api/auth/login",
                "error_type": "AuthenticationError",
                "client_ip": request.client.host if request.client else None
            }
        )
        record_error(e, endpoint="/api/auth/login", request_data={"email": login_data.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(
            f"Login failed with unexpected error: {str(e)}",
            extra={
                "email": login_data.email,
                "endpoint": "/api/auth/login",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        record_error(e, endpoint="/api/auth/login", request_data={"email": login_data.email}, stack_trace=traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post("/logout")
async def logout(current_user: Tuple[User, str] = Depends(get_current_user)):
    """
    Logout current user
    
    Invalidates the current session. Client should discard the token.
    """
    try:
        user, restaurant_id = current_user
        # For JWT tokens, logout is mainly client-side
        # In production, you might want to implement token blacklisting
        success = await get_auth_service().logout_user("")
        
        if success:
            return {"message": "Logout successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to server error"
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: Tuple[User, str] = Depends(get_current_user)):
    """
    Get current user information
    
    Returns information about the currently authenticated user and their restaurant.
    Useful for client-side user interface updates.
    """
    try:
        user, restaurant_id = current_user
        return {
            "user": user,
            "restaurant_id": restaurant_id,
            "authenticated": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post("/verify-token")
async def verify_token(current_user: Tuple[User, str] = Depends(get_current_user)):
    """
    Verify if the current token is valid
    
    Endpoint for clients to check if their stored token is still valid
    without making other API calls.
    """
    try:
        user, restaurant_id = current_user
        return {
            "valid": True,
            "user_id": user.id,
            "restaurant_id": restaurant_id,
            "message": "Token is valid"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )