"""Tests for dashboard UI components"""

import pytest
from dashboard.dashboard import metric_card
from dashboard.components import (
    status_badge, data_table, 
    loading_spinner, empty_state, error_message
)
from dashboard.charts import (
    revenue_line_chart, order_status_donut_chart,
    bar_chart, empty_chart_placeholder
)


class TestDashboardComponents:
    """Test dashboard UI components"""
    
    def test_metric_card_creation(self):
        """Test metric card component creation"""
        card = metric_card("Revenue", "$4,287.50", "+12.5%", "positive", "dollar_sign")
        assert card is not None
    
    def test_status_badge_creation(self):
        """Test status badge component creation"""
        badge = status_badge("completed")
        assert badge is not None
        
        badge = status_badge("pending")
        assert badge is not None
        
        badge = status_badge("in_progress")
        assert badge is not None
    
    def test_data_table_creation(self):
        """Test data table component creation"""
        headers = ["Order", "Table", "Customer", "Total", "Status"]
        rows = [
            ["#001", "5", "John Doe", "$45.50", "completed"],
            ["#002", "12", "Jane Smith", "$32.75", "in_progress"]
        ]
        
        table = data_table(headers, rows, "Recent Orders")
        assert table is not None
    
    def test_loading_spinner_creation(self):
        """Test loading spinner component creation"""
        spinner = loading_spinner("lg")
        assert spinner is not None
    
    def test_empty_state_creation(self):
        """Test empty state component creation"""
        empty = empty_state(
            "inbox",
            "No orders yet",
            "Orders will appear here when customers place them"
        )
        assert empty is not None
    
    def test_error_message_creation(self):
        """Test error message component creation"""
        error = error_message("Failed to load data")
        assert error is not None


class TestDashboardCharts:
    """Test dashboard chart components"""
    
    def test_revenue_line_chart_with_data(self):
        """Test revenue line chart with data"""
        data = [
            {"date": "2024-01-08", "revenue": 580.25, "orders": 18},
            {"date": "2024-01-09", "revenue": 720.50, "orders": 23},
            {"date": "2024-01-10", "revenue": 650.75, "orders": 21}
        ]
        
        chart = revenue_line_chart(data, "7d", 300)
        assert chart is not None
    
    def test_revenue_line_chart_empty_data(self):
        """Test revenue line chart with empty data"""
        chart = revenue_line_chart([], "7d", 300)
        assert chart is not None
    
    def test_order_status_donut_chart_with_data(self):
        """Test order status donut chart with data"""
        status_data = {
            "completed": 85,
            "in_progress": 12,
            "pending": 8
        }
        
        chart = order_status_donut_chart(status_data, 200)
        assert chart is not None
    
    def test_order_status_donut_chart_empty_data(self):
        """Test order status donut chart with empty data"""
        chart = order_status_donut_chart({}, 200)
        assert chart is not None
    
    def test_bar_chart_creation(self):
        """Test bar chart component creation"""
        data = [
            {"item": "Pizza", "sales": 45},
            {"item": "Salad", "sales": 32},
            {"item": "Chicken", "sales": 28}
        ]
        
        chart = bar_chart(data, "item", "sales", "Popular Items", 300)
        assert chart is not None
    
    def test_empty_chart_placeholder(self):
        """Test empty chart placeholder"""
        placeholder = empty_chart_placeholder("No data available", 300)
        assert placeholder is not None


class TestDashboardIntegration:
    """Test dashboard integration and component structure"""
    
    def test_dashboard_components_structure(self):
        """Test that dashboard components can be created"""
        # Test metric card
        card = metric_card("Test", "100", "+5%")
        assert card is not None
        
        # Test status badge
        badge = status_badge("completed")
        assert badge is not None
        
        # Test empty state
        empty = empty_state("inbox", "No data", "Description")
        assert empty is not None
    
    def test_chart_components_structure(self):
        """Test that chart components can be created"""
        # Test with sample data
        data = [{"date": "2024-01-01", "revenue": 100, "orders": 5}]
        
        # Test revenue chart
        chart = revenue_line_chart(data, "7d", 300)
        assert chart is not None
        
        # Test donut chart
        status_data = {"completed": 10, "pending": 5}
        donut = order_status_donut_chart(status_data, 200)
        assert donut is not None
        
        # Test bar chart
        bar = bar_chart(data, "date", "revenue", "Test Chart", 300)
        assert bar is not None


if __name__ == "__main__":
    pytest.main([__file__])