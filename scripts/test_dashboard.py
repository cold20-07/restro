#!/usr/bin/env python3
"""Script to test the dashboard components and verify they work correctly"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dashboard_import():
    """Test that dashboard components can be imported"""
    try:
        from dashboard.dashboard import DashboardState, metric_card
        from dashboard.components import status_badge, data_table
        from dashboard.charts import revenue_line_chart, order_status_donut_chart
        from dashboard.styles import COLORS, get_theme
        print("✅ All dashboard modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import dashboard modules: {e}")
        return False

def test_component_creation():
    """Test that components can be created"""
    try:
        from dashboard.dashboard import metric_card
        from dashboard.components import status_badge, loading_spinner
        from dashboard.charts import empty_chart_placeholder
        
        # Test metric card
        card = metric_card("Revenue", "$1,234", "+5%", "positive", "dollar_sign")
        print("✅ Metric card created successfully")
        
        # Test status badge
        badge = status_badge("completed")
        print("✅ Status badge created successfully")
        
        # Test loading spinner
        spinner = loading_spinner("lg")
        print("✅ Loading spinner created successfully")
        
        # Test chart placeholder
        placeholder = empty_chart_placeholder("No data", 300)
        print("✅ Chart placeholder created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create components: {e}")
        return False

def test_chart_creation():
    """Test that charts can be created with sample data"""
    try:
        from dashboard.charts import revenue_line_chart, order_status_donut_chart, bar_chart
        
        # Test revenue chart
        revenue_data = [
            {"date": "2024-01-01", "revenue": 100, "orders": 5},
            {"date": "2024-01-02", "revenue": 150, "orders": 8}
        ]
        revenue_chart = revenue_line_chart(revenue_data, "7d", 300)
        print("✅ Revenue chart created successfully")
        
        # Test donut chart
        status_data = {"completed": 10, "in_progress": 5, "pending": 2}
        donut_chart = order_status_donut_chart(status_data, 200)
        print("✅ Donut chart created successfully")
        
        # Test bar chart
        bar_data = [{"item": "Pizza", "sales": 45}, {"item": "Salad", "sales": 32}]
        bar_chart_comp = bar_chart(bar_data, "item", "sales", "Popular Items", 300)
        print("✅ Bar chart created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create charts: {e}")
        return False

def test_styles_and_theme():
    """Test that styles and theme work correctly"""
    try:
        from dashboard.styles import COLORS, get_theme, apply_component_style
        
        # Test colors
        assert COLORS["primary"] == "#FF6B35"
        print("✅ Colors loaded successfully")
        
        # Test theme
        theme = get_theme()
        print("✅ Theme created successfully")
        
        # Test component styles
        card_style = apply_component_style("card")
        print("✅ Component styles loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load styles: {e}")
        return False

def main():
    """Run all dashboard tests"""
    print("🧪 Testing Dashboard Components")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_dashboard_import),
        ("Component Creation Test", test_component_creation),
        ("Chart Creation Test", test_chart_creation),
        ("Styles and Theme Test", test_styles_and_theme)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All dashboard tests passed! The dashboard is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())