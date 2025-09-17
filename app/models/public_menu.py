"""Public menu response models for customer-facing API"""

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional


class PublicMenuItemResponse(BaseModel):
    """Menu item model for public menu display"""
    id: str = Field(..., description="Menu item ID")
    name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: Decimal = Field(..., description="Menu item price")
    category: str = Field(..., description="Menu item category")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                "price": "15.99",
                "category": "Pizza",
                "image_url": "https://example.com/images/margherita.jpg"
            }
        }


class PublicMenuResponse(BaseModel):
    """Complete menu response for public display"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    restaurant_name: str = Field(..., description="Restaurant name")
    categories: List[str] = Field(..., description="Available menu categories")
    items: List[PublicMenuItemResponse] = Field(..., description="Available menu items")
    total_items: int = Field(..., description="Total number of available items")
    
    class Config:
        schema_extra = {
            "example": {
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "restaurant_name": "Mario's Pizza Palace",
                "categories": ["Pizza", "Appetizers", "Beverages"],
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Margherita Pizza",
                        "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                        "price": "15.99",
                        "category": "Pizza",
                        "image_url": "https://example.com/images/margherita.jpg"
                    }
                ],
                "total_items": 1
            }
        }


class MenuCategoryResponse(BaseModel):
    """Menu items grouped by category"""
    category: str = Field(..., description="Category name")
    items: List[PublicMenuItemResponse] = Field(..., description="Items in this category")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "Pizza",
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Margherita Pizza",
                        "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                        "price": "15.99",
                        "category": "Pizza",
                        "image_url": "https://example.com/images/margherita.jpg"
                    }
                ]
            }
        }


class PublicMenuByCategory(BaseModel):
    """Menu response organized by categories"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    restaurant_name: str = Field(..., description="Restaurant name")
    categories: List[MenuCategoryResponse] = Field(..., description="Menu items grouped by category")
    total_items: int = Field(..., description="Total number of available items")
    
    class Config:
        schema_extra = {
            "example": {
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "restaurant_name": "Mario's Pizza Palace",
                "categories": [
                    {
                        "category": "Pizza",
                        "items": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440001",
                                "name": "Margherita Pizza",
                                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                                "price": "15.99",
                                "category": "Pizza",
                                "image_url": "https://example.com/images/margherita.jpg"
                            }
                        ]
                    }
                ],
                "total_items": 1
            }
        }