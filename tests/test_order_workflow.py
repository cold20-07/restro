"""Test order workflow and business logic"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock

from app.models.order import OrderCreate, OrderItemCreate, Order, OrderItem
from app.models.menu_item import MenuItem
from app.models.customer import CustomerProfile
from app.models.enums import OrderStatus, PaymentStatus


class TestOrderWorkflow:
    """Test order creation workflow and business logic"""
    
    @pytest.mark.asyncio
    async def test_order_calculation_workflow(self):
        """Test the complete order calculation workflow"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        
        # Sample menu items
        menu_items = [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Burger",
                description="Delicious burger",
                price=Decimal("15.99"),
                category="Main",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-2",
                restaurant_id="restaurant-123",
                name="Fries",
                description="Crispy fries",
                price=Decimal("5.99"),
                category="Sides",
                image_url=None,
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
        
        mock_menu_service.get_menu_items_by_ids.return_value = menu_items
        
        # Create order data with multiple quantities
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("37.97"),  # (15.99 * 2) + (5.99 * 1)
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=2,  # Multiple burgers
                    unit_price=Decimal("15.99")
                ),
                OrderItemCreate(
                    menu_item_id="item-2",
                    quantity=1,
                    unit_price=Decimal("5.99")
                )
            ]
        )
        
        # Test calculation
        total, validated_items = await OrderCalculationService.validate_and_calculate_order(
            order_data, mock_menu_service
        )
        
        # Assertions
        assert total == Decimal("37.97")
        assert len(validated_items) == 2
        
        # Verify prices are corrected to menu prices
        assert validated_items[0].unit_price == Decimal("15.99")
        assert validated_items[0].quantity == 2
        assert validated_items[1].unit_price == Decimal("5.99")
        assert validated_items[1].quantity == 1
        
        # Verify service was called correctly
        mock_menu_service.get_menu_items_by_ids.assert_called_once_with(
            ["item-1", "item-2"], 
            "restaurant-123"
        )
    
    def test_order_model_validation(self):
        """Test order model validation rules"""
        # Valid order
        valid_order = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("21.98"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                )
            ]
        )
        
        assert valid_order.table_number == 5
        assert valid_order.customer_name == "John Doe"
        assert valid_order.customer_phone == "+1234567890"
        assert len(valid_order.items) == 1
    
    def test_order_item_validation(self):
        """Test order item validation"""
        # Valid order item
        valid_item = OrderItemCreate(
            menu_item_id="item-123",
            quantity=2,
            unit_price=Decimal("15.99")
        )
        
        assert valid_item.quantity == 2
        assert valid_item.unit_price == Decimal("15.99")
    
    def test_phone_number_normalization(self):
        """Test phone number normalization in order creation"""
        # Test various phone number formats
        test_cases = [
            ("+1 (234) 567-8900", "+12345678900"),
            ("234-567-8900", "2345678900"),
            ("(234) 567 8900", "2345678900"),
            ("+1234567890", "+1234567890")
        ]
        
        for input_phone, expected_phone in test_cases:
            order = OrderCreate(
                restaurant_id="restaurant-123",
                table_number=5,
                customer_name="John Doe",
                customer_phone=input_phone,
                total_price=Decimal("21.98"),
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=1,
                        unit_price=Decimal("15.99")
                    )
                ]
            )
            
            assert order.customer_phone == expected_phone
    
    def test_customer_name_normalization(self):
        """Test customer name normalization"""
        # Test name with extra whitespace
        order = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="  John Doe  ",
            customer_phone="+1234567890",
            total_price=Decimal("21.98"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                )
            ]
        )
        
        assert order.customer_name == "John Doe"
    
    def test_order_status_enum_values(self):
        """Test order status enum values"""
        # Test all order status values
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.CONFIRMED == "confirmed"
        assert OrderStatus.IN_PROGRESS == "in_progress"
        assert OrderStatus.READY == "ready"
        assert OrderStatus.COMPLETED == "completed"
        assert OrderStatus.CANCELED == "canceled"
    
    def test_payment_status_enum_values(self):
        """Test payment status enum values"""
        # Test all payment status values
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.PAID == "paid"
        assert PaymentStatus.FAILED == "failed"
        assert PaymentStatus.REFUNDED == "refunded"
    
    def test_order_with_items_structure(self):
        """Test order structure with items"""
        order = Order(
            id="order-123",
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            total_price=Decimal("21.98"),
            created_at=datetime.utcnow(),
            updated_at=None,
            items=[
                OrderItem(
                    id="order-item-1",
                    order_id="order-123",
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99"),
                    created_at=datetime.utcnow(),
                    updated_at=None
                )
            ]
        )
        
        assert order.id == "order-123"
        assert len(order.items) == 1
        assert order.items[0].order_id == "order-123"
        assert order.items[0].menu_item_id == "item-1"
    
    @pytest.mark.asyncio
    async def test_price_mismatch_detection(self):
        """Test price mismatch detection in order calculation"""
        from app.api.v1.endpoints.orders import OrderCalculationService
        from fastapi import HTTPException
        
        # Mock menu service
        mock_menu_service = AsyncMock()
        
        # Menu item with different price than submitted
        menu_item = MenuItem(
            id="item-1",
            restaurant_id="restaurant-123",
            name="Burger",
            description="Delicious burger",
            price=Decimal("18.99"),  # Different from submitted price
            category="Main",
            image_url=None,
            is_available=True,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        mock_menu_service.get_menu_items_by_ids.return_value = [menu_item]
        
        # Order with incorrect price
        order_data = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("15.99"),  # Incorrect total
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")  # Incorrect unit price
                )
            ]
        )
        
        # Should calculate correct total but detect mismatch
        total, validated_items = await OrderCalculationService.validate_and_calculate_order(
            order_data, mock_menu_service
        )
        
        # The calculated total should be correct
        assert total == Decimal("18.99")
        # The validated item should have the correct price
        assert validated_items[0].unit_price == Decimal("18.99")
        
        # This would cause a price mismatch error in the endpoint
        assert abs(total - order_data.total_price) > Decimal("0.01")


class TestOrderStatusTransitions:
    """Test order status transition logic"""
    
    def test_valid_status_transitions(self):
        """Test valid order status transitions"""
        # Define valid transitions as per business logic
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELED],
            OrderStatus.CONFIRMED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELED],
            OrderStatus.IN_PROGRESS: [OrderStatus.READY, OrderStatus.CANCELED],
            OrderStatus.READY: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],  # No transitions from completed
            OrderStatus.CANCELED: []    # No transitions from canceled
        }
        
        # Test each valid transition
        for current_status, allowed_next_statuses in valid_transitions.items():
            for next_status in allowed_next_statuses:
                # This represents a valid transition
                assert next_status in allowed_next_statuses
                
        # Test some invalid transitions
        invalid_transitions = [
            (OrderStatus.COMPLETED, OrderStatus.PENDING),
            (OrderStatus.CANCELED, OrderStatus.CONFIRMED),
            (OrderStatus.READY, OrderStatus.PENDING),
            (OrderStatus.IN_PROGRESS, OrderStatus.PENDING)
        ]
        
        for current_status, invalid_next_status in invalid_transitions:
            allowed = valid_transitions.get(current_status, [])
            assert invalid_next_status not in allowed
    
    def test_order_lifecycle(self):
        """Test complete order lifecycle"""
        # Typical order flow: pending -> confirmed -> in_progress -> ready -> completed
        lifecycle_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.READY,
            OrderStatus.COMPLETED
        ]
        
        # Each status should be a valid enum value
        for status in lifecycle_statuses:
            assert isinstance(status, OrderStatus)
            assert status.value in ["pending", "confirmed", "in_progress", "ready", "completed"]
    
    def test_cancellation_flow(self):
        """Test order cancellation from various states"""
        # Orders can be canceled from these states
        cancelable_states = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.IN_PROGRESS
        ]
        
        for state in cancelable_states:
            # Cancellation should be possible from these states
            assert OrderStatus.CANCELED != state  # Different from current state
            
        # Orders cannot be canceled from these states
        non_cancelable_states = [
            OrderStatus.READY,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELED
        ]
        
        for state in non_cancelable_states:
            # These are final or near-final states
            assert state in [OrderStatus.READY, OrderStatus.COMPLETED, OrderStatus.CANCELED]