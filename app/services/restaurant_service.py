"""Restaurant database service"""

from typing import Optional, List
from supabase import Client
from app.database.base import BaseDatabaseService, DatabaseError, NotFoundError
from app.models.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate


class RestaurantService(BaseDatabaseService[Restaurant, RestaurantCreate, RestaurantUpdate]):
    """Service for restaurant database operations"""
    
    def __init__(self, client: Optional[Client] = None):
        super().__init__(Restaurant, "restaurants", client)
    
    async def get_by_owner_id(self, owner_id: str) -> Optional[Restaurant]:
        """Get restaurant by owner ID"""
        try:
            response = self.client.table(self.table_name).select("*").eq("owner_id", owner_id).execute()
            result = self._handle_response(response)
            
            if not result:
                return None
            
            return self.model(**result[0])
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get restaurant by owner_id: {str(e)}")
    
    async def create_with_owner(self, restaurant_data: RestaurantCreate) -> Restaurant:
        """Create a restaurant and ensure owner_id is set"""
        try:
            # Check if owner already has a restaurant
            existing = await self.get_by_owner_id(restaurant_data.owner_id)
            if existing:
                raise DatabaseError("Owner already has a restaurant")
            
            return await self.create(restaurant_data)
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to create restaurant: {str(e)}")
    
    async def get_restaurant_for_owner(self, owner_id: str) -> Restaurant:
        """Get restaurant for owner, raise NotFoundError if not found"""
        restaurant = await self.get_by_owner_id(owner_id)
        if not restaurant:
            raise NotFoundError(f"No restaurant found for owner {owner_id}")
        return restaurant
    
    async def update_restaurant_for_owner(
        self, 
        owner_id: str, 
        restaurant_update: RestaurantUpdate
    ) -> Restaurant:
        """Update restaurant for a specific owner"""
        restaurant = await self.get_restaurant_for_owner(owner_id)
        updated_restaurant = await self.update(restaurant.id, restaurant_update)
        
        if not updated_restaurant:
            raise NotFoundError(f"Restaurant not found after update")
        
        return updated_restaurant
    
    async def delete_restaurant_for_owner(self, owner_id: str) -> bool:
        """Delete restaurant for a specific owner"""
        restaurant = await self.get_restaurant_for_owner(owner_id)
        return await self.delete(restaurant.id)
    
    async def search_restaurants(self, name_query: str, limit: int = 10) -> List[Restaurant]:
        """Search restaurants by name (for admin purposes)"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .ilike("name", f"%{name_query}%")
                .limit(limit)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to search restaurants: {str(e)}")