"""
Unit tests for service layer functions and business logic
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

from app.services.order_service import OrderService
from app.services.menu_item_service import MenuItemService
from app.services.customer_service import CustomerService
from app.services.restaurant_service import RestaurantService
from app.services.analytics_service import AnalyticsService
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod
from app.models.menu_item import MenuItem
from app.models.customer import CustomerProfile
from app.models.restaurant import Restaurant
from app.core.exceptions import ValidationError, NotFoundError, AuthorizationError


class TestOrderService:
    """Unit tests for OrderService business logic"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def mock_realtime_service(self):
        return Mock()
    
    @pytest.fixture
    def order_service(self, mock_db_client, mock_realtime_service):
        return OrderService(mock_db_client, mock_realtime_service)
    
    @pytest.fixture
    def sample_order_data(self):
        return {
            "restaurant_id": str(uuid4()),
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "items": [
                {"menu_item_id": str(uuid4()), "quantity": 2},
                {"menu_item_id": str(uuid4()), "quantity": 1}
            ]
        }
    
    @pytest.fixture
    def sample_menu_items(self):
        return [
            MenuItem(
                id=str(uuid4()),
                restaurant_id=str(uuid4()),
                name="Burger",
                price=Decimal("12.99"),
                category="Main",
                is_available=True
            ),
            MenuItem(
                id=str(uuid4()),
                restaurant_id=str(uuid4()),
                name="Fries",
                price=Decimal("4.99"),
                category="Sides",
                is_available=True
            )
        ]
    
    async def test_calculate_order_total_success(self, order_service, sample_menu_items):
        """Test successful order total calculation"""
        # Arrange
        items = [
            {"menu_item_id": sample_menu_items[0].id, "quantity": 2},
            {"menu_item_id": sample_menu_items[1].id, "quantity": 1}
        ]
        
        # Act
        total = order_service._calculate_order_total(items, sample_menu_items)
        
        # Assert
        expected_total = (Decimal("12.99") * 2) + (Decimal("4.99") * 1)
        assert total == expected_total
    
    def test_validate_table_number_valid(self, order_service):
        """Test table number validation with valid input"""
        # Act & Assert - should not raise exception
        order_service._validate_table_number(5)
        order_service._validate_table_number(1)
        order_service._validate_table_number(100)
    
    def test_validate_table_number_invalid(self, order_service):
        """Test table number validation with invalid input"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Table number must be positive"):
            order_service._validate_table_number(0)
        
        with pytest.raises(ValidationError, match="Table number must be positive"):
            order_service._validate_table_number(-1)
    
    def test_validate_order_items_empty(self, order_service):
        """Test order items validation with empty list"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Order must contain at least one item"):
            order_service._validate_order_items([])
    
    def test_validate_order_items_invalid_quantity(self, order_service):
        """Test order items validation with invalid quantities"""
        items = [{"menu_item_id": str(uuid4()), "quantity": 0}]
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Item quantity must be positive"):
            order_service._validate_order_items(items)
    
    def test_generate_order_number_format(self, order_service):
        """Test order number generation format"""
        # Act
        order_number = order_service._generate_order_number()
        
        # Assert
        assert len(order_number) == 8
        assert order_number.isdigit()
    
    def test_generate_order_number_uniqueness(self, order_service):
        """Test order number uniqueness"""
        # Act
        numbers = [order_service._generate_order_number() for _ in range(100)]
        
        # Assert
        assert len(set(numbers)) == 100  # All should be unique


class TestMenuItemService:
    """Unit tests for MenuItemService business logic"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def menu_service(self, mock_db_client):
        return MenuItemService(mock_db_client)
    
    def test_validate_price_positive(self, menu_service):
        """Test price validation with positive values"""
        # Act & Assert - should not raise exception
        menu_service._validate_price(Decimal("10.99"))
        menu_service._validate_price(Decimal("0.01"))
    
    def test_validate_price_invalid(self, menu_service):
        """Test price validation with invalid values"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Price must be positive"):
            menu_service._validate_price(Decimal("0"))
        
        with pytest.raises(ValidationError, match="Price must be positive"):
            menu_service._validate_price(Decimal("-5.99"))
    
    def test_validate_menu_item_data_success(self, menu_service):
        """Test menu item data validation with valid data"""
        data = {
            "name": "Test Item",
            "description": "Test description",
            "price": Decimal("12.99"),
            "category": "Main",
            "is_available": True
        }
        
        # Act & Assert - should not raise exception
        menu_service._validate_menu_item_data(data)
    
    def test_validate_menu_item_data_missing_name(self, menu_service):
        """Test menu item data validation with missing name"""
        data = {
            "description": "Test description",
            "price": Decimal("12.99"),
            "category": "Main"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Menu item name is required"):
            menu_service._validate_menu_item_data(data)
    
    def test_validate_menu_item_data_empty_name(self, menu_service):
        """Test menu item data validation with empty name"""
        data = {
            "name": "",
            "price": Decimal("12.99"),
            "category": "Main"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Menu item name cannot be empty"):
            menu_service._validate_menu_item_data(data)


class TestCustomerService:
    """Unit tests for CustomerService business logic"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def customer_service(self, mock_db_client):
        return CustomerService(mock_db_client)
    
    def test_validate_phone_number_valid(self, customer_service):
        """Test phone number validation with valid formats"""
        valid_numbers = [
            "+1234567890",
            "+12345678901",
            "1234567890",
            "(123) 456-7890"
        ]
        
        for number in valid_numbers:
            # Act & Assert - should not raise exception
            customer_service._validate_phone_number(number)
    
    def test_validate_phone_number_invalid(self, customer_service):
        """Test phone number validation with invalid formats"""
        invalid_numbers = [
            "",
            "123",
            "abc1234567",
            "+123456789012345"  # too long
        ]
        
        for number in invalid_numbers:
            # Act & Assert
            with pytest.raises(ValidationError, match="Invalid phone number format"):
                customer_service._validate_phone_number(number)
    
    def test_normalize_phone_number(self, customer_service):
        """Test phone number normalization"""
        test_cases = [
            ("+1234567890", "+1234567890"),
            ("1234567890", "+1234567890"),
            ("(123) 456-7890", "+11234567890"),
            ("+1 (123) 456-7890", "+11234567890")
        ]
        
        for input_number, expected in test_cases:
            # Act
            result = customer_service._normalize_phone_number(input_number)
            
            # Assert
            assert result == expected


class TestAnalyticsService:
    """Unit tests for AnalyticsService business logic"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def analytics_service(self, mock_db_client):
        return AnalyticsService(mock_db_client)
    
    def test_calculate_average_order_value_with_orders(self, analytics_service):
        """Test average order value calculation with orders"""
        orders = [
            {"total_price": Decimal("25.99")},
            {"total_price": Decimal("18.50")},
            {"total_price": Decimal("32.75")}
        ]
        
        # Act
        avg = analytics_service._calculate_average_order_value(orders)
        
        # Assert
        expected = (Decimal("25.99") + Decimal("18.50") + Decimal("32.75")) / 3
        assert avg == expected.quantize(Decimal('0.01'))
    
    def test_calculate_average_order_value_no_orders(self, analytics_service):
        """Test average order value calculation with no orders"""
        # Act
        avg = analytics_service._calculate_average_order_value([])
        
        # Assert
        assert avg == Decimal("0.00")
    
    def test_calculate_total_revenue(self, analytics_service):
        """Test total revenue calculation"""
        orders = [
            {"total_price": Decimal("25.99")},
            {"total_price": Decimal("18.50")},
            {"total_price": Decimal("32.75")}
        ]
        
        # Act
        total = analytics_service._calculate_total_revenue(orders)
        
        # Assert
        expected = Decimal("25.99") + Decimal("18.50") + Decimal("32.75")
        assert total == expected
    
    def test_group_orders_by_hour(self, analytics_service):
        """Test grouping orders by hour"""
        orders = [
            {"created_at": datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)},
            {"created_at": datetime(2024, 1, 1, 12, 45, 0, tzinfo=timezone.utc)},
            {"created_at": datetime(2024, 1, 1, 13, 15, 0, tzinfo=timezone.utc)},
            {"created_at": datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)}
        ]
        
        # Act
        grouped = analytics_service._group_orders_by_hour(orders)
        
        # Assert
        assert grouped["12"] == 2
        assert grouped["13"] == 1
        assert grouped["14"] == 1
        assert len(grouped) == 24  # Should have all 24 hours
    
    def test_calculate_best_selling_items(self, analytics_service):
        """Test best selling items calculation"""
        order_items = [
            {"menu_item_id": "item1", "quantity": 2, "menu_item_name": "Burger"},
            {"menu_item_id": "item2", "quantity": 1, "menu_item_name": "Fries"},
            {"menu_item_id": "item1", "quantity": 3, "menu_item_name": "Burger"},
            {"menu_item_id": "item3", "quantity": 1, "menu_item_name": "Drink"},
            {"menu_item_id": "item2", "quantity": 2, "menu_item_name": "Fries"}
        ]
        
        # Act
        best_selling = analytics_service._calculate_best_selling_items(order_items, limit=2)
        
        # Assert
        assert len(best_selling) == 2
        assert best_selling[0]["name"] == "Burger"
        assert best_selling[0]["total_quantity"] == 5
        assert best_selling[1]["name"] == "Fries"
        assert best_selling[1]["total_quantity"] == 3


class TestRestaurantService:
    """Unit tests for RestaurantService business logic"""
    
    @pytest.fixture
    def mock_db_client(self):
        return Mock()
    
    @pytest.fixture
    def restaurant_service(self, mock_db_client):
        return RestaurantService(mock_db_client)
    
    def test_validate_restaurant_name_valid(self, restaurant_service):
        """Test restaurant name validation with valid names"""
        valid_names = [
            "Joe's Pizza",
            "The Golden Dragon",
            "Café Bistro",
            "Restaurant 123"
        ]
        
        for name in valid_names:
            # Act & Assert - should not raise exception
            restaurant_service._validate_restaurant_name(name)
    
    def test_validate_restaurant_name_invalid(self, restaurant_service):
        """Test restaurant name validation with invalid names"""
        invalid_names = [
            "",
            "   ",
            "A",  # too short
            "A" * 256  # too long
        ]
        
        for name in invalid_names:
            # Act & Assert
            with pytest.raises(ValidationError):
                restaurant_service._validate_restaurant_name(name)
    
    def test_check_restaurant_ownership_valid(self, restaurant_service):
        """Test restaurant ownership validation with valid owner"""
        restaurant = Restaurant(
            id=str(uuid4()),
            name="Test Restaurant",
            owner_id="user123"
        )
        
        # Act & Assert - should not raise exception
        restaurant_service._check_restaurant_ownership(restaurant, "user123")
    
    def test_check_restaurant_ownership_invalid(self, restaurant_service):
        """Test restaurant ownership validation with invalid owner"""
        restaurant = Restaurant(
            id=str(uuid4()),
            name="Test Restaurant",
            owner_id="user123"
        )
        
        # Act & Assert
        with pytest.raises(AuthorizationError, match="Access denied"):
            restaurant_service._check_restaurant_ownership(restaurant, "user456")