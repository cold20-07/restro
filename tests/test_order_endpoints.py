"""Integration tests for order management endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

from main import app
from app.models.order import Order, OrderCreate, OrderUpdate, OrderItem, OrderItemCreate
from app.models.menu_item import MenuItem
from app.models.customer import CustomerProfile
from app.models.enums import OrderStatus, PaymentStatus
from app.database.base import DatabaseError, NotFoundError


class TestOrderEndpoints:
    """Test cases for order management API endpoints"""
    
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
    def sample_order_create(self):
        """Sample order creation data"""
        return {
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
    
    @patch('app.api.v1.endpoints.orders.get_order_service')
    @patch('app.api.v1.endpoints.orders.get_menu_item_service')
    @patch('app.api.v1.endpoints.orders.get_customer_service')
    def test_create_order_success(
        self, 
        mock_get_customer_service, 
        mock_get_menu_service, 
        mock_get_order_service,
        client, 
        sample_order_create, 
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
        
        # Make request
        response = client.post("/api/orders/", json=sample_order_create)
        
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
    
    @patch('app.api.v1.endpoints.orders.get_menu_item_service')
    def test_create_order_invalid_menu_item(
        self, 
        mock_get_menu_service,
        client, 
        sample_order_create
    ):
        """Test order creation with invalid menu item"""
        # Mock service
        mock_menu_service = AsyncMock()
        mock_get_menu_service.return_value = mock_menu_service
        
        # Mock empty menu items response (item not found)
        mock_menu_service.get_menu_items_by_ids.return_value = []
        
        # Make request
        response = client.post("/api/orders/", json=sample_order_create)
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "not found or not available" in data["detail"]
    
    @patch('app.api.v1.endpoints.orders.get_menu_item_service')
    def test_create_order_unavailable_menu_item(
        self, 
        mock_get_menu_service,
        client, 
        sample_order_create, 
        sample_menu_items
    ):
        """Test order creation with unavailable menu item"""
        # Mock service
        mock_menu_service = AsyncMock()
        mock_get_menu_service.return_value = mock_menu_service
        
        # Make first menu item unavailable
        sample_menu_items[0].is_available = False
        mock_menu_service.get_menu_items_by_ids.return_value = sample_menu_items
        
        # Make request
        response = client.post("/api/orders/", json=sample_order_create)
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "currently unavailable" in data["detail"]
    
    @patch('app.api.v1.endpoints.orders.get_menu_item_service')
    def test_create_order_price_mismatch(
        self, 
        mock_get_menu_service,
        client, 
        sample_order_create, 
        sample_menu_items
    ):
        """Test order creation with price mismatch"""
        # Mock service
        mock_menu_service = AsyncMock()
        mock_get_menu_service.return_value = mock_menu_service
        mock_menu_service.get_menu_items_by_ids.return_value = sample_menu_items
        
        # Modify order total to create mismatch
        sample_order_create["total_price"] = "50.00"
        
        # Make request
        response = client.post("/api/orders/", json=sample_order_create)
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Price mismatch" in data["detail"]
    
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
        
        assert response.status_code == 400
        data = response.json()
        assert "at least one item" in data["detail"]
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_get_order_success(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client, 
        sample_order
    ):
        """Test successful order retrieval"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        mock_order_service.get_order_for_restaurant.return_value = sample_order
        
        # Make request
        response = client.get("/api/orders/order-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "order-123"
        assert data["restaurant_id"] == "restaurant-123"
        
        # Verify service call
        mock_order_service.get_order_for_restaurant.assert_called_once_with(
            order_id="order-123",
            restaurant_id="restaurant-123",
            include_items=True
        )
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_get_order_not_found(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client
    ):
        """Test order retrieval when order not found"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        mock_order_service.get_order_for_restaurant.return_value = None
        
        # Make request
        response = client.get("/api/orders/nonexistent-order")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_update_order_status_success(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client, 
        sample_order
    ):
        """Test successful order status update"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        
        # Mock current order for validation
        current_order = sample_order.copy()
        current_order.order_status = OrderStatus.PENDING
        
        # Mock updated order
        updated_order = sample_order.copy()
        updated_order.order_status = OrderStatus.CONFIRMED
        
        mock_order_service.get_order_for_restaurant.side_effect = [
            current_order,  # First call for validation
            updated_order   # Second call for final result
        ]
        mock_order_service.update.return_value = updated_order
        
        # Make request
        update_data = {"order_status": "confirmed"}
        response = client.put("/api/orders/order-123", json=update_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "confirmed"
        
        # Verify service calls
        assert mock_order_service.get_order_for_restaurant.call_count == 2
        mock_order_service.update.assert_called_once()
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_update_order_invalid_status_transition(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client, 
        sample_order
    ):
        """Test order status update with invalid transition"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        
        # Mock current order with completed status
        current_order = sample_order.copy()
        current_order.order_status = OrderStatus.COMPLETED
        mock_order_service.get_order_for_restaurant.return_value = current_order
        
        # Make request to change completed order to pending (invalid)
        update_data = {"order_status": "pending"}
        response = client.put("/api/orders/order-123", json=update_data)
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "Invalid status transition" in data["detail"]
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_get_orders_for_restaurant(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client, 
        sample_order
    ):
        """Test getting orders for restaurant"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        mock_order_service.get_orders_for_restaurant.return_value = [sample_order]
        
        # Make request
        response = client.get("/api/orders/?skip=0&limit=10")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "order-123"
        
        # Verify service call
        mock_order_service.get_orders_for_restaurant.assert_called_once_with(
            restaurant_id="restaurant-123",
            status_filter=None,
            skip=0,
            limit=10,
            include_items=True
        )
    
    @patch('app.core.auth.get_current_restaurant_id')
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_get_orders_by_table(
        self, 
        mock_get_order_service, 
        mock_get_restaurant_id,
        client, 
        sample_order
    ):
        """Test getting orders by table number"""
        # Mock authentication
        mock_get_restaurant_id.return_value = "restaurant-123"
        
        # Mock service
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        mock_order_service.get_orders_by_table.return_value = [sample_order]
        
        # Make request
        response = client.get("/api/orders/table/5")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["table_number"] == 5
        
        # Verify service call
        mock_order_service.get_orders_by_table.assert_called_once_with(
            restaurant_id="restaurant-123",
            table_number=5,
            active_only=True
        )
    
    def test_get_orders_by_invalid_table(self, client):
        """Test getting orders with invalid table number"""
        response = client.get("/api/orders/table/0")
        
        assert response.status_code == 400
        data = response.json()
        assert "must be positive" in data["detail"]
    
    @patch('app.api.v1.endpoints.orders.get_order_service')
    def test_database_error_handling(
        self, 
        mock_get_order_service,
        client, 
        sample_order_create
    ):
        """Test database error handling"""
        # Mock service to raise database error
        mock_order_service = AsyncMock()
        mock_get_order_service.return_value = mock_order_service
        mock_order_service.create_order_with_items.side_effect = DatabaseError("Database connection failed")
        
        # Make request
        response = client.post("/api/orders/", json=sample_order_create)
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]


class TestOrderCalculationService:
    """Test cases for order calculation and validation logic"""
    
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
    
    @pytest.mark.asyncio
    async def test_validate_and_calculate_order_success(self, sample_menu_items):
        """Test successful order validation and calculation"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        mock_menu_service.get_menu_items_by_ids.return_value = sample_menu_items
        
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
    async def test_validate_order_with_unavailable_item(self, sample_menu_items):
        """Test order validation with unavailable menu item"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        from fastapi import HTTPException
        
        # Make first item unavailable
        sample_menu_items[0].is_available = False
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        mock_menu_service.get_menu_items_by_ids.return_value = sample_menu_items
        
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
        
        # Test validation should raise exception
        with pytest.raises(HTTPException) as exc_info:
            await OrderCalculationService.validate_and_calculate_order(
                order_data, mock_menu_service
            )
        
        assert exc_info.value.status_code == 400
        assert "currently unavailable" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_order_with_missing_item(self):
        """Test order validation with missing menu item"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        from fastapi import HTTPException
        
        # Mock menu service to return empty list (item not found)
        mock_menu_service = AsyncMock()
        mock_menu_service.get_menu_items_by_ids.return_value = []
        
        # Create order data
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("15.99"),
            items=[
                OrderItemCreate(
                    menu_item_id="nonexistent-item",
                    quantity=1,
                    unit_price=Decimal("15.99")
                )
            ]
        )
        
        # Test validation should raise exception
        with pytest.raises(HTTPException) as exc_info:
            await OrderCalculationService.validate_and_calculate_order(
                order_data, mock_menu_service
            )
        
        assert exc_info.value.status_code == 400
        assert "not found or not available" in str(exc_info.value.detail)
