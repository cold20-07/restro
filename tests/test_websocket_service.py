"""Tests for WebSocket service and connection management"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from app.services.websocket_service import ConnectionManager
from app.models.order import Order
from app.models.enums import OrderStatus, PaymentStatus
from decimal import Decimal
from datetime import datetime


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
    
    async def accept(self):
        pass
    
    async def send_text(self, data: str):
        if self.closed:
            raise Exception("WebSocket is closed")
        self.messages.append(data)
    
    async def close(self, code: int = None, reason: str = None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket"""
    return MockWebSocket()


@pytest.fixture
def sample_order():
    """Create a sample order for testing"""
    return Order(
        id="test-order-id",
        restaurant_id="test-restaurant-id",
        table_number=5,
        customer_name="John Doe",
        customer_phone="+1234567890",
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        payment_method="cash",
        total_price=Decimal("25.50"),
        estimated_time=15,
        order_number="ORD-240115103045-A1B2",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        items=[]
    )


class TestConnectionManager:
    """Test ConnectionManager functionality"""
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, connection_manager, mock_websocket):
        """Test connecting a WebSocket"""
        restaurant_id = "test-restaurant-id"
        
        await connection_manager.connect(mock_websocket, restaurant_id)
        
        # Check connection is stored
        assert restaurant_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[restaurant_id]
        assert connection_manager.connection_restaurant_map[mock_websocket] == restaurant_id
        
        # Check connection confirmation message was sent
        assert len(mock_websocket.messages) == 1
        message = json.loads(mock_websocket.messages[0])
        assert message["type"] == "connection_established"
        assert message["restaurant_id"] == restaurant_id
    
    def test_disconnect_websocket(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket"""
        restaurant_id = "test-restaurant-id"
        
        # Manually add connection
        connection_manager.active_connections[restaurant_id] = {mock_websocket}
        connection_manager.connection_restaurant_map[mock_websocket] = restaurant_id
        
        # Disconnect
        connection_manager.disconnect(mock_websocket)
        
        # Check connection is removed
        assert restaurant_id not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.connection_restaurant_map
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending a personal message"""
        message = {"type": "test", "data": "hello"}
        
        await connection_manager.send_personal_message(mock_websocket, message)
        
        assert len(mock_websocket.messages) == 1
        received_message = json.loads(mock_websocket.messages[0])
        assert received_message == message
    
    @pytest.mark.asyncio
    async def test_send_personal_message_error_handling(self, connection_manager):
        """Test error handling when sending personal message"""
        # Create a WebSocket that raises an exception
        error_websocket = MockWebSocket()
        error_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))
        
        restaurant_id = "test-restaurant-id"
        connection_manager.active_connections[restaurant_id] = {error_websocket}
        connection_manager.connection_restaurant_map[error_websocket] = restaurant_id
        
        message = {"type": "test", "data": "hello"}
        
        # Should not raise exception
        await connection_manager.send_personal_message(error_websocket, message)
        
        # Connection should be cleaned up
        assert restaurant_id not in connection_manager.active_connections
        assert error_websocket not in connection_manager.connection_restaurant_map
    
    @pytest.mark.asyncio
    async def test_broadcast_to_restaurant(self, connection_manager):
        """Test broadcasting to all connections for a restaurant"""
        restaurant_id = "test-restaurant-id"
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        # Add connections
        await connection_manager.connect(websocket1, restaurant_id)
        await connection_manager.connect(websocket2, restaurant_id)
        
        # Clear connection messages
        websocket1.messages.clear()
        websocket2.messages.clear()
        
        message = {"type": "broadcast", "data": "hello all"}
        
        await connection_manager.broadcast_to_restaurant(restaurant_id, message)
        
        # Both connections should receive the message
        assert len(websocket1.messages) == 1
        assert len(websocket2.messages) == 1
        
        received_message1 = json.loads(websocket1.messages[0])
        received_message2 = json.loads(websocket2.messages[0])
        
        assert received_message1 == message
        assert received_message2 == message
    
    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_restaurant(self, connection_manager):
        """Test broadcasting to a restaurant with no connections"""
        message = {"type": "broadcast", "data": "hello"}
        
        # Should not raise exception
        await connection_manager.broadcast_to_restaurant("nonexistent-restaurant", message)
    
    @pytest.mark.asyncio
    async def test_broadcast_order_created(self, connection_manager, mock_websocket, sample_order):
        """Test broadcasting order creation"""
        restaurant_id = sample_order.restaurant_id
        
        await connection_manager.connect(mock_websocket, restaurant_id)
        mock_websocket.messages.clear()  # Clear connection message
        
        await connection_manager.broadcast_order_created(sample_order)
        
        assert len(mock_websocket.messages) == 1
        message = json.loads(mock_websocket.messages[0])
        
        assert message["type"] == "order_created"
        assert message["order"]["id"] == sample_order.id
        assert message["order"]["order_number"] == sample_order.order_number
        assert message["order"]["restaurant_id"] == sample_order.restaurant_id
        assert message["order"]["table_number"] == sample_order.table_number
        assert message["order"]["order_status"] == sample_order.order_status.value
        assert message["order"]["total_price"] == float(sample_order.total_price)
    
    @pytest.mark.asyncio
    async def test_broadcast_order_status_changed(self, connection_manager, mock_websocket, sample_order):
        """Test broadcasting order status change"""
        restaurant_id = sample_order.restaurant_id
        
        await connection_manager.connect(mock_websocket, restaurant_id)
        mock_websocket.messages.clear()  # Clear connection message
        
        await connection_manager.broadcast_order_status_changed(sample_order)
        
        assert len(mock_websocket.messages) == 1
        message = json.loads(mock_websocket.messages[0])
        
        assert message["type"] == "order_status_changed"
        assert message["order"]["id"] == sample_order.id
        assert message["order"]["order_status"] == sample_order.order_status.value
    
    def test_get_connection_count(self, connection_manager, mock_websocket):
        """Test getting connection count for a restaurant"""
        restaurant_id = "test-restaurant-id"
        
        # No connections initially
        assert connection_manager.get_connection_count(restaurant_id) == 0
        
        # Add connection
        connection_manager.active_connections[restaurant_id] = {mock_websocket}
        assert connection_manager.get_connection_count(restaurant_id) == 1
        
        # Add another connection
        websocket2 = MockWebSocket()
        connection_manager.active_connections[restaurant_id].add(websocket2)
        assert connection_manager.get_connection_count(restaurant_id) == 2
    
    def test_get_total_connections(self, connection_manager):
        """Test getting total connection count"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        websocket3 = MockWebSocket()
        
        # Add connections for different restaurants
        connection_manager.active_connections["restaurant1"] = {websocket1, websocket2}
        connection_manager.active_connections["restaurant2"] = {websocket3}
        
        assert connection_manager.get_total_connections() == 3
    
    def test_get_connected_restaurants(self, connection_manager):
        """Test getting list of connected restaurants"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        connection_manager.active_connections["restaurant1"] = {websocket1}
        connection_manager.active_connections["restaurant2"] = {websocket2}
        
        connected = connection_manager.get_connected_restaurants()
        assert set(connected) == {"restaurant1", "restaurant2"}
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_restaurant(self, connection_manager):
        """Test multiple connections for the same restaurant"""
        restaurant_id = "test-restaurant-id"
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        await connection_manager.connect(websocket1, restaurant_id)
        await connection_manager.connect(websocket2, restaurant_id)
        
        assert connection_manager.get_connection_count(restaurant_id) == 2
        assert len(connection_manager.active_connections[restaurant_id]) == 2
        
        # Disconnect one
        connection_manager.disconnect(websocket1)
        
        assert connection_manager.get_connection_count(restaurant_id) == 1
        assert websocket2 in connection_manager.active_connections[restaurant_id]
        assert websocket1 not in connection_manager.active_connections[restaurant_id]
    
    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connections(self, connection_manager):
        """Test broadcasting when some connections fail"""
        restaurant_id = "test-restaurant-id"
        good_websocket = MockWebSocket()
        bad_websocket = MockWebSocket()
        bad_websocket.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Add both connections
        await connection_manager.connect(good_websocket, restaurant_id)
        await connection_manager.connect(bad_websocket, restaurant_id)
        
        # Clear connection messages
        good_websocket.messages.clear()
        
        message = {"type": "test", "data": "broadcast"}
        
        await connection_manager.broadcast_to_restaurant(restaurant_id, message)
        
        # Good connection should receive message
        assert len(good_websocket.messages) == 1
        received_message = json.loads(good_websocket.messages[0])
        assert received_message == message
        
        # Bad connection should be cleaned up
        assert bad_websocket not in connection_manager.active_connections[restaurant_id]
        assert good_websocket in connection_manager.active_connections[restaurant_id]