"""Database service factory for dependency injection"""

from typing import Optional, TYPE_CHECKING
from supabase import Client
from app.database.supabase_client import supabase_client

if TYPE_CHECKING:
    from app.services.restaurant_service import RestaurantService
    from app.services.menu_item_service import MenuItemService
    from app.services.order_service import OrderService
    from app.services.customer_service import CustomerService
    from app.services.analytics_service import AnalyticsService


class DatabaseServiceFactory:
    """Factory class for creating database service instances"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase_client.client
        self._restaurant_service = None
        self._menu_item_service = None
        self._order_service = None
        self._customer_service = None
        self._analytics_service = None
    
    @property
    def restaurant_service(self):
        """Get restaurant service instance"""
        if self._restaurant_service is None:
            from app.services.restaurant_service import RestaurantService
            self._restaurant_service = RestaurantService(self.client)
        return self._restaurant_service
    
    @property
    def menu_item_service(self):
        """Get menu item service instance"""
        if self._menu_item_service is None:
            from app.services.menu_item_service import MenuItemService
            self._menu_item_service = MenuItemService(self.client)
        return self._menu_item_service
    
    @property
    def order_service(self):
        """Get order service instance"""
        if self._order_service is None:
            from app.services.order_service import OrderService
            self._order_service = OrderService(self.client)
        return self._order_service
    
    @property
    def customer_service(self):
        """Get customer service instance"""
        if self._customer_service is None:
            from app.services.customer_service import CustomerService
            self._customer_service = CustomerService(self.client)
        return self._customer_service
    
    @property
    def analytics_service(self):
        """Get analytics service instance"""
        if self._analytics_service is None:
            from app.services.analytics_service import AnalyticsService
            self._analytics_service = AnalyticsService(self.client)
        return self._analytics_service
    
    def get_authenticated_services(self, access_token: str) -> 'DatabaseServiceFactory':
        """Get service factory with authenticated client"""
        authenticated_client = supabase_client.get_authenticated_client(access_token)
        return DatabaseServiceFactory(authenticated_client)
    
    def get_service_client_services(self) -> 'DatabaseServiceFactory':
        """Get service factory with service client (admin privileges)"""
        return DatabaseServiceFactory(supabase_client.service_client)


# Global service factory instance (lazy initialization)
db_services = None


def get_db_services() -> DatabaseServiceFactory:
    """Get or create the global database service factory"""
    global db_services
    if db_services is None:
        db_services = DatabaseServiceFactory()
    return db_services


# Dependency injection functions for FastAPI
def get_restaurant_service():
    """Dependency injection for restaurant service"""
    return get_db_services().restaurant_service


def get_menu_item_service():
    """Dependency injection for menu item service"""
    return get_db_services().menu_item_service


def get_order_service():
    """Dependency injection for order service"""
    return get_db_services().order_service


def get_customer_service():
    """Dependency injection for customer service"""
    return get_db_services().customer_service


def get_analytics_service():
    """Dependency injection for analytics service"""
    return get_db_services().analytics_service


def get_authenticated_services(access_token: str) -> DatabaseServiceFactory:
    """Get authenticated service factory"""
    return get_db_services().get_authenticated_services(access_token)


def get_service_client_services() -> DatabaseServiceFactory:
    """Get service client factory (admin)"""
    return get_db_services().get_service_client_services()