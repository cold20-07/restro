"""Integration tests for real-time dashboard WebSocket functionality"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from main import app
from app.services.websocket_service import connection_manager
from app.models.order import Order, OrderStatus, PaymentStatus
# PaymentMethod not needed - using string directly
from datetime import datetime
from decimal import Decimal


class TestRealtimeDashboardIntegration:
    """Test real-time dashboard integration with WebSocket backend"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_order(self):
        """Create mock order for testing"""
        return Order(
            id="test_order_123",
            order_number="ORD-240115-TEST",
            restaurant_id="test_restaurant_456",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method="cash",
            total_price=Decimal("25.50"),
            estimated_time=15,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            items=[]
        )
    
    @pytest.mark.asyncio
    async def test_websocket_connection_manager(self):
        """Test WebSocket connection manager functionality"""
        restaurant_id = "test_restaurant_123"
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        
        # Test connection
        await connection_manager.connect(mock_websocket, restaurant_id)
        
        assert restaurant_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[restaurant_id]
        assert connection_manager.connection_restaurant_map[mock_websocket] == restaurant_id
        
        # Test connection count
        assert connection_manager.get_connection_count(restaurant_id) == 1
        assert connection_manager.get_total_connections() == 1
        
        # Test disconnection
        connection_manager.disconnect(mock_websocket)
        
        assert restaurant_id not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.connection_restaurant_map
    
    @pytest.mark.asyncio
    async def test_order_broadcast(self, mock_order):
        """Test order broadcasting to WebSocket connections"""
        restaurant_id = mock_order.restaurant_id
        
        # Mock WebSocket connections
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Connect WebSockets
        await connection_manager.connect(mock_websocket1, restaurant_id)
        await connection_manager.connect(mock_websocket2, restaurant_id)
        
        # Broadcast order update
        await connection_manager.broadcast_order_created(mock_order)
        
        # Verify both connections received the message
        assert mock_websocket1.send_text.call_count == 2  # Connection confirmation + order message
        assert mock_websocket2.send_text.call_count == 2  # Connection confirmation + order message
        
        # Verify message content
        order_message_call = mock_websocket1.send_text.call_args_list[1]
        message_data = json.loads(order_message_call[0][0])
        
        assert message_data["type"] == "order_created"
        assert message_data["order"]["id"] == mock_order.id
        assert message_data["order"]["order_number"] == mock_order.order_number
        assert message_data["order"]["restaurant_id"] == mock_order.restaurant_id
        assert message_data["order"]["table_number"] == mock_order.table_number
        assert message_data["order"]["customer_name"] == mock_order.customer_name
        assert message_data["order"]["order_status"] == mock_order.order_status.value
        assert float(message_data["order"]["total_price"]) == float(mock_order.total_price)
        
        # Clean up
        connection_manager.disconnect(mock_websocket1)
        connection_manager.disconnect(mock_websocket2)
    
    @pytest.mark.asyncio
    async def test_order_status_change_broadcast(self, mock_order):
        """Test order status change broadcasting"""
        restaurant_id = mock_order.restaurant_id
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        await connection_manager.connect(mock_websocket, restaurant_id)
        
        # Update order status
        mock_order.order_status = OrderStatus.COMPLETED
        mock_order.updated_at = datetime.now()
        
        # Broadcast status change
        await connection_manager.broadcast_order_status_changed(mock_order)
        
        # Verify message was sent
        assert mock_websocket.send_text.call_count == 2  # Connection + status change
        
        # Verify message content
        status_message_call = mock_websocket.send_text.call_args_list[1]
        message_data = json.loads(status_message_call[0][0])
        
        assert message_data["type"] == "order_status_changed"
        assert message_data["order"]["id"] == mock_order.id
        assert message_data["order"]["order_status"] == OrderStatus.COMPLETED.value
        
        # Clean up
        connection_manager.disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_authentication(self, client):
        """Test WebSocket endpoint authentication"""
        # Test without token
        with pytest.raises(Exception):  # Should fail without proper WebSocket setup
            with client.websocket_connect("/api/v1/ws/orders/live") as websocket:
                pass
        
        # Test with invalid token
        with pytest.raises(Exception):  # Should fail with invalid token
            with client.websocket_connect("/api/v1/ws/orders/live?token=invalid_token") as websocket:
                pass
    
    @pytest.mark.asyncio
    async def test_realtime_service_polling(self):
        """Test real-time service polling mechanism"""
        from app.services.realtime_service import RealtimeService
        
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_response = Mock()
        mock_response.data = []
        mock_table.select.return_value.eq.return_value.gt.return_value.order.return_value.execute.return_value = mock_response
        mock_client.table.return_value = mock_table
        
        realtime_service = RealtimeService(mock_client)
        
        # Test service initialization
        assert not realtime_service.is_running()
        
        # Mock connection manager
        with patch('app.services.realtime_service.connection_manager') as mock_conn_manager:
            mock_conn_manager.get_connected_restaurants.return_value = ["restaurant_123"]
            
            # Start service briefly
            task = asyncio.create_task(realtime_service.start_order_subscription())
            await asyncio.sleep(0.1)  # Let it run briefly
            
            assert realtime_service.is_running()
            
            # Stop service
            await realtime_service.stop_order_subscription()
            assert not realtime_service.is_running()
            
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_dashboard_websocket_client_integration(self):
        """Test dashboard WebSocket client integration with backend"""
        from dashboard.websocket_client import DashboardWebSocketClient
        
        # Create client
        ws_client = DashboardWebSocketClient("ws://localhost:8000")
        ws_client.set_auth("test_token", "restaurant_123")
        
        # Mock event handlers
        on_order_created = Mock()
        on_order_status_changed = Mock()
        on_connection_established = Mock()
        on_connection_lost = Mock()
        on_error = Mock()
        
        ws_client.set_event_handlers(
            on_order_created=on_order_created,
            on_order_status_changed=on_order_status_changed,
            on_connection_established=on_connection_established,
            on_connection_lost=on_connection_lost,
            on_error=on_error
        )
        
        # Test connection status
        status = ws_client.get_connection_status()
        assert not status["is_connected"]
        assert not status["is_connecting"]
        assert status["has_auth"]
        assert status["restaurant_id"] == "restaurant_123"
        
        # Test message handling
        test_messages = [
            {
                "type": "connection_established",
                "restaurant_id": "restaurant_123",
                "message": "Connected"
            },
            {
                "type": "order_created",
                "order": {
                    "id": "order_123",
                    "order_number": "ORD-001",
                    "table_number": 5,
                    "total_price": 25.50
                }
            },
            {
                "type": "order_status_changed",
                "order": {
                    "id": "order_123",
                    "order_status": "completed"
                }
            }
        ]
        
        for message in test_messages:
            await ws_client._handle_message(message)
        
        # Verify handlers were called
        on_connection_established.assert_called_once()
        on_order_created.assert_called_once()
        on_order_status_changed.assert_called_once()
    
    def test_websocket_status_endpoint(self, client):
        """Test WebSocket status endpoint"""
        # Mock authentication
        with patch('app.core.auth.get_current_user_from_token') as mock_auth:
            mock_user = Mock()
            mock_user.restaurant_id = "restaurant_123"
            mock_auth.return_value = mock_user
            
            # Test status endpoint
            response = client.get(
                "/api/v1/ws/orders/live/status",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "restaurant_id" in data
            assert "active_connections" in data
            assert "realtime_service_running" in data
            assert "total_system_connections" in data
            
            assert data["restaurant_id"] == "restaurant_123"
            assert isinstance(data["active_connections"], int)
            assert isinstance(data["realtime_service_running"], bool)
            assert isinstance(data["total_system_connections"], int)
    
    def test_websocket_connections_endpoint(self, client):
        """Test WebSocket connections endpoint"""
        # Mock authentication
        with patch('app.core.auth.get_current_user_from_token') as mock_auth:
            mock_user = Mock()
            mock_user.restaurant_id = "restaurant_123"
            mock_auth.return_value = mock_user
            
            # Test connections endpoint
            response = client.get(
                "/api/v1/ws/orders/live/connections",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "restaurant_connections" in data
            assert "connected_restaurants" in data
            assert "total_connections" in data
            assert "realtime_service_status" in data
            
            assert isinstance(data["restaurant_connections"], int)
            assert isinstance(data["connected_restaurants"], list)
            assert isinstance(data["total_connections"], int)
            assert isinstance(data["realtime_service_status"], dict)
            assert "running" in data["realtime_service_status"]


if __name__ == "__main__":
    pytest.main([__file__])