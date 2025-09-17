"""Customer profile database service"""

from typing import Optional, List
from datetime import datetime
from supabase import Client
from app.database.base import BaseDatabaseService, DatabaseError, NotFoundError
from app.models.customer import CustomerProfile, CustomerProfileCreate, CustomerProfileUpdate


class CustomerService(BaseDatabaseService[CustomerProfile, CustomerProfileCreate, CustomerProfileUpdate]):
    """Service for customer profile database operations"""
    
    def __init__(self, client: Optional[Client] = None):
        super().__init__(CustomerProfile, "customer_profiles", client)
    
    async def get_by_phone_and_restaurant(
        self, 
        phone_number: str, 
        restaurant_id: str
    ) -> Optional[CustomerProfile]:
        """Get customer profile by phone number and restaurant"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("phone_number", phone_number)
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
            raise DatabaseError(f"Failed to get customer by phone and restaurant: {str(e)}")
    
    async def create_or_update_customer(
        self,
        restaurant_id: str,
        phone_number: str,
        name: str
    ) -> CustomerProfile:
        """Create a new customer profile or update existing one"""
        try:
            # Check if customer already exists
            existing_customer = await self.get_by_phone_and_restaurant(phone_number, restaurant_id)
            
            if existing_customer:
                # Update existing customer
                update_data = CustomerProfileUpdate(name=name)
                updated_customer = await self.update(existing_customer.id, update_data)
                if not updated_customer:
                    raise DatabaseError("Failed to update existing customer")
                return updated_customer
            else:
                # Create new customer
                create_data = CustomerProfileCreate(
                    restaurant_id=restaurant_id,
                    phone_number=phone_number,
                    name=name
                )
                return await self.create(create_data)
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to create or update customer: {str(e)}")
    
    async def update_last_order_time(
        self,
        customer_id: str,
        last_order_at: datetime
    ) -> Optional[CustomerProfile]:
        """Update the last order timestamp for a customer"""
        try:
            update_data = CustomerProfileUpdate(last_order_at=last_order_at)
            return await self.update(customer_id, update_data)
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to update customer last order time: {str(e)}")
    
    async def get_customers_for_restaurant(
        self,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "last_order_at"
    ) -> List[CustomerProfile]:
        """Get all customers for a specific restaurant"""
        try:
            filters = {"restaurant_id": restaurant_id}
            return await self.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by=f"{order_by}.desc.nullslast"
            )
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get customers for restaurant: {str(e)}")
    
    async def get_recent_customers(
        self,
        restaurant_id: str,
        limit: int = 10
    ) -> List[CustomerProfile]:
        """Get recently active customers for a restaurant"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .not_.is_("last_order_at", "null")
                .order("last_order_at", desc=True)
                .limit(limit)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get recent customers: {str(e)}")
    
    async def search_customers(
        self,
        restaurant_id: str,
        search_query: str,
        limit: int = 20
    ) -> List[CustomerProfile]:
        """Search customers by name or phone number"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .or_(f"name.ilike.%{search_query}%,phone_number.ilike.%{search_query}%")
                .order("name")
                .limit(limit)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to search customers: {str(e)}")
    
    async def get_customer_stats_for_restaurant(self, restaurant_id: str) -> dict:
        """Get customer statistics for a restaurant"""
        try:
            # Total customers
            total_customers = await self.count({"restaurant_id": restaurant_id})
            
            # Customers with orders (have last_order_at set)
            response = (
                self.client.table(self.table_name)
                .select("id", count="exact")
                .eq("restaurant_id", restaurant_id)
                .not_.is_("last_order_at", "null")
                .execute()
            )
            active_customers = response.count or 0
            
            return {
                "total_customers": total_customers,
                "active_customers": active_customers,
                "new_customers": total_customers - active_customers
            }
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get customer stats: {str(e)}")