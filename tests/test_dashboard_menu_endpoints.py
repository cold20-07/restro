"""Tests for dashboard menu management endpoints"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from main import app
from app.models.menu_item import MenuItem, MenuItemCreate, MenuItemUpdate
from app.database.base import NotFoundError, DatabaseError


class TestDashboardMenuEndpoints:
    """Test suite for dashboard menu management endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_menu_service(self):
        """Mock menu item service"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_menu_item(self):
        """Sample menu item for testing"""
        return MenuItem(
            id="item-123",
            restaurant_id="restaurant-123",
            name="Test Pizza",
            description="A delicious test pizza",
            price=Decimal("15.99"),
            category="Pizza",
            image_url="https://example.com/pizza.jpg",
            is_available=True,
            created_at="2024-01-15T10:30:00Z",
            updated_at=None
        )
    
    @pytest.fixture
    def sample_menu_items(self, sample_menu_item):
        """Sample list of menu items"""
        item2 = MenuItem(
            id="item-456",
            restaurant_id="restaurant-123",
            name="Test Burger",
            description="A tasty test burger",
            price=Decimal("12.99"),
            category="Burgers",
            image_url="https://example.com/burger.jpg",
            is_available=False,
            created_at="2024-01-15T11:00:00Z",
            updated_at=None
        )
        return [sample_menu_item, item2]
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for testing"""
        return {"Authorization": "Bearer test-token"}
    
    def test_get_restaurant_menu_items_success(
        self, client: TestClient, mock_menu_service, sample_menu_items, auth_headers
    ):
        """Test successful retrieval of restaurant menu items"""
        mock_menu_service.get_by_restaurant.return_value = sample_menu_items
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get("/api/dashboard/menu", headers=auth_headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Test Pizza"
            assert data[1]["name"] == "Test Burger"
            
            mock_menu_service.get_by_restaurant.assert_called_once_with(
                restaurant_id="restaurant-123",
                include_unavailable=True,
                category=None,
                skip=0,
                limit=100
            )
    
    def test_get_restaurant_menu_items_with_filters(
        self, client: TestClient, mock_menu_service, sample_menu_items, auth_headers
    ):
        """Test menu items retrieval with filters"""
        mock_menu_service.get_by_restaurant.return_value = [sample_menu_items[0]]
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get(
                "/api/dashboard/menu?include_unavailable=false&category=Pizza&skip=10&limit=50",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["category"] == "Pizza"
            
            mock_menu_service.get_by_restaurant.assert_called_once_with(
                restaurant_id="restaurant-123",
                include_unavailable=False,
                category="Pizza",
                skip=10,
                limit=50
            )
    
    def test_get_restaurant_menu_items_database_error(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test menu items retrieval with database error"""
        mock_menu_service.get_by_restaurant.side_effect = DatabaseError("Database connection failed")
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get("/api/dashboard/menu", headers=auth_headers)
            
            assert response.status_code == 500
            assert "Failed to retrieve menu items" in response.json()["detail"]
    
    def test_create_menu_item_success(
        self, client: TestClient, mock_menu_service, sample_menu_item, auth_headers
    ):
        """Test successful menu item creation"""
        mock_menu_service.create_menu_item.return_value = sample_menu_item
        
        menu_item_data = {
            "restaurant_id": "will-be-overridden",
            "name": "Test Pizza",
            "description": "A delicious test pizza",
            "price": "15.99",
            "category": "Pizza",
            "image_url": "https://example.com/pizza.jpg",
            "is_available": True
        }
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.post("/api/dashboard/menu", json=menu_item_data, headers=auth_headers)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Pizza"
            assert data["restaurant_id"] == "restaurant-123"
            
            # Verify the service was called with correct data
            mock_menu_service.create_menu_item.assert_called_once()
            call_args = mock_menu_service.create_menu_item.call_args[0][0]
            assert call_args.restaurant_id == "restaurant-123"  # Should be overridden
            assert call_args.name == "Test Pizza"
    
    def test_create_menu_item_validation_error(self, client: TestClient, auth_headers):
        """Test menu item creation with validation error"""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "price": "-5.00",  # Negative price should fail
            "category": "Pizza"
        }
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            response = client.post("/api/dashboard/menu", json=invalid_data, headers=auth_headers)
            
            assert response.status_code == 422  # Validation error
    
    def test_create_menu_item_database_error(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test menu item creation with database error"""
        mock_menu_service.create_menu_item.side_effect = DatabaseError("Failed to insert")
        
        menu_item_data = {
            "name": "Test Pizza",
            "price": "15.99",
            "category": "Pizza"
        }
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.post("/api/dashboard/menu", json=menu_item_data, headers=auth_headers)
            
            assert response.status_code == 500
            assert "Failed to create menu item" in response.json()["detail"]
    
    def test_get_menu_item_success(
        self, client: TestClient, mock_menu_service, sample_menu_item, auth_headers
    ):
        """Test successful menu item retrieval by ID"""
        mock_menu_service.get_menu_item_for_restaurant.return_value = sample_menu_item
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get("/api/dashboard/menu/item-123", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "item-123"
            assert data["name"] == "Test Pizza"
            
            mock_menu_service.get_menu_item_for_restaurant.assert_called_once_with(
                "item-123", "restaurant-123"
            )
    
    def test_get_menu_item_not_found(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test menu item retrieval when item not found"""
        mock_menu_service.get_menu_item_for_restaurant.return_value = None
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get("/api/dashboard/menu/nonexistent", headers=auth_headers)
            
            assert response.status_code == 404
            assert "Menu item not found" in response.json()["detail"]
    
    def test_update_menu_item_success(
        self, client: TestClient, mock_menu_service, sample_menu_item, auth_headers
    ):
        """Test successful menu item update"""
        updated_item = sample_menu_item.copy()
        updated_item.name = "Updated Pizza"
        updated_item.price = Decimal("17.99")
        
        mock_menu_service.update_menu_item_for_restaurant.return_value = updated_item
        
        update_data = {
            "name": "Updated Pizza",
            "price": "17.99"
        }
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.put("/api/dashboard/menu/item-123", json=update_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Pizza"
            assert data["price"] == "17.99"
            
            mock_menu_service.update_menu_item_for_restaurant.assert_called_once()
            call_args = mock_menu_service.update_menu_item_for_restaurant.call_args
            assert call_args[1]["item_id"] == "item-123"
            assert call_args[1]["restaurant_id"] == "restaurant-123"
    
    def test_update_menu_item_not_found(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test menu item update when item not found"""
        mock_menu_service.update_menu_item_for_restaurant.side_effect = NotFoundError(
            "Menu item not found"
        )
        
        update_data = {"name": "Updated Pizza"}
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.put("/api/dashboard/menu/item-123", json=update_data, headers=auth_headers)
            
            assert response.status_code == 404
            assert "Menu item not found" in response.json()["detail"]
    
    def test_delete_menu_item_success(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test successful menu item deletion"""
        mock_menu_service.delete_menu_item_for_restaurant.return_value = True
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.delete("/api/dashboard/menu/item-123", headers=auth_headers)
            
            assert response.status_code == 204
            assert response.content == b""
            
            mock_menu_service.delete_menu_item_for_restaurant.assert_called_once_with(
                "item-123", "restaurant-123"
            )
    
    def test_delete_menu_item_not_found(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test menu item deletion when item not found"""
        mock_menu_service.delete_menu_item_for_restaurant.side_effect = NotFoundError(
            "Menu item not found"
        )
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.delete("/api/dashboard/menu/item-123", headers=auth_headers)
            
            assert response.status_code == 404
            assert "Menu item not found" in response.json()["detail"]
    
    def test_toggle_menu_item_availability_success(
        self, client: TestClient, mock_menu_service, sample_menu_item, auth_headers
    ):
        """Test successful menu item availability toggle"""
        updated_item = sample_menu_item.copy()
        updated_item.is_available = False
        
        mock_menu_service.toggle_availability.return_value = updated_item
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.patch(
                "/api/dashboard/menu/item-123/availability?is_available=false",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_available"] is False
            
            mock_menu_service.toggle_availability.assert_called_once_with(
                item_id="item-123",
                restaurant_id="restaurant-123",
                is_available=False
            )
    
    def test_get_menu_categories_success(
        self, client: TestClient, mock_menu_service, auth_headers
    ):
        """Test successful menu categories retrieval"""
        categories = ["Pizza", "Burgers", "Salads", "Drinks"]
        mock_menu_service.get_categories_for_restaurant.return_value = categories
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_menu_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            response = client.get("/api/dashboard/menu/categories/list", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data == categories
            
            mock_menu_service.get_categories_for_restaurant.assert_called_once_with("restaurant-123")
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication"""
        # Test without auth headers
        response = client.get("/api/dashboard/menu")
        assert response.status_code == 403  # Should be unauthorized
        
        response = client.post("/api/dashboard/menu", json={"name": "Test"})
        assert response.status_code == 403
        
        response = client.put("/api/dashboard/menu/item-123", json={"name": "Test"})
        assert response.status_code == 403
        
        response = client.delete("/api/dashboard/menu/item-123")
        assert response.status_code == 403
    
    def test_invalid_query_parameters(self, client: TestClient, auth_headers):
        """Test endpoints with invalid query parameters"""
        with patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            # Test negative skip
            response = client.get("/api/dashboard/menu?skip=-1", headers=auth_headers)
            assert response.status_code == 422
            
            # Test limit too high
            response = client.get("/api/dashboard/menu?limit=1000", headers=auth_headers)
            assert response.status_code == 422
            
            # Test limit too low
            response = client.get("/api/dashboard/menu?limit=0", headers=auth_headers)
            assert response.status_code == 422


class TestDashboardMenuAuthorization:
    """Test suite for dashboard menu authorization"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for testing"""
        return {"Authorization": "Bearer test-token"}
    
    def test_restaurant_isolation(self, client: TestClient, auth_headers):
        """Test that restaurants can only access their own menu items"""
        mock_service = AsyncMock()
        
        # Mock the service to verify restaurant_id is passed correctly
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-456"):
            
            # Test GET request
            client.get("/api/dashboard/menu", headers=auth_headers)
            mock_service.get_by_restaurant.assert_called_with(
                restaurant_id="restaurant-456",
                include_unavailable=True,
                category=None,
                skip=0,
                limit=100
            )
            
            # Test POST request
            menu_data = {"name": "Test Item", "price": "10.00", "category": "Test"}
            client.post("/api/dashboard/menu", json=menu_data, headers=auth_headers)
            
            # Verify restaurant_id was set correctly in create call
            create_call = mock_service.create_menu_item.call_args[0][0]
            assert create_call.restaurant_id == "restaurant-456"
    
    def test_cross_restaurant_access_prevention(self, client: TestClient, auth_headers):
        """Test that users cannot access menu items from other restaurants"""
        mock_service = AsyncMock()
        mock_service.get_menu_item_for_restaurant.return_value = None
        
        with patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service), \
             patch('app.api.v1.endpoints.dashboard_menu.get_current_restaurant_id', return_value="restaurant-123"):
            
            # Try to access item from different restaurant
            response = client.get("/api/dashboard/menu/item-from-other-restaurant", headers=auth_headers)
            
            # Should call service with correct restaurant_id
            mock_service.get_menu_item_for_restaurant.assert_called_once_with(
                "item-from-other-restaurant", "restaurant-123"
            )
            
            # Should return 404 since item doesn't belong to this restaurant
            assert response.status_code == 404
