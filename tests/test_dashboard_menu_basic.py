"""Basic tests for dashboard menu management endpoints"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from main import app
from app.models.menu_item import MenuItem


class TestDashboardMenuBasic:
    """Basic test suite for dashboard menu management endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
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
    
    def test_get_restaurant_menu_items_success(self, client, sample_menu_item):
        """Test successful retrieval of restaurant menu items"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_service = AsyncMock()
        mock_service.get_by_restaurant.return_value = [sample_menu_item]
        
        with patch('app.core.auth.get_current_user', return_value=(mock_user, "restaurant-123")), \
             patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service):
            
            headers = {"Authorization": "Bearer test-token"}
            response = client.get("/api/dashboard/menu", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Test Pizza"
            
            mock_service.get_by_restaurant.assert_called_once_with(
                restaurant_id="restaurant-123",
                include_unavailable=True,
                category=None,
                skip=0,
                limit=100
            )
    
    def test_create_menu_item_success(self, client, sample_menu_item):
        """Test successful menu item creation"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_service = AsyncMock()
        mock_service.create_menu_item.return_value = sample_menu_item
        
        menu_item_data = {
            "name": "Test Pizza",
            "description": "A delicious test pizza",
            "price": "15.99",
            "category": "Pizza",
            "image_url": "https://example.com/pizza.jpg",
            "is_available": True
        }
        
        with patch('app.core.auth.get_current_user', return_value=(mock_user, "restaurant-123")), \
             patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service):
            
            headers = {"Authorization": "Bearer test-token"}
            response = client.post("/api/dashboard/menu", json=menu_item_data, headers=headers)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Pizza"
            assert data["restaurant_id"] == "restaurant-123"
            
            mock_service.create_menu_item.assert_called_once()
    
    def test_get_menu_item_success(self, client, sample_menu_item):
        """Test successful menu item retrieval by ID"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_service = AsyncMock()
        mock_service.get_menu_item_for_restaurant.return_value = sample_menu_item
        
        with patch('app.core.auth.get_current_user', return_value=(mock_user, "restaurant-123")), \
             patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service):
            
            headers = {"Authorization": "Bearer test-token"}
            response = client.get("/api/dashboard/menu/item-123", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "item-123"
            assert data["name"] == "Test Pizza"
            
            mock_service.get_menu_item_for_restaurant.assert_called_once_with(
                "item-123", "restaurant-123"
            )
    
    def test_update_menu_item_success(self, client, sample_menu_item):
        """Test successful menu item update"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        updated_item = sample_menu_item.copy()
        updated_item.name = "Updated Pizza"
        updated_item.price = Decimal("17.99")
        
        mock_service = AsyncMock()
        mock_service.update_menu_item_for_restaurant.return_value = updated_item
        
        update_data = {
            "name": "Updated Pizza",
            "price": "17.99"
        }
        
        with patch('app.core.auth.get_current_user', return_value=(mock_user, "restaurant-123")), \
             patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service):
            
            headers = {"Authorization": "Bearer test-token"}
            response = client.put("/api/dashboard/menu/item-123", json=update_data, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Pizza"
            assert data["price"] == "17.99"
            
            mock_service.update_menu_item_for_restaurant.assert_called_once()
    
    def test_delete_menu_item_success(self, client):
        """Test successful menu item deletion"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_service = AsyncMock()
        mock_service.delete_menu_item_for_restaurant.return_value = True
        
        with patch('app.core.auth.get_current_user', return_value=(mock_user, "restaurant-123")), \
             patch('app.api.v1.endpoints.dashboard_menu.get_menu_item_service', return_value=mock_service):
            
            headers = {"Authorization": "Bearer test-token"}
            response = client.delete("/api/dashboard/menu/item-123", headers=headers)
            
            assert response.status_code == 204
            
            mock_service.delete_menu_item_for_restaurant.assert_called_once_with(
                "item-123", "restaurant-123"
            )
    
    def test_unauthorized_access(self, client):
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