"""Integration tests for dashboard menu management endpoints"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from main import app
from app.models.menu_item import MenuItem


class TestDashboardMenuIntegration:
    """Integration test suite for dashboard menu management"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def restaurant_data(self):
        """Sample restaurant data for testing"""
        return {
            "restaurant_name": "Test Restaurant",
            "email": "test@restaurant.com",
            "password": "TestPassword123"
        }
    
    @pytest.fixture
    def menu_item_data(self):
        """Sample menu item data for testing"""
        return {
            "name": "Integration Test Pizza",
            "description": "A pizza created during integration testing",
            "price": "18.99",
            "category": "Pizza",
            "image_url": "https://example.com/test-pizza.jpg",
            "is_available": True
        }
    
    @pytest.fixture
    def auth_headers(self, client: TestClient, restaurant_data):
        """Get authentication headers by registering and logging in"""
        # Register restaurant
        register_response = client.post("/api/auth/register", json=restaurant_data)
        print(f"Register response: {register_response.status_code}, {register_response.content}")
        assert register_response.status_code == 201
        
        # Login to get token
        login_data = {
            "email": restaurant_data["email"],
            "password": restaurant_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_complete_menu_management_workflow(
        self, client: TestClient, auth_headers, menu_item_data
    ):
        """Test complete CRUD workflow for menu management"""
        
        # 1. Initially, restaurant should have no menu items
        response = client.get("/api/dashboard/menu", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
        
        # 2. Create a new menu item
        create_response = client.post(
            "/api/dashboard/menu", 
            json=menu_item_data, 
            headers=auth_headers
        )
        assert create_response.status_code == 201
        created_item = create_response.json()
        
        assert created_item["name"] == menu_item_data["name"]
        assert created_item["price"] == menu_item_data["price"]
        assert created_item["category"] == menu_item_data["category"]
        assert created_item["is_available"] is True
        assert "id" in created_item
        assert "restaurant_id" in created_item
        assert "created_at" in created_item
        
        item_id = created_item["id"]
        
        # 3. Verify item appears in restaurant menu list
        list_response = client.get("/api/dashboard/menu", headers=auth_headers)
        assert list_response.status_code == 200
        menu_items = list_response.json()
        assert len(menu_items) == 1
        assert menu_items[0]["id"] == item_id
        
        # 4. Get specific menu item by ID
        get_response = client.get(f"/api/dashboard/menu/{item_id}", headers=auth_headers)
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        assert retrieved_item["id"] == item_id
        assert retrieved_item["name"] == menu_item_data["name"]
        
        # 5. Update the menu item
        update_data = {
            "name": "Updated Integration Test Pizza",
            "price": "21.99",
            "description": "Updated description for integration testing"
        }
        update_response = client.put(
            f"/api/dashboard/menu/{item_id}", 
            json=update_data, 
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_item = update_response.json()
        
        assert updated_item["name"] == update_data["name"]
        assert updated_item["price"] == update_data["price"]
        assert updated_item["description"] == update_data["description"]
        assert updated_item["category"] == menu_item_data["category"]  # Unchanged
        assert "updated_at" in updated_item
        
        # 6. Toggle availability
        toggle_response = client.patch(
            f"/api/dashboard/menu/{item_id}/availability?is_available=false",
            headers=auth_headers
        )
        assert toggle_response.status_code == 200
        toggled_item = toggle_response.json()
        assert toggled_item["is_available"] is False
        
        # 7. Verify unavailable item is still in dashboard list (include_unavailable=true by default)
        list_response = client.get("/api/dashboard/menu", headers=auth_headers)
        assert list_response.status_code == 200
        menu_items = list_response.json()
        assert len(menu_items) == 1
        assert menu_items[0]["is_available"] is False
        
        # 8. Verify unavailable item is excluded when include_unavailable=false
        list_response = client.get(
            "/api/dashboard/menu?include_unavailable=false", 
            headers=auth_headers
        )
        assert list_response.status_code == 200
        menu_items = list_response.json()
        assert len(menu_items) == 0
        
        # 9. Delete the menu item
        delete_response = client.delete(f"/api/dashboard/menu/{item_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # 10. Verify item is deleted
        get_response = client.get(f"/api/dashboard/menu/{item_id}", headers=auth_headers)
        assert get_response.status_code == 404
        
        list_response = client.get("/api/dashboard/menu", headers=auth_headers)
        assert list_response.status_code == 200
        assert response.json() == []
    
    def test_menu_filtering_and_pagination(
        self, client: TestClient, auth_headers
    ):
        """Test menu filtering and pagination functionality"""
        
        # Create multiple menu items with different categories
        menu_items = [
            {
                "name": "Margherita Pizza",
                "price": "15.99",
                "category": "Pizza",
                "is_available": True
            },
            {
                "name": "Pepperoni Pizza", 
                "price": "17.99",
                "category": "Pizza",
                "is_available": True
            },
            {
                "name": "Cheeseburger",
                "price": "12.99", 
                "category": "Burgers",
                "is_available": True
            },
            {
                "name": "Veggie Burger",
                "price": "11.99",
                "category": "Burgers", 
                "is_available": False
            },
            {
                "name": "Caesar Salad",
                "price": "9.99",
                "category": "Salads",
                "is_available": True
            }
        ]
        
        created_items = []
        for item_data in menu_items:
            response = client.post("/api/dashboard/menu", json=item_data, headers=auth_headers)
            assert response.status_code == 201
            created_items.append(response.json())
        
        # Test category filtering
        pizza_response = client.get(
            "/api/dashboard/menu?category=Pizza", 
            headers=auth_headers
        )
        assert pizza_response.status_code == 200
        pizza_items = pizza_response.json()
        assert len(pizza_items) == 2
        assert all(item["category"] == "Pizza" for item in pizza_items)
        
        # Test availability filtering
        available_response = client.get(
            "/api/dashboard/menu?include_unavailable=false",
            headers=auth_headers
        )
        assert available_response.status_code == 200
        available_items = available_response.json()
        assert len(available_items) == 4  # All except Veggie Burger
        assert all(item["is_available"] for item in available_items)
        
        # Test pagination
        page1_response = client.get(
            "/api/dashboard/menu?limit=2&skip=0",
            headers=auth_headers
        )
        assert page1_response.status_code == 200
        page1_items = page1_response.json()
        assert len(page1_items) == 2
        
        page2_response = client.get(
            "/api/dashboard/menu?limit=2&skip=2",
            headers=auth_headers
        )
        assert page2_response.status_code == 200
        page2_items = page2_response.json()
        assert len(page2_items) == 2
        
        # Verify no overlap between pages
        page1_ids = {item["id"] for item in page1_items}
        page2_ids = {item["id"] for item in page2_items}
        assert page1_ids.isdisjoint(page2_ids)
        
        # Test combined filters
        combined_response = client.get(
            "/api/dashboard/menu?category=Burgers&include_unavailable=false",
            headers=auth_headers
        )
        assert combined_response.status_code == 200
        combined_items = combined_response.json()
        assert len(combined_items) == 1  # Only Cheeseburger
        assert combined_items[0]["name"] == "Cheeseburger"
    
    def test_menu_categories_endpoint(
        self, client: TestClient, auth_headers
    ):
        """Test menu categories listing endpoint"""
        
        # Initially no categories
        response = client.get("/api/dashboard/menu/categories/list", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
        
        # Create items in different categories
        menu_items = [
            {"name": "Pizza Item", "price": "15.99", "category": "Pizza", "is_available": True},
            {"name": "Burger Item", "price": "12.99", "category": "Burgers", "is_available": True},
            {"name": "Salad Item", "price": "9.99", "category": "Salads", "is_available": True},
            {"name": "Unavailable Item", "price": "8.99", "category": "Desserts", "is_available": False}
        ]
        
        for item_data in menu_items:
            response = client.post("/api/dashboard/menu", json=item_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Get categories (should only include categories with available items)
        response = client.get("/api/dashboard/menu/categories/list", headers=auth_headers)
        assert response.status_code == 200
        categories = response.json()
        
        # Should be sorted and only include available categories
        expected_categories = ["Burgers", "Pizza", "Salads"]  # Desserts excluded (unavailable)
        assert categories == expected_categories
    
    def test_restaurant_isolation(
        self, client: TestClient, menu_item_data
    ):
        """Test that restaurants can only access their own menu items"""
        
        # Create two restaurants
        restaurant1_data = {
            "name": "Restaurant 1",
            "email": "restaurant1@test.com", 
            "password": "password123"
        }
        restaurant2_data = {
            "name": "Restaurant 2",
            "email": "restaurant2@test.com",
            "password": "password123"
        }
        
        # Register both restaurants
        client.post("/api/auth/register", json=restaurant1_data)
        client.post("/api/auth/register", json=restaurant2_data)
        
        # Get auth tokens for both
        login1 = client.post("/api/auth/login", json={
            "email": restaurant1_data["email"],
            "password": restaurant1_data["password"]
        })
        login2 = client.post("/api/auth/login", json={
            "email": restaurant2_data["email"], 
            "password": restaurant2_data["password"]
        })
        
        headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
        
        # Restaurant 1 creates a menu item
        create_response = client.post(
            "/api/dashboard/menu",
            json=menu_item_data,
            headers=headers1
        )
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]
        
        # Restaurant 1 can see their item
        response = client.get("/api/dashboard/menu", headers=headers1)
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        # Restaurant 2 cannot see Restaurant 1's item
        response = client.get("/api/dashboard/menu", headers=headers2)
        assert response.status_code == 200
        assert len(response.json()) == 0
        
        # Restaurant 2 cannot access Restaurant 1's item directly
        response = client.get(f"/api/dashboard/menu/{item_id}", headers=headers2)
        assert response.status_code == 404
        
        # Restaurant 2 cannot update Restaurant 1's item
        response = client.put(
            f"/api/dashboard/menu/{item_id}",
            json={"name": "Hacked Item"},
            headers=headers2
        )
        assert response.status_code == 404
        
        # Restaurant 2 cannot delete Restaurant 1's item
        response = client.delete(f"/api/dashboard/menu/{item_id}", headers=headers2)
        assert response.status_code == 404
    
    def test_error_handling(
        self, client: TestClient, auth_headers
    ):
        """Test error handling for various scenarios"""
        
        # Test invalid menu item data
        invalid_data = {
            "name": "",  # Empty name
            "price": "-5.00",  # Negative price
            "category": ""  # Empty category
        }
        response = client.post("/api/dashboard/menu", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Test accessing non-existent item
        response = client.get("/api/dashboard/menu/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
        
        # Test updating non-existent item
        response = client.put(
            "/api/dashboard/menu/nonexistent-id",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test deleting non-existent item
        response = client.delete("/api/dashboard/menu/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
        
        # Test invalid query parameters
        response = client.get("/api/dashboard/menu?skip=-1", headers=auth_headers)
        assert response.status_code == 422
        
        response = client.get("/api/dashboard/menu?limit=0", headers=auth_headers)
        assert response.status_code == 422
        
        response = client.get("/api/dashboard/menu?limit=1000", headers=auth_headers)
        assert response.status_code == 422
    
    def test_partial_updates(
        self, client: TestClient, auth_headers, menu_item_data
    ):
        """Test partial updates of menu items"""
        
        # Create a menu item
        create_response = client.post("/api/dashboard/menu", json=menu_item_data, headers=auth_headers)
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]
        original_item = create_response.json()
        
        # Update only the name
        update_response = client.put(
            f"/api/dashboard/menu/{item_id}",
            json={"name": "Partially Updated Pizza"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_item = update_response.json()
        
        # Verify only name changed
        assert updated_item["name"] == "Partially Updated Pizza"
        assert updated_item["price"] == original_item["price"]
        assert updated_item["category"] == original_item["category"]
        assert updated_item["description"] == original_item["description"]
        
        # Update only availability
        availability_response = client.put(
            f"/api/dashboard/menu/{item_id}",
            json={"is_available": False},
            headers=auth_headers
        )
        assert availability_response.status_code == 200
        availability_item = availability_response.json()
        
        # Verify only availability changed
        assert availability_item["is_available"] is False
        assert availability_item["name"] == "Partially Updated Pizza"  # From previous update
        assert availability_item["price"] == original_item["price"]
