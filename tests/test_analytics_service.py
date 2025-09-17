"""Tests for analytics service functionality"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from app.services.analytics_service import AnalyticsService
from app.models.analytics import (
    AnalyticsResponse, 
    MenuItemStats, 
    OrderVolumeByHour, 
    RevenueByDay,
    OrderStatusBreakdown,
    PaymentStatusBreakdown
)
from app.models.enums import OrderStatus, PaymentStatus
from app.database.base import DatabaseError


class TestAnalyticsService:
    """Test suite for AnalyticsService"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock Supabase client"""
        client = Mock()
        client.table.return_value = Mock()
        return client
    
    @pytest.fixture
    def analytics_service(self, mock_client):
        """Analytics service with mocked client"""
        return AnalyticsService(mock_client)
    
    @pytest.fixture
    def sample_orders_data(self):
        """Sample orders data for testing"""
        return [
            {
                'id': 'order-1',
                'restaurant_id': 'restaurant-1',
                'total_price': '25.50',
                'order_status': 'completed',
                'payment_status': 'paid',
                'created_at': '2024-01-15T12:30:00Z'
            },
            {
                'id': 'order-2',
                'restaurant_id': 'restaurant-1',
                'total_price': '18.75',
                'order_status': 'completed',
                'payment_status': 'paid',
                'created_at': '2024-01-15T13:45:00Z'
            },
            {
                'id': 'order-3',
                'restaurant_id': 'restaurant-1',
                'total_price': '32.00',
                'order_status': 'pending',
                'payment_status': 'pending',
                'created_at': '2024-01-15T14:20:00Z'
            }
        ]
    
    @pytest.fixture
    def sample_order_items_data(self):
        """Sample order items data for testing"""
        return [
            {
                'menu_item_id': 'item-1',
                'quantity': 2,
                'unit_price': '12.75',
                'menu_items': {'name': 'Margherita Pizza'},
                'orders': {'id': 'order-1', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T12:30:00Z'}
            },
            {
                'menu_item_id': 'item-1',
                'quantity': 1,
                'unit_price': '12.75',
                'menu_items': {'name': 'Margherita Pizza'},
                'orders': {'id': 'order-2', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T13:45:00Z'}
            },
            {
                'menu_item_id': 'item-2',
                'quantity': 1,
                'unit_price': '18.75',
                'menu_items': {'name': 'Caesar Salad'},
                'orders': {'id': 'order-2', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T13:45:00Z'}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics_success(self, analytics_service, mock_client, sample_orders_data, sample_order_items_data):
        """Test successful comprehensive analytics generation"""
        # Mock the database responses with different responses for different tables
        def mock_table_query(table_name):
            table_mock = Mock()
            
            if table_name == 'orders':
                mock_response = Mock()
                mock_response.data = sample_orders_data
                table_mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
            elif table_name == 'order_items':
                mock_response = Mock()
                mock_response.data = sample_order_items_data
                table_mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
            
            return table_mock
        
        mock_client.table.side_effect = mock_table_query
        
        # Test the method
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the result
        assert isinstance(result, AnalyticsResponse)
        assert result.total_orders == 3
        assert result.total_revenue == Decimal('76.25')
        assert result.average_order_value == Decimal('76.25') / 3
        assert result.date_range.start_date == start_date
        assert result.date_range.end_date == end_date
        assert isinstance(result.generated_at, datetime)
    
    @pytest.mark.asyncio
    async def test_get_orders_for_period(self, analytics_service, mock_client, sample_orders_data):
        """Test getting orders for a specific period"""
        # Mock the database response
        mock_response = Mock()
        mock_response.data = sample_orders_data
        
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test the method
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service._get_orders_for_period(
            restaurant_id='restaurant-1',
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the result
        assert len(result) == 3
        assert result == sample_orders_data
        
        # Verify the database call
        mock_client.table.assert_called_with('orders')
    
    @pytest.mark.asyncio
    async def test_get_best_selling_items(self, analytics_service, mock_client, sample_order_items_data):
        """Test getting best-selling items analysis"""
        # Mock the database response
        mock_response = Mock()
        mock_response.data = sample_order_items_data
        
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test the method
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service._get_best_selling_items(
            restaurant_id='restaurant-1',
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        
        # Verify the result
        assert len(result) == 2  # Two unique menu items
        assert isinstance(result[0], MenuItemStats)
        
        # Find the Margherita Pizza item (should be first due to higher quantity)
        pizza_item = next(item for item in result if item.menu_item_name == 'Margherita Pizza')
        assert pizza_item.total_quantity_sold == 3  # 2 + 1
        assert pizza_item.total_revenue == Decimal('38.25')  # (2 * 12.75) + (1 * 12.75)
        assert pizza_item.order_count == 2
    
    @pytest.mark.asyncio
    async def test_get_orders_by_hour(self, analytics_service, sample_orders_data):
        """Test analyzing orders by hour of day"""
        result = await analytics_service._get_orders_by_hour(sample_orders_data)
        
        # Verify the result
        assert len(result) == 24  # All hours represented
        assert isinstance(result[0], OrderVolumeByHour)
        
        # Check specific hours with orders
        hour_12 = next(hour for hour in result if hour.hour == 12)
        assert hour_12.order_count == 1
        assert hour_12.revenue == Decimal('25.50')
        
        hour_13 = next(hour for hour in result if hour.hour == 13)
        assert hour_13.order_count == 1
        assert hour_13.revenue == Decimal('18.75')
        
        hour_14 = next(hour for hour in result if hour.hour == 14)
        assert hour_14.order_count == 1
        assert hour_14.revenue == Decimal('32.00')
        
        # Check hour with no orders
        hour_0 = next(hour for hour in result if hour.hour == 0)
        assert hour_0.order_count == 0
        assert hour_0.revenue == Decimal('0')
    
    @pytest.mark.asyncio
    async def test_get_revenue_by_day(self, analytics_service, sample_orders_data):
        """Test calculating daily revenue statistics"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 16)
        
        result = await analytics_service._get_revenue_by_day(
            sample_orders_data, start_date, end_date
        )
        
        # Verify the result
        assert len(result) == 2  # Two days in range
        assert isinstance(result[0], RevenueByDay)
        
        # Check the day with orders
        jan_15 = next(day for day in result if day.date == date(2024, 1, 15))
        assert jan_15.order_count == 3
        assert jan_15.revenue == Decimal('76.25')
        assert jan_15.average_order_value == Decimal('76.25') / 3
        
        # Check the day without orders
        jan_16 = next(day for day in result if day.date == date(2024, 1, 16))
        assert jan_16.order_count == 0
        assert jan_16.revenue == Decimal('0')
        assert jan_16.average_order_value == Decimal('0')
    
    def test_get_order_status_breakdown(self, analytics_service, sample_orders_data):
        """Test calculating order status breakdown"""
        result = analytics_service._get_order_status_breakdown(sample_orders_data)
        
        # Verify the result
        assert isinstance(result, OrderStatusBreakdown)
        assert result.completed == 2
        assert result.pending == 1
        assert result.confirmed == 0
        assert result.in_progress == 0
        assert result.ready == 0
        assert result.canceled == 0
    
    def test_get_payment_status_breakdown(self, analytics_service, sample_orders_data):
        """Test calculating payment status breakdown"""
        result = analytics_service._get_payment_status_breakdown(sample_orders_data)
        
        # Verify the result
        assert isinstance(result, PaymentStatusBreakdown)
        assert result.paid == 2
        assert result.pending == 1
        assert result.failed == 0
        assert result.refunded == 0
    
    @pytest.mark.asyncio
    async def test_get_quick_metrics(self, analytics_service, mock_client, sample_orders_data):
        """Test getting quick metrics for dashboard"""
        # Mock the database response
        mock_response = Mock()
        mock_response.data = sample_orders_data
        
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test the method
        result = await analytics_service.get_quick_metrics(
            restaurant_id='restaurant-1',
            days=7
        )
        
        # Verify the result
        assert result['total_orders'] == 3
        assert result['total_revenue'] == 76.25
        assert result['average_order_value'] == 76.25 / 3
        assert result['completion_rate'] == 66.7  # 2 completed out of 3 total
        assert result['period_days'] == 7
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, analytics_service, mock_client):
        """Test database error handling"""
        # Mock database error
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.side_effect = Exception("Database connection failed")
        
        # Test that DatabaseError is raised
        with pytest.raises(DatabaseError, match="Failed to generate analytics"):
            await analytics_service.get_comprehensive_analytics(
                restaurant_id='restaurant-1',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self, analytics_service, mock_client):
        """Test handling of empty data sets"""
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test the method
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Verify the result handles empty data gracefully
        assert result.total_orders == 0
        assert result.total_revenue == Decimal('0')
        assert result.average_order_value == Decimal('0')
        assert len(result.best_selling_items) == 0
        assert len(result.orders_by_hour) == 24  # All hours still represented
    
    @pytest.mark.asyncio
    async def test_default_date_range(self, analytics_service, mock_client, sample_orders_data):
        """Test default date range when none provided"""
        # Mock the database response
        mock_response = Mock()
        mock_response.data = sample_orders_data
        
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test without providing dates
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1'
        )
        
        # Verify default date range is set (30 days)
        expected_end = date.today()
        expected_start = expected_end - timedelta(days=30)
        
        assert result.date_range.end_date == expected_end
        assert result.date_range.start_date == expected_start
    
    def test_handle_response_with_valid_data(self, analytics_service):
        """Test _handle_response with valid data"""
        mock_response = Mock()
        mock_response.data = [{'id': '1', 'name': 'test'}]
        
        result = analytics_service._handle_response(mock_response)
        assert result == [{'id': '1', 'name': 'test'}]
    
    def test_handle_response_with_none_data(self, analytics_service):
        """Test _handle_response with None data"""
        mock_response = Mock()
        mock_response.data = None
        
        result = analytics_service._handle_response(mock_response)
        assert result == []
    
    def test_handle_response_without_data_attribute(self, analytics_service):
        """Test _handle_response without data attribute"""
        mock_response = Mock(spec=[])  # Mock without data attribute
        
        result = analytics_service._handle_response(mock_response)
        assert result == []