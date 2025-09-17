"""Public menu service for customer-facing menu operations"""

from typing import List, Optional, Dict
from collections import defaultdict
from app.services.menu_item_service import MenuItemService
from app.services.restaurant_service import RestaurantService
from app.models.public_menu import (
    PublicMenuResponse, 
    PublicMenuItemResponse, 
    PublicMenuByCategory,
    MenuCategoryResponse
)
from app.database.base import NotFoundError


class PublicMenuService:
    """Service for public menu operations"""
    
    def __init__(self, menu_item_service: MenuItemService, restaurant_service: RestaurantService):
        self.menu_item_service = menu_item_service
        self.restaurant_service = restaurant_service
    
    def _convert_to_public_menu_item(self, menu_item) -> PublicMenuItemResponse:
        """Convert internal menu item to public response format"""
        return PublicMenuItemResponse(
            id=menu_item.id,
            name=menu_item.name,
            description=menu_item.description,
            price=menu_item.price,
            category=menu_item.category,
            image_url=menu_item.image_url
        )
    
    async def get_public_menu(
        self, 
        restaurant_id: str, 
        category: Optional[str] = None
    ) -> PublicMenuResponse:
        """Get public menu for a restaurant with only available items"""
        # Verify restaurant exists
        restaurant = await self.restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundError(f"Restaurant {restaurant_id} not found")
        
        # Get available menu items
        menu_items = await self.menu_item_service.get_by_restaurant(
            restaurant_id=restaurant_id,
            include_unavailable=False,  # Only available items for public menu
            category=category
        )
        
        # Convert to public format
        public_items = [self._convert_to_public_menu_item(item) for item in menu_items]
        
        # Get unique categories from available items
        categories = list(set(item.category for item in public_items))
        categories.sort()
        
        return PublicMenuResponse(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant.name,
            categories=categories,
            items=public_items,
            total_items=len(public_items)
        )
    
    async def get_public_menu_by_category(self, restaurant_id: str) -> PublicMenuByCategory:
        """Get public menu organized by categories"""
        # Verify restaurant exists
        restaurant = await self.restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundError(f"Restaurant {restaurant_id} not found")
        
        # Get available menu items
        menu_items = await self.menu_item_service.get_available_menu(restaurant_id)
        
        # Convert to public format
        public_items = [self._convert_to_public_menu_item(item) for item in menu_items]
        
        # Group by category
        items_by_category: Dict[str, List[PublicMenuItemResponse]] = defaultdict(list)
        for item in public_items:
            items_by_category[item.category].append(item)
        
        # Create category responses
        categories = []
        for category_name in sorted(items_by_category.keys()):
            category_items = items_by_category[category_name]
            # Sort items within category by name
            category_items.sort(key=lambda x: x.name)
            categories.append(MenuCategoryResponse(
                category=category_name,
                items=category_items
            ))
        
        return PublicMenuByCategory(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant.name,
            categories=categories,
            total_items=len(public_items)
        )
    
    async def get_menu_categories(self, restaurant_id: str) -> List[str]:
        """Get available categories for a restaurant's public menu"""
        # Verify restaurant exists
        restaurant = await self.restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundError(f"Restaurant {restaurant_id} not found")
        
        return await self.menu_item_service.get_categories_for_restaurant(restaurant_id)
    
    async def search_public_menu(
        self, 
        restaurant_id: str, 
        search_query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[PublicMenuItemResponse]:
        """Search available menu items for public display"""
        # Verify restaurant exists
        restaurant = await self.restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundError(f"Restaurant {restaurant_id} not found")
        
        # Search menu items
        menu_items = await self.menu_item_service.search_menu_items(
            restaurant_id=restaurant_id,
            search_query=search_query,
            category=category,
            limit=limit
        )
        
        # Convert to public format
        return [self._convert_to_public_menu_item(item) for item in menu_items]