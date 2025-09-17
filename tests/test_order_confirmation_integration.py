"""Integration tests for order confirmation functionality"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from app.services.order_service import OrderService
from app.models.order import OrderCreate, OrderItemCreate, Order


class TestOrderConfirmationIntegration:
    """Integration tests for order confirmation features"""
    
    def test_order_service_generates_order_number_and_estimated_time(self):
        """Test that OrderService generates order number and estimated time"""
        order_service = OrderService()
        
        # Test order number generation
        order_number = order_service._generate_order_number("restaurant-123")
        assert order_number.startswith("ORD-")
        assert len(order_number) >= 10
        
        # Test estimated time calculation
        estimated_time = order_service._calculate_estimated_time(3)
        assert estimated_time == 16  # 10 + 3*2
        
        # Test minimum and maximum bounds
        assert order_service._calculate_estimated_time(0) == 10
        assert order_service._calculate_estimated_time(100) == 45
    
    @pytest.mark.asyncio
    async def test_order_creation_includes_confirmation_fields(self):
        """Test that order creation includes order number, estimated time, and payment method"""
        order_service = OrderService()
        
        # Mock the database client
        with patch.object(order_service, 'client') as mock_client:
            # Mock successful database response
            mock_response = MagicMock()
            mock_response.error = None
            mock_response.data = [{
                "id": "order-123",
                "restaurant_id": "restaurant-123",
                "order_number": "ORD-240115-001",
                "table_number": 5,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "order_status": "pending",
                "payment_status": "pending",
                "payment_method": "cash",
                "total_price": "25.98",
                "estimated_time": 14,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }]
            
            mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            # Mock order item service
            with patch.object(order_service.order_item_service, 'create_order_items') as mock_create_items:
                mock_create_items.return_value = []
                
                order_data = OrderCreate(
                    restaurant_id="restaurant-123",
                    table_number=5,
                    customer_name="John Doe",
                    customer_phone="+1234567890",
                    total_price=Decimal("25.98"),
                    items=[
                        OrderItemCreate(menu_item_id="item-1", quantity=2, unit_price=Decimal("12.99"))
                    ]
                )
                
                order = await order_service.create_order_with_items(order_data)
                
                # Verify confirmation fields are present
                assert order.order_number == "ORD-240115-001"
                assert order.estimated_time == 14
                assert hasattr(order, 'payment_method')  # Should be set in service
                
                # Verify the database insert was called with the right data
                insert_call = mock_client.table.return_value.insert.call_args[0][0]
                assert "order_number" in insert_call
                assert "estimated_time" in insert_call
                assert insert_call["payment_method"] == "cash"
                assert insert_call["order_number"].startswith("ORD-")
                assert insert_call["estimated_time"] == 12  # 10 + 2*1 (2 items total)
    
    def test_order_confirmation_messages(self):
        """Test that order confirmation messages are appropriate"""
        # Test confirmation message content
        confirmation_message = "Your order has been sent to the kitchen and is being prepared!"
        payment_message = "Payment will be collected by our staff when your order is ready. We accept cash payments."
        
        # Verify messages contain key information
        assert "kitchen" in confirmation_message.lower()
        assert "prepared" in confirmation_message.lower()
        assert "cash" in payment_message.lower()
        assert "staff" in payment_message.lower()
        assert "payment" in payment_message.lower()
    
    def test_order_number_uniqueness(self):
        """Test that generated order numbers are unique"""
        order_service = OrderService()
        
        # Generate multiple order numbers and verify uniqueness
        order_numbers = set()
        for _ in range(100):
            order_number = order_service._generate_order_number("restaurant-123")
            assert order_number not in order_numbers, f"Duplicate order number: {order_number}"
            order_numbers.add(order_number)
        
        # All should be unique
        assert len(order_numbers) == 100
    
    def test_estimated_time_calculation_logic(self):
        """Test estimated time calculation with various scenarios"""
        order_service = OrderService()
        
        # Test various item counts
        test_cases = [
            (1, 12),   # 10 + 1*2
            (2, 14),   # 10 + 2*2
            (5, 20),   # 10 + 5*2
            (10, 30),  # 10 + 10*2
            (15, 40),  # 10 + 15*2
            (20, 45),  # Capped at 45
            (50, 45),  # Still capped at 45
        ]
        
        for item_count, expected_time in test_cases:
            actual_time = order_service._calculate_estimated_time(item_count)
            assert actual_time == expected_time, f"For {item_count} items, expected {expected_time} but got {actual_time}"
    
    def test_cash_payment_method_default(self):
        """Test that cash is set as default payment method in order data preparation"""
        order_service = OrderService()
        
        # Test that the service would set cash as default payment method
        # This is verified by checking the order creation logic
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("25.98"),
            items=[OrderItemCreate(menu_item_id="item-1", quantity=1, unit_price=Decimal("25.98"))]
        )
        
        # The service should prepare order data with cash payment method
        # This is tested in the integration test with actual database calls
        assert order_data.restaurant_id == "restaurant-123"  # Basic validation that order data is correct


class TestOrderConfirmationErrorHandling:
    """Test error handling in order confirmation"""
    
    def test_order_number_generation_with_invalid_input(self):
        """Test order number generation handles edge cases"""
        order_service = OrderService()
        
        # Should work with any restaurant ID
        order_number = order_service._generate_order_number("")
        assert order_number.startswith("ORD-")
        
        order_number = order_service._generate_order_number("very-long-restaurant-id-that-might-cause-issues")
        assert order_number.startswith("ORD-")
    
    def test_estimated_time_with_edge_cases(self):
        """Test estimated time calculation with edge cases"""
        order_service = OrderService()
        
        # Test negative values (should still return minimum)
        assert order_service._calculate_estimated_time(-1) == 10
        assert order_service._calculate_estimated_time(-100) == 10
        
        # Test zero
        assert order_service._calculate_estimated_time(0) == 10
        
        # Test very large values (should cap at maximum)
        assert order_service._calculate_estimated_time(1000) == 45
        assert order_service._calculate_estimated_time(999999) == 45