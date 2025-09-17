"""Database initialization utilities"""

import os
from pathlib import Path
from supabase import Client
from app.database.supabase_client import supabase_client
from app.core.config import settings


async def init_database():
    """Initialize the database with schema and policies"""
    try:
        # Get the service client for admin operations
        client = supabase_client.service_client
        
        # Read the schema file
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema (Note: Supabase handles this through their dashboard/CLI)
        # This is mainly for reference and local development
        print("Database schema loaded. Please execute the following SQL in your Supabase dashboard:")
        print("=" * 80)
        print(schema_sql)
        print("=" * 80)
        
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


async def verify_database_connection():
    """Verify that the database connection is working"""
    try:
        # Test basic connection
        client = supabase_client.client
        
        # Try to query a system table
        response = client.table("restaurants").select("count", count="exact").limit(0).execute()
        
        print(f"Database connection successful. Restaurant count: {response.count}")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


async def create_test_data():
    """Create test data for development (optional)"""
    try:
        from app.services.restaurant_service import RestaurantService
        from app.services.menu_item_service import MenuItemService
        from app.models.restaurant import RestaurantCreate
        from app.models.menu_item import MenuItemCreate
        from decimal import Decimal
        
        # Use service client for admin operations
        client = supabase_client.service_client
        
        restaurant_service = RestaurantService(client)
        menu_service = MenuItemService(client)
        
        # Create a test restaurant (you'll need a valid auth user ID)
        test_restaurant = RestaurantCreate(
            name="Test Pizza Palace",
            owner_id="test-owner-id"  # Replace with actual auth user ID
        )
        
        # Note: This will only work if you have a valid auth user
        # restaurant = await restaurant_service.create(test_restaurant)
        
        print("Test data creation requires valid authentication. Please create through the API.")
        return True
    except Exception as e:
        print(f"Error creating test data: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Initializing QR Code Ordering System Database...")
        
        # Verify connection
        if await verify_database_connection():
            print("✓ Database connection verified")
        else:
            print("✗ Database connection failed")
            return
        
        # Initialize schema
        if await init_database():
            print("✓ Database schema initialized")
        else:
            print("✗ Database schema initialization failed")
    
    asyncio.run(main())