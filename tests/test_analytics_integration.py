"""Integration tests for analytics functionality"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from app.services.analytics_service import AnalyticsService
from app.models.analytics import AnalyticsResponse
from app.database.base import DatabaseError


class TestAnalyticsIntegration:
    """Integration tests for analytics service and endpoints"""
    
    @pytest.fixture
    def mock_supabase_data(self):
        """Mock comprehensive Supabase data for integration testing"""
        return {
            'orders': [
                {
                    'id': 'order-1',
                    'restaurant_id': 'restaurant-1',
                    'total_price': '25.50',
                    'order_status': 'completed',
                    'payment_status': 'paid',
                    'created_at': '2024-01-15T12:30:00Z',
                    'table_number': 1,
                    'customer_name': 'John Doe'
                },
                {
                    'id': 'order-2',
                    'restaurant_id': 'restaurant-1',
                    'total_price': '18.75',
                    'order_status': 'completed',
                    'payment_status': 'paid',
                    'created_at': '2024-01-15T13:45:00Z',
                    'table_number': 2,
                    'customer_name': 'Jane Smith'
                },
                {
                    'id': 'order-3',
                    'restaurant_id': 'restaurant-1',
                    'total_price': '32.00',
                    'order_status': 'pending',
                    'payment_status': 'pending',
                    'created_at': '2024-01-15T14:20:00Z',
                    'table_number': 3,
                    'customer_name': 'Bob Johnson'
                },
                {
                    'id': 'order-4',
                    'restaurant_id': 'restaurant-1',
                    'total_price': '45.25',
                    'order_status': 'completed',
                    'payment_status': 'paid',
                    'created_at': '2024-01-16T11:15:00Z',
                    'table_number': 1,
                    'customer_name': 'Alice Brown'
                }
            ],
            'order_items': [
                {
                    'menu_item_id': 'item-1',
                    'quantity': 2,
                    'unit_price': '12.75',
                    'menu_items': {'name': 'Margherita Pizza'},
                    'orders': {'id': 'order-1', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T12:30:00Z'}
                },
                {
                    'menu_item_id': 'item-2',
                    'quantity': 1,
                    'unit_price': '18.75',
                    'menu_items': {'name': 'Caesar Salad'},
                    'orders': {'id': 'order-2', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T13:45:00Z'}
                },
                {
                    'menu_item_id': 'item-1',
                    'quantity': 1,
                    'unit_price': '12.75',
                    'menu_items': {'name': 'Margherita Pizza'},
                    'orders': {'id': 'order-3', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T14:20:00Z'}
                },
                {
                    'menu_item_id': 'item-3',
                    'quantity': 1,
                    'unit_price': '19.25',
                    'menu_items': {'name': 'Grilled Chicken'},
                    'orders': {'id': 'order-3', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-15T14:20:00Z'}
                },
                {
                    'menu_item_id': 'item-1',
                    'quantity': 3,
                    'unit_price': '12.75',
                    'menu_items': {'name': 'Margherita Pizza'},
                    'orders': {'id': 'order-4', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-16T11:15:00Z'}
                },
                {
                    'menu_item_id': 'item-4',
                    'quantity': 1,
                    'unit_price': '6.50',
                    'menu_items': {'name': 'Garlic Bread'},
                    'orders': {'id': 'order-4', 'restaurant_id': 'restaurant-1', 'created_at': '2024-01-16T11:15:00Z'}
                }
            ]
        }
    
    @pytest.fixture
    def mock_client_with_data(self, mock_supabase_data):
        """Mock Supabase client with comprehensive test data"""
        client = Mock()
        
        def mock_table_query(table_name):
            table_mock = Mock()
            
            if table_name == 'orders':
                # Mock orders query chain
                select_mock = Mock()
                eq_mock = Mock()
                gte_mock = Mock()
                lte_mock = Mock()
                execute_mock = Mock()
                
                execute_mock.data = mock_supabase_data['orders']
                lte_mock.execute.return_value = execute_mock
                gte_mock.lte.return_value = lte_mock
                eq_mock.gte.return_value = gte_mock
                select_mock.eq.return_value = eq_mock
                table_mock.select.return_value = select_mock
                
            elif table_name == 'order_items':
                # Mock order_items query chain
                select_mock = Mock()
                eq_mock = Mock()
                gte_mock = Mock()
                lte_mock = Mock()
                execute_mock = Mock()
                
                execute_mock.data = mock_supabase_data['order_items']
                lte_mock.execute.return_value = execute_mock
                gte_mock.lte.return_value = lte_mock
                eq_mock.gte.return_value = gte_mock
                select_mock.eq.return_value = eq_mock
                table_mock.select.return_value = select_mock
            
            return table_mock
        
        client.table.side_effect = mock_table_query
        return client
    
    @pytest.mark.asyncio
    async def test_comprehensive_analytics_integration(self, mock_client_with_data):
        """Test complete analytics generation with realistic data"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Test analytics generation
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16)
        )
        
        # Verify comprehensive analytics
        assert isinstance(result, AnalyticsResponse)
        
        # Verify summary metrics
        assert result.total_orders == 4
        assert result.total_revenue == Decimal('121.50')  # 25.50 + 18.75 + 32.00 + 45.25
        expected_avg = Decimal('121.50') / 4
        assert result.average_order_value == expected_avg
        
        # Verify date range
        assert result.date_range.start_date == date(2024, 1, 15)
        assert result.date_range.end_date == date(2024, 1, 16)
        
        # Verify order status breakdown
        assert result.order_status_breakdown.completed == 3
        assert result.order_status_breakdown.pending == 1
        
        # Verify payment status breakdown
        assert result.payment_status_breakdown.paid == 3
        assert result.payment_status_breakdown.pending == 1
        
        # Verify orders by hour (should have data for hours 11, 12, 13, 14)
        assert len(result.orders_by_hour) == 24  # All hours represented
        
        hour_11 = next(h for h in result.orders_by_hour if h.hour == 11)
        assert hour_11.order_count == 1
        assert hour_11.revenue == Decimal('45.25')
        
        hour_12 = next(h for h in result.orders_by_hour if h.hour == 12)
        assert hour_12.order_count == 1
        assert hour_12.revenue == Decimal('25.50')
        
        # Verify revenue by day
        assert len(result.revenue_by_day) == 2  # Two days in range
        
        jan_15 = next(d for d in result.revenue_by_day if d.date == date(2024, 1, 15))
        assert jan_15.order_count == 3
        assert jan_15.revenue == Decimal('76.25')  # 25.50 + 18.75 + 32.00
        
        jan_16 = next(d for d in result.revenue_by_day if d.date == date(2024, 1, 16))
        assert jan_16.order_count == 1
        assert jan_16.revenue == Decimal('45.25')
        
        # Verify best-selling items are populated
        assert len(result.best_selling_items) > 0
    
    @pytest.mark.asyncio
    async def test_best_selling_items_integration(self, mock_client_with_data):
        """Test best-selling items analysis with realistic data"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Test best-selling items
        result = await analytics_service._get_best_selling_items(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
            limit=10
        )
        
        # Verify results
        assert len(result) == 4  # Four unique menu items
        
        # Find Margherita Pizza (should be #1 with 6 total quantity: 2+1+3)
        pizza_item = next(item for item in result if item.menu_item_name == 'Margherita Pizza')
        assert pizza_item.total_quantity_sold == 6
        assert pizza_item.total_revenue == Decimal('76.50')  # 6 * 12.75
        assert pizza_item.order_count == 3  # Appears in 3 different orders
        
        # Verify items are sorted by quantity (descending)
        quantities = [item.total_quantity_sold for item in result]
        assert quantities == sorted(quantities, reverse=True)
    
    @pytest.mark.asyncio
    async def test_quick_metrics_integration(self, mock_client_with_data):
        """Test quick metrics calculation with realistic data"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Test quick metrics
        result = await analytics_service.get_quick_metrics(
            restaurant_id='restaurant-1',
            days=7
        )
        
        # Verify metrics
        assert result['total_orders'] == 4
        assert result['total_revenue'] == 121.50
        assert result['average_order_value'] == 121.50 / 4
        assert result['completion_rate'] == 75.0  # 3 completed out of 4 total
        assert result['period_days'] == 7
    
    @pytest.mark.asyncio
    async def test_analytics_with_empty_data(self):
        """Test analytics behavior with empty data"""
        # Mock client with empty responses
        client = Mock()
        
        def mock_empty_table(table_name):
            table_mock = Mock()
            select_mock = Mock()
            eq_mock = Mock()
            gte_mock = Mock()
            lte_mock = Mock()
            execute_mock = Mock()
            
            execute_mock.data = []
            lte_mock.execute.return_value = execute_mock
            gte_mock.lte.return_value = lte_mock
            eq_mock.gte.return_value = gte_mock
            select_mock.eq.return_value = eq_mock
            table_mock.select.return_value = select_mock
            
            return table_mock
        
        client.table.side_effect = mock_empty_table
        
        analytics_service = AnalyticsService(client)
        
        # Test with empty data
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Verify empty data is handled gracefully
        assert result.total_orders == 0
        assert result.total_revenue == Decimal('0')
        assert result.average_order_value == Decimal('0')
        assert len(result.best_selling_items) == 0
        assert len(result.orders_by_hour) == 24  # All hours still represented with 0 values
        assert len(result.revenue_by_day) == 31  # All days in January represented
        
        # Verify all status breakdowns are zero
        assert result.order_status_breakdown.completed == 0
        assert result.order_status_breakdown.pending == 0
        assert result.payment_status_breakdown.paid == 0
        assert result.payment_status_breakdown.pending == 0
    
    @pytest.mark.asyncio
    async def test_analytics_error_handling_integration(self):
        """Test error handling in analytics integration"""
        # Mock client that raises exceptions
        client = Mock()
        client.table.side_effect = Exception("Database connection failed")
        
        analytics_service = AnalyticsService(client)
        
        # Test that DatabaseError is properly raised and wrapped
        with pytest.raises(DatabaseError, match="Failed to generate analytics"):
            await analytics_service.get_comprehensive_analytics(
                restaurant_id='restaurant-1',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    @pytest.mark.asyncio
    async def test_analytics_date_calculations(self, mock_client_with_data):
        """Test date-based calculations in analytics"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Test with single day range
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15)
        )
        
        # Should only include orders from Jan 15
        assert result.total_orders == 3  # Only orders 1, 2, 3 from Jan 15
        assert result.total_revenue == Decimal('76.25')  # 25.50 + 18.75 + 32.00
        
        # Revenue by day should only have one day
        assert len(result.revenue_by_day) == 1
        assert result.revenue_by_day[0].date == date(2024, 1, 15)
        assert result.revenue_by_day[0].order_count == 3
    
    @pytest.mark.asyncio
    async def test_analytics_time_zone_handling(self, mock_client_with_data):
        """Test that analytics properly handles time zones in data"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Test orders by hour calculation
        orders_data = [
            {
                'id': 'order-1',
                'total_price': '25.50',
                'created_at': '2024-01-15T12:30:00Z'  # UTC time
            },
            {
                'id': 'order-2',
                'total_price': '18.75',
                'created_at': '2024-01-15T23:45:00Z'  # Late UTC time
            }
        ]
        
        result = await analytics_service._get_orders_by_hour(orders_data)
        
        # Verify hours are correctly parsed
        hour_12 = next(h for h in result if h.hour == 12)
        assert hour_12.order_count == 1
        assert hour_12.revenue == Decimal('25.50')
        
        hour_23 = next(h for h in result if h.hour == 23)
        assert hour_23.order_count == 1
        assert hour_23.revenue == Decimal('18.75')
    
    @pytest.mark.asyncio
    async def test_analytics_data_accuracy(self, mock_client_with_data):
        """Test accuracy of analytics calculations"""
        analytics_service = AnalyticsService(mock_client_with_data)
        
        # Get analytics for full date range
        result = await analytics_service.get_comprehensive_analytics(
            restaurant_id='restaurant-1',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16)
        )
        
        # Manually verify calculations
        expected_total_revenue = Decimal('25.50') + Decimal('18.75') + Decimal('32.00') + Decimal('45.25')
        assert result.total_revenue == expected_total_revenue
        
        expected_avg = expected_total_revenue / 4
        assert result.average_order_value == expected_avg
        
        # Verify revenue by day sums to total
        daily_revenue_sum = sum(day.revenue for day in result.revenue_by_day)
        assert daily_revenue_sum == result.total_revenue
        
        # Verify order counts match
        daily_order_sum = sum(day.order_count for day in result.revenue_by_day)
        assert daily_order_sum == result.total_orders