"""Integration tests for authentication endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime

from main import app
from app.models.restaurant import Restaurant
from app.services.auth_service import AuthenticationError


class TestAuthEndpoints:
    """Test cases for authentication API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
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
    
    @patch('app.api.v1.endpoints.auth.get_auth_service')
    def test_register_success(self, mock_get_service, client):
        """Test successful user registration"""
        # Mock successful registration response
        from app.models.auth import AuthResponse, User, Token
        
        mock_user = User(
            id="user-123",
            email="test@restaurant.com",
            email_confirmed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        mock_token = Token(
            access_token="mock.jwt.token",
            token_type="bearer",
            expires_in=1800,
            user_id="user-123",
            restaurant_id="restaurant-123"
        )
        
        mock_auth_response = AuthResponse(
            message="Registration successful",
            user=mock_user,
            token=mock_token
        )
        
        mock_service = Mock()
        mock_service.register_user = AsyncMock(return_value=mock_auth_response)
        mock_get_service.return_value = mock_service
        
        # Make registration request
        response = client.post("/api/auth/register", json={
            "email": "test@restaurant.com",
            "password": "SecurePass123",
            "restaurant_name": "Test Restaurant"
        })
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Registration successful"
        assert data["user"]["email"] == "test@restaurant.com"
        assert data["token"]["user_id"] == "user-123"
        assert data["token"]["restaurant_id"] == "restaurant-123"
        
        # Verify service was called
        mock_service.register_user.assert_called_once()
    
    @patch('app.api.v1.endpoints.auth.get_auth_service')
    def test_register_failure(self, mock_get_service, client):
        """Test registration failure"""
        # Mock registration failure
        mock_service = Mock()
        mock_service.register_user = AsyncMock(side_effect=AuthenticationError("Email already exists"))
        mock_get_service.return_value = mock_service
        
        # Make registration request
        response = client.post("/api/auth/register", json={
            "email": "existing@restaurant.com",
            "password": "SecurePass123",
            "restaurant_name": "Test Restaurant"
        })
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "Email already exists" in data["detail"]
    
    def test_register_invalid_data(self, client):
        """Test registration with invalid data"""
        # Test invalid email
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "password": "SecurePass123",
            "restaurant_name": "Test Restaurant"
        })
        assert response.status_code == 422