"""Simple integration tests for order endpoints without database dependencies"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from decimal import Decimal
from datetime import datetime

# Mock the database services before importing the app
with patch('app.database.supabase_client.supabase_client'):
    from main import app

from app.models.order import Order, OrderItem
from app.models.menu_item import MenuItem
from app.models.customer import CustomerProfile
from app.models.enums import OrderStatus, PaymentStatus


class TestOrderEndpointsSimple:
    """Simple test cases for order endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_menu_items(self):
        """Sample menu items for testing"""
        return [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Burger",
                description="Delicious burger",
                price=Decimal("15.99"),
                category="Main",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-2",
                restaurant_id="restaurant-123",
                name="Fries",
                description="Crispy fries",
                price=Decimal("5.99"),
                category="Sides",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
    
    @pytest.fixture
    def sample_order(self):
        """Sample order for testing"""
        return Order(
            id="order-123",
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            total_price=Decimal("21.98"),
            created_at=datetime.utcnow(),
            updated_at=None,
            items=[
                OrderItem(
                    id="order-item-1",
                    order_id="order-123",
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99"),
                    created_at=datetime.utcnow(),
                    updated_at=None
                ),
                OrderItem(
                    id="order-item-2",
                    order_id="order-123",
                    menu_item_id="item-2",
                    quantity=1,
                    unit_price=Decimal("5.99"),
                    created_at=datetime.utcnow(),
                    updated_at=None
                )
            ]
        )
    
    @pytest.fixture
    def sample_customer(self):
        """Sample customer profile"""
        return CustomerProfile(
            id="customer-123",
            restaurant_id="restaurant-123",
            phone_number="+1234567890",
            name="John Doe",
            last_order_at=None,
            created_at=datetime.utcnow(),
            updated_at=None
        )
    
    @patch('app.database.service_factory.get_order_service')
    @patch('app.database.service_factory.get_menu_item_service')
    @patch('app.database.service_factory.get_customer_service')
    def test_create_order_success(
        self, 
        mock_get_customer_service, 
        mock_get_menu_service, 
        mock_get_order_service,
        client, 
        sample_menu_items, 
        sample_order, 
        sample_customer
    ):
        """Test successful order creation"""
        # Mock services
        mock_menu_service = AsyncMock()
        mock_order_service = AsyncMock()
        mock_customer_service = AsyncMock()
        
        mock_get_menu_service.return_value = mock_menu_service
        mock_get_order_service.return_value = mock_order_service
        mock_get_customer_service.return_value = mock_customer_service
        
        # Mock service responses
        mock_menu_service.get_menu_items_by_ids.return_value = sample_menu_items
        mock_customer_service.create_or_update_customer.return_value = sample_customer
        mock_order_service.create_order_with_items.return_value = sample_order
        mock_customer_service.update_last_order_time.return_value = sample_customer
        
        # Order data
        order_data = {
            "restaurant_id": "restaurant-123",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "21.98",
            "items": [
                {
                    "menu_item_id": "item-1",
                    "quantity": 1,
                    "unit_price": "15.99"
                },
                {
                    "menu_item_id": "item-2",
                    "quantity": 1,
                    "unit_price": "5.99"
                }
            ]
        }
        
        # Make request
        response = client.post("/api/orders/", json=order_data)
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "order-123"
        assert data["restaurant_id"] == "restaurant-123"
        assert data["table_number"] == 5
        assert data["customer_name"] == "John Doe"
        assert data["order_status"] == "pending"
        assert data["total_price"] == "21.98"
        assert len(data["items"]) == 2
        
        # Verify service calls
        mock_menu_service.get_menu_items_by_ids.assert_called_once()
        mock_customer_service.create_or_update_customer.assert_called_once()
        mock_order_service.create_order_with_items.assert_called_once()
        mock_customer_service.update_last_order_time.assert_called_once()
    
    def test_create_order_validation_error(self, client):
        """Test order creation with validation errors"""
        # Order data with invalid table number
        order_data = {
            "restaurant_id": "restaurant-123",
            "table_number": 0,  # Invalid
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "21.98",
            "items": [
                {
                    "menu_item_id": "item-1",
                    "quantity": 1,
                    "unit_price": "15.99"
                }
            ]
        }
        
        response = client.post("/api/orders/", json=order_data)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_order_empty_items(self, client):
        """Test order creation with empty items list"""
        order_data = {
            "restaurant_id": "restaurant-123",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "0.00",
            "items": []
        }
        
        response = client.post("/api/orders/", json=order_data)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @patch('app.database.service_factory.get_menu_item_service')
    def test_create_order_menu_item_not_found(
        self, 
        mock_get_menu_service,
        client
    ):
        """Test order creation with non-existent menu item"""
        # Mock service
        mock_menu_service = AsyncMock()
        mock_get_menu_service.return_value = mock_menu_service
        
        # Mock empty menu items response (item not found)
        mock_menu_service.get_menu_items_by_ids.return_value = []
        
        order_data = {
            "restaurant_id": "restaurant-123",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "15.99",
            "items": [
                {
                    "menu_item_id": "nonexistent-item",
                    "quantity": 1,
                    "unit_price": "15.99"
                }
            ]
        }
        
        response = client.post("/api/orders/", json=order_data)
        
        # Should return error for missing menu item
        assert response.status_code == 400
        data = response.json()
        assert "not found or not available" in data["detail"]


class TestOrderCalculationLogic:
    """Test order calculation and validation logic"""
    
    @pytest.mark.asyncio
    async def test_order_calculation_success(self):
        """Test successful order calculation"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        from app.models.order import OrderCreate, OrderItemCreate
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        
        # Sample menu items
        menu_items = [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Burger",
                description="Delicious burger",
                price=Decimal("15.99"),
                category="Main",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-2",
                restaurant_id="restaurant-123",
                name="Fries",
                description="Crispy fries",
                price=Decimal("5.99"),
                category="Sides",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
        
        mock_menu_service.get_menu_items_by_ids.return_value = menu_items
        
        # Create order data
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("21.98"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                ),
                OrderItemCreate(
                    menu_item_id="item-2",
                    quantity=1,
                    unit_price=Decimal("5.99")
                )
            ]
        )
        
        # Test calculation
        total, validated_items = await OrderCalculationService.validate_and_calculate_order(
            order_data, mock_menu_service
        )
        
        # Assertions
        assert total == Decimal("21.98")
        assert len(validated_items) == 2
        assert validated_items[0].unit_price == Decimal("15.99")
        assert validated_items[1].unit_price == Decimal("5.99")
    
    @pytest.mark.asyncio
    async def test_order_calculation_unavailable_item(self):
        """Test order calculation with unavailable menu item"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        from app.models.order import OrderCreate, OrderItemCreate
        from fastapi import HTTPException
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        
        # Sample menu item (unavailable)
        menu_item = MenuItem(
            id="item-1",
            restaurant_id="restaurant-123",
            name="Burger",
            description="Delicious burger",
            price=Decimal("15.99"),
            category="Main",
            image_url=None,
            is_available=False,  # Unavailable
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        mock_menu_service.get_menu_items_by_ids.return_value = [menu_item]
        
        # Create order data
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("15.99"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                )
            ]
        )
        
        # Test calculation should raise exception
        with pytest.raises(HTTPException) as exc_info:
            await OrderCalculationService.validate_and_calculate_order(
                order_data, mock_menu_service
            )
        
        assert exc_info.value.status_code == 400
        assert "currently unavailable" in str(exc_info.value.detail)