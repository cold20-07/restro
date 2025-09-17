"""Integration tests for authentication flow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from dashboard.state import AuthState


class TestAuthenticationIntegration:
    """Test complete authentication integration scenarios."""
    
    @pytest.fixture
    def auth_state(self):
        """Create a fresh AuthState instance for testing."""
        return AuthState()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_login_flow(self, mock_client, auth_state):
        """Test complete login flow from form submission to dashboard access."""
        # Mock successful login response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "restaurant_id": "rest_456",
            "expires_in": 3600
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Simulate form input
        auth_state.set_email("owner@restaurant.com")
        auth_state.set_password("securepassword123")
        
        # Perform login
        result = await auth_state.login()
        
        # Verify authentication state
        assert auth_state.is_authenticated
        assert auth_state.access_token == "test_token_123"
        assert auth_state.restaurant_id == "rest_456"
        assert auth_state.user_email == "owner@restaurant.com"
        
        # Verify session is valid
        assert auth_state.is_session_valid()
        
        # Verify form fields are cleared
        assert auth_state.email == ""
        assert auth_state.password == ""
        assert auth_state.error_message == ""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_registration_flow(self, mock_client, auth_state):
        """Test complete registration flow from form submission to success."""
        # Mock successful registration response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "user_id": "user_789",
            "restaurant_id": "rest_101",
            "message": "Account created successfully"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Simulate form input
        auth_state.set_email("newowner@restaurant.com")
        auth_state.set_password("newpassword123")
        auth_state.set_confirm_password("newpassword123")
        auth_state.set_restaurant_name("New Restaurant")
        
        # Perform registration
        with patch('asyncio.sleep'):  # Mock the delay
            result = await auth_state.register()
        
        # Verify success state
        assert auth_state.success_message == "Account created successfully! You can now log in."
        assert auth_state.error_message == ""
        
        # Verify form fields are cleared
        assert auth_state.email == ""
        assert auth_state.password == ""
        assert auth_state.confirm_password == ""
        assert auth_state.restaurant_name == ""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_token_verification_and_user_info_flow(self, mock_client, auth_state):
        """Test token verification and user info retrieval flow."""
        # Set up authenticated state
        auth_state.access_token = "valid_token"
        
        # Mock successful token verification
        verify_response = MagicMock()
        verify_response.status_code = 200
        
        # Mock successful user info retrieval
        user_info_response = MagicMock()
        user_info_response.status_code = 200
        user_info_response.json.return_value = {
            "user": {
                "id": "user_123",
                "email": "owner@restaurant.com"
            },
            "restaurant_id": "rest_456",
            "restaurant_name": "Test Restaurant"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = verify_response
        mock_client_instance.get.return_value = user_info_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Verify token
        is_valid = await auth_state.verify_token()
        assert is_valid
        
        # Get user info
        user_data = await auth_state.get_user_info()
        
        # Verify state is updated
        assert auth_state.user_id == "user_123"
        assert auth_state.user_email == "owner@restaurant.com"
        assert auth_state.restaurant_id == "rest_456"
        assert user_data is not None
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_session_expiry_handling(self, mock_client, auth_state):
        """Test handling of expired session tokens."""
        # Set up authenticated state with expired token
        auth_state.is_authenticated = True
        auth_state.access_token = "expired_token"
        auth_state.user_email = "owner@restaurant.com"
        auth_state.restaurant_id = "rest_456"
        
        # Mock failed token verification (expired)
        verify_response = MagicMock()
        verify_response.status_code = 401
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = verify_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Verify token (should fail and trigger logout)
        is_valid = await auth_state.verify_token()
        
        # Verify session is cleared
        assert not is_valid
        assert not auth_state.is_authenticated
        assert auth_state.access_token == ""
        assert auth_state.user_email == ""
        assert auth_state.restaurant_id == ""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_logout_flow(self, mock_client, auth_state):
        """Test complete logout flow."""
        # Set up authenticated state
        auth_state.is_authenticated = True
        auth_state.access_token = "valid_token"
        auth_state.user_email = "owner@restaurant.com"
        auth_state.restaurant_id = "rest_456"
        auth_state.email = "form_email"
        auth_state.password = "form_password"
        
        # Mock logout API call
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Perform logout
        result = await auth_state.logout()
        
        # Verify all state is cleared
        assert not auth_state.is_authenticated
        assert auth_state.access_token == ""
        assert auth_state.user_email == ""
        assert auth_state.restaurant_id == ""
        assert auth_state.email == ""
        assert auth_state.password == ""
        assert auth_state.error_message == ""
        assert auth_state.success_message == ""
        
        # Verify logout API was called
        mock_client_instance.post.assert_called_once_with(
            "http://localhost:8000/api/v1/auth/logout",
            headers={"Authorization": "Bearer valid_token"},
            timeout=5.0
        )
    
    @pytest.mark.asyncio
    async def test_auth_check_initialization(self, auth_state):
        """Test authentication check on app initialization."""
        # Mock no stored token
        auth_state.access_token = ""
        
        await auth_state.check_auth_status()
        
        # Should not be authenticated
        assert not auth_state.is_authenticated
        assert not auth_state.is_checking_auth
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_auth_check_with_valid_token(self, mock_client, auth_state):
        """Test authentication check with valid stored token."""
        # Set up stored token
        auth_state.access_token = "stored_token"
        
        # Mock successful verification and user info
        verify_response = MagicMock()
        verify_response.status_code = 200
        
        user_info_response = MagicMock()
        user_info_response.status_code = 200
        user_info_response.json.return_value = {
            "user": {"id": "user_123", "email": "owner@restaurant.com"},
            "restaurant_id": "rest_456"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = verify_response
        mock_client_instance.get.return_value = user_info_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        await auth_state.check_auth_status()
        
        # Should be authenticated with user info loaded
        assert auth_state.is_authenticated
        assert auth_state.user_id == "user_123"
        assert auth_state.user_email == "owner@restaurant.com"
        assert auth_state.restaurant_id == "rest_456"
        assert not auth_state.is_checking_auth


class TestAuthenticationErrorHandling:
    """Test authentication error handling scenarios."""
    
    @pytest.fixture
    def auth_state(self):
        """Create a fresh AuthState instance for testing."""
        return AuthState()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_login_network_error(self, mock_client, auth_state):
        """Test login with network connectivity issues."""
        # Mock network error
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        auth_state.set_email("test@example.com")
        auth_state.set_password("password123")
        
        await auth_state.login()
        
        assert not auth_state.is_authenticated
        assert "Unable to connect to server" in auth_state.error_message
        assert not auth_state.is_loading
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_login_timeout_error(self, mock_client, auth_state):
        """Test login with request timeout."""
        # Mock timeout error
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timed out")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        auth_state.set_email("test@example.com")
        auth_state.set_password("password123")
        
        await auth_state.login()
        
        assert not auth_state.is_authenticated
        assert "Login request timed out" in auth_state.error_message
        assert not auth_state.is_loading
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_registration_validation_errors(self, mock_client, auth_state):
        """Test registration with server validation errors."""
        # Mock validation error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "Email already exists"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        auth_state.set_email("existing@example.com")
        auth_state.set_password("password123")
        auth_state.set_confirm_password("password123")
        auth_state.set_restaurant_name("Test Restaurant")
        
        await auth_state.register()
        
        assert auth_state.error_message == "Email already exists"
        assert auth_state.success_message == ""
        assert not auth_state.is_loading


if __name__ == "__main__":
    pytest.main([__file__])