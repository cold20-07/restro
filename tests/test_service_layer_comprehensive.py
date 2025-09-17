"""Comprehensive unit tests for all service layer functions and business logic"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.services.restaurant_service import RestaurantService
from app.services.menu_item_service import MenuItemService
from app.services.order_service import OrderService
from app.services.customer_service import CustomerService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.public_menu_service import PublicMenuService
from app.services.realtime_service import RealtimeService
from app.services.websocket_service import WebSocketService

from app.models.restaurant import Restaurant, RestaurantCreate
from app.models.menu_item import MenuItem, MenuItemCreate, MenuItemUpdate
from app.models.order import Order, OrderCreate, OrderItem, OrderStatus
from app.models.customer import Customer, CustomerCreate
from app.models.auth import UserCreate, UserLogin
from app.core.exceptions import (
    ValidationError, 
    AuthenticationError, 
    AuthorizationError,
    NotFoundError,
    BusinessLogicError
)


class TestRestaurantService:
    """Test cases for RestaurantService business logic"""
    
    @pytest.fixture
    def restaurant_service(self):
        mock_client = Mock()
        return RestaurantService(mock_client)
    
    @pytest.fixture
    def sample_restaurant_data(self):
        return {
            "id": "restaurant-123",
            "name": "Test Restaurant",
            "owner_id": "owner-123",
            "created_at": datetime.utcnow()
        }
    
    async def test_create_restaurant_success(self, restaurant_service, sample_restaurant_data):
        """Test successful restaurant creation"""
        restaurant_service.db.table().insert().execute.return_value.data = [sample_restaurant_data]
        
        restaurant_create = RestaurantCreate(name="Test Restaurant")
        result = await restaurant_service.create_restaurant(restaurant_create, "owner-123")
        
        assert result.name == "Test Restaurant"
        assert result.owner_id == "owner-123"
        restaurant_service.db.table.assert_called_with("restaurants")
    
    async def test_create_restaurant_duplicate_name(self, restaurant_service):
        """Test restaurant creation with duplicate name for same owner"""
        restaurant_service.db.table().select().eq().eq().execute.return_value.data = [{"id": "existing"}]
        
        restaurant_create = RestaurantCreate(name="Existing Restaurant")
        
        with pytest.raises(ValidationError, match="Restaurant name already exists"):
            await restaurant_service.create_restaurant(restaurant_create, "owner-123")
    
    async def test_get_restaurant_by_owner_success(self, restaurant_service, sample_restaurant_data):
        """Test successful restaurant retrieval by owner"""
        restaurant_service.db.table().select().eq().execute.return_value.data = [sample_restaurant_data]
        
        result = await restaurant_service.get_restaurant_by_owner("owner-123")
        
        assert result.id == "restaurant-123"
        assert result.name == "Test Restaurant"
    
    async def test_get_restaurant_by_owner_not_found(self, restaurant_service):
        """Test restaurant retrieval when owner has no restaurant"""
        restaurant_service.db.table().select().eq().execute.return_value.data = []
        
        with pytest.raises(NotFoundError, match="Restaurant not found"):
            await restaurant_service.get_restaurant_by_owner("nonexistent-owner")


class TestMenuItemService:
    """Test cases for MenuItemService business logic"""
    
    @pytest.fixture
    def menu_service(self):
        mock_client = Mock()
        return MenuItemService(mock_client)
    
    @pytest.fixture
    def sample_menu_item(self):
        return {
            "id": "item-123",
            "restaurant_id": "restaurant-123",
            "name": "Test Burger",
            "description": "Delicious test burger",
            "price": "15.99",
            "category": "Main Course",
            "is_available": True,
            "created_at": datetime.utcnow()
        }
    
    async def test_create_menu_item_success(self, menu_service, sample_menu_item):
        """Test successful menu item creation"""
        menu_service.db.table().insert().execute.return_value.data = [sample_menu_item]
        
        menu_item_create = MenuItemCreate(
            name="Test Burger",
            description="Delicious test burger",
            price=Decimal("15.99"),
            category="Main Course"
        )
        
        result = await menu_service.create_menu_item(menu_item_create, "restaurant-123")
        
        assert result.name == "Test Burger"
        assert result.price == Decimal("15.99")
        assert result.restaurant_id == "restaurant-123"
    
    async def test_create_menu_item_invalid_price(self, menu_service):
        """Test menu item creation with invalid price"""
        menu_item_create = MenuItemCreate(
            name="Test Item",
            description="Test description",
            price=Decimal("-5.00"),  # Invalid negative price
            category="Test"
        )
        
        with pytest.raises(ValidationError, match="Price must be positive"):
            await menu_service.create_menu_item(menu_item_create, "restaurant-123")
    
    async def test_update_menu_item_availability(self, menu_service, sample_menu_item):
        """Test updating menu item availability"""
        updated_item = sample_menu_item.copy()
        updated_item["is_available"] = False
        menu_service.db.table().update().eq().execute.return_value.data = [updated_item]
        
        menu_item_update = MenuItemUpdate(is_available=False)
        result = await menu_service.update_menu_item("item-123", menu_item_update, "restaurant-123")
        
        assert result.is_available is False
    
    async def test_get_available_items_only(self, menu_service):
        """Test retrieving only available menu items"""
        available_items = [
            {"id": "item-1", "name": "Available Item", "is_available": True},
            {"id": "item-2", "name": "Another Available", "is_available": True}
        ]
        menu_service.db.table().select().eq().eq().execute.return_value.data = available_items
        
        result = await menu_service.get_available_menu_items("restaurant-123")
        
        assert len(result) == 2
        assert all(item.is_available for item in result)


class TestOrderService:
    """Test cases for OrderService business logic"""
    
    @pytest.fixture
    def order_service(self):
        mock_client = Mock()
        return OrderService(mock_client)
    
    @pytest.fixture
    def sample_order_data(self):
        return {
            "restaurant_id": "restaurant-123",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "items": [
                {"menu_item_id": "item-1", "quantity": 2},
                {"menu_item_id": "item-2", "quantity": 1}
            ]
        }
    
    @pytest.fixture
    def sample_menu_items(self):
        return [
            {"id": "item-1", "name": "Burger", "price": "15.99", "is_available": True},
            {"id": "item-2", "name": "Fries", "price": "8.99", "is_available": True}
        ]
    
    async def test_calculate_order_total(self, order_service, sample_menu_items):
        """Test order total calculation logic"""
        order_items = [
            {"menu_item_id": "item-1", "quantity": 2},  # 2 * 15.99 = 31.98
            {"menu_item_id": "item-2", "quantity": 1}   # 1 * 8.99 = 8.99
        ]
        
        total = await order_service._calculate_order_total(order_items, sample_menu_items)
        
        assert total == Decimal("40.97")
    
    async def test_validate_order_items_success(self, order_service, sample_menu_items):
        """Test successful order item validation"""
        order_items = [
            {"menu_item_id": "item-1", "quantity": 2},
            {"menu_item_id": "item-2", "quantity": 1}
        ]
        
        # Should not raise any exception
        await order_service._validate_order_items(order_items, sample_menu_items)
    
    async def test_validate_order_items_unavailable_item(self, order_service):
        """Test order validation with unavailable item"""
        menu_items = [
            {"id": "item-1", "name": "Burger", "price": "15.99", "is_available": False}
        ]
        order_items = [{"menu_item_id": "item-1", "quantity": 1}]
        
        with pytest.raises(ValidationError, match="Menu item .* is not available"):
            await order_service._validate_order_items(order_items, menu_items)
    
    async def test_validate_order_items_nonexistent_item(self, order_service, sample_menu_items):
        """Test order validation with nonexistent item"""
        order_items = [{"menu_item_id": "nonexistent-item", "quantity": 1}]
        
        with pytest.raises(ValidationError, match="Menu item .* not found"):
            await order_service._validate_order_items(order_items, sample_menu_items)
    
    async def test_validate_table_number(self, order_service):
        """Test table number validation"""
        # Valid table numbers
        assert order_service._validate_table_number(1) is True
        assert order_service._validate_table_number(50) is True
        
        # Invalid table numbers
        with pytest.raises(ValidationError, match="Table number must be positive"):
            order_service._validate_table_number(0)
        
        with pytest.raises(ValidationError, match="Table number must be positive"):
            order_service._validate_table_number(-1)
    
    async def test_generate_order_number(self, order_service):
        """Test order number generation"""
        order_number = order_service._generate_order_number()
        
        assert len(order_number) == 8
        assert order_number.isdigit()
    
    async def test_update_order_status_valid_transition(self, order_service):
        """Test valid order status transitions"""
        valid_transitions = [
            (OrderStatus.PENDING, OrderStatus.CONFIRMED),
            (OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS),
            (OrderStatus.IN_PROGRESS, OrderStatus.READY),
            (OrderStatus.READY, OrderStatus.COMPLETED),
            (OrderStatus.PENDING, OrderStatus.CANCELED)
        ]
        
        for current, new in valid_transitions:
            assert order_service._is_valid_status_transition(current, new) is True
    
    async def test_update_order_status_invalid_transition(self, order_service):
        """Test invalid order status transitions"""
        invalid_transitions = [
            (OrderStatus.COMPLETED, OrderStatus.PENDING),
            (OrderStatus.CANCELED, OrderStatus.CONFIRMED),
            (OrderStatus.READY, OrderStatus.PENDING)
        ]
        
        for current, new in invalid_transitions:
            assert order_service._is_valid_status_transition(current, new) is False


class TestCustomerService:
    """Test cases for CustomerService business logic"""
    
    @pytest.fixture
    def customer_service(self):
        mock_client = Mock()
        return CustomerService(mock_client)
    
    async def test_create_or_update_customer_new(self, customer_service):
        """Test creating new customer profile"""
        customer_service.db.table().select().eq().eq().execute.return_value.data = []
        customer_service.db.table().insert().execute.return_value.data = [{
            "id": "customer-123",
            "restaurant_id": "restaurant-123",
            "phone_number": "+1234567890",
            "name": "John Doe"
        }]
        
        result = await customer_service.create_or_update_customer(
            "restaurant-123", "+1234567890", "John Doe"
        )
        
        assert result.phone_number == "+1234567890"
        assert result.name == "John Doe"
    
    async def test_create_or_update_customer_existing(self, customer_service):
        """Test updating existing customer profile"""
        existing_customer = {
            "id": "customer-123",
            "restaurant_id": "restaurant-123", 
            "phone_number": "+1234567890",
            "name": "John Smith"
        }
        customer_service.db.table().select().eq().eq().execute.return_value.data = [existing_customer]
        
        updated_customer = existing_customer.copy()
        updated_customer["name"] = "John Doe"
        customer_service.db.table().update().eq().execute.return_value.data = [updated_customer]
        
        result = await customer_service.create_or_update_customer(
            "restaurant-123", "+1234567890", "John Doe"
        )
        
        assert result.name == "John Doe"
    
    async def test_validate_phone_number(self, customer_service):
        """Test phone number validation"""
        valid_numbers = ["+1234567890", "+44123456789", "+33123456789"]
        invalid_numbers = ["123", "invalid", "", "+"]
        
        for number in valid_numbers:
            assert customer_service._validate_phone_number(number) is True
        
        for number in invalid_numbers:
            with pytest.raises(ValidationError):
                customer_service._validate_phone_number(number)


class TestAnalyticsService:
    """Test cases for AnalyticsService business logic"""
    
    @pytest.fixture
    def analytics_service(self):
        mock_client = Mock()
        return AnalyticsService(mock_client)
    
    @pytest.fixture
    def sample_orders_data(self):
        return [
            {
                "id": "order-1",
                "total_price": "25.99",
                "created_at": "2024-01-15T10:00:00Z",
                "order_status": "completed"
            },
            {
                "id": "order-2", 
                "total_price": "18.50",
                "created_at": "2024-01-15T14:30:00Z",
                "order_status": "completed"
            },
            {
                "id": "order-3",
                "total_price": "32.75",
                "created_at": "2024-01-15T19:15:00Z", 
                "order_status": "completed"
            }
        ]
    
    async def test_calculate_total_revenue(self, analytics_service, sample_orders_data):
        """Test total revenue calculation"""
        analytics_service.db.table().select().eq().gte().lte().execute.return_value.data = sample_orders_data
        
        total_revenue = await analytics_service._calculate_total_revenue(
            "restaurant-123", datetime(2024, 1, 15), datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert total_revenue == Decimal("77.24")
    
    async def test_calculate_average_order_value(self, analytics_service, sample_orders_data):
        """Test average order value calculation"""
        analytics_service.db.table().select().eq().gte().lte().execute.return_value.data = sample_orders_data
        
        avg_order_value = await analytics_service._calculate_average_order_value(
            "restaurant-123", datetime(2024, 1, 15), datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert avg_order_value == Decimal("25.75")  # 77.24 / 3
    
    async def test_get_orders_by_hour(self, analytics_service):
        """Test orders by hour distribution"""
        orders_data = [
            {"created_at": "2024-01-15T10:00:00Z"},
            {"created_at": "2024-01-15T10:30:00Z"},
            {"created_at": "2024-01-15T14:00:00Z"},
            {"created_at": "2024-01-15T14:15:00Z"},
            {"created_at": "2024-01-15T14:45:00Z"}
        ]
        analytics_service.db.table().select().eq().gte().lte().execute.return_value.data = orders_data
        
        orders_by_hour = await analytics_service._get_orders_by_hour(
            "restaurant-123", datetime(2024, 1, 15), datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert orders_by_hour["10"] == 2
        assert orders_by_hour["14"] == 3
        assert orders_by_hour.get("12", 0) == 0
    
    async def test_get_best_selling_items(self, analytics_service):
        """Test best selling items calculation"""
        order_items_data = [
            {"menu_item_id": "item-1", "quantity": 2, "menu_items": {"name": "Burger"}},
            {"menu_item_id": "item-1", "quantity": 1, "menu_items": {"name": "Burger"}},
            {"menu_item_id": "item-2", "quantity": 3, "menu_items": {"name": "Pizza"}},
            {"menu_item_id": "item-2", "quantity": 1, "menu_items": {"name": "Pizza"}},
            {"menu_item_id": "item-3", "quantity": 1, "menu_items": {"name": "Salad"}}
        ]
        analytics_service.db.table().select().eq().gte().lte().execute.return_value.data = order_items_data
        
        best_selling = await analytics_service._get_best_selling_items(
            "restaurant-123", datetime(2024, 1, 15), datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert len(best_selling) >= 2
        assert best_selling[0]["name"] == "Pizza"  # 4 total quantity
        assert best_selling[0]["total_quantity"] == 4
        assert best_selling[1]["name"] == "Burger"  # 3 total quantity
        assert best_selling[1]["total_quantity"] == 3


class TestAuthService:
    """Test cases for AuthService business logic"""
    
    @pytest.fixture
    def auth_service(self):
        mock_client = Mock()
        return AuthService(mock_client)
    
    async def test_validate_password_strength(self, auth_service):
        """Test password strength validation"""
        strong_passwords = ["StrongPass123!", "MySecure@Pass1", "Complex#Password9"]
        weak_passwords = ["weak", "12345678", "password", "PASSWORD", "Pass123"]
        
        for password in strong_passwords:
            assert auth_service._validate_password_strength(password) is True
        
        for password in weak_passwords:
            with pytest.raises(ValidationError, match="Password must be at least"):
                auth_service._validate_password_strength(password)
    
    async def test_validate_email_format(self, auth_service):
        """Test email format validation"""
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "admin@restaurant.org"]
        invalid_emails = ["invalid", "@domain.com", "user@", "user@domain", "user.domain.com"]
        
        for email in valid_emails:
            assert auth_service._validate_email_format(email) is True
        
        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email format"):
                auth_service._validate_email_format(email)
    
    async def test_generate_jwt_token(self, auth_service):
        """Test JWT token generation"""
        user_data = {"user_id": "user-123", "restaurant_id": "restaurant-123"}
        
        with patch('app.services.auth_service.jwt.encode') as mock_encode:
            mock_encode.return_value = "mock.jwt.token"
            
            token = auth_service._generate_jwt_token(user_data)
            
            assert token == "mock.jwt.token"
            mock_encode.assert_called_once()
    
    async def test_verify_jwt_token(self, auth_service):
        """Test JWT token verification"""
        token = "valid.jwt.token"
        expected_payload = {"user_id": "user-123", "restaurant_id": "restaurant-123"}
        
        with patch('app.services.auth_service.jwt.decode') as mock_decode:
            mock_decode.return_value = expected_payload
            
            payload = auth_service._verify_jwt_token(token)
            
            assert payload == expected_payload
            mock_decode.assert_called_once_with(token, auth_service.secret_key, algorithms=["HS256"])


class TestRealtimeService:
    """Test cases for RealtimeService business logic"""
    
    @pytest.fixture
    def realtime_service(self):
        mock_client = Mock()
        return RealtimeService(mock_client)
    
    async def test_subscribe_to_orders(self, realtime_service):
        """Test order subscription setup"""
        callback = Mock()
        restaurant_id = "restaurant-123"
        
        realtime_service.client.table().on().filter().subscribe.return_value = Mock()
        
        subscription = await realtime_service.subscribe_to_orders(restaurant_id, callback)
        
        assert subscription is not None
        realtime_service.client.table.assert_called_with("orders")
    
    async def test_publish_order_update(self, realtime_service):
        """Test order update publishing"""
        order_id = "order-123"
        status = "confirmed"
        
        realtime_service.client.table().update().eq().execute.return_value = Mock()
        
        await realtime_service.publish_order_update(order_id, status)
        
        realtime_service.client.table.assert_called_with("orders")
    
    async def test_handle_connection_error(self, realtime_service):
        """Test connection error handling"""
        with patch.object(realtime_service, '_reconnect') as mock_reconnect:
            await realtime_service._handle_connection_error("Connection lost")
            mock_reconnect.assert_called_once()


class TestWebSocketService:
    """Test cases for WebSocketService business logic"""
    
    @pytest.fixture
    def websocket_service(self):
        return WebSocketService()
    
    async def test_add_connection(self, websocket_service):
        """Test adding WebSocket connection"""
        mock_websocket = Mock()
        restaurant_id = "restaurant-123"
        
        await websocket_service.add_connection(restaurant_id, mock_websocket)
        
        assert restaurant_id in websocket_service.connections
        assert mock_websocket in websocket_service.connections[restaurant_id]
    
    async def test_remove_connection(self, websocket_service):
        """Test removing WebSocket connection"""
        mock_websocket = Mock()
        restaurant_id = "restaurant-123"
        
        # Add connection first
        await websocket_service.add_connection(restaurant_id, mock_websocket)
        
        # Then remove it
        await websocket_service.remove_connection(restaurant_id, mock_websocket)
        
        assert mock_websocket not in websocket_service.connections.get(restaurant_id, [])
    
    async def test_broadcast_to_restaurant(self, websocket_service):
        """Test broadcasting message to restaurant connections"""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        restaurant_id = "restaurant-123"
        message = {"type": "order_update", "data": {"order_id": "order-123"}}
        
        # Add connections
        await websocket_service.add_connection(restaurant_id, mock_websocket1)
        await websocket_service.add_connection(restaurant_id, mock_websocket2)
        
        # Broadcast message
        await websocket_service.broadcast_to_restaurant(restaurant_id, message)
        
        # Verify both connections received the message
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)
    
    async def test_broadcast_handles_disconnected_clients(self, websocket_service):
        """Test broadcasting handles disconnected clients gracefully"""
        mock_websocket_good = AsyncMock()
        mock_websocket_bad = AsyncMock()
        mock_websocket_bad.send_json.side_effect = Exception("Connection closed")
        
        restaurant_id = "restaurant-123"
        message = {"type": "test"}
        
        # Add connections
        await websocket_service.add_connection(restaurant_id, mock_websocket_good)
        await websocket_service.add_connection(restaurant_id, mock_websocket_bad)
        
        # Broadcast should not fail even if one connection is bad
        await websocket_service.broadcast_to_restaurant(restaurant_id, message)
        
        # Good connection should still receive message
        mock_websocket_good.send_json.assert_called_once_with(message)
        
        # Bad connection should be removed from connections
        assert mock_websocket_bad not in websocket_service.connections[restaurant_id]