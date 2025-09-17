"""Integration tests for real-time order notifications"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.websocket_service import ConnectionManager
from app.models.order import Order, OrderCreate, OrderItemCreate
from app.models.enums import OrderStatus, PaymentStatus
from decimal import Decimal
from datetime import datetime


@pytest.fixture
def connection_manager():
    """Create ConnectionManager instance"""
    return ConnectionManager()


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
    
    async def accept(self):
        pass
    
    async def send_text(self, data: str):
        if self.closed:
            raise Exception("WebSocket is closed")
        self.messages.append(data)


class TestRealtimeIntegration:
    """Test real-time integration functionality"""
    
    @pytest.mark.asyncio
    async def test_connection_manager_handles_multiple_restaurants(self, connection_manager):
        """Test that connection manager properly isolates restaurants"""
        # Create mock WebSockets for different restaurants
        restaurant1_ws = MockWebSocket()
        restaurant2_ws = MockWebSocket()
        
        # Connect to different restaurants
        await connection_manager.connect(restaurant1_ws, "restaurant-1")
        await connection_manager.connect(restaurant2_ws, "restaurant-2")
        
        # Clear connection messages
        restaurant1_ws.messages.clear()
        restaurant2_ws.messages.clear()
        
        # Create order for restaurant 1
        order1 = Order(
            id="order-1",
            restaurant_id="restaurant-1",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method="cash",
            total_price=Decimal("25.50"),
            estimated_time=15,
            order_number="ORD-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            items=[]
        )
        
        # Broadcast order to restaurant 1
        await connection_manager.broadcast_order_created(order1)
        
        # Only restaurant 1 should receive the message
        assert len(restaurant1_ws.messages) == 1
        assert len(restaurant2_ws.messages) == 0
        
        # Verify message content
        import json
        message = json.loads(restaurant1_ws.messages[0])
        assert message["type"] == "order_created"
        assert message["order"]["restaurant_id"] == "restaurant-1"
        assert message["order"]["id"] == "order-1"
    
    @pytest.mark.asyncio
    async def test_order_service_integration_with_websocket(self):
        """Test that order service can integrate with WebSocket broadcasting"""
        from app.services.order_service import OrderService
        
        # Mock Supabase client
        mock_client = MagicMock()
        order_data = {
            "id": "test-order-id",
            "restaurant_id": "test-restaurant-id",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "order_status": "pending",
            "payment_status": "pending",
            "payment_method": "cash",
            "total_price": 25.50,
            "estimated_time": 15,
            "order_number": "ORD-240115103045-A1B2",
            "created_at": "2024-01-15T10:30:45Z",
            "updated_at": "2024-01-15T10:30:45Z"
        }
        
        mock_response = MagicMock()
        mock_response.data = [order_data]
        mock_response.error = None
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        order_service = OrderService(client=mock_client)
        
        # Mock order item creation
        with patch.object(order_service.order_item_service, 'create_order_items') as mock_create_items:
            mock_create_items.return_value = []
            
            # Create order request
            order_request = OrderCreate(
                restaurant_id="test-restaurant-id",
                table_number=5,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=Decimal("25.50"),
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=2,
                        unit_price=Decimal("12.75")
                    )
                ]
            )
            
            # Test with real-time notifications enabled (default)
            result = await order_service.create_order_with_items(order_request)
            
            # Verify order was created
            assert result is not None
            assert result.id == "test-order-id"
            assert result.restaurant_id == "test-restaurant-id"
            
            # Test with real-time notifications disabled
            result2 = await order_service.create_order_with_items(order_request, notify_realtime=False)
            
            # Verify order was still created
            assert result2 is not None
            assert result2.id == "test-order-id"
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_with_order_items(self, connection_manager):
        """Test WebSocket broadcast includes order items"""
        from app.models.order import OrderItem
        
        # Create mock WebSocket
        mock_ws = MockWebSocket()
        await connection_manager.connect(mock_ws, "test-restaurant")
        mock_ws.messages.clear()
        
        # Create order with items
        order_item = OrderItem(
            id="item-1",
            order_id="order-1",
            menu_item_id="menu-item-1",
            quantity=2,
            unit_price=Decimal("12.75")
        )
        
        order = Order(
            id="order-1",
            restaurant_id="test-restaurant",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method="cash",
            total_price=Decimal("25.50"),
            estimated_time=15,
            order_number="ORD-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            items=[order_item]
        )
        
        # Broadcast order
        await connection_manager.broadcast_order_created(order)
        
        # Verify message was sent
        assert len(mock_ws.messages) == 1
        
        # Verify message content includes items
        import json
        message = json.loads(mock_ws.messages[0])
        assert message["type"] == "order_created"
        assert len(message["order"]["items"]) == 1
        assert message["order"]["items"][0]["id"] == "item-1"
        assert message["order"]["items"][0]["quantity"] == 2
        assert message["order"]["items"][0]["unit_price"] == 12.75
    
    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup_on_error(self, connection_manager):
        """Test that failed WebSocket connections are cleaned up"""
        # Create a WebSocket that will fail on send
        class FailingWebSocket:
            def __init__(self):
                self.messages = []
            
            async def accept(self):
                pass
            
            async def send_text(self, data: str):
                raise Exception("Connection failed")
        
        failing_ws = FailingWebSocket()
        good_ws = MockWebSocket()
        
        # Connect both WebSockets to the same restaurant
        await connection_manager.connect(failing_ws, "test-restaurant")
        await connection_manager.connect(good_ws, "test-restaurant")
        
        # Clear connection messages
        good_ws.messages.clear()
        
        # Verify both connections are registered initially
        # Note: The failing connection might be cleaned up during connect due to the error
        initial_count = connection_manager.get_connection_count("test-restaurant")
        assert initial_count >= 1  # At least the good connection should be there
        
        # Create and broadcast an order
        order = Order(
            id="order-1",
            restaurant_id="test-restaurant",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method="cash",
            total_price=Decimal("25.50"),
            estimated_time=15,
            order_number="ORD-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            items=[]
        )
        
        await connection_manager.broadcast_order_created(order)
        
        # After broadcast, failing connections should be cleaned up
        final_count = connection_manager.get_connection_count("test-restaurant")
        assert final_count == 1  # Only the good connection should remain
        
        # Good connection should still receive the message
        assert len(good_ws.messages) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_order_status_changes(self, connection_manager):
        """Test broadcasting multiple order status changes"""
        mock_ws = MockWebSocket()
        await connection_manager.connect(mock_ws, "test-restaurant")
        mock_ws.messages.clear()
        
        # Create base order
        order = Order(
            id="order-1",
            restaurant_id="test-restaurant",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method="cash",
            total_price=Decimal("25.50"),
            estimated_time=15,
            order_number="ORD-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            items=[]
        )
        
        # Broadcast order creation
        await connection_manager.broadcast_order_created(order)
        
        # Update order status and broadcast changes
        order.order_status = OrderStatus.CONFIRMED
        await connection_manager.broadcast_order_status_changed(order)
        
        order.order_status = OrderStatus.IN_PROGRESS
        await connection_manager.broadcast_order_status_changed(order)
        
        order.order_status = OrderStatus.READY
        await connection_manager.broadcast_order_status_changed(order)
        
        # Verify all messages were received
        assert len(mock_ws.messages) == 4  # 1 creation + 3 status changes
        
        # Verify message types
        import json
        messages = [json.loads(msg) for msg in mock_ws.messages]
        
        assert messages[0]["type"] == "order_created"
        assert messages[1]["type"] == "order_status_changed"
        assert messages[2]["type"] == "order_status_changed"
        assert messages[3]["type"] == "order_status_changed"
        
        # Verify final status
        assert messages[3]["order"]["order_status"] == "ready"