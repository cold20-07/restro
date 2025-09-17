"""Customer profile model definitions"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel


class CustomerProfileBase(BaseModel):
    """Base customer profile model with common fields"""
    phone_number: str = Field(..., min_length=10, max_length=20, description="Customer phone number")
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    
    @validator('phone_number')
    def phone_number_validation(cls, v):
        # Remove any spaces, dashes, or parentheses
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Customer name cannot be empty')
        return v.strip()


class CustomerProfile(BaseDBModel, CustomerProfileBase):
    """Customer profile model for database representation"""
    restaurant_id: str = Field(..., description="ID of the restaurant this customer profile belongs to")
    last_order_at: Optional[datetime] = Field(None, description="Timestamp of the customer's last order")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "phone_number": "+1234567890",
                "name": "John Doe",
                "last_order_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }
        }


class CustomerProfileCreate(BaseCreateModel, CustomerProfileBase):
    """Model for creating a new customer profile"""
    restaurant_id: str = Field(..., description="ID of the restaurant this customer profile belongs to")
    
    class Config:
        schema_extra = {
            "example": {
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "phone_number": "+1234567890",
                "name": "John Doe"
            }
        }


class CustomerProfileUpdate(BaseUpdateModel):
    """Model for updating customer profile information"""
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, description="Customer phone number")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Customer name")
    last_order_at: Optional[datetime] = Field(None, description="Timestamp of the customer's last order")
    
    @validator('phone_number')
    def phone_number_validation(cls, v):
        if v is not None:
            # Remove any spaces, dashes, or parentheses
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Phone number must be at least 10 digits')
            return cleaned
        return v
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Customer name cannot be empty')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Updated Doe",
                "phone_number": "+1234567891"
            }
        }