"""Unit tests for public menu service"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

from app.services.public_menu_service import PublicMenuService
from app.services.menu_item_service import MenuItemService
from app.services.restaurant_service import RestaurantService
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.public_menu import (
    PublicMenuResponse, 
    PublicMenuItemResponse, 
    PublicMenuByCategory,
    MenuCategoryResponse
)
from app.database.base import NotFoundError


class TestPublicMenuService:
    """Test cases for PublicMenuService"""
    
    @pytest.fixture
    def mock_menu_item_service(self):
        """Mock menu item service"""
        return Mock(spec=MenuItemService)
    
    @pytest.fixture
    def mock_restaurant_service(self):
        """Mock restaurant service"""
        return Mock(spec=RestaurantService)
    
    @pytest.fixture
    def public_menu_service(self, mock_menu_item_service, mock_restaurant_service):
        """Public menu service with mocked dependencies"""
        return PublicMenuService(mock_menu_item_service, mock_restaurant_service)
    
    @pytest.fixture
    def sample_restaurant(self):
        """Sample restaurant data"""
        return Restaurant(
            id="restaurant-123",
            name="Mario's Pizza Palace",
            owner_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=None
        )
    
    @pytest.fixture
    def sample_menu_items(self):
        """Sample menu items data"""
        return [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Margherita Pizza",
                description="Classic pizza with tomato sauce, mozzarella, and fresh basil",
                price=Decimal("15.99"),
                category="Pizza",
                image_url="https://example.com/margherita.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-2",
                restaurant_id="restaurant-123",
                name="Caesar Salad",
                description="Fresh romaine lettuce with caesar dressing",
                price=Decimal("8.99"),
                category="Salads",
                image_url="https://example.com/caesar.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            MenuItem(
                id="item-3",
                restaurant_id="restaurant-123",
                name="Pepperoni Pizza",
                description="Pizza with pepperoni and mozzarella",
                price=Decimal("17.99"),
                category="Pizza",
                image_url="https://example.com/pepperoni.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_public_menu_success(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant,
        sample_menu_items
    ):
        """Test successful public menu retrieval"""
        # Setup mocks
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.get_by_restaurant = AsyncMock(return_value=sample_menu_items)
        
        # Call service
        result = await public_menu_service.get_public_menu("restaurant-123")
        
        # Verify result
        assert isinstance(result, PublicMenuResponse)
        assert result.restaurant_id == "restaurant-123"
        assert result.restaurant_name == "Mario's Pizza Palace"
        assert result.total_items == 3
        assert len(result.items) == 3
        assert len(result.categories) == 2
        assert "Pizza" in result.categories
        assert "Salads" in result.categories
        
        # Verify items are converted to public format (no is_available field)
        for item in result.items:
            assert isinstance(item, PublicMenuItemResponse)
            assert hasattr(item, 'id')
            assert hasattr(item, 'name')
            assert hasattr(item, 'price')
            assert hasattr(item, 'category')
            assert not hasattr(item, 'is_available')  # Should not expose internal fields
        
        # Verify service calls
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.get_by_restaurant.assert_called_once_with(
            restaurant_id="restaurant-123",
            include_unavailable=False,
            category=None
        )
    
    @pytest.mark.asyncio
    async def test_get_public_menu_with_category_filter(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant
    ):
        """Test public menu retrieval with category filter"""
        # Setup mocks - only pizza items
        pizza_items = [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Margherita Pizza",
                description="Classic pizza",
                price=Decimal("15.99"),
                category="Pizza",
                image_url="https://example.com/margherita.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
        
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.get_by_restaurant = AsyncMock(return_value=pizza_items)
        
        # Call service with category filter
        result = await public_menu_service.get_public_menu("restaurant-123", "Pizza")
        
        # Verify result
        assert result.total_items == 1
        assert len(result.items) == 1
        assert result.items[0].category == "Pizza"
        assert result.categories == ["Pizza"]
        
        # Verify service was called with category filter
        mock_menu_item_service.get_by_restaurant.assert_called_once_with(
            restaurant_id="restaurant-123",
            include_unavailable=False,
            category="Pizza"
        )
    
    @pytest.mark.asyncio
    async def test_get_public_menu_restaurant_not_found(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service
    ):
        """Test public menu retrieval for non-existent restaurant"""
        # Setup mock to return None (restaurant not found)
        mock_restaurant_service.get_by_id = AsyncMock(return_value=None)
        
        # Call service and expect NotFoundError
        with pytest.raises(NotFoundError, match="Restaurant restaurant-123 not found"):
            await public_menu_service.get_public_menu("restaurant-123")
        
        # Verify restaurant service was called but menu service was not
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.get_by_restaurant.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_public_menu_by_category_success(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant,
        sample_menu_items
    ):
        """Test successful menu retrieval organized by categories"""
        # Setup mocks
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.get_available_menu = AsyncMock(return_value=sample_menu_items)
        
        # Call service
        result = await public_menu_service.get_public_menu_by_category("restaurant-123")
        
        # Verify result structure
        assert isinstance(result, PublicMenuByCategory)
        assert result.restaurant_id == "restaurant-123"
        assert result.restaurant_name == "Mario's Pizza Palace"
        assert result.total_items == 3
        assert len(result.categories) == 2
        
        # Verify categories are sorted
        category_names = [cat.category for cat in result.categories]
        assert category_names == ["Pizza", "Salads"]  # Should be alphabetically sorted
        
        # Verify items are grouped correctly
        pizza_category = next(cat for cat in result.categories if cat.category == "Pizza")
        salads_category = next(cat for cat in result.categories if cat.category == "Salads")
        
        assert len(pizza_category.items) == 2  # Margherita and Pepperoni
        assert len(salads_category.items) == 1  # Caesar Salad
        
        # Verify items within categories are sorted by name
        pizza_names = [item.name for item in pizza_category.items]
        assert pizza_names == ["Margherita Pizza", "Pepperoni Pizza"]  # Alphabetically sorted
        
        # Verify service calls
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.get_available_menu.assert_called_once_with("restaurant-123")
    
    @pytest.mark.asyncio
    async def test_get_menu_categories_success(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant
    ):
        """Test successful retrieval of menu categories"""
        # Setup mocks
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.get_categories_for_restaurant = AsyncMock(
            return_value=["Appetizers", "Pizza", "Salads", "Beverages"]
        )
        
        # Call service
        result = await public_menu_service.get_menu_categories("restaurant-123")
        
        # Verify result
        assert result == ["Appetizers", "Pizza", "Salads", "Beverages"]
        
        # Verify service calls
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.get_categories_for_restaurant.assert_called_once_with("restaurant-123")
    
    @pytest.mark.asyncio
    async def test_search_public_menu_success(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant
    ):
        """Test successful menu search"""
        # Setup mocks
        search_results = [
            MenuItem(
                id="item-1",
                restaurant_id="restaurant-123",
                name="Margherita Pizza",
                description="Classic pizza",
                price=Decimal("15.99"),
                category="Pizza",
                image_url="https://example.com/margherita.jpg",
                is_available=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
        
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.search_menu_items = AsyncMock(return_value=search_results)
        
        # Call service
        result = await public_menu_service.search_public_menu(
            restaurant_id="restaurant-123",
            search_query="pizza",
            category="Pizza",
            limit=10
        )
        
        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], PublicMenuItemResponse)
        assert result[0].name == "Margherita Pizza"
        assert result[0].category == "Pizza"
        
        # Verify service calls
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.search_menu_items.assert_called_once_with(
            restaurant_id="restaurant-123",
            search_query="pizza",
            category="Pizza",
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_convert_to_public_menu_item(self, public_menu_service):
        """Test conversion of internal menu item to public format"""
        # Create internal menu item
        internal_item = MenuItem(
            id="item-1",
            restaurant_id="restaurant-123",
            name="Test Item",
            description="Test description",
            price=Decimal("10.99"),
            category="Test Category",
            image_url="https://example.com/test.jpg",
            is_available=True,  # This should not appear in public format
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        # Convert to public format
        public_item = public_menu_service._convert_to_public_menu_item(internal_item)
        
        # Verify conversion
        assert isinstance(public_item, PublicMenuItemResponse)
        assert public_item.id == "item-1"
        assert public_item.name == "Test Item"
        assert public_item.description == "Test description"
        assert public_item.price == Decimal("10.99")
        assert public_item.category == "Test Category"
        assert public_item.image_url == "https://example.com/test.jpg"
        
        # Verify internal fields are not exposed
        assert not hasattr(public_item, 'is_available')
        assert not hasattr(public_item, 'restaurant_id')
        assert not hasattr(public_item, 'created_at')
        assert not hasattr(public_item, 'updated_at')
    
    @pytest.mark.asyncio
    async def test_empty_menu_handling(
        self, 
        public_menu_service, 
        mock_restaurant_service, 
        mock_menu_item_service,
        sample_restaurant
    ):
        """Test handling of restaurant with no available menu items"""
        # Setup mocks - empty menu
        mock_restaurant_service.get_by_id = AsyncMock(return_value=sample_restaurant)
        mock_menu_item_service.get_by_restaurant = AsyncMock(return_value=[])
        
        # Call service
        result = await public_menu_service.get_public_menu("restaurant-123")
        
        # Verify result
        assert result.restaurant_id == "restaurant-123"
        assert result.restaurant_name == "Mario's Pizza Palace"
        assert result.total_items == 0
        assert len(result.items) == 0
        assert len(result.categories) == 0
        
        # Verify service calls
        mock_restaurant_service.get_by_id.assert_called_once_with("restaurant-123")
        mock_menu_item_service.get_by_restaurant.assert_called_once_with(
            restaurant_id="restaurant-123",
            include_unavailable=False,
            category=None
        )