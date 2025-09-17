"""
Comprehensive input validation decorators and utilities

This module provides decorators and utilities for validating input data
across all API endpoints with consistent error handling.
"""

import inspect
from typing import Any, Dict, List, Optional, Callable, Type, get_type_hints
from functools import wraps
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError, raise_validation_error
from app.core.validation import (
    validate_email,
    validate_phone_number,
    validate_uuid,
    validate_price,
    validate_quantity,
    validate_table_number,
    validate_string_length,
    validate_password,
    validate_order_items,
    validate_date_range,
    convert_pydantic_errors
)


class InputValidator:
    """Comprehensive input validator with configurable rules"""
    
    def __init__(self):
        self.field_validators = {
            'email': lambda value, field_name='email': validate_email(value),
            'phone': lambda value, field_name='phone': validate_phone_number(value),
            'phone_number': lambda value, field_name='phone_number': validate_phone_number(value),
            'uuid': validate_uuid,
            'id': validate_uuid,
            'restaurant_id': validate_uuid,
            'menu_item_id': validate_uuid,
            'order_id': validate_uuid,
            'customer_id': validate_uuid,
            'price': lambda value, field_name='price': validate_price(value, field_name),
            'quantity': lambda value, field_name='quantity': validate_quantity(value, field_name),
            'table_number': lambda value, field_name='table_number': validate_table_number(value),
            'password': lambda value, field_name='password': validate_password(value),
        }
        
        self.string_field_rules = {
            'name': {'min_length': 2, 'max_length': 100},
            'restaurant_name': {'min_length': 2, 'max_length': 100},
            'customer_name': {'min_length': 2, 'max_length': 100},
            'description': {'min_length': 0, 'max_length': 500},
            'category': {'min_length': 2, 'max_length': 50},
            'notes': {'min_length': 0, 'max_length': 1000},
        }
    
    def validate_field(self, field_name: str, value: Any, field_type: Optional[Type] = None) -> Any:
        """Validate a single field based on its name and type"""
        if value is None:
            return value
        
        # Check for specific field validators
        if field_name in self.field_validators:
            return self.field_validators[field_name](value, field_name)
        
        # Check for string field rules
        if field_name in self.string_field_rules and isinstance(value, str):
            rules = self.string_field_rules[field_name]
            return validate_string_length(
                value, 
                field_name,
                min_length=rules.get('min_length', 0),
                max_length=rules.get('max_length', 255),
                required=True
            )
        
        # Generic string validation
        if isinstance(value, str) and field_type == str:
            return validate_string_length(value, field_name, 0, 1000, False)
        
        return value
    
    def validate_model(self, model_instance: BaseModel) -> BaseModel:
        """Validate a Pydantic model instance"""
        try:
            # Get model fields and their values
            model_dict = model_instance.dict()
            validated_dict = {}
            
            # Get type hints for the model
            type_hints = get_type_hints(type(model_instance))
            
            # Validate each field
            for field_name, value in model_dict.items():
                field_type = type_hints.get(field_name)
                validated_dict[field_name] = self.validate_field(field_name, value, field_type)
            
            # Create new model instance with validated data
            return type(model_instance)(**validated_dict)
            
        except PydanticValidationError as e:
            field_errors = convert_pydantic_errors(e)
            raise_validation_error("Model validation failed", field_errors)
        except ValidationError:
            raise
        except Exception as e:
            raise_validation_error(f"Unexpected validation error: {str(e)}")
    
    def validate_dict(self, data: Dict[str, Any], field_rules: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """Validate a dictionary of data"""
        validated_data = {}
        field_errors = {}
        
        for field_name, value in data.items():
            try:
                # Apply custom rules if provided
                if field_rules and field_name in field_rules:
                    rules = field_rules[field_name]
                    if 'validator' in rules:
                        validated_data[field_name] = rules['validator'](value)
                    else:
                        validated_data[field_name] = self.validate_field(field_name, value)
                else:
                    validated_data[field_name] = self.validate_field(field_name, value)
            except ValidationError as e:
                if e.field_errors:
                    field_errors.update(e.field_errors)
                else:
                    field_errors[field_name] = [e.message]
        
        if field_errors:
            raise_validation_error("Dictionary validation failed", field_errors)
        
        return validated_data


# Global validator instance
input_validator = InputValidator()


def validate_input(*validation_rules, **field_rules):
    """
    Decorator to validate input parameters for API endpoints
    
    Args:
        *validation_rules: List of validation functions to apply
        **field_rules: Dictionary of field-specific validation rules
    
    Example:
        @validate_input(
            email=validate_email,
            restaurant_name={'min_length': 2, 'max_length': 100}
        )
        async def create_restaurant(data: RestaurantCreate):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument
            for param_name, param_value in bound_args.arguments.items():
                if param_value is None:
                    continue
                
                # Skip non-data parameters (like request, db, etc.)
                if param_name in ['request', 'db', 'current_user', 'background_tasks']:
                    continue
                
                try:
                    # Validate Pydantic models
                    if isinstance(param_value, BaseModel):
                        validated_model = input_validator.validate_model(param_value)
                        bound_args.arguments[param_name] = validated_model
                    
                    # Validate dictionaries
                    elif isinstance(param_value, dict):
                        validated_dict = input_validator.validate_dict(param_value, field_rules)
                        bound_args.arguments[param_name] = validated_dict
                    
                    # Validate individual fields
                    elif param_name in field_rules:
                        rule = field_rules[param_name]
                        if callable(rule):
                            bound_args.arguments[param_name] = rule(param_value)
                        elif isinstance(rule, dict) and 'validator' in rule:
                            bound_args.arguments[param_name] = rule['validator'](param_value)
                        else:
                            bound_args.arguments[param_name] = input_validator.validate_field(
                                param_name, param_value
                            )
                    
                    # Apply general validation rules
                    for validation_rule in validation_rules:
                        if callable(validation_rule):
                            await validation_rule(param_value) if inspect.iscoroutinefunction(validation_rule) else validation_rule(param_value)
                
                except ValidationError:
                    raise
                except Exception as e:
                    raise_validation_error(f"Validation failed for {param_name}: {str(e)}")
            
            # Call the original function with validated arguments
            return await func(*bound_args.args, **bound_args.kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for synchronous functions
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name, param_value in bound_args.arguments.items():
                if param_value is None:
                    continue
                
                if param_name in ['request', 'db', 'current_user', 'background_tasks']:
                    continue
                
                try:
                    if isinstance(param_value, BaseModel):
                        validated_model = input_validator.validate_model(param_value)
                        bound_args.arguments[param_name] = validated_model
                    elif isinstance(param_value, dict):
                        validated_dict = input_validator.validate_dict(param_value, field_rules)
                        bound_args.arguments[param_name] = validated_dict
                    elif param_name in field_rules:
                        rule = field_rules[param_name]
                        if callable(rule):
                            bound_args.arguments[param_name] = rule(param_value)
                        else:
                            bound_args.arguments[param_name] = input_validator.validate_field(
                                param_name, param_value
                            )
                
                except ValidationError:
                    raise
                except Exception as e:
                    raise_validation_error(f"Validation failed for {param_name}: {str(e)}")
            
            return func(*bound_args.args, **bound_args.kwargs)
        
        # Return appropriate wrapper based on function type
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_request_body(model_class: Type[BaseModel]):
    """
    Decorator to validate request body against a Pydantic model
    
    Example:
        @validate_request_body(RestaurantCreate)
        async def create_restaurant(restaurant_data: RestaurantCreate):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Find the model instance in arguments
            for i, arg in enumerate(args):
                if isinstance(arg, model_class):
                    validated_model = input_validator.validate_model(arg)
                    args = list(args)
                    args[i] = validated_model
                    args = tuple(args)
                    break
            
            # Check keyword arguments
            for key, value in kwargs.items():
                if isinstance(value, model_class):
                    kwargs[key] = input_validator.validate_model(value)
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for i, arg in enumerate(args):
                if isinstance(arg, model_class):
                    validated_model = input_validator.validate_model(arg)
                    args = list(args)
                    args[i] = validated_model
                    args = tuple(args)
                    break
            
            for key, value in kwargs.items():
                if isinstance(value, model_class):
                    kwargs[key] = input_validator.validate_model(value)
            
            return func(*args, **kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_query_params(**param_validators):
    """
    Decorator to validate query parameters
    
    Example:
        @validate_query_params(
            limit=lambda x: validate_quantity(x, 'limit'),
            offset=lambda x: validate_quantity(x, 'offset')
        )
        async def get_items(limit: int = 10, offset: int = 0):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Validate query parameters
            for param_name, validator in param_validators.items():
                if param_name in kwargs and kwargs[param_name] is not None:
                    try:
                        kwargs[param_name] = validator(kwargs[param_name])
                    except ValidationError:
                        raise
                    except Exception as e:
                        raise_validation_error(f"Invalid {param_name}: {str(e)}")
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for param_name, validator in param_validators.items():
                if param_name in kwargs and kwargs[param_name] is not None:
                    try:
                        kwargs[param_name] = validator(kwargs[param_name])
                    except ValidationError:
                        raise
                    except Exception as e:
                        raise_validation_error(f"Invalid {param_name}: {str(e)}")
            
            return func(*args, **kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_path_params(**param_validators):
    """
    Decorator to validate path parameters
    
    Example:
        @validate_path_params(
            restaurant_id=validate_uuid,
            order_id=validate_uuid
        )
        async def get_order(restaurant_id: str, order_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature to map positional args to parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate path parameters
            for param_name, validator in param_validators.items():
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
            
            return await func(*bound_args.args, **bound_args.kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name, validator in param_validators.items():
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
            
            return func(*bound_args.args, **bound_args.kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Convenience decorators for common validation scenarios
def validate_restaurant_endpoint(func: Callable) -> Callable:
    """Decorator for restaurant-related endpoints"""
    return validate_path_params(restaurant_id=validate_uuid)(func)


def validate_order_endpoint(func: Callable) -> Callable:
    """Decorator for order-related endpoints"""
    return validate_path_params(
        restaurant_id=validate_uuid,
        order_id=validate_uuid
    )(func)


def validate_menu_endpoint(func: Callable) -> Callable:
    """Decorator for menu-related endpoints"""
    return validate_path_params(
        restaurant_id=validate_uuid,
        menu_item_id=validate_uuid
    )(func)


def validate_pagination(func: Callable) -> Callable:
    """Decorator for endpoints with pagination"""
    return validate_query_params(
        limit=lambda x: validate_quantity(int(x) if x else 10, 'limit'),
        offset=lambda x: validate_quantity(int(x) if x else 0, 'offset')
    )(func)