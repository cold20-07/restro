"""Integration tests for dashboard pages and navigation"""

import pytest
import reflex as rx
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from dashboard.state import DashboardState, OrdersState, MenuState, NavigationState
from dashboard.pages.dashboard import dashboard_page
from dashboard.pages.orders import orders_page
from dashboard.pages.menu import menu_page


class TestDashboardPageIntegration:
    """Test dashboard page integration and functionality"""
    
    def test_dashboard_page_structure(self):
        """Test that dashboard page has correct structure"""
        page = dashboard_page()
        
        # Verify page is a component
        assert isinstance(page, rx.Component)
        
        # Test that navigation state is set correctly
        assert NavigationState.current_page == "dashboard"
    
    def test_dashboard_metrics_section(self):
        """Test dashboard metrics section renders correctly"""
        from dashboard.pages.dashboard import dashboard_metrics
        
        # Mock dashboard state with sample data
        with patch.object(DashboardState, 'total_revenue', 4287.50):
            with patch.object(DashboardState, 'total_orders', 127):
                with patch.object(DashboardState, 'total_customers', 89):
                    with patch.object(DashboardState, 'average_rating', 4.8):
                        metrics = dashboard_metrics()
                        assert isinstance(metrics, rx.Component)
    
    def test_dashboard_charts_section(self):
        """Test dashboard charts section renders correctly"""
        from dashboard.pages.dashboard import dashboard_charts
        
        # Mock dashboard state
        with patch.object(DashboardState, 'revenue_period', '7d'):
            with patch.object(DashboardState, 'total_revenue', 4287.50):
                with patch.object(DashboardState, 'order_status_data', {
                    'completed': 85, 'in_progress': 12, 'pending': 8
                }):
                    charts = dashboard_charts()
                    assert isinstance(charts, rx.Component)
    
    def test_dashboard_activity_section(self):
        """Test dashboard activity section with orders and popular items"""
        from dashboard.pages.dashboard import dashboard_activity
        
        # Mock recent orders data
        mock_orders = [
            {
                "order_number": "ORD-001",
                "table_number": 5,
                "customer_name": "John Doe",
                "total": 45.50,
                "status": "completed"
            }
        ]
        
        # Mock popular items data
        mock_items = [
            {
                "name": "Margherita Pizza",
                "sales_count": 45,
                "revenue": 675.0,
                "percentage": 35.4
            }
        ]
        
        with patch.object(DashboardState, 'recent_orders', mock_orders):
            with patch.object(DashboardState, 'popular_items', mock_items):
                activity = dashboard_activity()
                assert isinstance(activity, rx.Component)
    
    def test_dashboard_table_status_section(self):
        """Test dashboard table status section"""
        from dashboard.pages.dashboard import dashboard_table_status
        
        # Mock table status data
        mock_tables = {
            "1": {"status": "available", "capacity": 2},
            "2": {"status": "occupied", "capacity": 4}
        }
        
        with patch.object(DashboardState, 'table_status', mock_tables):
            table_status = dashboard_table_status()
            assert isinstance(table_status, rx.Component)


class TestOrdersPageIntegration:
    """Test orders page integration and functionality"""
    
    def test_orders_page_structure(self):
        """Test that orders page has correct structure"""
        page = orders_page()
        
        # Verify page is a component
        assert isinstance(page, rx.Component)
    
    def test_orders_filters_component(self):
        """Test orders filters component"""
        from dashboard.pages.orders import orders_filters
        
        filters = orders_filters()
        assert isinstance(filters, rx.Component)
    
    def test_orders_table_component(self):
        """Test orders table component"""
        from dashboard.pages.orders import orders_table
        
        # Mock orders data
        mock_orders = [
            {
                "id": "ord_001",
                "order_number": "ORD-001",
                "table_number": 5,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "total": 45.50,
                "status": "completed",
                "items_count": 3,
                "created_at": "2024-01-14T14:30:00"
            }
        ]
        
        with patch.object(OrdersState, 'orders', mock_orders):
            with patch.object(OrdersState, 'is_loading', False):
                with patch.object(OrdersState, 'error_message', ""):
                    table = orders_table()
                    assert isinstance(table, rx.Component)
    
    def test_orders_pagination_component(self):
        """Test orders pagination component"""
        from dashboard.pages.orders import orders_pagination
        
        with patch.object(OrdersState, 'current_page', 1):
            with patch.object(OrdersState, 'orders_per_page', 10):
                with patch.object(OrdersState, 'total_orders', 50):
                    pagination = orders_pagination()
                    assert isinstance(pagination, rx.Component)


class TestMenuPageIntegration:
    """Test menu page integration and functionality"""
    
    def test_menu_page_structure(self):
        """Test that menu page has correct structure"""
        page = menu_page()
        
        # Verify page is a component
        assert isinstance(page, rx.Component)
    
    def test_menu_filters_component(self):
        """Test menu filters component"""
        from dashboard.pages.menu import menu_filters
        
        filters = menu_filters()
        assert isinstance(filters, rx.Component)
    
    def test_menu_items_grid_component(self):
        """Test menu items grid component"""
        from dashboard.pages.menu import menu_items_grid
        
        # Mock menu items data
        mock_items = [
            {
                "id": "item_001",
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                "price": 15.00,
                "category": "Pizza",
                "is_available": True,
                "image_url": "/images/margherita.jpg"
            }
        ]
        
        with patch.object(MenuState, 'filtered_menu_items', mock_items):
            with patch.object(MenuState, 'is_loading', False):
                with patch.object(MenuState, 'error_message', ""):
                    grid = menu_items_grid()
                    assert isinstance(grid, rx.Component)
    
    def test_menu_item_modal_component(self):
        """Test menu item modal component"""
        from dashboard.pages.menu import menu_item_modal
        
        modal = menu_item_modal()
        assert isinstance(modal, rx.Component)


class TestNavigationIntegration:
    """Test navigation and routing integration"""
    
    def test_navigation_state_management(self):
        """Test navigation state management"""
        # Test setting different pages
        NavigationState.current_page = "dashboard"
        assert NavigationState.current_page == "dashboard"
        
        NavigationState.current_page = "orders"
        assert NavigationState.current_page == "orders"
        
        NavigationState.current_page = "menu"
        assert NavigationState.current_page == "menu"
    
    def test_sidebar_navigation_component(self):
        """Test sidebar navigation component"""
        from dashboard.layout import sidebar_nav
        
        nav = sidebar_nav()
        assert isinstance(nav, rx.Component)
    
    def test_base_layout_component(self):
        """Test base layout component"""
        from dashboard.layout import base_layout
        
        # Create a simple test content
        test_content = rx.text("Test content")
        
        layout = base_layout(
            content=test_content,
            page_title="Test Page"
        )
        assert isinstance(layout, rx.Component)


class TestStateIntegration:
    """Test state management integration across pages"""
    
    @pytest.mark.asyncio
    async def test_dashboard_state_loading(self):
        """Test dashboard state data loading"""
        state = DashboardState()
        
        # Mock the load methods
        with patch.object(state, 'load_analytics_data', new_callable=AsyncMock) as mock_analytics:
            with patch.object(state, 'load_recent_orders', new_callable=AsyncMock) as mock_orders:
                with patch.object(state, 'load_popular_items', new_callable=AsyncMock) as mock_items:
                    with patch.object(state, 'load_table_status', new_callable=AsyncMock) as mock_tables:
                        
                        await state.load_dashboard_data()
                        
                        # Verify all load methods were called
                        mock_analytics.assert_called_once()
                        mock_orders.assert_called_once()
                        mock_items.assert_called_once()
                        mock_tables.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orders_state_loading(self):
        """Test orders state data loading"""
        state = OrdersState()
        
        # Test loading orders
        await state.load_orders()
        
        # Verify orders were loaded (mock data)
        assert isinstance(state.orders, list)
        assert state.is_loading == False
    
    @pytest.mark.asyncio
    async def test_menu_state_loading(self):
        """Test menu state data loading"""
        state = MenuState()
        
        # Test loading menu items
        await state.load_menu_items()
        
        # Verify menu items were loaded (mock data)
        assert isinstance(state.menu_items, list)
        assert state.is_loading == False
    
    def test_state_error_handling(self):
        """Test state error handling"""
        state = DashboardState()
        
        # Test setting error states
        state.orders_error = "Test error"
        assert state.orders_error == "Test error"
        
        state.analytics_error = "Analytics error"
        assert state.analytics_error == "Analytics error"
        
        state.tables_error = "Tables error"
        assert state.tables_error == "Tables error"


class TestComponentIntegration:
    """Test component integration and reusability"""
    
    def test_loading_spinner_component(self):
        """Test loading spinner component"""
        from dashboard.components import loading_spinner
        
        spinner = loading_spinner("lg")
        assert isinstance(spinner, rx.Component)
        
        spinner_md = loading_spinner("md")
        assert isinstance(spinner_md, rx.Component)
    
    def test_empty_state_component(self):
        """Test empty state component"""
        from dashboard.components import empty_state
        
        empty = empty_state(
            icon="inbox",
            title="No data",
            description="No data available"
        )
        assert isinstance(empty, rx.Component)
    
    def test_error_message_component(self):
        """Test error message component"""
        from dashboard.components import error_message
        
        error = error_message("Test error message")
        assert isinstance(error, rx.Component)
    
    def test_stat_card_component(self):
        """Test stat card component"""
        from dashboard.components import stat_card
        
        card = stat_card(
            title="Revenue",
            value="$4,287.50",
            icon="dollar_sign",
            color="green"
        )
        assert isinstance(card, rx.Component)
    
    def test_status_badge_component(self):
        """Test status badge component"""
        from dashboard.components import status_badge
        
        badge = status_badge("completed")
        assert isinstance(badge, rx.Component)
        
        badge_pending = status_badge("pending")
        assert isinstance(badge_pending, rx.Component)


class TestLayoutIntegration:
    """Test layout components integration"""
    
    def test_page_header_component(self):
        """Test page header component"""
        from dashboard.layout import page_header
        
        header = page_header("Test Title", "Test subtitle")
        assert isinstance(header, rx.Component)
    
    def test_content_card_component(self):
        """Test content card component"""
        from dashboard.layout import content_card
        
        test_content = rx.text("Test content")
        card = content_card(test_content, title="Test Card")
        assert isinstance(card, rx.Component)
    
    def test_metric_grid_component(self):
        """Test metric grid component"""
        from dashboard.layout import metric_grid
        from dashboard.components import stat_card
        
        metrics = [
            stat_card("Revenue", "$1000", "dollar_sign"),
            stat_card("Orders", "50", "shopping_cart")
        ]
        
        grid = metric_grid(metrics)
        assert isinstance(grid, rx.Component)
    
    def test_two_column_layout_component(self):
        """Test two column layout component"""
        from dashboard.layout import two_column_layout
        
        left_content = rx.text("Left content")
        right_content = rx.text("Right content")
        
        layout = two_column_layout(left_content, right_content)
        assert isinstance(layout, rx.Component)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])