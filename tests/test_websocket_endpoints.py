"""Tests for WebSocket endpoints"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from main import app
from app.models.auth import User
from app.models.enums import UserRole


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user"""
    return User(
        id="test-user-id",
        email="test@example.com",
        restaurant_id="test-restaurant-id",
        role=UserRole.OWNER,
        is_active=True,
        created_at="2024-01-15T10:30:45Z"
    )


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"


class TestWebSocketEndpoints:
    """Test WebSocket endpoint functionality"""
    
    def test_websocket_status_endpoint_success(self, client, mock_user, mock_jwt_token):
        """Test WebSocket status endpoint with valid authentication"""
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = mock_user
            
            with patch('app.api.v1.endpoints.websocket.connection_manager') as mock_manager:
                mock_manager.get_connection_count.return_value = 2
                mock_manager.get_total_connections.return_value = 5
                
                with patch('app.api.v1.endpoints.websocket.get_realtime_service') as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_running.return_value = True
                    mock_get_service.return_value = mock_service
                    
                    response = client.get(
                        "/api/ws/orders/live/status",
                        headers={"Authorization": f"Bearer {mock_jwt_token}"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["restaurant_id"] == mock_user.restaurant_id
                    assert data["active_connections"] == 2
                    assert data["realtime_service_running"] is True
                    assert data["total_system_connections"] == 5
    
    def test_websocket_status_endpoint_no_restaurant(self, client, mock_jwt_token):
        """Test WebSocket status endpoint with user having no restaurant"""
        user_without_restaurant = User(
            id="test-user-id",
            email="test@example.com",
            restaurant_id=None,
            role=UserRole.OWNER,
            is_active=True,
            created_at="2024-01-15T10:30:45Z"
        )
        
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = user_without_restaurant
            
            response = client.get(
                "/api/ws/orders/live/status",
                headers={"Authorization": f"Bearer {mock_jwt_token}"}
            )
            
            assert response.status_code == 400
            assert "No restaurant associated" in response.json()["detail"]
    
    def test_websocket_status_endpoint_unauthorized(self, client):
        """Test WebSocket status endpoint without authentication"""
        response = client.get("/api/ws/orders/live/status")
        
        assert response.status_code == 401
    
    def test_websocket_connections_endpoint_success(self, client, mock_user, mock_jwt_token):
        """Test WebSocket connections endpoint with valid authentication"""
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = mock_user
            
            with patch('app.api.v1.endpoints.websocket.connection_manager') as mock_manager:
                mock_manager.get_connection_count.return_value = 3
                mock_manager.get_connected_restaurants.return_value = ["restaurant1", "restaurant2"]
                mock_manager.get_total_connections.return_value = 8
                
                with patch('app.api.v1.endpoints.websocket.get_realtime_service') as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_running.return_value = True
                    mock_get_service.return_value = mock_service
                    
                    response = client.get(
                        "/api/ws/orders/live/connections",
                        headers={"Authorization": f"Bearer {mock_jwt_token}"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["restaurant_connections"] == 3
                    assert data["connected_restaurants"] == ["restaurant1", "restaurant2"]
                    assert data["total_connections"] == 8
                    assert data["realtime_service_status"]["running"] is True
    
    def test_websocket_connections_endpoint_no_restaurant(self, client, mock_jwt_token):
        """Test WebSocket connections endpoint with user having no restaurant"""
        user_without_restaurant = User(
            id="test-user-id",
            email="test@example.com",
            restaurant_id=None,
            role=UserRole.OWNER,
            is_active=True,
            created_at="2024-01-15T10:30:45Z"
        )
        
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = user_without_restaurant
            
            response = client.get(
                "/api/ws/orders/live/connections",
                headers={"Authorization": f"Bearer {mock_jwt_token}"}
            )
            
            assert response.status_code == 400
            assert "No restaurant associated" in response.json()["detail"]


class TestWebSocketConnection:
    """Test WebSocket connection functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_success(self, mock_user, mock_jwt_token):
        """Test successful WebSocket connection"""
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = mock_user
            
            with patch('app.api.v1.endpoints.websocket.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = MagicMock()
                mock_manager.send_personal_message = AsyncMock()
                
                with patch('app.api.v1.endpoints.websocket.get_realtime_service') as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_running.return_value = False
                    mock_service.start_order_subscription = AsyncMock()
                    mock_get_service.return_value = mock_service
                    
                    # Mock WebSocket
                    mock_websocket = MagicMock()
                    mock_websocket.receive_text = AsyncMock(side_effect=["ping", Exception("disconnect")])
                    
                    # Import the websocket function
                    from app.api.v1.endpoints.websocket import websocket_order_updates
                    
                    # Should not raise exception
                    try:
                        await websocket_order_updates(mock_websocket, mock_jwt_token)
                    except:
                        pass  # Expected to fail due to mocked disconnect
                    
                    # Verify connection was established
                    mock_manager.connect.assert_called_once_with(mock_websocket, mock_user.restaurant_id)
                    
                    # Verify real-time service was started
                    mock_service.start_order_subscription.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_authentication_failure(self, mock_jwt_token):
        """Test WebSocket connection with authentication failure"""
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.side_effect = Exception("Invalid token")
            
            mock_websocket = MagicMock()
            mock_websocket.close = AsyncMock()
            
            from app.api.v1.endpoints.websocket import websocket_order_updates
            
            # Should handle authentication error gracefully
            try:
                await websocket_order_updates(mock_websocket, "invalid_token")
            except:
                pass  # Expected to fail
            
            # Should close WebSocket with appropriate code
            mock_websocket.close.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_no_restaurant(self, mock_jwt_token):
        """Test WebSocket connection with user having no restaurant"""
        user_without_restaurant = User(
            id="test-user-id",
            email="test@example.com",
            restaurant_id=None,
            role=UserRole.OWNER,
            is_active=True,
            created_at="2024-01-15T10:30:45Z"
        )
        
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = user_without_restaurant
            
            mock_websocket = MagicMock()
            mock_websocket.close = AsyncMock()
            
            from app.api.v1.endpoints.websocket import websocket_order_updates
            
            await websocket_order_updates(mock_websocket, mock_jwt_token)
            
            # Should close WebSocket with policy violation
            mock_websocket.close.assert_called_with(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="No restaurant associated"
            )
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, mock_user, mock_jwt_token):
        """Test WebSocket ping/pong functionality"""
        with patch('app.api.v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = mock_user
            
            with patch('app.api.v1.endpoints.websocket.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = MagicMock()
                mock_manager.send_personal_message = AsyncMock()
                
                with patch('app.api.v1.endpoints.websocket.get_realtime_service') as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.is_running.return_value = True
                    mock_get_service.return_value = mock_service
                    
                    mock_websocket = MagicMock()
                    mock_websocket.receive_text = AsyncMock(side_effect=["ping", Exception("disconnect")])
                    
                    from app.api.v1.endpoints.websocket import websocket_order_updates
                    
                    try:
                        await websocket_order_updates(mock_websocket, mock_jwt_token)
                    except:
                        pass  # Expected to fail due to mocked disconnect
                    
                    # Should respond to ping with pong
                    mock_manager.send_personal_message.assert_called_with(
                        mock_websocket,
                        {
                            "type": "pong",
                            "message": "Connection is alive"
                        }
                    )


class TestWebSocketIntegration:
    """Test WebSocket integration with order service"""
    
    @pytest.mark.asyncio
    async def test_order_creation_triggers_websocket_broadcast(self):
        """Test that creating an order triggers WebSocket broadcast"""
        from app.services.order_service import OrderService
        from app.models.order import OrderCreate, OrderItemCreate
        
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
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
        }]
        
        order_service = OrderService(client=mock_client)
        
        with patch('app.services.order_service.connection_manager') as mock_manager:
            mock_manager.broadcast_order_created = AsyncMock()
            
            order_data = OrderCreate(
                restaurant_id="test-restaurant-id",
                table_number=5,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=25.50,
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=2,
                        unit_price=12.75
                    )
                ]
            )
            
            # Mock order item creation
            with patch.object(order_service.order_item_service, 'create_order_items') as mock_create_items:
                mock_create_items.return_value = []
                
                await order_service.create_order_with_items(order_data)
                
                # Should broadcast order creation
                mock_manager.broadcast_order_created.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_order_status_update_triggers_websocket_broadcast(self):
        """Test that updating order status triggers WebSocket broadcast"""
        from app.services.order_service import OrderService
        from app.models.enums import OrderStatus
        
        mock_client = MagicMock()
        
        # Mock get_order_for_restaurant
        existing_order_data = {
            "id": "test-order-id",
            "restaurant_id": "test-restaurant-id",
            "order_status": "pending"
        }
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_order_data]
        
        # Mock update
        updated_order_data = existing_order_data.copy()
        updated_order_data["order_status"] = "confirmed"
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated_order_data]
        
        order_service = OrderService(client=mock_client)
        
        with patch('app.services.order_service.connection_manager') as mock_manager:
            mock_manager.broadcast_order_status_changed = AsyncMock()
            
            with patch.object(order_service, 'get_order_with_items') as mock_get_order:
                mock_get_order.return_value = None
                
                await order_service.update_order_status(
                    "test-order-id",
                    "test-restaurant-id",
                    OrderStatus.CONFIRMED
                )
                
                # Should broadcast status change
                mock_manager.broadcast_order_status_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_error_handling(self):
        """Test that WebSocket broadcast errors don't break order operations"""
        from app.services.order_service import OrderService
        from app.models.order import OrderCreate, OrderItemCreate
        
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
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
        }]
        
        order_service = OrderService(client=mock_client)
        
        with patch('app.services.order_service.connection_manager') as mock_manager:
            # Make broadcast fail
            mock_manager.broadcast_order_created = AsyncMock(side_effect=Exception("Broadcast failed"))
            
            order_data = OrderCreate(
                restaurant_id="test-restaurant-id",
                table_number=5,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=25.50,
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=2,
                        unit_price=12.75
                    )
                ]
            )
            
            # Mock order item creation
            with patch.object(order_service.order_item_service, 'create_order_items') as mock_create_items:
                mock_create_items.return_value = []
                
                # Should not raise exception even if broadcast fails
                result = await order_service.create_order_with_items(order_data)
                
                # Order should still be created successfully
                assert result is not None
                assert result.id == "test-order-id"