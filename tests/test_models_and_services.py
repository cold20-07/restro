"""Test script for models and services structure"""

import pytest
from decimal import Decimal
from datetime import datetime

# Test model imports
def test_model_imports():
    """Test that all models can be imported"""
    from app.models import (
        Restaurant, RestaurantCreate, RestaurantUpdate,
        MenuItem, MenuItemCreate, MenuItemUpdate,
        Order, OrderCreate, OrderUpdate, OrderItem, OrderItemCreate,
        CustomerProfile, CustomerProfileCreate, CustomerProfileUpdate,
        OrderStatus, PaymentStatus
    )
    assert True  # If we get here, imports worked


def test_restaurant_model():
    """Test restaurant model validation"""
    from app.models.restaurant import RestaurantCreate, RestaurantUpdate
    
    # Valid restaurant
    restaurant = RestaurantCreate(name="Test Restaurant", owner_id="test-owner")
    assert restaurant.name == "Test Restaurant"
    assert restaurant.owner_id == "test-owner"
    
    # Test validation - empty name should fail
    with pytest.raises(ValueError):
        RestaurantCreate(name="", owner_id="test-owner")
    
    # Test update model
    update = RestaurantUpdate(name="Updated Restaurant")
    assert update.name == "Updated Restaurant"


def test_menu_item_model():
    """Test menu item model validation"""
    from app.models.menu_item import MenuItemCreate, MenuItemUpdate
    
    # Valid menu item
    item = MenuItemCreate(
        restaurant_id="test-id",
        name="Test Pizza",
        price=Decimal("15.99"),
        category="Pizza",
        description="Delicious pizza"
    )
    assert item.name == "Test Pizza"
    assert item.price == Decimal("15.99")
    assert item.category == "Pizza"
    
    # Test validation - negative price should fail
    with pytest.raises(ValueError):
        MenuItemCreate(
            restaurant_id="test-id",
            name="Test Pizza",
            price=Decimal("-5.00"),
            category="Pizza"
        )
    
    # Test validation - empty name should fail
    with pytest.raises(ValueError):
        MenuItemCreate(
            restaurant_id="test-id",
            name="",
            price=Decimal("15.99"),
            category="Pizza"
        )


def test_customer_model():
    """Test customer model validation"""
    from app.models.customer import CustomerProfileCreate
    
    # Valid customer
    customer = CustomerProfileCreate(
        restaurant_id="test-id",
        phone_number="+1234567890",
        name="John Doe"
    )
    assert customer.name == "John Doe"
    assert customer.phone_number == "+1234567890"
    
    # Test phone number cleaning
    customer2 = CustomerProfileCreate(
        restaurant_id="test-id",
        phone_number="(123) 456-7890",
        name="Jane Doe"
    )
    assert customer2.phone_number == "1234567890"
    
    # Test validation - short phone number should fail
    with pytest.raises(ValueError):
        CustomerProfileCreate(
            restaurant_id="test-id",
            phone_number="123",
            name="John Doe"
        )


def test_order_model():
    """Test order model validation"""
    from app.models.order import OrderCreate, OrderItemCreate
    
    # Valid order item
    order_item = OrderItemCreate(
        menu_item_id="test-item-id",
        quantity=2,
        unit_price=Decimal("15.99")
    )
    assert order_item.quantity == 2
    assert order_item.unit_price == Decimal("15.99")
    
    # Valid order
    order = OrderCreate(
        restaurant_id="test-restaurant-id",
        table_number=5,
        customer_name="John Doe",
        customer_phone="+1234567890",
        total_price=Decimal("31.98"),
        items=[order_item]
    )
    assert order.table_number == 5
    assert order.customer_name == "John Doe"
    assert order.total_price == Decimal("31.98")
    assert len(order.items) == 1
    
    # Test validation - negative table number should fail
    with pytest.raises(ValueError):
        OrderCreate(
            restaurant_id="test-restaurant-id",
            table_number=-1,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("31.98"),
            items=[order_item]
        )
    
    # Test validation - empty items should fail
    with pytest.raises(ValueError):
        OrderCreate(
            restaurant_id="test-restaurant-id",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("31.98"),
            items=[]
        )


def test_enums():
    """Test enum values"""
    from app.models.enums import OrderStatus, PaymentStatus
    
    # Test order status enum
    assert OrderStatus.PENDING.value == "pending"
    assert OrderStatus.CONFIRMED.value == "confirmed"
    assert OrderStatus.COMPLETED.value == "completed"
    
    # Test payment status enum
    assert PaymentStatus.PENDING.value == "pending"
    assert PaymentStatus.PAID.value == "paid"
    assert PaymentStatus.FAILED.value == "failed"


def test_service_structure():
    """Test that service classes can be imported and instantiated"""
    # This test doesn't require a database connection
    from app.services.restaurant_service import RestaurantService
    from app.services.menu_item_service import MenuItemService
    from app.services.order_service import OrderService
    from app.services.customer_service import CustomerService
    
    # Test that classes exist and have expected methods
    assert hasattr(RestaurantService, 'create')
    assert hasattr(RestaurantService, 'get')
    assert hasattr(RestaurantService, 'update')
    assert hasattr(RestaurantService, 'delete')
    assert hasattr(RestaurantService, 'get_by_owner_id')
    
    assert hasattr(MenuItemService, 'get_by_restaurant')
    assert hasattr(MenuItemService, 'get_available_menu')
    
    assert hasattr(OrderService, 'create_order_with_items')
    assert hasattr(OrderService, 'get_orders_for_restaurant')
    
    assert hasattr(CustomerService, 'get_by_phone_and_restaurant')
    assert hasattr(CustomerService, 'create_or_update_customer')


if __name__ == "__main__":
    # Run tests manually
    test_model_imports()
    print("✓ Model imports test passed")
    
    test_restaurant_model()
    print("✓ Restaurant model test passed")
    
    test_menu_item_model()
    print("✓ Menu item model test passed")
    
    test_customer_model()
    print("✓ Customer model test passed")
    
    test_order_model()
    print("✓ Order model test passed")
    
    test_enums()
    print("✓ Enums test passed")
    
    test_service_structure()
    print("✓ Service structure test passed")
    
    print("\n✓ All tests passed successfully!")