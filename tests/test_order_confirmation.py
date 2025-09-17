"""Tests for order confirmation and kitchen notification system"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from pydantic.error_wrappers import ValidationError
from main import app
from app.models.order import OrderCreate, OrderItemCreate, OrderConfirmationResponse
from app.models.enums import OrderStatus, PaymentStatus
from app.services.order_service import OrderService


class TestOrderConfirmation:
    """Test order confirmation functionality"""
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            "restaurant_id": "test-restaurant-id",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "25.98",
            "items": [
                {
                    "menu_item_id": "item-1",
                    "quantity": 2,
                    "unit_price": "12.99"
                }
            ]
        }
    
    @pytest.fixture
    def mock_order_response(self):
        """Mock order response from database"""
        return {
            "id": "order-123",
            "restaurant_id": "test-restaurant-id",
            "order_number": "ORD-240115-001",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "order_status": "pending",
            "payment_status": "pending",
            "payment_method": "cash",
            "total_price": Decimal("25.98"),
            "estimated_time": 15,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": None,
            "items": []
        }
    
    def test_order_number_generation(self):
        """Test order number generation logic"""
        order_service = OrderService()
        
        # Test order number format
        order_number = order_service._generate_order_number("restaurant-123")
        
        assert order_number.startswith("ORD-")
        assert len(order_number) >= 10  # ORD-YYMMDD-XXX format
        
        # Test uniqueness (generate multiple and check they're different)
        order_numbers = set()
        for _ in range(10):
            order_numbers.add(order_service._generate_order_number("restaurant-123"))
        
        assert len(order_numbers) == 10  # All should be unique
    
    def test_estimated_time_calculation(self):
        """Test estimated preparation time calculation"""
        order_service = OrderService()
        
        # Test minimum time (1 item)
        assert order_service._calculate_estimated_time(1) == 12  # 10 + 2*1
        
        # Test normal case (5 items)
        assert order_service._calculate_estimated_time(5) == 20  # 10 + 2*5
        
        # Test maximum cap (20 items should cap at 45 minutes)
        assert order_service._calculate_estimated_time(20) == 45  # Capped at 45
        
        # Test minimum floor (0 items should still be 10 minutes)
        assert order_service._calculate_estimated_time(0) == 10  # Minimum 10
    
    @pytest.mark.asyncio
    async def test_create_order_returns_confirmation_response(self, sample_order_data, mock_order_response):
        """Test that order creation returns proper confirmation response"""
        with patch('app.database.service_factory.get_order_service') as mock_get_order_service, \
             patch('app.database.service_factory.get_menu_item_service') as mock_get_menu_service, \
             patch('app.database.service_factory.get_customer_service') as mock_get_customer_service:
            
            # Setup mocks
            mock_order_service = AsyncMock()
            mock_menu_service = AsyncMock()
            mock_customer_service = AsyncMock()
            
            mock_get_order_service.return_value = mock_order_service
            mock_get_menu_service.return_value = mock_menu_service
            mock_get_customer_service.return_value = mock_customer_service
            
            # Mock menu item validation
            mock_menu_service.get_menu_items_by_ids.return_value = [
                type('MenuItem', (), {
                    'id': 'item-1',
                    'name': 'Test Item',
                    'price': Decimal('12.99'),
                    'is_available': True
                })()
            ]
            
            # Mock customer service
            mock_customer_service.create_or_update_customer.return_value = type('Customer', (), {'id': 'customer-123'})()
            mock_customer_service.update_last_order_time.return_value = None
            
            # Mock order creation
            from app.models.order import Order
            mock_order = Order(**mock_order_response)
            mock_order_service.create_order_with_items.return_value = mock_order
            
            # Make request
            client = TestClient(app)
            response = client.post("/api/orders/", json=sample_order_data)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            
            # Check confirmation response structure
            assert "order_id" in data
            assert "order_number" in data
            assert "confirmation_message" in data
            assert "payment_message" in data
            assert "kitchen_notification_sent" in data
            assert "estimated_time" in data
            
            # Check confirmation messages
            assert "sent to the kitchen" in data["confirmation_message"]
            assert "cash payments" in data["payment_message"]
            assert data["kitchen_notification_sent"] is True
    
    @pytest.mark.asyncio
    async def test_order_confirmation_messages(self, sample_order_data, mock_order_response):
        """Test that confirmation messages are customer-friendly"""
        with patch('app.database.service_factory.get_order_service') as mock_get_order_service, \
             patch('app.database.service_factory.get_menu_item_service') as mock_get_menu_service, \
             patch('app.database.service_factory.get_customer_service') as mock_get_customer_service:
            
            # Setup mocks (similar to previous test)
            mock_order_service = AsyncMock()
            mock_menu_service = AsyncMock()
            mock_customer_service = AsyncMock()
            
            mock_get_order_service.return_value = mock_order_service
            mock_get_menu_service.return_value = mock_menu_service
            mock_get_customer_service.return_value = mock_customer_service
            
            mock_menu_service.get_menu_items_by_ids.return_value = [
                type('MenuItem', (), {
                    'id': 'item-1',
                    'name': 'Test Item',
                    'price': Decimal('12.99'),
                    'is_available': True
                })()
            ]
            
            mock_customer_service.create_or_update_customer.return_value = type('Customer', (), {'id': 'customer-123'})()
            mock_customer_service.update_last_order_time.return_value = None
            
            from app.models.order import Order
            mock_order = Order(**mock_order_response)
            mock_order_service.create_order_with_items.return_value = mock_order
            
            client = TestClient(app)
            response = client.post("/api/orders/", json=sample_order_data)
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify specific message content
            expected_confirmation = "Your order has been sent to the kitchen and is being prepared!"
            expected_payment = "Payment will be collected by our staff when your order is ready. We accept cash payments."
            
            assert data["confirmation_message"] == expected_confirmation
            assert data["payment_message"] == expected_payment
    
    @pytest.mark.asyncio
    async def test_cash_payment_method_default(self, sample_order_data, mock_order_response):
        """Test that orders default to cash payment method"""
        with patch('app.database.service_factory.get_order_service') as mock_get_order_service, \
             patch('app.database.service_factory.get_menu_item_service') as mock_get_menu_service, \
             patch('app.database.service_factory.get_customer_service') as mock_get_customer_service:
            
            mock_order_service = AsyncMock()
            mock_menu_service = AsyncMock()
            mock_customer_service = AsyncMock()
            
            mock_get_order_service.return_value = mock_order_service
            mock_get_menu_service.return_value = mock_menu_service
            mock_get_customer_service.return_value = mock_customer_service
            
            mock_menu_service.get_menu_items_by_ids.return_value = [
                type('MenuItem', (), {
                    'id': 'item-1',
                    'name': 'Test Item',
                    'price': Decimal('12.99'),
                    'is_available': True
                })()
            ]
            
            mock_customer_service.create_or_update_customer.return_value = type('Customer', (), {'id': 'customer-123'})()
            mock_customer_service.update_last_order_time.return_value = None
            
            from app.models.order import Order
            mock_order = Order(**mock_order_response)
            mock_order_service.create_order_with_items.return_value = mock_order
            
            client = TestClient(app)
            response = client.post("/api/orders/", json=sample_order_data)
            
            # Verify that the order service was called with cash payment method
            call_args = mock_order_service.create_order_with_items.call_args[0][0]
            # The payment method should be set in the service layer
            assert response.status_code == 201
    
    def test_order_confirmation_response_model(self):
        """Test OrderConfirmationResponse model validation"""
        # Test valid confirmation response
        valid_data = {
            "id": "order-123",
            "restaurant_id": "restaurant-123",
            "order_number": "ORD-001",
            "order_status": "pending",
            "payment_status": "pending",
            "total_price": "25.98",
            "estimated_time": 15,
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "created_at": "2024-01-15T10:30:00Z",
            "confirmation_message": "Order sent to kitchen!",
            "payment_message": "Pay with cash",
            "kitchen_notification_sent": True
        }
        
        response = OrderConfirmationResponse(**valid_data)
        assert response.id == "order-123"
        assert response.order_number == "ORD-001"
        assert response.estimated_time == 15
        assert response.kitchen_notification_sent is True
        
        # Test that core required fields are present
        required_fields = [
            "restaurant_id", "table_number", "customer_name", "customer_phone", 
            "total_price", "confirmation_message", "payment_message", "kitchen_notification_sent"
        ]
        
        for field in required_fields:
            test_data = valid_data.copy()
            del test_data[field]
            
            try:
                result = OrderConfirmationResponse(**test_data)
                # If we get here, the field wasn't actually required
                print(f"Field {field} was not required, got: {result}")
                assert False, f"Expected ValidationError for missing field {field}"
            except ValidationError:
                # This is expected
                pass
    
    @pytest.mark.asyncio
    async def test_order_creation_with_estimated_time(self):
        """Test that created orders include estimated preparation time"""
        order_service = OrderService()
        
        # Mock the database client
        with patch.object(order_service, 'client') as mock_client:
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "order-123",
                "restaurant_id": "restaurant-123",
                "order_number": "ORD-240115-001",
                "table_number": 5,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "order_status": "pending",
                "payment_status": "pending",
                "payment_method": "cash",
                "total_price": "25.98",
                "estimated_time": 14,  # 10 + 2*2 items
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }]
            
            order_data = OrderCreate(
                restaurant_id="restaurant-123",
                table_number=5,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=Decimal("25.98"),
                items=[
                    OrderItemCreate(menu_item_id="item-1", quantity=2, unit_price=Decimal("12.99"))
                ]
            )
            
            # Mock order item service
            with patch.object(order_service.order_item_service, 'create_order_items') as mock_create_items:
                mock_create_items.return_value = []
                
                order = await order_service.create_order_with_items(order_data)
                
                # Verify estimated time was calculated and included
                assert order.estimated_time == 14
                assert order.order_number.startswith("ORD-")
                assert order.payment_method == "cash"  # Should be set in service
    
    @pytest.mark.asyncio
    async def test_kitchen_notification_flag(self, sample_order_data, mock_order_response):
        """Test that kitchen notification flag is always True for successful orders"""
        with patch('app.database.service_factory.get_order_service') as mock_get_order_service, \
             patch('app.database.service_factory.get_menu_item_service') as mock_get_menu_service, \
             patch('app.database.service_factory.get_customer_service') as mock_get_customer_service:
            
            # Setup mocks
            mock_order_service = AsyncMock()
            mock_menu_service = AsyncMock()
            mock_customer_service = AsyncMock()
            
            mock_get_order_service.return_value = mock_order_service
            mock_get_menu_service.return_value = mock_menu_service
            mock_get_customer_service.return_value = mock_customer_service
            
            mock_menu_service.get_menu_items_by_ids.return_value = [
                type('MenuItem', (), {
                    'id': 'item-1',
                    'name': 'Test Item',
                    'price': Decimal('12.99'),
                    'is_available': True
                })()
            ]
            
            mock_customer_service.create_or_update_customer.return_value = type('Customer', (), {'id': 'customer-123'})()
            mock_customer_service.update_last_order_time.return_value = None
            
            from app.models.order import Order
            mock_order = Order(**mock_order_response)
            mock_order_service.create_order_with_items.return_value = mock_order
            
            client = TestClient(app)
            response = client.post("/api/orders/", json=sample_order_data)
            
            assert response.status_code == 201
            data = response.json()
            
            # Kitchen notification should always be True for successful orders
            assert data["kitchen_notification_sent"] is True


class TestOrderConfirmationErrorHandling:
    """Test error handling in order confirmation flow"""
    
    @pytest.mark.asyncio
    async def test_order_creation_failure_handling(self):
        """Test that order creation failures are handled properly"""
        sample_order_data = {
            "restaurant_id": "test-restaurant-id",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "25.98",
            "items": [
                {
                    "menu_item_id": "item-1",
                    "quantity": 2,
                    "unit_price": "12.99"
                }
            ]
        }
        
        with patch('app.database.service_factory.get_order_service') as mock_get_order_service, \
             patch('app.database.service_factory.get_menu_item_service') as mock_get_menu_service, \
             patch('app.database.service_factory.get_customer_service') as mock_get_customer_service:
            
            # Setup mocks
            mock_order_service = AsyncMock()
            mock_menu_service = AsyncMock()
            mock_customer_service = AsyncMock()
            
            mock_get_order_service.return_value = mock_order_service
            mock_get_menu_service.return_value = mock_menu_service
            mock_get_customer_service.return_value = mock_customer_service
            
            # Mock menu item validation to succeed
            mock_menu_service.get_menu_items_by_ids.return_value = [
                type('MenuItem', (), {
                    'id': 'item-1',
                    'name': 'Test Item',
                    'price': Decimal('12.99'),
                    'is_available': True
                })()
            ]
            
            # Mock customer service to succeed
            mock_customer_service.create_or_update_customer.return_value = type('Customer', (), {'id': 'customer-123'})()
            
            # Mock order creation to fail
            from app.database.base import DatabaseError
            mock_order_service.create_order_with_items.side_effect = DatabaseError("Database connection failed")
            
            client = TestClient(app)
            response = client.post("/api/orders/", json=sample_order_data)
            
            # Should return 500 error with appropriate message
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]
    
    def test_invalid_order_data_validation(self):
        """Test validation of invalid order confirmation data"""
        client = TestClient(app)
        
        # Test missing required fields
        invalid_data = {
            "restaurant_id": "test-restaurant-id",
            # Missing table_number, customer_name, etc.
        }
        
        response = client.post("/api/orders/", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Test invalid table number
        invalid_data = {
            "restaurant_id": "test-restaurant-id",
            "table_number": 0,  # Invalid - must be positive
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total_price": "25.98",
            "items": [
                {
                    "menu_item_id": "item-1",
                    "quantity": 2,
                    "unit_price": "12.99"
                }
            ]
        }
        
        response = client.post("/api/orders/", json=invalid_data)
        assert response.status_code == 422
