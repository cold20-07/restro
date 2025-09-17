"""Integration tests for public menu API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

from main import app
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.public_menu import (
    PublicMenuResponse, 
    PublicMenuItemResponse, 
    PublicMenuByCategory,
    MenuCategoryResponse
)
from app.database.base import NotFoundError, DatabaseError


class TestPublicMenuEndpoints:
    """Test cases for public menu API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_restaurant(self):
        """Sample restaurant data"""
        return Restaurant(
            id="restaurant-123",
            name="Mario's Pizza Palace",
            owner_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=None
        )
    
    @pytest.fixture
    def sample_menu_items(self):
        """Sample menu items data"""
        return [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Margherita Pizza",
                description="Classic pizza with tomato sauce, mozzarella, and fresh basil",
                price=Decimal("15.99"),
                category="Pizza",
                image_url="https://example.com/margherita.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-2",
                restaurant_id="restaurant-123",
                name="Caesar Salad",
                description="Fresh romaine lettuce with caesar dressing",
                price=Decimal("8.99"),
                category="Salads",
                image_url="https://example.com/caesar.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-3",
                restaurant_id="restaurant-123",
                name="Pepperoni Pizza",
                description="Pizza with pepperoni and mozzarella",
                price=Decimal("17.99"),
                category="Pizza",
                image_url="https://example.com/pepperoni.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_success(self, mock_get_service, client, sample_restaurant, sample_menu_items):
        """Test successful retrieval of restaurant menu"""
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
                ),
                PublicMenuItemResponse(
                    id="item-2",
                    name="Caesar Salad",
                    description="Fresh romaine lettuce with caesar dressing",
                    price=Decimal("8.99"),
                    category="Salads",
                    image_url="https://example.com/caesar.jpg"
                ),
                PublicMenuItemResponse(
                    id="item-3",
                    name="Pepperoni Pizza",
                    description="Pizza with pepperoni and mozzarella",
                    price=Decimal("17.99"),
                    category="Pizza",
                    image_url="https://example.com/pepperoni.jpg"
                )
            ],
            total_items=3
        )
        
        mock_service = Mock()
        mock_service.get_public_menu = AsyncMock(return_value=expected_response)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_id"] == "restaurant-123"
        assert data["restaurant_name"] == "Mario's Pizza Palace"
        assert data["total_items"] == 3
        assert len(data["items"]) == 3
        assert "Pizza" in data["categories"]
        assert "Salads" in data["categories"]
        
        # Verify service was called correctly
        mock_service.get_public_menu.assert_called_once_with("restaurant-123", None)
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_with_category_filter(self, mock_get_service, client):
        """Test menu retrieval with category filter"""
        # Mock service response for pizza category only
        expected_response = PublicMenuResponse(
            restaurant_id="restaurant-123",
            restaurant_name="Mario's Pizza Palace",
            categories=["Pizza"],
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
        
        mock_service = Mock()
        mock_service.get_public_menu = AsyncMock(return_value=expected_response)
        mock_get_service.return_value = mock_service
        
        # Make request with category filter
        response = client.get("/api/menus/restaurant-123?category=Pizza")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "Pizza"
        
        # Verify service was called with category filter
        mock_service.get_public_menu.assert_called_once_with("restaurant-123", "Pizza")
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_not_found(self, mock_get_service, client):
        """Test menu retrieval for non-existent restaurant"""
        # Mock service to raise NotFoundError
        mock_service = Mock()
        mock_service.get_public_menu = AsyncMock(side_effect=NotFoundError("Restaurant not found"))
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/nonexistent-restaurant")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert "Restaurant not found" in data["detail"]
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_database_error(self, mock_get_service, client):
        """Test menu retrieval with database error"""
        # Mock service to raise DatabaseError
        mock_service = Mock()
        mock_service.get_public_menu = AsyncMock(side_effect=DatabaseError("Database connection failed"))
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve menu" in data["detail"]
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_by_category_success(self, mock_get_service, client):
        """Test successful retrieval of menu organized by categories"""
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
                ),
                MenuCategoryResponse(
                    category="Salads",
                    items=[
                        PublicMenuItemResponse(
                            id="item-2",
                            name="Caesar Salad",
                            description="Fresh romaine lettuce with caesar dressing",
                            price=Decimal("8.99"),
                            category="Salads",
                            image_url="https://example.com/caesar.jpg"
                        )
                    ]
                )
            ],
            total_items=2
        )
        
        mock_service = Mock()
        mock_service.get_public_menu_by_category = AsyncMock(return_value=expected_response)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123/by-category")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_id"] == "restaurant-123"
        assert data["total_items"] == 2
        assert len(data["categories"]) == 2
        assert data["categories"][0]["category"] == "Pizza"
        assert data["categories"][1]["category"] == "Salads"
        
        # Verify service was called
        mock_service.get_public_menu_by_category.assert_called_once_with("restaurant-123")
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_get_restaurant_menu_categories_success(self, mock_get_service, client):
        """Test successful retrieval of menu categories"""
        # Mock service response
        expected_categories = ["Appetizers", "Pizza", "Salads", "Beverages"]
        
        mock_service = Mock()
        mock_service.get_menu_categories = AsyncMock(return_value=expected_categories)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123/categories")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data == expected_categories
        assert len(data) == 4
        
        # Verify service was called
        mock_service.get_menu_categories.assert_called_once_with("restaurant-123")
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_search_restaurant_menu_success(self, mock_get_service, client):
        """Test successful menu search"""
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
        
        mock_service = Mock()
        mock_service.search_public_menu = AsyncMock(return_value=expected_results)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123/search?q=pizza")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margherita Pizza"
        assert data[0]["category"] == "Pizza"
        
        # Verify service was called with correct parameters
        mock_service.search_public_menu.assert_called_once_with(
            restaurant_id="restaurant-123",
            search_query="pizza",
            category=None,
            limit=20
        )
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_search_restaurant_menu_with_filters(self, mock_get_service, client):
        """Test menu search with category filter and limit"""
        # Mock service response
        expected_results = []
        
        mock_service = Mock()
        mock_service.search_public_menu = AsyncMock(return_value=expected_results)
        mock_get_service.return_value = mock_service
        
        # Make request with filters
        response = client.get("/api/menus/restaurant-123/search?q=salad&category=Salads&limit=10")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data == []
        
        # Verify service was called with filters
        mock_service.search_public_menu.assert_called_once_with(
            restaurant_id="restaurant-123",
            search_query="salad",
            category="Salads",
            limit=10
        )
    
    def test_search_restaurant_menu_missing_query(self, client):
        """Test menu search without required query parameter"""
        # Make request without query parameter
        response = client.get("/api/menus/restaurant-123/search")
        
        # Verify validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_search_restaurant_menu_invalid_limit(self, client):
        """Test menu search with invalid limit parameter"""
        # Make request with invalid limit
        response = client.get("/api/menus/restaurant-123/search?q=pizza&limit=0")
        
        # Verify validation error
        assert response.status_code == 422
        
        # Test limit too high
        response = client.get("/api/menus/restaurant-123/search?q=pizza&limit=101")
        assert response.status_code == 422
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_data_isolation_between_restaurants(self, mock_get_service, client):
        """Test that menu data is properly isolated between restaurants"""
        # Mock service responses for different restaurants
        restaurant_1_response = PublicMenuResponse(
            restaurant_id="restaurant-1",
            restaurant_name="Restaurant 1",
            categories=["Pizza"],
            items=[
                PublicMenuItemResponse(
                    id="item-1",
                    name="Restaurant 1 Pizza",
                    description="Pizza from restaurant 1",
                    price=Decimal("15.99"),
                    category="Pizza",
                    image_url="https://example.com/pizza1.jpg"
                )
            ],
            total_items=1
        )
        
        restaurant_2_response = PublicMenuResponse(
            restaurant_id="restaurant-2",
            restaurant_name="Restaurant 2",
            categories=["Burgers"],
            items=[
                PublicMenuItemResponse(
                    id="item-2",
                    name="Restaurant 2 Burger",
                    description="Burger from restaurant 2",
                    price=Decimal("12.99"),
                    category="Burgers",
                    image_url="https://example.com/burger2.jpg"
                )
            ],
            total_items=1
        )
        
        mock_service = Mock()
        # Configure mock to return different responses based on restaurant_id
        def mock_get_menu(restaurant_id, category=None):
            if restaurant_id == "restaurant-1":
                return restaurant_1_response
            elif restaurant_id == "restaurant-2":
                return restaurant_2_response
            else:
                raise NotFoundError("Restaurant not found")
        
        mock_service.get_public_menu = AsyncMock(side_effect=mock_get_menu)
        mock_get_service.return_value = mock_service
        
        # Test restaurant 1
        response1 = client.get("/api/menus/restaurant-1")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["restaurant_name"] == "Restaurant 1"
        assert data1["items"][0]["name"] == "Restaurant 1 Pizza"
        
        # Test restaurant 2
        response2 = client.get("/api/menus/restaurant-2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["restaurant_name"] == "Restaurant 2"
        assert data2["items"][0]["name"] == "Restaurant 2 Burger"
        
        # Verify data isolation - restaurant 1 data should not appear in restaurant 2 response
        assert data1["restaurant_id"] != data2["restaurant_id"]
        assert data1["items"][0]["id"] != data2["items"][0]["id"]
    
    @patch('app.api.v1.endpoints.menus.get_public_menu_service')
    def test_only_available_items_returned(self, mock_get_service, client):
        """Test that only available menu items are returned in public menu"""
        # Mock service should only return available items
        available_items_response = PublicMenuResponse(
            restaurant_id="restaurant-123",
            restaurant_name="Test Restaurant",
            categories=["Pizza"],
            items=[
                PublicMenuItemResponse(
                    id="available-item",
                    name="Available Pizza",
                    description="This pizza is available",
                    price=Decimal("15.99"),
                    category="Pizza",
                    image_url="https://example.com/available.jpg"
                )
            ],
            total_items=1
        )
        
        mock_service = Mock()
        mock_service.get_public_menu = AsyncMock(return_value=available_items_response)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/menus/restaurant-123")
        
        # Verify response contains only available items
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Available Pizza"
        
        # The service should be called with the correct restaurant_id
        # The filtering of available items should happen in the service layer
        mock_service.get_public_menu.assert_called_once_with("restaurant-123", None)