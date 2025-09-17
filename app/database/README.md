# Database Models and Services

This directory contains the database models, services, and configuration for the QR Code Ordering System.

## Overview

The database layer is built using:
- **Supabase** as the PostgreSQL database with real-time capabilities
- **Pydantic** models for data validation and serialization
- **Row-Level Security (RLS)** for multi-tenant data isolation
- **Service layer pattern** for database operations

## Directory Structure

```
app/database/
├── __init__.py              # Package exports
├── README.md               # This file
├── base.py                 # Base database service class
├── init_db.py              # Database initialization utilities
├── schema.sql              # Complete database schema with RLS policies
├── service_factory.py      # Service factory for dependency injection
└── supabase_client.py      # Supabase client configuration

app/models/
├── __init__.py             # Model exports
├── base.py                 # Base model classes
├── enums.py                # Enum definitions
├── restaurant.py           # Restaurant models
├── menu_item.py            # Menu item models
├── customer.py             # Customer profile models
└── order.py                # Order and order item models

app/services/
├── __init__.py             # Service exports
├── restaurant_service.py   # Restaurant CRUD operations
├── menu_item_service.py    # Menu item CRUD operations
├── customer_service.py     # Customer profile CRUD operations
└── order_service.py        # Order and order item CRUD operations
```

## Database Schema

### Core Tables

1. **restaurants** - Restaurant information and ownership
2. **menu_items** - Menu items belonging to restaurants
3. **customer_profiles** - Customer information per restaurant
4. **orders** - Customer orders with status tracking
5. **order_items** - Individual items within orders

### Key Features

- **Multi-tenancy**: All data is isolated by `restaurant_id` using RLS policies
- **Audit trails**: Automatic `created_at` and `updated_at` timestamps
- **Data integrity**: Foreign key constraints and check constraints
- **Performance**: Optimized indexes for common queries

## Models

### Base Models

All models inherit from base classes that provide:
- Automatic ID generation (UUID)
- Timestamp management
- Pydantic validation
- JSON serialization

### Model Types

Each entity has three model types:
- **Base Model**: Database representation with all fields
- **Create Model**: For creating new records (excludes auto-generated fields)
- **Update Model**: For updating existing records (all fields optional)

### Example Usage

```python
from app.models.restaurant import RestaurantCreate
from decimal import Decimal

# Create a new restaurant
restaurant_data = RestaurantCreate(
    name="Mario's Pizza Palace",
    owner_id="auth_user_id_123"
)

# Create a menu item
from app.models.menu_item import MenuItemCreate

menu_item_data = MenuItemCreate(
    restaurant_id=restaurant.id,
    name="Margherita Pizza",
    description="Classic pizza with tomato sauce and mozzarella",
    price=Decimal("15.99"),
    category="Pizza",
    is_available=True
)
```

## Services

### Service Layer Pattern

Each model has a corresponding service class that provides:
- CRUD operations (Create, Read, Update, Delete)
- Business logic methods
- Database transaction handling
- Error handling and validation

### Base Service Features

All services inherit from `BaseDatabaseService` which provides:
- Standard CRUD methods
- Pagination support
- Filtering capabilities
- Error handling
- Response validation

### Service Usage

```python
from app.database import get_restaurant_service, get_menu_item_service

# Get service instances
restaurant_service = get_restaurant_service()
menu_service = get_menu_item_service()

# Create a restaurant
restaurant = await restaurant_service.create(restaurant_data)

# Get menu items for a restaurant
menu_items = await menu_service.get_by_restaurant(
    restaurant_id=restaurant.id,
    include_unavailable=False
)

# Update menu item availability
await menu_service.toggle_availability(
    item_id=menu_item.id,
    restaurant_id=restaurant.id,
    is_available=False
)
```

## Authentication and Authorization

### Row-Level Security (RLS)

All tables have RLS policies that ensure:
- Restaurant owners can only access their own data
- Public endpoints can read available menu items
- Customers can create orders but not modify existing ones

### Service Client vs Regular Client

- **Regular Client**: Uses anon key, subject to RLS policies
- **Service Client**: Uses service key, bypasses RLS for admin operations
- **Authenticated Client**: Uses user JWT token, applies user-specific RLS

### Usage in API Endpoints

```python
from fastapi import Depends
from app.database import get_authenticated_services

async def create_menu_item(
    menu_item_data: MenuItemCreate,
    services: DatabaseServiceFactory = Depends(get_authenticated_services)
):
    # This will automatically enforce RLS based on the authenticated user
    return await services.menu_item_service.create(menu_item_data)
```

## Database Initialization

### Setup Steps

1. **Configure Environment Variables**:
   ```bash
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   ```

2. **Run Database Schema**:
   Execute the SQL in `schema.sql` in your Supabase dashboard or via CLI

3. **Verify Connection**:
   ```python
   from app.database.init_db import verify_database_connection
   await verify_database_connection()
   ```

### Schema Migration

The `schema.sql` file contains the complete database schema including:
- Table definitions with constraints
- Enum types for order and payment status
- RLS policies for multi-tenant security
- Indexes for performance optimization
- Triggers for automatic timestamp updates

## Error Handling

### Exception Hierarchy

```python
DatabaseError              # Base database exception
├── NotFoundError          # Record not found
├── ValidationError        # Data validation failed
└── AuthorizationError     # Access denied
```

### Error Handling in Services

All service methods handle errors gracefully and provide meaningful error messages:

```python
try:
    restaurant = await restaurant_service.get(restaurant_id)
    if not restaurant:
        raise NotFoundError(f"Restaurant {restaurant_id} not found")
except DatabaseError as e:
    # Handle database-specific errors
    logger.error(f"Database error: {e}")
    raise
```

## Testing

### Model Testing

Models are tested for:
- Validation rules (required fields, data types, constraints)
- Business logic (phone number formatting, price validation)
- Serialization/deserialization

### Service Testing

Services can be tested with:
- Mock Supabase clients for unit tests
- Test database instances for integration tests
- Pytest fixtures for common test data

### Running Tests

```bash
# Run model and service structure tests
python -m pytest tests/test_models_and_services.py -v

# Run with coverage
python -m pytest tests/ --cov=app/models --cov=app/services
```

## Performance Considerations

### Indexing Strategy

The schema includes indexes on:
- Foreign key columns for join performance
- Frequently filtered columns (restaurant_id, is_available, order_status)
- Timestamp columns for date range queries

### Query Optimization

Services use:
- Pagination to limit result sets
- Selective field loading where appropriate
- Efficient filtering at the database level
- Batch operations for multiple records

### Caching Strategy

Consider implementing caching for:
- Menu items (rarely change, frequently accessed)
- Restaurant information
- Customer profiles for repeat customers

## Security Best Practices

### Data Isolation

- All queries automatically filter by restaurant_id through RLS
- No cross-tenant data access possible
- Service layer validates ownership before operations

### Input Validation

- Pydantic models validate all input data
- SQL injection prevention through parameterized queries
- Business rule validation in service layer

### Access Control

- JWT tokens required for authenticated operations
- Service key restricted to admin operations only
- Public endpoints limited to read-only menu access

## Monitoring and Logging

### Database Monitoring

Monitor:
- Query performance and slow queries
- Connection pool usage
- RLS policy effectiveness
- Error rates by operation type

### Logging Strategy

Log:
- All database errors with context
- Performance metrics for slow operations
- Authentication and authorization failures
- Data validation errors

## Future Enhancements

### Potential Improvements

1. **Caching Layer**: Redis for frequently accessed data
2. **Read Replicas**: For analytics and reporting queries
3. **Database Migrations**: Automated schema versioning
4. **Audit Logging**: Track all data changes
5. **Soft Deletes**: Preserve data for compliance
6. **Backup Strategy**: Automated backups and recovery procedures