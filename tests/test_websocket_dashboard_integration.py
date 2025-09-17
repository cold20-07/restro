"""Tests for WebSocket dashboard integration"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from dashboard.websocket_client import DashboardWebSocketClient, get_websocket_client
from dashboard.state import WebSocketState, DashboardState, OrdersState


class TestDashboardWebSocketClient:
    """Test WebSocket client functionality"""
    
    @pytest.fixture
    def ws_client(self):
        """Create WebSocket client instance"""
        return DashboardWebSocketClient("ws://localhost:8000")
    
    def test_client_initialization(self, ws_client):
        """Test WebSocket client initialization"""
        assert ws_client.base_url == "ws://localhost:8000"
        assert ws_client.websocket is None
        assert not ws_client.is_connected
        assert not ws_client.is_connecting
        assert ws_client.access_token is None
        assert ws_client.restaurant_id is None
        assert ws_client.reconnect_attempts == 0
    
    def test_set_auth(self, ws_client):
        """Test setting authentication credentials"""
        token = "test_token_123"
        restaurant_id = "restaurant_456"
        
        ws_client.set_auth(token, restaurant_id)
        
        assert ws_client.access_token == token
        assert ws_client.restaurant_id == restaurant_id
    
    def test_set_event_handlers(self, ws_client):
        """Test setting event handlers"""
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
        
        assert ws_client.on_order_created == on_order_created
        assert ws_client.on_order_status_changed == on_order_status_changed
        assert ws_client.on_connection_established == on_connection_established
        assert ws_client.on_connection_lost == on_connection_lost
        assert ws_client.on_error == on_error
    
    @pytest.mark.asyncio
    async def test_connect_without_auth(self, ws_client):
        """Test connection attempt without authentication"""
        result = await ws_client.connect()
        
        assert not result
        assert not ws_client.is_connected
        assert not ws_client.is_connecting
    
    @pytest.mark.asyncio
    async def test_connect_with_auth(self, ws_client):
        """Test connection with authentication"""
        ws_client.set_auth("test_token", "restaurant_id")
        
        with patch('websockets.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            result = await ws_client.connect()
            
            assert result
            assert ws_client.is_connected
            assert not ws_client.is_connecting
            assert ws_client.websocket == mock_websocket
            
            # Verify connection URL
            expected_url = "ws://localhost:8000/api/v1/ws/orders/live?token=test_token"
            mock_connect.assert_called_once_with(
                expected_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ws_client):
        """Test WebSocket disconnection"""
        # Set up connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        ws_client.websocket = mock_websocket
        ws_client.is_connected = True
        
        await ws_client.disconnect()
        
        mock_websocket.close.assert_called_once()
        assert not ws_client.is_connected
        assert not ws_client.is_connecting
        assert ws_client.websocket is None
    
    @pytest.mark.asyncio
    async def test_send_ping(self, ws_client):
        """Test sending ping message"""
        mock_websocket = AsyncMock()
        ws_client.websocket = mock_websocket
        ws_client.is_connected = True
        
        await ws_client.send_ping()
        
        mock_websocket.send.assert_called_once_with("ping")
    
    @pytest.mark.asyncio
    async def test_handle_message_connection_established(self, ws_client):
        """Test handling connection established message"""
        handler = Mock()
        ws_client.on_connection_established = handler
        
        message_data = {
            "type": "connection_established",
            "restaurant_id": "test_restaurant",
            "message": "Connected"
        }
        
        await ws_client._handle_message(message_data)
        
        handler.assert_called_once_with(message_data)
    
    @pytest.mark.asyncio
    async def test_handle_message_order_created(self, ws_client):
        """Test handling order created message"""
        handler = Mock()
        ws_client.on_order_created = handler
        
        message_data = {
            "type": "order_created",
            "order": {
                "id": "order_123",
                "order_number": "ORD-001",
                "table_number": 5,
                "customer_name": "John Doe",
                "total_price": 25.50
            }
        }
        
        await ws_client._handle_message(message_data)
        
        handler.assert_called_once_with(message_data)
    
    @pytest.mark.asyncio
    async def test_handle_message_order_status_changed(self, ws_client):
        """Test handling order status changed message"""
        handler = Mock()
        ws_client.on_order_status_changed = handler
        
        message_data = {
            "type": "order_status_changed",
            "order": {
                "id": "order_123",
                "order_status": "completed"
            }
        }
        
        await ws_client._handle_message(message_data)
        
        handler.assert_called_once_with(message_data)
    
    def test_get_connection_status(self, ws_client):
        """Test getting connection status"""
        ws_client.is_connected = True
        ws_client.is_connecting = False
        ws_client.reconnect_attempts = 2
        ws_client.access_token = "test_token"
        ws_client.restaurant_id = "test_restaurant"
        
        status = ws_client.get_connection_status()
        
        expected_status = {
            "is_connected": True,
            "is_connecting": False,
            "reconnect_attempts": 2,
            "has_auth": True,
            "restaurant_id": "test_restaurant"
        }
        
        assert status == expected_status
    
    def test_global_client_instance(self):
        """Test global WebSocket client instance"""
        client1 = get_websocket_client()
        client2 = get_websocket_client()
        
        assert client1 is client2  # Should be the same instance


class TestWebSocketState:
    """Test WebSocket state management"""
    
    @pytest.fixture
    def ws_state(self):
        """Create WebSocket state instance"""
        return WebSocketState()
    
    def test_initial_state(self, ws_state):
        """Test initial WebSocket state"""
        assert not ws_state.is_connected
        assert not ws_state.is_connecting
        assert ws_state.connection_error == ""
        assert ws_state.connection_status == "disconnected"
        assert ws_state.reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_connect_websocket_success(self, ws_state):
        """Test successful WebSocket connection"""
        with patch('dashboard.websocket_client.get_websocket_client') as mock_get_client:
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.set_auth = Mock()
            mock_client.set_event_handlers = Mock()
            mock_get_client.return_value = mock_client
            
            await ws_state.connect_websocket("test_token", "restaurant_id")
            
            assert ws_state.is_connected
            assert not ws_state.is_connecting
            assert ws_state.connection_status == "connected"
            assert ws_state.connection_error == ""
            assert ws_state.reconnect_attempts == 0
            
            mock_client.set_auth.assert_called_once_with("test_token", "restaurant_id")
            mock_client.set_event_handlers.assert_called_once()
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_websocket_failure(self, ws_state):
        """Test failed WebSocket connection"""
        with patch('dashboard.websocket_client.get_websocket_client') as mock_get_client:
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client.set_auth = Mock()
            mock_client.set_event_handlers = Mock()
            mock_get_client.return_value = mock_client
            
            await ws_state.connect_websocket("test_token", "restaurant_id")
            
            assert not ws_state.is_connected
            assert not ws_state.is_connecting
            assert ws_state.connection_status == "error"
            assert ws_state.connection_error == "Failed to connect"
    
    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, ws_state):
        """Test WebSocket disconnection"""
        # Set up connected state
        ws_state.is_connected = True
        ws_state.connection_status = "connected"
        
        with patch('dashboard.websocket_client.get_websocket_client') as mock_get_client:
            mock_client = Mock()
            mock_client.disconnect = AsyncMock()
            mock_get_client.return_value = mock_client
            
            await ws_state.disconnect_websocket()
            
            assert not ws_state.is_connected
            assert not ws_state.is_connecting
            assert ws_state.connection_status == "disconnected"
            assert ws_state.connection_error == ""
            
            mock_client.disconnect.assert_called_once()
    
    def test_handle_order_created(self, ws_state):
        """Test handling order created event"""
        # Mock dashboard state
        mock_dashboard_state = Mock()
        mock_dashboard_state.recent_orders = []
        mock_dashboard_state.total_orders = 100
        mock_dashboard_state.total_revenue = 1000.0
        
        # Mock orders state
        mock_orders_state = Mock()
        mock_orders_state.orders = []
        mock_orders_state.orders_per_page = 10
        mock_orders_state.total_orders = 100
        
        with patch.object(ws_state, 'get_state') as mock_get_state:
            def get_state_side_effect(state_class):
                if state_class == DashboardState:
                    return mock_dashboard_state
                elif state_class == OrdersState:
                    return mock_orders_state
                return None
            
            mock_get_state.side_effect = get_state_side_effect
            
            order_data = {
                "order": {
                    "id": "order_123",
                    "order_number": "ORD-001",
                    "table_number": 5,
                    "customer_name": "John Doe",
                    "customer_phone": "+1234567890",
                    "total_price": 25.50,
                    "order_status": "pending",
                    "created_at": "2024-01-15T10:30:00Z",
                    "items": [{"id": "item1"}, {"id": "item2"}],
                    "estimated_time": 15,
                    "payment_method": "cash"
                }
            }
            
            ws_state._handle_order_created(order_data)
            
            # Verify dashboard state was updated
            assert len(mock_dashboard_state.recent_orders) == 1
            assert mock_dashboard_state.recent_orders[0]["id"] == "order_123"
            assert mock_dashboard_state.total_orders == 101
            assert mock_dashboard_state.total_revenue == 1025.50
            
            # Verify orders state was updated
            assert len(mock_orders_state.orders) == 1
            assert mock_orders_state.orders[0]["id"] == "order_123"
            assert mock_orders_state.total_orders == 101
    
    def test_handle_order_status_changed(self, ws_state):
        """Test handling order status changed event"""
        # Mock dashboard state with existing order
        mock_dashboard_state = Mock()
        mock_dashboard_state.recent_orders = [
            {"id": "order_123", "status": "pending"},
            {"id": "order_456", "status": "completed"}
        ]
        
        # Mock orders state with existing order
        mock_orders_state = Mock()
        mock_orders_state.orders = [
            {"id": "order_123", "status": "pending"}
        ]
        mock_orders_state.selected_order = {"id": "order_123", "status": "pending"}
        
        with patch.object(ws_state, 'get_state') as mock_get_state:
            def get_state_side_effect(state_class):
                if state_class == DashboardState:
                    return mock_dashboard_state
                elif state_class == OrdersState:
                    return mock_orders_state
                return None
            
            mock_get_state.side_effect = get_state_side_effect
            
            status_change_data = {
                "order": {
                    "id": "order_123",
                    "order_status": "completed"
                }
            }
            
            ws_state._handle_order_status_changed(status_change_data)
            
            # Verify dashboard state was updated
            assert mock_dashboard_state.recent_orders[0]["status"] == "completed"
            assert mock_dashboard_state.recent_orders[1]["status"] == "completed"  # Should remain unchanged
            
            # Verify orders state was updated
            assert mock_orders_state.orders[0]["status"] == "completed"
            assert mock_orders_state.selected_order["status"] == "completed"
    
    def test_connection_indicator_methods(self, ws_state):
        """Test connection indicator helper methods"""
        # Test connected state
        ws_state.connection_status = "connected"
        assert ws_state.get_connection_indicator_color() == "green"
        assert ws_state.get_connection_indicator_text() == "Connected"
        
        # Test connecting state
        ws_state.connection_status = "connecting"
        assert ws_state.get_connection_indicator_color() == "yellow"
        assert ws_state.get_connection_indicator_text() == "Connecting..."
        
        # Test disconnected state
        ws_state.connection_status = "disconnected"
        assert ws_state.get_connection_indicator_color() == "gray"
        assert ws_state.get_connection_indicator_text() == "Disconnected"
        
        # Test error state
        ws_state.connection_status = "error"
        assert ws_state.get_connection_indicator_color() == "red"
        assert ws_state.get_connection_indicator_text() == "Connection Error"


class TestWebSocketIntegration:
    """Test end-to-end WebSocket integration"""
    
    @pytest.mark.asyncio
    async def test_auth_state_websocket_integration(self):
        """Test WebSocket connection during authentication"""
        from dashboard.state import AuthState
        
        auth_state = AuthState()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token",
                "restaurant_id": "restaurant_123"
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with patch.object(auth_state, 'get_state') as mock_get_state:
                mock_ws_state = Mock()
                mock_ws_state.connect_websocket = AsyncMock()
                mock_get_state.return_value = mock_ws_state
                
                auth_state.email = "test@example.com"
                auth_state.password = "password123"
                
                await auth_state.login()
                
                # Verify WebSocket connection was initiated
                mock_ws_state.connect_websocket.assert_called_once_with(
                    "test_token", "restaurant_123"
                )
    
    @pytest.mark.asyncio
    async def test_logout_websocket_disconnection(self):
        """Test WebSocket disconnection during logout"""
        from dashboard.state import AuthState
        
        auth_state = AuthState()
        auth_state.access_token = "test_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with patch.object(auth_state, 'get_state') as mock_get_state:
                mock_ws_state = Mock()
                mock_ws_state.disconnect_websocket = AsyncMock()
                mock_get_state.return_value = mock_ws_state
                
                await auth_state.logout()
                
                # Verify WebSocket disconnection was called
                mock_ws_state.disconnect_websocket.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])