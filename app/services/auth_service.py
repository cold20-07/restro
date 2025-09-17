"""Authentication service with Supabase Auth integration"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from supabase import Client
from gotrue.errors import AuthError

from app.core.config import settings
from app.database.supabase_client import supabase_client
from app.models.auth import User, UserRegister, UserLogin, Token, TokenData, AuthResponse
from app.models.restaurant import RestaurantCreate
from app.services.restaurant_service import RestaurantService
from app.core.exceptions import DatabaseError, AuthenticationError, AuthorizationError
from app.core.logging_config import get_logger, LogOperationTime

logger = get_logger("auth")


class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase_client.client
        self.service_client = supabase_client.service_client
        self.restaurant_service = RestaurantService(self.service_client)
    
    async def register_user(self, user_data: UserRegister) -> AuthResponse:
        """Register a new user with restaurant"""
        with LogOperationTime(logger, "register_user", user_email=user_data.email):
            try:
                # Register user with Supabase Auth
                auth_response = self.client.auth.sign_up({
                    "email": user_data.email,
                    "password": user_data.password
                })
                
                if not auth_response.user:
                    logger.error("Failed to create user account with Supabase Auth")
                    raise AuthenticationError("Failed to create user account")
                
                # Create restaurant for the user
                restaurant_data = RestaurantCreate(
                    name=user_data.restaurant_name,
                    owner_id=auth_response.user.id
                )
                
                restaurant = await self.restaurant_service.create_with_owner(restaurant_data)
                
                # Create user model
                user = User(
                    id=auth_response.user.id,
                    email=auth_response.user.email,
                    email_confirmed_at=auth_response.user.email_confirmed_at,
                    created_at=auth_response.user.created_at
                )
                
                # Generate JWT token
                token = self._create_access_token(
                    user_id=user.id,
                    restaurant_id=restaurant.id,
                    email=user.email
                )
                
                logger.info("User registration successful", extra={
                    "user_id": user.id,
                    "restaurant_id": restaurant.id,
                    "email": user_data.email
                })
                
                return AuthResponse(
                    message="Registration successful",
                    user=user,
                    token=token
                )
                
            except AuthError as e:
                logger.error(f"Supabase Auth registration failed: {str(e)}")
                raise AuthenticationError(f"Registration failed: {str(e)}")
            except DatabaseError as e:
                # If restaurant creation fails, we should clean up the user
                # For now, we'll let the user know and they can try again
                logger.error(f"Restaurant creation failed during registration: {str(e)}")
                raise AuthenticationError(f"Failed to create restaurant: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during registration: {str(e)}")
                raise AuthenticationError(f"Registration failed: {str(e)}")
    
    async def login_user(self, login_data: UserLogin) -> AuthResponse:
        """Authenticate user and return JWT token"""
        try:
            # Authenticate with Supabase Auth
            auth_response = self.client.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not auth_response.user:
                raise AuthenticationError("Invalid email or password")
            
            # Get user's restaurant
            restaurant = await self.restaurant_service.get_by_owner_id(auth_response.user.id)
            if not restaurant:
                raise AuthenticationError("No restaurant found for user")
            
            # Create user model
            user = User(
                id=auth_response.user.id,
                email=auth_response.user.email,
                email_confirmed_at=auth_response.user.email_confirmed_at,
                created_at=auth_response.user.created_at
            )
            
            # Generate JWT token
            token = self._create_access_token(
                user_id=user.id,
                restaurant_id=restaurant.id,
                email=user.email
            )
            
            return AuthResponse(
                message="Login successful",
                user=user,
                token=token
            )
            
        except AuthError as e:
            raise AuthenticationError("Invalid email or password")
        except DatabaseError as e:
            raise AuthenticationError(f"Failed to retrieve user data: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Login failed: {str(e)}")
    
    def _create_access_token(self, user_id: str, restaurant_id: str, email: str) -> Token:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        payload = {
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            payload, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=user_id,
            restaurant_id=restaurant_id
        )
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            
            user_id = payload.get("user_id")
            restaurant_id = payload.get("restaurant_id")
            email = payload.get("email")
            exp = payload.get("exp")
            
            if not user_id or not restaurant_id or not email:
                raise AuthenticationError("Invalid token payload")
            
            return TokenData(
                user_id=user_id,
                restaurant_id=restaurant_id,
                email=email,
                exp=datetime.fromtimestamp(exp)
            )
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    async def get_current_user(self, token: str) -> Tuple[User, str]:
        """Get current user from token and return user with restaurant_id"""
        token_data = self.verify_token(token)
        
        # Verify user still exists and has access to restaurant
        try:
            restaurant = await self.restaurant_service.get_by_id(token_data.restaurant_id)
            if not restaurant or restaurant.owner_id != token_data.user_id:
                raise AuthorizationError("User does not have access to this restaurant")
            
            # Create user model (we don't store full user data, just what we need)
            user = User(
                id=token_data.user_id,
                email=token_data.email,
                email_confirmed_at=None,  # We don't track this in JWT
                created_at=datetime.utcnow()  # Placeholder
            )
            
            return user, token_data.restaurant_id
            
        except DatabaseError as e:
            raise AuthorizationError(f"Failed to verify user access: {str(e)}")
    
    async def verify_restaurant_access(self, user_id: str, restaurant_id: str) -> bool:
        """Verify that a user has access to a specific restaurant"""
        try:
            restaurant = await self.restaurant_service.get_by_id(restaurant_id)
            return restaurant is not None and restaurant.owner_id == user_id
        except DatabaseError:
            return False
    
    async def logout_user(self, token: str) -> bool:
        """Logout user (invalidate token on Supabase side)"""
        try:
            # For JWT tokens, we can't really "invalidate" them server-side
            # without maintaining a blacklist. For now, we'll just return success
            # In a production system, you might want to implement token blacklisting
            # or use shorter-lived tokens with refresh tokens
            return True
        except Exception:
            return False


# Global auth service instance (initialized lazily to avoid issues during testing)
auth_service = None

def get_auth_service() -> AuthService:
    """Get or create the global auth service instance"""
    global auth_service
    if auth_service is None:
        auth_service = AuthService()
    return auth_service