"""Integration tests for public menu API endpoints with proper mocking"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

from app.models.public_menu import (
    PublicMenuResponse, 
    PublicMenuItemResponse, 
    PublicMenuByCategory,
    MenuCategoryResponse
)
from app.database.base import NotFoundError, DatabaseError


class TestPublicMenuEndpointsIntegration:
    """Integration test cases for public menu API endpoints with proper dependency mocking"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app with mocked dependencies"""
        # Mock the database service factory to avoid Supabase initialization
        with patch('app.database.service_factory.get_db_services') as mock_get_db_services:
            mock_db_services = Mock()
            mock_db_services.menu_item_service = Mock()
            mock_db_services.restaurant_service = Mock()
            mock_get_db_services.return_value = mock_db_services
            
            # Import and create client after mocking
            from main import app
            return TestClient(app)
    
    @patch('app.services.public_menu_service.PublicMenuService.get_public_menu')
    def test_get_restaurant_menu_success_integration(self, mock_get_menu, client):
        """Test successful retrieval of restaurant menu through full API stack"""
        # Mock service response
        expected_response = PublicMenuResponse(
            restaurant_id="restaurant-123",
            restaurant_name="Mario's Pizza Palace",
            categories=["Pizza", "Salads"],
            items=[
                PublicMenuItemResponse(
                    id="item-1",
                    name="Margherita Pizza",
                    description="Classic pizza with tomato sauce, mozzarella, and fresh basil",
                    price=Decimal("15.99"),
                    category="Pizza",
                    image_url="https://example.com/margherita.jpg"
                )
            ],
            total_items=1
        )
        
        mock_get_menu.return_value = expected_response
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_id"] == "restaurant-123"
        assert data["restaurant_name"] == "Mario's Pizza Palace"
        assert data["total_items"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Margherita Pizza"
        
        # Verify service was called correctly
        mock_get_menu.assert_called_once_with("restaurant-123", None)
    
    @patch('app.services.public_menu_service.PublicMenuService.get_public_menu')
    def test_get_restaurant_menu_not_found_integration(self, mock_get_menu, client):
        """Test menu retrieval for non-existent restaurant through full API stack"""
        # Mock service to raise NotFoundError
        mock_get_menu.side_effect = NotFoundError("Restaurant restaurant-123 not found")
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert "Restaurant restaurant-123 not found" in data["detail"]
    
    @patch('app.services.public_menu_service.PublicMenuService.get_public_menu')
    def test_get_restaurant_menu_database_error_integration(self, mock_get_menu, client):
        """Test menu retrieval with database error through full API stack"""
        # Mock service to raise DatabaseError
        mock_get_menu.side_effect = DatabaseError("Database connection failed")
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve menu" in data["detail"]
    
    @patch('app.services.public_menu_service.PublicMenuService.search_public_menu')
    def test_search_restaurant_menu_success_integration(self, mock_search, client):
        """Test successful menu search through full API stack"""
        # Mock service response
        expected_results = [
            PublicMenuItemResponse(
                id="item-1",
                name="Margherita Pizza",
                description="Classic pizza with tomato sauce, mozzarella, and fresh basil",
                price=Decimal("15.99"),
                category="Pizza",
                image_url="https://example.com/margherita.jpg"
            )
        ]
        
        mock_search.return_value = expected_results
        
        # Make request
        response = client.get("/api/menus/restaurant-123/search?q=pizza")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margherita Pizza"
        assert data[0]["category"] == "Pizza"
        
        # Verify service was called with correct parameters
        mock_search.assert_called_once_with(
            restaurant_id="restaurant-123",
            search_query="pizza",
            category=None,
            limit=20
        )
    
    def test_search_restaurant_menu_missing_query_integration(self, client):
        """Test menu search without required query parameter through full API stack"""
        # Make request without query parameter
        response = client.get("/api/menus/restaurant-123/search")
        
        # Verify validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that the error is about missing query parameter
        assert any("q" in str(error) for error in data["detail"])
    
    def test_search_restaurant_menu_invalid_limit_integration(self, client):
        """Test menu search with invalid limit parameter through full API stack"""
        # Make request with invalid limit (too low)
        response = client.get("/api/menus/restaurant-123/search?q=pizza&limit=0")
        
        # Verify validation error
        assert response.status_code == 422
        
        # Test limit too high
        response = client.get("/api/menus/restaurant-123/search?q=pizza&limit=101")
        assert response.status_code == 422
    
    @patch('app.services.public_menu_service.PublicMenuService.get_menu_categories')
    def test_get_restaurant_menu_categories_integration(self, mock_get_categories, client):
        """Test successful retrieval of menu categories through full API stack"""
        # Mock service response
        expected_categories = ["Appetizers", "Pizza", "Salads", "Beverages"]
        
        mock_get_categories.return_value = expected_categories
        
        # Make request
        response = client.get("/api/menus/restaurant-123/categories")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data == expected_categories
        assert len(data) == 4
        
        # Verify service was called
        mock_get_categories.assert_called_once_with("restaurant-123")
    
    @patch('app.services.public_menu_service.PublicMenuService.get_public_menu_by_category')
    def test_get_restaurant_menu_by_category_integration(self, mock_get_by_category, client):
        """Test successful retrieval of menu organized by categories through full API stack"""
        # Mock service response
        expected_response = PublicMenuByCategory(
            restaurant_id="restaurant-123",
            restaurant_name="Mario's Pizza Palace",
            categories=[
                MenuCategoryResponse(
                    category="Pizza",
                    items=[
                        PublicMenuItemResponse(
                            id="item-1",
                            name="Margherita Pizza",
                            description="Classic pizza with tomato sauce, mozzarella, and fresh basil",
                            price=Decimal("15.99"),
                            category="Pizza",
                            image_url="https://example.com/margherita.jpg"
                        )
                    ]
                )
            ],
            total_items=1
        )
        
        mock_get_by_category.return_value = expected_response
        
        # Make request
        response = client.get("/api/menus/restaurant-123/by-category")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_id"] == "restaurant-123"
        assert data["total_items"] == 1
        assert len(data["categories"]) == 1
        assert data["categories"][0]["category"] == "Pizza"
        
        # Verify service was called
        mock_get_by_category.assert_called_once_with("restaurant-123")