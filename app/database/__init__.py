"""Database package for the QR Code Ordering System"""

from .supabase_client import supabase_client, SupabaseClient
from .service_factory import (
    DatabaseServiceFactory,
    get_db_services,
    get_restaurant_service,
    get_menu_item_service,
    get_order_service,
    get_customer_service,
    get_authenticated_services,
    get_service_client_services
)
from .base import BaseDatabaseService, DatabaseError, NotFoundError, ValidationError
from .init_db import init_database, verify_database_connection

__all__ = [
    # Client
    "supabase_client",
    "SupabaseClient",
    
    # Service Factory
    "DatabaseServiceFactory",
    "get_db_services",
    "get_restaurant_service",
    "get_menu_item_service", 
    "get_order_service",
    "get_customer_service",
    "get_authenticated_services",
    "get_service_client_services",
    
    # Base Classes and Exceptions
    "BaseDatabaseService",
    "DatabaseError",
    "NotFoundError",
    "ValidationError",
    
    # Utilities
    "init_database",
    "verify_database_connection",
]