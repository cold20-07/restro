"""Menu item model definitions"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel


class MenuItemBase(BaseModel):
    """Base menu item model with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Menu item name")
    description: Optional[str] = Field(None, max_length=1000, description="Menu item description")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Menu item price")
    category: str = Field(..., min_length=1, max_length=100, description="Menu item category")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    is_available: bool = Field(True, description="Whether the menu item is available for ordering")
    
    @validator('name', 'category')
    def fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('description')
    def description_cleanup(cls, v):
        return v.strip() if v else v


class MenuItem(BaseDBModel, MenuItemBase):
    """Menu item model for database representation"""
    restaurant_id: str = Field(..., description="ID of the restaurant this menu item belongs to")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                "price": "15.99",
                "category": "Pizza",
                "image_url": "https://example.com/images/margherita.jpg",
                "is_available": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }
        }


class MenuItemCreate(BaseCreateModel, MenuItemBase):
    """Model for creating a new menu item"""
    restaurant_id: str = Field(..., description="ID of the restaurant this menu item belongs to")
    
    class Config:
        schema_extra = {
            "example": {
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                "price": "15.99",
                "category": "Pizza",
                "image_url": "https://example.com/images/margherita.jpg",
                "is_available": True
            }
        }


class MenuItemUpdate(BaseUpdateModel):
    """Model for updating menu item information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Menu item name")
    description: Optional[str] = Field(None, max_length=1000, description="Menu item description")
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Menu item price")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="Menu item category")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    is_available: Optional[bool] = Field(None, description="Whether the menu item is available for ordering")
    
    @validator('name', 'category')
    def fields_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Field cannot be empty')
        return v.strip() if v else v
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('description')
    def description_cleanup(cls, v):
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Margherita Pizza",
                "price": "16.99",
                "is_available": False
            }
        }