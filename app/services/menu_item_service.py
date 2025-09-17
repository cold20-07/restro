"""Menu item database service"""

from typing import Optional, List, Dict, Any
from supabase import Client
from app.database.base import BaseDatabaseService, DatabaseError, NotFoundError
from app.models.menu_item import MenuItem, MenuItemCreate, MenuItemUpdate


class MenuItemService(BaseDatabaseService[MenuItem, MenuItemCreate, MenuItemUpdate]):
    """Service for menu item database operations"""
    
    def __init__(self, client: Optional[Client] = None):
        super().__init__(MenuItem, "menu_items", client)
    
    async def get_by_restaurant(
        self, 
        restaurant_id: str, 
        include_unavailable: bool = False,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MenuItem]:
        """Get menu items for a specific restaurant"""
        try:
            query = self.client.table(self.table_name).select("*").eq("restaurant_id", restaurant_id)
            
            # Filter by availability
            if not include_unavailable:
                query = query.eq("is_available", True)
            
            # Filter by category
            if category:
                query = query.eq("category", category)
            
            # Apply pagination
            query = query.range(skip, skip + limit - 1).order("category", desc=False).order("name", desc=False)
            
            response = query.execute()
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get menu items for restaurant: {str(e)}")
    
    async def get_available_menu(self, restaurant_id: str) -> List[MenuItem]:
        """Get only available menu items for public menu display"""
        return await self.get_by_restaurant(restaurant_id, include_unavailable=False)
    
    async def get_categories_for_restaurant(self, restaurant_id: str) -> List[str]:
        """Get unique categories for a restaurant's menu"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("category")
                .eq("restaurant_id", restaurant_id)
                .eq("is_available", True)
                .execute()
            )
            result = self._handle_response(response)
            
            # Extract unique categories
            categories = list(set(item["category"] for item in result))
            return sorted(categories)
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get categories for restaurant: {str(e)}")
    
    async def create_menu_item(self, menu_item_data: MenuItemCreate) -> MenuItem:
        """Create a new menu item"""
        return await self.create(menu_item_data)
    
    async def get_menu_item_for_restaurant(
        self, 
        item_id: str, 
        restaurant_id: str
    ) -> Optional[MenuItem]:
        """Get a specific menu item that belongs to a restaurant"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", item_id)
                .eq("restaurant_id", restaurant_id)
                .execute()
            )
            result = self._handle_response(response)
            
            if not result:
                return None
            
            return self.model(**result[0])
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get menu item for restaurant: {str(e)}")
    
    async def update_menu_item_for_restaurant(
        self,
        item_id: str,
        restaurant_id: str,
        menu_item_update: MenuItemUpdate
    ) -> MenuItem:
        """Update a menu item that belongs to a specific restaurant"""
        # First verify the item belongs to the restaurant
        existing_item = await self.get_menu_item_for_restaurant(item_id, restaurant_id)
        if not existing_item:
            raise NotFoundError(f"Menu item {item_id} not found for restaurant {restaurant_id}")
        
        updated_item = await self.update(item_id, menu_item_update)
        if not updated_item:
            raise NotFoundError(f"Menu item not found after update")
        
        return updated_item
    
    async def delete_menu_item_for_restaurant(
        self,
        item_id: str,
        restaurant_id: str
    ) -> bool:
        """Delete a menu item that belongs to a specific restaurant"""
        # First verify the item belongs to the restaurant
        existing_item = await self.get_menu_item_for_restaurant(item_id, restaurant_id)
        if not existing_item:
            raise NotFoundError(f"Menu item {item_id} not found for restaurant {restaurant_id}")
        
        return await self.delete(item_id)
    
    async def toggle_availability(
        self,
        item_id: str,
        restaurant_id: str,
        is_available: bool
    ) -> MenuItem:
        """Toggle menu item availability"""
        update_data = MenuItemUpdate(is_available=is_available)
        return await self.update_menu_item_for_restaurant(item_id, restaurant_id, update_data)
    
    async def get_menu_items_by_ids(
        self, 
        item_ids: List[str], 
        restaurant_id: str
    ) -> List[MenuItem]:
        """Get multiple menu items by their IDs for a specific restaurant"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .in_("id", item_ids)
                .eq("restaurant_id", restaurant_id)
                .eq("is_available", True)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get menu items by IDs: {str(e)}")
    
    async def search_menu_items(
        self,
        restaurant_id: str,
        search_query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[MenuItem]:
        """Search menu items by name or description"""
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .eq("is_available", True)
            )
            
            # Add text search (name or description)
            query = query.or_(f"name.ilike.%{search_query}%,description.ilike.%{search_query}%")
            
            # Filter by category if provided
            if category:
                query = query.eq("category", category)
            
            query = query.limit(limit).order("name")
            
            response = query.execute()
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to search menu items: {str(e)}")