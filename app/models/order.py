"""Order and order item model definitions"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import List, Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel
from .enums import OrderStatus, PaymentStatus


class OrderItemBase(BaseModel):
    """Base order item model with common fields"""
    menu_item_id: str = Field(..., description="ID of the menu item")
    quantity: int = Field(..., gt=0, description="Quantity of the menu item")
    unit_price: Decimal = Field(..., gt=0, decimal_places=2, description="Unit price of the menu item")
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('unit_price')
    def unit_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Unit price must be positive')
        return v


class OrderItem(BaseDBModel, OrderItemBase):
    """Order item model for database representation"""
    order_id: str = Field(..., description="ID of the order this item belongs to")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "order_id": "550e8400-e29b-41d4-a716-446655440003",
                "menu_item_id": "550e8400-e29b-41d4-a716-446655440001",
                "quantity": 2,
                "unit_price": "15.99",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None
            }
        }


class OrderItemCreate(BaseCreateModel, OrderItemBase):
    """Model for creating a new order item"""
    
    class Config:
        schema_extra = {
            "example": {
                "menu_item_id": "550e8400-e29b-41d4-a716-446655440001",
                "quantity": 2,
                "unit_price": "15.99"
            }
        }


class OrderBase(BaseModel):
    """Base order model with common fields"""
    table_number: int = Field(..., gt=0, description="Table number for the order")
    customer_name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    customer_phone: str = Field(..., min_length=10, max_length=20, description="Customer phone number")
    
    @validator('table_number')
    def table_number_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Table number must be positive')
        return v
    
    @validator('customer_name')
    def customer_name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Customer name cannot be empty')
        return v.strip()
    
    @validator('customer_phone')
    def customer_phone_validation(cls, v):
        # Remove any spaces, dashes, or parentheses
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned


class Order(BaseDBModel, OrderBase):
    """Order model for database representation"""
    restaurant_id: str = Field(..., description="ID of the restaurant this order belongs to")
    order_number: Optional[str] = Field(None, description="Human-readable order number for customer reference")
    order_status: OrderStatus = Field(OrderStatus.PENDING, description="Current status of the order")
    payment_status: PaymentStatus = Field(PaymentStatus.PENDING, description="Payment status of the order")
    payment_method: Optional[str] = Field("cash", description="Payment method for the order")
    total_price: Decimal = Field(..., gt=0, decimal_places=2, description="Total price of the order")
    estimated_time: Optional[int] = Field(None, description="Estimated preparation time in minutes")
    items: Optional[List[OrderItem]] = Field(None, description="List of order items")
    
    @validator('total_price')
    def total_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Total price must be positive')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "table_number": 5,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "order_status": "pending",
                "payment_status": "pending",
                "total_price": "31.98",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": None,
                "items": []
            }
        }


class OrderCreate(BaseCreateModel, OrderBase):
    """Model for creating a new order"""
    restaurant_id: str = Field(..., description="ID of the restaurant this order belongs to")
    total_price: Decimal = Field(..., gt=0, decimal_places=2, description="Total price of the order")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="List of order items")
    
    @validator('total_price')
    def total_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Total price must be positive')
        return v
    
    @validator('items')
    def items_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
                "table_number": 5,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "total_price": "31.98",
                "items": [
                    {
                        "menu_item_id": "550e8400-e29b-41d4-a716-446655440001",
                        "quantity": 2,
                        "unit_price": "15.99"
                    }
                ]
            }
        }


class OrderUpdate(BaseUpdateModel):
    """Model for updating order information"""
    order_status: Optional[OrderStatus] = Field(None, description="Current status of the order")
    payment_status: Optional[PaymentStatus] = Field(None, description="Payment status of the order")
    estimated_time: Optional[int] = Field(None, description="Estimated preparation time in minutes")
    
    class Config:
        schema_extra = {
            "example": {
                "order_status": "confirmed",
                "payment_status": "paid",
                "estimated_time": 15
            }
        }


class OrderConfirmationResponse(Order):
    """Response model for order confirmation with customer-friendly messaging"""
    confirmation_message: str = Field(..., description="Confirmation message for the customer")
    payment_message: str = Field(..., description="Payment instruction message")
    kitchen_notification_sent: bool = Field(..., description="Indicates order was sent to kitchen")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440003",
                "order_number": "ORD-001",
                "order_status": "pending",
                "total_price": "31.98",
                "estimated_time": 15,
                "table_number": 5,
                "customer_name": "John Doe",
                "confirmation_message": "Your order has been sent to the kitchen and is being prepared!",
                "payment_message": "Payment will be collected by our staff when your order is ready. We accept cash payments.",
                "kitchen_notification_sent": True
            }
        }