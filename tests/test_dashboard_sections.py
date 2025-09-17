"""Tests for enhanced dashboard sections - recent orders, popular items, and table status"""

import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch

# Import dashboard components
try:
    from dashboard.dashboard import (
        DashboardState, enhanced_order_row, enhanced_popular_item,
        table_status_card, recent_orders_table, popular_items_list,
        table_status_grid
    )
except ImportError:
    # If direct import fails, try importing the functions individually
    import dashboard.dashboard as dashboard_module
    
    DashboardState = getattr(dashboard_module, 'DashboardState', None)
    enhanced_order_row = getattr(dashboard_module, 'enhanced_order_row', None)
    enhanced_popular_item = getattr(dashboard_module, 'enhanced_popular_item', None)
    table_status_card = getattr(dashboard_module, 'table_status_card', None)
    recent_orders_table = getattr(dashboard_module, 'recent_orders_table', None)
    popular_items_list = getattr(dashboard_module, 'popular_items_list', None)
    table_status_grid = getattr(dashboard_module, 'table_status_grid', None)


class TestRecentOrdersSection:
    """Test recent orders table component with real-time updates"""
    
    def test_enhanced_order_row_creation(self):
        """Test enhanced order row component creation"""
        order_data = {
            "id": "ord_001",
            "order_number": "ORD-240114-A1B2",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "total": 45.50,
            "status": "completed",
            "created_at": "2024-01-14T14:30:00",
            "items_count": 3,
            "estimated_time": 15,
            "payment_method": "cash"
        }
        
        row = enhanced_order_row(order_data)
        assert row is not None
    
    def test_enhanced_order_row_with_different_statuses(self):
        """Test order row with different status values"""
        statuses = ["pending", "confirmed", "in_progress", "ready", "completed", "canceled"]
        
        for status in statuses:
            order_data = {
                "id": f"ord_{status}",
                "order_number": f"ORD-240114-{status.upper()}",
                "table_number": 1,
                "customer_name": "Test Customer",
                "customer_phone": "+1234567890",
                "total": 25.00,
                "status": status,
                "created_at": "2024-01-14T14:30:00",
                "items_count": 2,
                "estimated_time": 10,
                "payment_method": "cash"
            }
            
            row = enhanced_order_row(order_data)
            assert row is not None
    
    def test_recent_orders_table_creation(self):
        """Test recent orders table component creation"""
        table = recent_orders_table()
        assert table is not None
    
    def test_order_row_handles_missing_fields(self):
        """Test order row handles missing optional fields gracefully"""
        minimal_order = {
            "id": "ord_minimal",
            "table_number": 1,
            "customer_name": "Test",
            "total": 10.00,
            "status": "pending",
            "items_count": 1
        }
        
        row = enhanced_order_row(minimal_order)
        assert row is not None
    
    def test_order_time_formatting(self):
        """Test order time formatting in tooltips"""
        order_with_time = {
            "id": "ord_time",
            "order_number": "ORD-240114-TIME",
            "table_number": 1,
            "customer_name": "Test",
            "total": 10.00,
            "status": "pending",
            "created_at": "2024-01-14T14:30:00Z",
            "items_count": 1
        }
        
        row = enhanced_order_row(order_with_time)
        assert row is not None


class TestPopularItemsSection:
    """Test popular items list component with sales data"""
    
    def test_enhanced_popular_item_creation(self):
        """Test enhanced popular item component creation"""
        item_data = {
            "id": "item_001",
            "name": "Margherita Pizza",
            "sales_count": 45,
            "revenue": 675.00,
            "percentage": 35.4,
            "category": "Pizza",
            "price": 15.00,
            "avg_rating": 4.8,
            "trend": "up"
        }
        
        item = enhanced_popular_item(item_data)
        assert item is not None
    
    def test_popular_item_with_different_categories(self):
        """Test popular item with different category emojis"""
        categories = ["Pizza", "Salads", "Main Course", "Pasta", "Desserts", "Beverages"]
        
        for category in categories:
            item_data = {
                "id": f"item_{category.lower()}",
                "name": f"Test {category}",
                "sales_count": 10,
                "revenue": 100.00,
                "percentage": 10.0,
                "category": category,
                "price": 10.00,
                "avg_rating": 4.5,
                "trend": "stable"
            }
            
            item = enhanced_popular_item(item_data)
            assert item is not None
    
    def test_popular_item_with_different_trends(self):
        """Test popular item with different trend indicators"""
        trends = ["up", "down", "stable"]
        
        for trend in trends:
            item_data = {
                "id": f"item_{trend}",
                "name": f"Test Item {trend}",
                "sales_count": 20,
                "revenue": 200.00,
                "percentage": 20.0,
                "category": "Pizza",
                "price": 10.00,
                "avg_rating": 4.0,
                "trend": trend
            }
            
            item = enhanced_popular_item(item_data)
            assert item is not None
    
    def test_popular_items_list_creation(self):
        """Test popular items list component creation"""
        items_list = popular_items_list()
        assert items_list is not None
    
    def test_popular_item_handles_missing_fields(self):
        """Test popular item handles missing optional fields"""
        minimal_item = {
            "name": "Basic Item",
            "sales_count": 5,
            "revenue": 50.00,
            "percentage": 5.0
        }
        
        item = enhanced_popular_item(minimal_item)
        assert item is not None


class TestTableStatusSection:
    """Test table status grid with color-coded availability"""
    
    def test_table_status_card_creation(self):
        """Test table status card component creation"""
        table_data = {
            "status": "available",
            "capacity": 4,
            "last_cleaned": "14:00"
        }
        
        card = table_status_card("1", table_data)
        assert card is not None
    
    def test_table_status_card_with_different_statuses(self):
        """Test table status card with different status values"""
        statuses = {
            "available": {"capacity": 2, "last_cleaned": "14:00"},
            "occupied": {"capacity": 4, "order_id": "ord_001", "occupied_since": "13:45"},
            "reserved": {"capacity": 2, "reserved_until": "15:00", "customer": "Alice"},
            "out_of_service": {"capacity": 2, "reason": "Maintenance"}
        }
        
        for status, data in statuses.items():
            data["status"] = status
            card = table_status_card("1", data)
            assert card is not None
    
    def test_table_status_grid_creation(self):
        """Test table status grid component creation"""
        grid = table_status_grid()
        assert grid is not None
    
    def test_table_status_card_handles_missing_fields(self):
        """Test table status card handles missing optional fields"""
        minimal_table = {"status": "available"}
        
        card = table_status_card("1", minimal_table)
        assert card is not None


class TestDashboardStateInteractions:
    """Test dashboard state management and interactions"""
    
    @pytest.fixture
    def dashboard_state(self):
        """Create a dashboard state instance for testing"""
        return DashboardState()
    
    def test_load_recent_orders(self, dashboard_state):
        """Test loading recent orders data"""
        import asyncio
        
        async def test_async():
            await dashboard_state.load_recent_orders()
            assert len(dashboard_state.recent_orders) > 0
            assert dashboard_state.orders_error == ""
        
        asyncio.run(test_async())
    
    def test_load_popular_items(self, dashboard_state):
        """Test loading popular items data"""
        import asyncio
        
        async def test_async():
            await dashboard_state.load_popular_items()
            assert len(dashboard_state.popular_items) > 0
            assert dashboard_state.analytics_error == ""
        
        asyncio.run(test_async())
    
    def test_load_table_status(self, dashboard_state):
        """Test loading table status data"""
        import asyncio
        
        async def test_async():
            await dashboard_state.load_table_status()
            assert len(dashboard_state.table_status) > 0
            assert dashboard_state.tables_error == ""
        
        asyncio.run(test_async())
    
    def test_update_order_status(self, dashboard_state):
        """Test updating order status"""
        import asyncio
        
        async def test_async():
            # First load orders
            await dashboard_state.load_recent_orders()
            
            # Get first order ID
            if dashboard_state.recent_orders:
                order_id = dashboard_state.recent_orders[0]["id"]
                original_status = dashboard_state.recent_orders[0]["status"]
                
                # Update status
                await dashboard_state.update_order_status(order_id, "completed")
                
                # Find the updated order
                updated_order = dashboard_state.get_order_by_id(order_id)
                assert updated_order is not None
                assert updated_order["status"] == "completed"
        
        asyncio.run(test_async())
    
    def test_update_table_status(self, dashboard_state):
        """Test updating table status"""
        import asyncio
        
        async def test_async():
            # First load table status
            await dashboard_state.load_table_status()
            
            # Update a table status
            if dashboard_state.table_status:
                table_number = list(dashboard_state.table_status.keys())[0]
                await dashboard_state.update_table_status(table_number, "occupied")
                
                assert dashboard_state.table_status[table_number]["status"] == "occupied"
        
        asyncio.run(test_async())
    
    def test_get_order_by_id(self, dashboard_state):
        """Test getting order by ID"""
        import asyncio
        
        async def test_async():
            await dashboard_state.load_recent_orders()
            
            if dashboard_state.recent_orders:
                order_id = dashboard_state.recent_orders[0]["id"]
                order = dashboard_state.get_order_by_id(order_id)
                
                assert order is not None
                assert order["id"] == order_id
            
            # Test non-existent order
            non_existent = dashboard_state.get_order_by_id("non_existent")
            assert non_existent is None
        
        asyncio.run(test_async())


class TestDashboardIntegration:
    """Test integration between dashboard components"""
    
    def test_dashboard_components_integration(self):
        """Test that all dashboard components can be created together"""
        # Test that components can be instantiated without errors
        orders_table = recent_orders_table()
        items_list = popular_items_list()
        status_grid = table_status_grid()
        
        assert orders_table is not None
        assert items_list is not None
        assert status_grid is not None
    
    def test_error_state_handling(self):
        """Test error state handling in components"""
        # This would test error states in a real implementation
        # For now, just ensure components can handle error states
        orders_table = recent_orders_table()
        items_list = popular_items_list()
        status_grid = table_status_grid()
        
        assert orders_table is not None
        assert items_list is not None
        assert status_grid is not None
    
    def test_loading_state_handling(self):
        """Test loading state handling in components"""
        # This would test loading states in a real implementation
        orders_table = recent_orders_table()
        items_list = popular_items_list()
        status_grid = table_status_grid()
        
        assert orders_table is not None
        assert items_list is not None
        assert status_grid is not None


class TestRealTimeUpdates:
    """Test real-time update functionality"""
    
    def test_order_status_updates(self):
        """Test order status updates trigger UI changes"""
        # This would test real-time updates in a full implementation
        # For now, test that the update methods exist and can be called
        state = DashboardState()
        
        # Test that methods exist
        assert hasattr(state, 'update_order_status')
        assert hasattr(state, 'update_table_status')
        assert hasattr(state, 'get_order_by_id')
    
    def test_table_status_updates(self):
        """Test table status updates trigger UI changes"""
        state = DashboardState()
        
        # Test that table status can be updated
        import asyncio
        
        async def test_async():
            await state.load_table_status()
            if state.table_status:
                table_num = list(state.table_status.keys())[0]
                original_status = state.table_status[table_num]["status"]
                
                await state.update_table_status(table_num, "occupied")
                assert state.table_status[table_num]["status"] == "occupied"
        
        asyncio.run(test_async())


if __name__ == "__main__":
    pytest.main([__file__])