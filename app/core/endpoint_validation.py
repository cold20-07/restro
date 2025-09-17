"""
Comprehensive endpoint validation utilities

This module provides validation decorators and utilities specifically
designed for API endpoints with comprehensive error handling.
"""

import inspect
import traceback
from typing import Any, Dict, List, Optional, Callable, Type
from functools import wraps
from fastapi import Request, HTTPException, status
from pydantic import BaseModel

from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ConflictError,
    BusinessLogicError,
    raise_validation_error
)
from app.core.input_validation import InputValidator, input_validator
from app.core.validation import (
    validate_uuid,
    validate_email,
    validate_phone_number,
    validate_price,
    validate_quantity,
    validate_table_number,
    validate_order_items,
    validate_date_range
)
from app.core.error_monitoring import record_error
from app.core.logging_config import get_logger

logger = get_logger("endpoint_validation")


def validate_endpoint_input(
    path_params: Optional[Dict[str, Callable]] = None,
    query_params: Optional[Dict[str, Callable]] = None,
    body_model: Optional[Type[BaseModel]] = None,
    business_rules: Optional[List[Callable]] = None
):
    """
    Comprehensive endpoint validation decorator
    
    Args:
        path_params: Dictionary of path parameter validators
        query_params: Dictionary of query parameter validators  
        body_model: Pydantic model for request body validation
        business_rules: List of business rule validation functions
    
    Example:
        @validate_endpoint_input(
            path_params={"restaurant_id": validate_uuid, "order_id": validate_uuid},
            query_params={"limit": lambda x: validate_quantity(int(x) if x else 10)},
            body_model=OrderCreate,
            business_rules=[validate_restaurant_exists, validate_menu_items_available]
        )
        async def create_order(restaurant_id: str, order_data: OrderCreate, limit: int = 10):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = None
            endpoint_name = func.__name__
            
            try:
                # Find request object in arguments
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                # Get function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Validate path parameters
                if path_params:
                    for param_name, validator in path_params.items():
                        if param_name in bound_args.arguments:
                            param_value = bound_args.arguments[param_name]
                            if param_value is not None:
                                try:
                                    validated_value = validator(param_value, param_name)
                                    bound_args.arguments[param_name] = validated_value
                                except ValidationError:
                                    raise
                                except Exception as e:
                                    raise_validation_error(f"Invalid {param_name}: {str(e)}")
                
                # Validate query parameters
                if query_params:
                    for param_name, validator in query_params.items():
                        if param_name in bound_args.arguments:
                            param_value = bound_args.arguments[param_name]
                            if param_value is not None:
                                try:
                                    validated_value = validator(param_value)
                                    bound_args.arguments[param_name] = validated_value
                                except ValidationError:
                                    raise
                                except Exception as e:
                                    raise_validation_error(f"Invalid {param_name}: {str(e)}")
                
                # Validate request body
                if body_model:
                    for param_name, param_value in bound_args.arguments.items():
                        if isinstance(param_value, body_model):
                            try:
                                validated_model = input_validator.validate_model(param_value)
                                bound_args.arguments[param_name] = validated_model
                            except ValidationError:
                                raise
                            break
                
                # Apply business rules
                if business_rules:
                    for rule in business_rules:
                        try:
                            if inspect.iscoroutinefunction(rule):
                                await rule(*bound_args.args, **bound_args.kwargs)
                            else:
                                rule(*bound_args.args, **bound_args.kwargs)
                        except ValidationError:
                            raise
                        except Exception as e:
                            raise_validation_error(f"Business rule validation failed: {str(e)}")
                
                # Call the original function with validated arguments
                result = await func(*bound_args.args, **bound_args.kwargs)
                
                # Log successful request
                logger.info(
                    f"Endpoint {endpoint_name} completed successfully",
                    extra={
                        "endpoint": endpoint_name,
                        "path_params": {k: v for k, v in bound_args.arguments.items() if k in (path_params or {})},
                        "success": True
                    }
                )
                
                return result
                
            except ValidationError as e:
                logger.warning(
                    f"Validation error in {endpoint_name}: {e.message}",
                    extra={
                        "endpoint": endpoint_name,
                        "error_type": "ValidationError",
                        "field_errors": e.field_errors,
                        "client_ip": request.client.host if request and request.client else None
                    }
                )
                record_error(
                    e, 
                    endpoint=endpoint_name,
                    request_data=dict(bound_args.arguments) if 'bound_args' in locals() else {}
                )
                raise
                
            except (AuthenticationError, AuthorizationError, DatabaseError, NotFoundError, ConflictError, BusinessLogicError) as e:
                logger.error(
                    f"Application error in {endpoint_name}: {str(e)}",
                    extra={
                        "endpoint": endpoint_name,
                        "error_type": type(e).__name__,
                        "client_ip": request.client.host if request and request.client else None
                    }
                )
                record_error(
                    e,
                    endpoint=endpoint_name,
                    request_data=dict(bound_args.arguments) if 'bound_args' in locals() else {}
                )
                raise
                
            except Exception as e:
                logger.error(
                    f"Unexpected error in {endpoint_name}: {str(e)}",
                    extra={
                        "endpoint": endpoint_name,
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                        "client_ip": request.client.host if request and request.client else None
                    }
                )
                record_error(
                    e,
                    endpoint=endpoint_name,
                    request_data=dict(bound_args.arguments) if 'bound_args' in locals() else {},
                    stack_trace=traceback.format_exc()
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for synchronous functions
            request = None
            endpoint_name = func.__name__
            
            try:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Validate path parameters
                if path_params:
                    for param_name, validator in path_params.items():
                        if param_name in bound_args.arguments:
                            param_value = bound_args.arguments[param_name]
                            if param_value is not None:
                                try:
                                    validated_value = validator(param_value, param_name)
                                    bound_args.arguments[param_name] = validated_value
                                except ValidationError:
                                    raise
                                except Exception as e:
                                    raise_validation_error(f"Invalid {param_name}: {str(e)}")
                
                # Validate query parameters
                if query_params:
                    for param_name, validator in query_params.items():
                        if param_name in bound_args.arguments:
                            param_value = bound_args.arguments[param_name]
                            if param_value is not None:
                                try:
                                    validated_value = validator(param_value)
                                    bound_args.arguments[param_name] = validated_value
                                except ValidationError:
                                    raise
                                except Exception as e:
                                    raise_validation_error(f"Invalid {param_name}: {str(e)}")
                
                # Validate request body
                if body_model:
                    for param_name, param_value in bound_args.arguments.items():
                        if isinstance(param_value, body_model):
                            try:
                                validated_model = input_validator.validate_model(param_value)
                                bound_args.arguments[param_name] = validated_model
                            except ValidationError:
                                raise
                            break
                
                # Apply business rules (sync only)
                if business_rules:
                    for rule in business_rules:
                        if not inspect.iscoroutinefunction(rule):
                            try:
                                rule(*bound_args.args, **bound_args.kwargs)
                            except ValidationError:
                                raise
                            except Exception as e:
                                raise_validation_error(f"Business rule validation failed: {str(e)}")
                
                result = func(*bound_args.args, **bound_args.kwargs)
                
                logger.info(
                    f"Endpoint {endpoint_name} completed successfully",
                    extra={
                        "endpoint": endpoint_name,
                        "success": True
                    }
                )
                
                return result
                
            except ValidationError as e:
                logger.warning(
                    f"Validation error in {endpoint_name}: {e.message}",
                    extra={
                        "endpoint": endpoint_name,
                        "error_type": "ValidationError",
                        "field_errors": e.field_errors
                    }
                )
                record_error(e, endpoint=endpoint_name)
                raise
                
            except Exception as e:
                logger.error(
                    f"Unexpected error in {endpoint_name}: {str(e)}",
                    extra={
                        "endpoint": endpoint_name,
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc()
                    }
                )
                record_error(e, endpoint=endpoint_name, stack_trace=traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )
        
        # Return appropriate wrapper based on function type
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Convenience decorators for common validation patterns
def validate_restaurant_endpoint(func: Callable) -> Callable:
    """Decorator for restaurant-related endpoints"""
    return validate_endpoint_input(
        path_params={"restaurant_id": validate_uuid}
    )(func)


def validate_order_endpoint(func: Callable) -> Callable:
    """Decorator for order-related endpoints"""
    return validate_endpoint_input(
        path_params={
            "restaurant_id": validate_uuid,
            "order_id": validate_uuid
        }
    )(func)


def validate_menu_endpoint(func: Callable) -> Callable:
    """Decorator for menu-related endpoints"""
    return validate_endpoint_input(
        path_params={
            "restaurant_id": validate_uuid,
            "menu_item_id": validate_uuid
        }
    )(func)


def validate_pagination_endpoint(func: Callable) -> Callable:
    """Decorator for endpoints with pagination"""
    return validate_endpoint_input(
        query_params={
            "limit": lambda x: validate_quantity(int(x) if x else 10, "limit"),
            "offset": lambda x: validate_quantity(int(x) if x else 0, "offset")
        }
    )(func)


# Business rule validators
async def validate_restaurant_exists(restaurant_service, restaurant_id: str):
    """Validate that a restaurant exists"""
    restaurant = await restaurant_service.get_by_id(restaurant_id)
    if not restaurant:
        raise_validation_error(
            "Restaurant not found",
            {"restaurant_id": [f"Restaurant with ID {restaurant_id} does not exist"]}
        )
    return restaurant


async def validate_menu_item_exists_and_available(menu_service, menu_item_id: str, restaurant_id: str):
    """Validate that a menu item exists, belongs to restaurant, and is available"""
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


async def validate_order_belongs_to_restaurant(order_service, order_id: str, restaurant_id: str):
    """Validate that an order exists and belongs to the restaurant"""
    order = await order_service.get_order_for_restaurant(order_id, restaurant_id)
    if not order:
        raise_validation_error(
            "Order not found",
            {"order_id": [f"Order with ID {order_id} does not exist or does not belong to this restaurant"]}
        )
    return order


def validate_order_status_transition(current_status: str, new_status: str):
    """Validate that an order status transition is valid"""
    from app.models.enums import OrderStatus
    
    # Define valid transitions
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELED],
        OrderStatus.CONFIRMED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELED],
        OrderStatus.IN_PROGRESS: [OrderStatus.READY, OrderStatus.CANCELED],
        OrderStatus.READY: [OrderStatus.COMPLETED],
        OrderStatus.COMPLETED: [],  # No transitions from completed
        OrderStatus.CANCELED: []    # No transitions from canceled
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise_validation_error(
            "Invalid status transition",
            {"order_status": [f"Cannot transition from {current_status} to {new_status}"]}
        )


# Rate limiting validation
def validate_rate_limit(request: Request, max_requests: int = 100, window_minutes: int = 1):
    """Validate rate limiting for endpoints"""
    # This would integrate with the rate limiting middleware
    # For now, it's a placeholder that could be extended
    pass


# Security validation
def validate_request_security(request: Request):
    """Validate request security (CSRF, headers, etc.)"""
    # Check for required security headers
    user_agent = request.headers.get("user-agent", "")
    if not user_agent or len(user_agent.strip()) == 0:
        raise_validation_error(
            "Missing user agent",
            {"user_agent": ["User agent header is required"]}
        )
    
    # Check for suspicious patterns
    suspicious_patterns = ["<script", "javascript:", "data:", "vbscript:"]
    for header_name, header_value in request.headers.items():
        if any(pattern in str(header_value).lower() for pattern in suspicious_patterns):
            raise_validation_error(
                "Suspicious request detected",
                {"security": ["Request contains suspicious content"]}
            )