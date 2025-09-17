"""Restaurant model definitions"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel


class RestaurantBase(BaseModel):
    """Base restaurant model with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Restaurant name cannot be empty')
        return v.strip()


class Restaurant(BaseDBModel, RestaurantBase):
    """Restaurant model for database representation"""
    owner_id: str = Field(..., description="ID of the restaurant owner")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Mario's Pizza Palace",
                "owner_id": "auth_user_id_123",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }
        }


class RestaurantCreate(BaseCreateModel, RestaurantBase):
    """Model for creating a new restaurant"""
    owner_id: str = Field(..., description="ID of the restaurant owner")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Mario's Pizza Palace",
                "owner_id": "auth_user_id_123"
            }
        }


class RestaurantUpdate(BaseUpdateModel):
    """Model for updating restaurant information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Restaurant name")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Restaurant name cannot be empty')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Mario's Updated Pizza Palace"
            }
        }