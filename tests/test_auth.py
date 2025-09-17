"""Unit tests for authentication system"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import jwt

from app.models.auth import UserRegister, UserLogin, User, Token, TokenData
from app.models.restaurant import Restaurant
from app.services.auth_service import AuthService, AuthenticationError, AuthorizationError
from app.core.config import settings


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.auth = Mock()
        return mock_client
    
    @pytest.fixture
    def mock_restaurant_service(self):
        """Mock restaurant service"""
        mock_service = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def auth_service(self, mock_supabase_client, mock_restaurant_service):
        """Create AuthService instance with mocked dependencies"""
        service = AuthService(mock_supabase_client)
        service.restaurant_service = mock_restaurant_service
        return service
    
    @pytest.fixture
    def sample_user_register(self):
        """Sample user registration data"""
        return UserRegister(
            email="test@restaurant.com",
            password="SecurePass123",
            restaurant_name="Test Restaurant"
        )
    
    @pytest.fixture
    def sample_user_login(self):
        """Sample user login data"""
        return UserLogin(
            email="test@restaurant.com",
            password="SecurePass123"
        )
    
    @pytest.fixture
    def sample_restaurant(self):
        """Sample restaurant data"""
        return Restaurant(
            id="restaurant-123",
            name="Test Restaurant",
            owner_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=None
        )
    
    @pytest.mark.asyncio
    async def test_register_user_success(
        self, 
        auth_service, 
        sample_user_register, 
        sample_restaurant,
        mock_supabase_client,
        mock_restaurant_service
    ):
        """Test successful user registration"""
        # Mock Supabase auth response
        mock_auth_user = Mock()
        mock_auth_user.id = "user-123"
        mock_auth_user.email = "test@restaurant.com"
        mock_auth_user.email_confirmed_at = datetime.utcnow()
        mock_auth_user.created_at = datetime.utcnow()
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_auth_user
        
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        mock_restaurant_service.create_with_owner.return_value = sample_restaurant
        
        # Execute registration
        result = await auth_service.register_user(sample_user_register)
        
        # Verify results
        assert result.message == "Registration successful"
        assert result.user.id == "user-123"
        assert result.user.email == "test@restaurant.com"
        assert result.token.user_id == "user-123"
        assert result.token.restaurant_id == "restaurant-123"
        
        # Verify service calls
        mock_supabase_client.auth.sign_up.assert_called_once()
        mock_restaurant_service.create_with_owner.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_auth_failure(
        self, 
        auth_service, 
        sample_user_register,
        mock_supabase_client
    ):
        """Test registration failure due to auth error"""
        # Mock failed auth response
        mock_auth_response = Mock()
        mock_auth_response.user = None
        
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        
        # Execute and verify exception
        with pytest.raises(AuthenticationError, match="Failed to create user account"):
            await auth_service.register_user(sample_user_register)
    
    @pytest.mark.asyncio
    async def test_login_user_success(
        self, 
        auth_service, 
        sample_user_login, 
        sample_restaurant,
        mock_supabase_client,
        mock_restaurant_service
    ):
        """Test successful user login"""
        # Mock Supabase auth response
        mock_auth_user = Mock()
        mock_auth_user.id = "user-123"
        mock_auth_user.email = "test@restaurant.com"
        mock_auth_user.email_confirmed_at = datetime.utcnow()
        mock_auth_user.created_at = datetime.utcnow()
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_auth_user
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_restaurant_service.get_by_owner_id.return_value = sample_restaurant
        
        # Execute login
        result = await auth_service.login_user(sample_user_login)
        
        # Verify results
        assert result.message == "Login successful"
        assert result.user.id == "user-123"
        assert result.user.email == "test@restaurant.com"
        assert result.token.user_id == "user-123"
        assert result.token.restaurant_id == "restaurant-123"
        
        # Verify service calls
        mock_supabase_client.auth.sign_in_with_password.assert_called_once()
        mock_restaurant_service.get_by_owner_id.assert_called_once_with("user-123")
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(
        self, 
        auth_service, 
        sample_user_login,
        mock_supabase_client
    ):
        """Test login failure due to invalid credentials"""
        # Mock failed auth response
        mock_auth_response = Mock()
        mock_auth_response.user = None
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        # Execute and verify exception
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await auth_service.login_user(sample_user_login)
    
    @pytest.mark.asyncio
    async def test_login_user_no_restaurant(
        self, 
        auth_service, 
        sample_user_login,
        mock_supabase_client,
        mock_restaurant_service
    ):
        """Test login failure when user has no restaurant"""
        # Mock successful auth but no restaurant
        mock_auth_user = Mock()
        mock_auth_user.id = "user-123"
        mock_auth_user.email = "test@restaurant.com"
        mock_auth_user.email_confirmed_at = datetime.utcnow()
        mock_auth_user.created_at = datetime.utcnow()
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_auth_user
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_restaurant_service.get_by_owner_id.return_value = None
        
        # Execute and verify exception
        with pytest.raises(AuthenticationError, match="No restaurant found for user"):
            await auth_service.login_user(sample_user_login)
    
    def test_create_access_token(self, auth_service):
        """Test JWT token creation"""
        user_id = "user-123"
        restaurant_id = "restaurant-123"
        email = "test@restaurant.com"
        
        token = auth_service._create_access_token(user_id, restaurant_id, email)
        
        # Verify token structure
        assert token.token_type == "bearer"
        assert token.user_id == user_id
        assert token.restaurant_id == restaurant_id
        assert token.expires_in == settings.access_token_expire_minutes * 60
        
        # Verify token can be decoded
        payload = jwt.decode(
            token.access_token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        assert payload["user_id"] == user_id
        assert payload["restaurant_id"] == restaurant_id
        assert payload["email"] == email
        assert payload["type"] == "access"
    
    def test_verify_token_success(self, auth_service):
        """Test successful token verification"""
        # Create a valid token
        user_id = "user-123"
        restaurant_id = "restaurant-123"
        email = "test@restaurant.com"
        
        token = auth_service._create_access_token(user_id, restaurant_id, email)
        
        # Verify the token
        token_data = auth_service.verify_token(token.access_token)
        
        assert token_data.user_id == user_id
        assert token_data.restaurant_id == restaurant_id
        assert token_data.email == email
        assert isinstance(token_data.exp, datetime)
    
    def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token"""
        # Create an expired token
        expire = datetime.utcnow() - timedelta(minutes=1)  # 1 minute ago
        
        payload = {
            "user_id": "user-123",
            "restaurant_id": "restaurant-123",
            "email": "test@restaurant.com",
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(minutes=2),
            "type": "access"
        }
        
        expired_token = jwt.encode(
            payload, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        # Verify exception is raised
        with pytest.raises(AuthenticationError, match="Token has expired"):
            auth_service.verify_token(expired_token)
    
    def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token"""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.verify_token(invalid_token)
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, 
        auth_service, 
        sample_restaurant,
        mock_restaurant_service
    ):
        """Test successful current user retrieval"""
        # Create a valid token
        user_id = "user-123"
        restaurant_id = "restaurant-123"
        email = "test@restaurant.com"
        
        token = auth_service._create_access_token(user_id, restaurant_id, email)
        mock_restaurant_service.get_by_id.return_value = sample_restaurant
        
        # Get current user
        user, returned_restaurant_id = await auth_service.get_current_user(token.access_token)
        
        assert user.id == user_id
        assert user.email == email
        assert returned_restaurant_id == restaurant_id
        
        mock_restaurant_service.get_by_id.assert_called_once_with(restaurant_id)
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized_restaurant(
        self, 
        auth_service,
        mock_restaurant_service
    ):
        """Test current user retrieval with unauthorized restaurant access"""
        # Create a valid token
        user_id = "user-123"
        restaurant_id = "restaurant-123"
        email = "test@restaurant.com"
        
        token = auth_service._create_access_token(user_id, restaurant_id, email)
        
        # Mock restaurant with different owner
        different_restaurant = Restaurant(
            id=restaurant_id,
            name="Test Restaurant",
            owner_id="different-user",  # Different owner
            created_at=datetime.utcnow(),
            updated_at=None
        )
        mock_restaurant_service.get_by_id.return_value = different_restaurant
        
        # Verify exception is raised
        with pytest.raises(AuthorizationError, match="User does not have access to this restaurant"):
            await auth_service.get_current_user(token.access_token)
    
    @pytest.mark.asyncio
    async def test_verify_restaurant_access_success(
        self, 
        auth_service, 
        sample_restaurant,
        mock_restaurant_service
    ):
        """Test successful restaurant access verification"""
        mock_restaurant_service.get_by_id.return_value = sample_restaurant
        
        has_access = await auth_service.verify_restaurant_access("user-123", "restaurant-123")
        
        assert has_access is True
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
    
    @pytest.mark.asyncio
    async def test_verify_restaurant_access_failure(
        self, 
        auth_service,
        mock_restaurant_service
    ):
        """Test restaurant access verification failure"""
        # Mock restaurant with different owner
        different_restaurant = Restaurant(
            id="restaurant-123",
            name="Test Restaurant",
            owner_id="different-user",
            created_at=datetime.utcnow(),
            updated_at=None
        )
        mock_restaurant_service.get_by_id.return_value = different_restaurant
        
        has_access = await auth_service.verify_restaurant_access("user-123", "restaurant-123")
        
        assert has_access is False


class TestAuthModels:
    """Test cases for authentication models"""
    
    def test_user_register_valid(self):
        """Test valid user registration data"""
        user_data = UserRegister(
            email="test@restaurant.com",
            password="SecurePass123",
            restaurant_name="Test Restaurant"
        )
        
        assert user_data.email == "test@restaurant.com"
        assert user_data.password == "SecurePass123"
        assert user_data.restaurant_name == "Test Restaurant"
    
    def test_user_register_invalid_password(self):
        """Test user registration with invalid password"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@restaurant.com",
                password="short",
                restaurant_name="Test Restaurant"
            )
        
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            UserRegister(
                email="test@restaurant.com",
                password="lowercase123",
                restaurant_name="Test Restaurant"
            )
        
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            UserRegister(
                email="test@restaurant.com",
                password="UPPERCASE123",
                restaurant_name="Test Restaurant"
            )
        
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            UserRegister(
                email="test@restaurant.com",
                password="NoDigitsHere",
                restaurant_name="Test Restaurant"
            )
    
    def test_user_register_empty_restaurant_name(self):
        """Test user registration with empty restaurant name"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@restaurant.com",
                password="SecurePass123",
                restaurant_name=""
            )
        
        with pytest.raises(ValueError, match="Restaurant name cannot be empty"):
            UserRegister(
                email="test@restaurant.com",
                password="SecurePass123",
                restaurant_name="   "
            )
    
    def test_token_data_model(self):
        """Test TokenData model"""
        exp_time = datetime.utcnow() + timedelta(minutes=30)
        
        token_data = TokenData(
            user_id="user-123",
            restaurant_id="restaurant-123",
            email="test@restaurant.com",
            exp=exp_time
        )
        
        assert token_data.user_id == "user-123"
        assert token_data.restaurant_id == "restaurant-123"
        assert token_data.email == "test@restaurant.com"
        assert token_data.exp == exp_time