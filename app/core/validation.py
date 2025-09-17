"""
Enhanced validation utilities for the QR Code Ordering System

This module provides comprehensive validation functions and decorators
for input validation across all API endpoints and business logic.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from functools import wraps
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError, raise_validation_error


# Common validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?1?[0-9]{10,15}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
ORDER_NUMBER_PATTERN = re.compile(r'^ORD-\d{12}-[A-Z0-9]{4}$')


class ValidationRules:
    """Common validation rules and constraints"""
    
    # String length constraints
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    MIN_DESCRIPTION_LENGTH = 0
    MAX_DESCRIPTION_LENGTH = 500
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Numeric constraints
    MIN_PRICE = Decimal('0.01')
    MAX_PRICE = Decimal('999.99')
    MIN_QUANTITY = 1
    MAX_QUANTITY = 99
    MIN_TABLE_NUMBER = 1
    MAX_TABLE_NUMBER = 999
    
    # Business logic constraints
    MAX_ORDER_ITEMS = 50
    MAX_MENU_ITEMS_PER_RESTAURANT = 1000
    MIN_ESTIMATED_TIME = 5
    MAX_ESTIMATED_TIME = 120


def validate_email(email: str) -> str:
    """Validate email format"""
    if not email or not isinstance(email, str):
        raise_validation_error("Email is required", {"email": ["Email is required"]})
    
    email = email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise_validation_error("Invalid email format", {"email": ["Invalid email format"]})
    
    return email


def validate_phone_number(phone: str) -> str:
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        raise_validation_error("Phone number is required", {"phone": ["Phone number is required"]})
    
    # Remove common formatting characters
    cleaned_phone = re.sub(r'[^\d+]', '', phone.strip())
    
    if not PHONE_PATTERN.match(cleaned_phone):
        raise_validation_error(
            "Invalid phone number format", 
            {"phone": ["Phone number must be 10-15 digits, optionally starting with +"]}
        )
    
    return cleaned_phone


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate UUID format"""
    if not value or not isinstance(value, str):
        raise_validation_error(f"{field_name} is required", {field_name: [f"{field_name} is required"]})
    
    value = value.strip()
    if not UUID_PATTERN.match(value):
        try:
            # Try to parse as UUID to get better error message
            uuid.UUID(value)
        except ValueError:
            raise_validation_error(
                f"Invalid {field_name} format", 
                {field_name: [f"{field_name} must be a valid UUID"]}
            )
    
    return value


def validate_price(price: Union[str, int, float, Decimal], field_name: str = "price") -> Decimal:
    """Validate price value"""
    if price is None:
        raise_validation_error(f"{field_name} is required", {field_name: [f"{field_name} is required"]})
    
    try:
        decimal_price = Decimal(str(price))
    except (InvalidOperation, ValueError):
        raise_validation_error(
            f"Invalid {field_name} format", 
            {field_name: [f"{field_name} must be a valid decimal number"]}
        )
    
    if decimal_price < ValidationRules.MIN_PRICE:
        raise_validation_error(
            f"{field_name} too low", 
            {field_name: [f"{field_name} must be at least ${ValidationRules.MIN_PRICE}"]}
        )
    
    if decimal_price > ValidationRules.MAX_PRICE:
        raise_validation_error(
            f"{field_name} too high", 
            {field_name: [f"{field_name} cannot exceed ${ValidationRules.MAX_PRICE}"]}
        )
    
    # Ensure only 2 decimal places
    if decimal_price.as_tuple().exponent < -2:
        raise_validation_error(
            f"Invalid {field_name} precision", 
            {field_name: [f"{field_name} can have at most 2 decimal places"]}
        )
    
    return decimal_price


def validate_quantity(quantity: Union[str, int], field_name: str = "quantity") -> int:
    """Validate quantity value"""
    if quantity is None:
        raise_validation_error(f"{field_name} is required", {field_name: [f"{field_name} is required"]})
    
    try:
        int_quantity = int(quantity)
    except (ValueError, TypeError):
        raise_validation_error(
            f"Invalid {field_name} format", 
            {field_name: [f"{field_name} must be a valid integer"]}
        )
    
    if int_quantity < ValidationRules.MIN_QUANTITY:
        raise_validation_error(
            f"{field_name} too low", 
            {field_name: [f"{field_name} must be at least {ValidationRules.MIN_QUANTITY}"]}
        )
    
    if int_quantity > ValidationRules.MAX_QUANTITY:
        raise_validation_error(
            f"{field_name} too high", 
            {field_name: [f"{field_name} cannot exceed {ValidationRules.MAX_QUANTITY}"]}
        )
    
    return int_quantity


def validate_table_number(table_number: Union[str, int]) -> int:
    """Validate table number"""
    if table_number is None:
        raise_validation_error("Table number is required", {"table_number": ["Table number is required"]})
    
    try:
        int_table = int(table_number)
    except (ValueError, TypeError):
        raise_validation_error(
            "Invalid table number format", 
            {"table_number": ["Table number must be a valid integer"]}
        )
    
    if int_table < ValidationRules.MIN_TABLE_NUMBER:
        raise_validation_error(
            "Table number too low", 
            {"table_number": [f"Table number must be at least {ValidationRules.MIN_TABLE_NUMBER}"]}
        )
    
    if int_table > ValidationRules.MAX_TABLE_NUMBER:
        raise_validation_error(
            "Table number too high", 
            {"table_number": [f"Table number cannot exceed {ValidationRules.MAX_TABLE_NUMBER}"]}
        )
    
    return int_table


def validate_string_length(
    value: str, 
    field_name: str,
    min_length: int = 0,
    max_length: int = 255,
    required: bool = True
) -> str:
    """Validate string length constraints"""
    if not value or not isinstance(value, str):
        if required:
            raise_validation_error(f"{field_name} is required", {field_name: [f"{field_name} is required"]})
        return ""
    
    value = value.strip()
    
    if len(value) < min_length:
        raise_validation_error(
            f"{field_name} too short", 
            {field_name: [f"{field_name} must be at least {min_length} characters"]}
        )
    
    if len(value) > max_length:
        raise_validation_error(
            f"{field_name} too long", 
            {field_name: [f"{field_name} cannot exceed {max_length} characters"]}
        )
    
    return value


def validate_password(password: str) -> str:
    """Validate password strength"""
    if not password or not isinstance(password, str):
        raise_validation_error("Password is required", {"password": ["Password is required"]})
    
    if len(password) < ValidationRules.MIN_PASSWORD_LENGTH:
        raise_validation_error(
            "Password too short", 
            {"password": [f"Password must be at least {ValidationRules.MIN_PASSWORD_LENGTH} characters"]}
        )
    
    if len(password) > ValidationRules.MAX_PASSWORD_LENGTH:
        raise_validation_error(
            "Password too long", 
            {"password": [f"Password cannot exceed {ValidationRules.MAX_PASSWORD_LENGTH} characters"]}
        )
    
    # Check for basic password requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    errors = []
    if not has_upper:
        errors.append("Password must contain at least one uppercase letter")
    if not has_lower:
        errors.append("Password must contain at least one lowercase letter")
    if not has_digit:
        errors.append("Password must contain at least one digit")
    
    if errors:
        raise_validation_error("Password requirements not met", {"password": errors})
    
    return password


def validate_order_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate order items list"""
    if not items or not isinstance(items, list):
        raise_validation_error("Order items are required", {"items": ["At least one item is required"]})
    
    if len(items) > ValidationRules.MAX_ORDER_ITEMS:
        raise_validation_error(
            "Too many items", 
            {"items": [f"Cannot order more than {ValidationRules.MAX_ORDER_ITEMS} items at once"]}
        )
    
    validated_items = []
    field_errors = {}
    
    for i, item in enumerate(items):
        item_errors = []
        
        # Validate menu_item_id
        try:
            validate_uuid(item.get("menu_item_id", ""), "menu_item_id")
        except ValidationError as e:
            item_errors.extend(e.field_errors.get("menu_item_id", []))
        
        # Validate quantity
        try:
            validated_quantity = validate_quantity(item.get("quantity", 0))
            item["quantity"] = validated_quantity
        except ValidationError as e:
            item_errors.extend(e.field_errors.get("quantity", []))
        
        if item_errors:
            field_errors[f"items.{i}"] = item_errors
        else:
            validated_items.append(item)
    
    if field_errors:
        raise_validation_error("Invalid order items", field_errors)
    
    return validated_items


def validate_date_range(
    start_date: Optional[Union[str, datetime, date]],
    end_date: Optional[Union[str, datetime, date]]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Validate date range for analytics queries"""
    validated_start = None
    validated_end = None
    field_errors = {}
    
    # Validate start_date
    if start_date:
        try:
            if isinstance(start_date, str):
                validated_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif isinstance(start_date, date):
                validated_start = datetime.combine(start_date, datetime.min.time())
            elif isinstance(start_date, datetime):
                validated_start = start_date
        except ValueError:
            field_errors["start_date"] = ["Invalid start date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"]
    
    # Validate end_date
    if end_date:
        try:
            if isinstance(end_date, str):
                validated_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            elif isinstance(end_date, date):
                validated_end = datetime.combine(end_date, datetime.max.time())
            elif isinstance(end_date, datetime):
                validated_end = end_date
        except ValueError:
            field_errors["end_date"] = ["Invalid end date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"]
    
    # Validate date range logic
    if validated_start and validated_end:
        if validated_start >= validated_end:
            field_errors["date_range"] = ["Start date must be before end date"]
        
        # Check for reasonable date range (not more than 1 year)
        if (validated_end - validated_start).days > 365:
            field_errors["date_range"] = ["Date range cannot exceed 1 year"]
    
    if field_errors:
        raise_validation_error("Invalid date range", field_errors)
    
    return validated_start, validated_end


# Validation decorators
def validate_request_data(validation_func: Callable):
    """Decorator to validate request data using a custom validation function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request data in arguments
            for arg in args:
                if isinstance(arg, BaseModel):
                    try:
                        validation_func(arg)
                    except ValidationError:
                        raise
                    except Exception as e:
                        raise_validation_error(f"Validation failed: {str(e)}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_business_rules(rules: List[Callable]):
    """Decorator to validate business rules"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for rule in rules:
                try:
                    await rule(*args, **kwargs) if callable(rule) else rule(*args, **kwargs)
                except ValidationError:
                    raise
                except Exception as e:
                    raise_validation_error(f"Business rule validation failed: {str(e)}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Common validation functions for business logic
async def validate_restaurant_exists(restaurant_service, restaurant_id: str):
    """Validate that a restaurant exists"""
    restaurant = await restaurant_service.get_by_id(restaurant_id)
    if not restaurant:
        raise_validation_error(
            "Restaurant not found", 
            {"restaurant_id": [f"Restaurant with ID {restaurant_id} does not exist"]}
        )
    return restaurant


async def validate_menu_item_exists(menu_service, menu_item_id: str, restaurant_id: str):
    """Validate that a menu item exists and belongs to the restaurant"""
    menu_item = await menu_service.get_by_id(menu_item_id)
    if not menu_item:
        raise_validation_error(
            "Menu item not found", 
            {"menu_item_id": [f"Menu item with ID {menu_item_id} does not exist"]}
        )
    
    if menu_item.restaurant_id != restaurant_id:
        raise_validation_error(
            "Menu item not found", 
            {"menu_item_id": ["Menu item does not belong to this restaurant"]}
        )
    
    if not menu_item.is_available:
        raise_validation_error(
            "Menu item unavailable", 
            {"menu_item_id": ["This menu item is currently unavailable"]}
        )
    
    return menu_item


async def validate_order_exists(order_service, order_id: str, restaurant_id: str):
    """Validate that an order exists and belongs to the restaurant"""
    order = await order_service.get_order_for_restaurant(order_id, restaurant_id)
    if not order:
        raise_validation_error(
            "Order not found", 
            {"order_id": [f"Order with ID {order_id} does not exist or does not belong to this restaurant"]}
        )
    return order


# Utility function to convert Pydantic validation errors
def convert_pydantic_errors(exc: PydanticValidationError) -> Dict[str, List[str]]:
    """Convert Pydantic validation errors to our format"""
    field_errors = {}
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        if field_path not in field_errors:
            field_errors[field_path] = []
        field_errors[field_path].append(error["msg"])
    return field_errors