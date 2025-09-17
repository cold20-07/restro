"""Tests for real-time service and Supabase integration"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.realtime_service import RealtimeService
from app.models.order import Order
from app.models.enums import OrderStatus, PaymentStatus
from decimal import Decimal
from datetime import datetime


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    client = MagicMock()
    
    # Mock table method chain
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    # Mock query methods
    table_mock.select.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.gt.return_value = table_mock
    table_mock.gte.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[])
    
    return client


@pytest.fixture
def realtime_service(mock_supabase_client):
    """Create a RealtimeService instance with mocked client"""
    return RealtimeService(client=mock_supabase_client)


@pytest.fixture
def sample_order_data():
    """Create sample order data for testing"""
    return {
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
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


class TestRealtimeService:
    """Test RealtimeService functionality"""
    
    def test_initialization(self, mock_supabase_client):
        """Test RealtimeService initialization"""
        service = RealtimeService(client=mock_supabase_client)
        
        assert service.client == mock_supabase_client
        assert service.subscriptions == {}
        assert not service._is_running
        assert service.order_service is not None
    
    def test_is_running(self, realtime_service):
        """Test is_running method"""
        assert not realtime_service.is_running()
        
        realtime_service._is_running = True
        assert realtime_service.is_running()
    
    @pytest.mark.asyncio
    async def test_start_order_subscription(self, realtime_service):
        """Test starting order subscription"""
        with patch.object(realtime_service, '_start_polling_mechanism') as mock_polling:
            mock_polling.return_value = None
            
            await realtime_service.start_order_subscription()
            
            assert realtime_service._is_running
            mock_polling.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_order_subscription_already_running(self, realtime_service):
        """Test starting subscription when already running"""
        realtime_service._is_running = True
        
        with patch.object(realtime_service, '_start_polling_mechanism') as mock_polling:
            await realtime_service.start_order_subscription()
            
            # Should not call polling mechanism again
            mock_polling.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_order_subscription(self, realtime_service):
        """Test stopping order subscription"""
        realtime_service._is_running = True
        realtime_service.subscriptions = {"test": "subscription"}
        
        await realtime_service.stop_order_subscription()
        
        assert not realtime_service._is_running
        assert realtime_service.subscriptions == {}
    
    @pytest.mark.asyncio
    async def test_check_restaurant_orders_first_time(self, realtime_service, mock_supabase_client, sample_order_data):
        """Test checking restaurant orders for the first time"""
        restaurant_id = "test-restaurant-id"
        last_check_timestamps = {}
        
        # Mock response with order data
        mock_supabase_client.table.return_value.execute.return_value.data = [sample_order_data]
        
        with patch.object(realtime_service, '_handle_order_change') as mock_handle:
            mock_handle.return_value = None
            
            await realtime_service._check_restaurant_orders(restaurant_id, last_check_timestamps)
            
            # Should query for recent orders (first time)
            mock_supabase_client.table.assert_called_with("orders")
            
            # Should handle the order change
            mock_handle.assert_called_once_with(sample_order_data)
            
            # Should update timestamp
            assert restaurant_id in last_check_timestamps
    
    @pytest.mark.asyncio
    async def test_check_restaurant_orders_with_timestamp(self, realtime_service, mock_supabase_client, sample_order_data):
        """Test checking restaurant orders with existing timestamp"""
        restaurant_id = "test-restaurant-id"
        last_timestamp = "2024-01-15T10:00:00Z"
        last_check_timestamps = {restaurant_id: last_timestamp}
        
        # Mock response with order data
        mock_supabase_client.table.return_value.execute.return_value.data = [sample_order_data]
        
        with patch.object(realtime_service, '_handle_order_change') as mock_handle:
            mock_handle.return_value = None
            
            await realtime_service._check_restaurant_orders(restaurant_id, last_check_timestamps)
            
            # Should query for orders updated since last check
            table_mock = mock_supabase_client.table.return_value
            table_mock.gt.assert_called_with("updated_at", last_timestamp)
            
            # Should handle the order change
            mock_handle.assert_called_once_with(sample_order_data)
    
    @pytest.mark.asyncio
    async def test_check_restaurant_orders_no_data(self, realtime_service, mock_supabase_client):
        """Test checking restaurant orders with no new data"""
        restaurant_id = "test-restaurant-id"
        last_check_timestamps = {}
        
        # Mock empty response
        mock_supabase_client.table.return_value.execute.return_value.data = []
        
        with patch.object(realtime_service, '_handle_order_change') as mock_handle:
            await realtime_service._check_restaurant_orders(restaurant_id, last_check_timestamps)
            
            # Should not handle any order changes
            mock_handle.assert_not_called()
            
            # Should not update timestamp
            assert restaurant_id not in last_check_timestamps
    
    @pytest.mark.asyncio
    async def test_check_restaurant_orders_error_handling(self, realtime_service, mock_supabase_client):
        """Test error handling in check_restaurant_orders"""
        restaurant_id = "test-restaurant-id"
        last_check_timestamps = {}
        
        # Mock exception
        mock_supabase_client.table.side_effect = Exception("Database error")
        
        # Should not raise exception
        await realtime_service._check_restaurant_orders(restaurant_id, last_check_timestamps)
    
    @pytest.mark.asyncio
    async def test_handle_order_change_new_order(self, realtime_service, sample_order_data):
        """Test handling new order change"""
        # Set created_at and updated_at to same time (new order)
        now = datetime.utcnow()
        sample_order_data["created_at"] = now.isoformat()
        sample_order_data["updated_at"] = now.isoformat()
        
        with patch.object(realtime_service.order_service, 'get_order_with_items') as mock_get_order:
            mock_get_order.return_value = None
            
            with patch('app.services.realtime_service.connection_manager') as mock_connection_manager:
                mock_connection_manager.broadcast_order_created = AsyncMock()
                
                await realtime_service._handle_order_change(sample_order_data)
                
                # Should broadcast as new order
                mock_connection_manager.broadcast_order_created.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_order_change_updated_order(self, realtime_service, sample_order_data):
        """Test handling updated order change"""
        # Set updated_at later than created_at (updated order)
        created_at = datetime.utcnow()
        updated_at = datetime(created_at.year, created_at.month, created_at.day, 
                             created_at.hour, created_at.minute + 1, created_at.second)
        
        sample_order_data["created_at"] = created_at.isoformat()
        sample_order_data["updated_at"] = updated_at.isoformat()
        
        with patch.object(realtime_service.order_service, 'get_order_with_items') as mock_get_order:
            mock_get_order.return_value = None
            
            with patch('app.services.realtime_service.connection_manager') as mock_connection_manager:
                mock_connection_manager.broadcast_order_status_changed = AsyncMock()
                
                await realtime_service._handle_order_change(sample_order_data)
                
                # Should broadcast as status change
                mock_connection_manager.broadcast_order_status_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_order_change_with_items(self, realtime_service, sample_order_data):
        """Test handling order change with items"""
        # Mock order with items
        mock_order_with_items = Order(**sample_order_data)
        
        with patch.object(realtime_service.order_service, 'get_order_with_items') as mock_get_order:
            mock_get_order.return_value = mock_order_with_items
            
            with patch('app.services.realtime_service.connection_manager') as mock_connection_manager:
                mock_connection_manager.broadcast_order_created = AsyncMock()
                
                await realtime_service._handle_order_change(sample_order_data)
                
                # Should use order with items
                mock_connection_manager.broadcast_order_created.assert_called_once()
                call_args = mock_connection_manager.broadcast_order_created.call_args[0]
                assert call_args[0] == mock_order_with_items
    
    @pytest.mark.asyncio
    async def test_handle_order_change_error_handling(self, realtime_service, sample_order_data):
        """Test error handling in handle_order_change"""
        # Make Order creation fail
        invalid_data = sample_order_data.copy()
        del invalid_data["id"]  # Remove required field
        
        # Should not raise exception
        await realtime_service._handle_order_change(invalid_data)
    
    @pytest.mark.asyncio
    async def test_polling_mechanism_integration(self, realtime_service):
        """Test the polling mechanism with connection manager integration"""
        with patch('app.services.realtime_service.connection_manager') as mock_connection_manager:
            mock_connection_manager.get_connected_restaurants.return_value = ["restaurant1", "restaurant2"]
            
            with patch.object(realtime_service, '_check_restaurant_orders') as mock_check:
                mock_check.return_value = None
                
                # Start polling and let it run for a short time
                realtime_service._is_running = True
                
                # Create a task that will stop after a short time
                async def stop_after_delay():
                    await asyncio.sleep(0.1)
                    realtime_service._is_running = False
                
                # Run both tasks concurrently
                await asyncio.gather(
                    realtime_service._start_polling_mechanism(),
                    stop_after_delay()
                )
                
                # Should have checked both restaurants
                assert mock_check.call_count >= 2  # At least one call per restaurant
    
    @pytest.mark.asyncio
    async def test_polling_mechanism_error_handling(self, realtime_service):
        """Test polling mechanism handles errors gracefully"""
        with patch('app.services.realtime_service.connection_manager') as mock_connection_manager:
            mock_connection_manager.get_connected_restaurants.side_effect = Exception("Connection error")
            
            realtime_service._is_running = True
            
            # Create a task that will stop after a short time
            async def stop_after_delay():
                await asyncio.sleep(0.1)
                realtime_service._is_running = False
            
            # Should not raise exception even with errors
            try:
                await asyncio.gather(
                    realtime_service._start_polling_mechanism(),
                    stop_after_delay()
                )
            except Exception as e:
                pytest.fail(f"Polling mechanism should handle errors gracefully, but raised: {e}")
            
            # Test passes if no exception is raised