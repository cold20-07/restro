"""Authentication model definitions"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.core.validation import validate_email, validate_password, validate_string_length, ValidationRules


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr = Field(..., description="User email address")


class User(UserBase):
    """User model for authentication"""
    id: str = Field(..., description="User ID from Supabase Auth")
    restaurant_id: Optional[str] = Field(None, description="Associated restaurant ID")
    role: str = Field(default="owner", description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")
    email_confirmed_at: Optional[datetime] = Field(None, description="Email confirmation timestamp")
    created_at: str = Field(..., description="User creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "auth_user_id_123",
                "email": "owner@restaurant.com",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "owner",
                "is_active": True,
                "email_confirmed_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class UserRegister(UserBase):
    """Model for user registration"""
    password: str = Field(..., min_length=8, description="User password")
    restaurant_name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    
    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(v)
    
    @validator('password')
    def validate_password_strength(cls, v):
        return validate_password(v)
    
    @validator('restaurant_name')
    def validate_restaurant_name_length(cls, v):
        return validate_string_length(
            v, 
            "restaurant_name", 
            min_length=ValidationRules.MIN_NAME_LENGTH,
            max_length=ValidationRules.MAX_NAME_LENGTH
        )
    
    class Config:
        schema_extra = {
            "example": {
                "email": "owner@restaurant.com",
                "password": "SecurePass123",
                "restaurant_name": "Mario's Pizza Palace"
            }
        }


class UserLogin(UserBase):
    """Model for user login"""
    password: str = Field(..., description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "owner@restaurant.com",
                "password": "SecurePass123"
            }
        }


class Token(BaseModel):
    """JWT token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User ID")
    restaurant_id: str = Field(..., description="Restaurant ID associated with the user")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_id": "auth_user_id_123",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str = Field(..., description="User ID")
    restaurant_id: str = Field(..., description="Restaurant ID")
    email: str = Field(..., description="User email")
    exp: datetime = Field(..., description="Token expiration time")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "auth_user_id_123",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "owner@restaurant.com",
                "exp": "2024-01-15T11:00:00Z"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response model"""
    message: str = Field(..., description="Response message")
    user: User = Field(..., description="User information")
    token: Token = Field(..., description="Authentication token")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Authentication successful",
                "user": {
                    "id": "auth_user_id_123",
                    "email": "owner@restaurant.com",
                    "email_confirmed_at": "2024-01-15T10:30:00Z",
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "user_id": "auth_user_id_123",
                    "restaurant_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            }
        }