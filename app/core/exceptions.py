"""
Comprehensive exception handling for the QR Code Ordering System

This module defines custom exceptions, error response models, and global exception handlers
to provide consistent error handling across all API endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


# Base Exception Classes
class QROrderingException(Exception):
    """Base exception for QR ordering system"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(QROrderingException):
    """Authentication related errors"""
    pass


class AuthorizationError(QROrderingException):
    """Authorization related errors"""
    pass


class ValidationError(QROrderingException):
    """Data validation errors"""
    
    def __init__(
        self, 
        message: str, 
        field_errors: Optional[Dict[str, List[str]]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or {}
        if self.field_errors:
            self.details["field_errors"] = self.field_errors


class BusinessLogicError(QROrderingException):
    """Business logic validation errors"""
    pass


class DatabaseError(QROrderingException):
    """Database operation errors"""
    pass


class NotFoundError(QROrderingException):
    """Resource not found errors"""
    pass


class ConflictError(QROrderingException):
    """Resource conflict errors (e.g., duplicate entries)"""
    pass


class ExternalServiceError(QROrderingException):
    """External service integration errors"""
    pass


class RateLimitError(QROrderingException):
    """Rate limiting errors"""
    pass


class MaintenanceError(QROrderingException):
    """System maintenance errors"""
    pass


# Error Response Models
class ErrorDetail(BaseModel):
    """Individual error detail"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    error: bool = True
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field_errors: Optional[Dict[str, List[str]]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    def dict(self, **kwargs):
        """Override dict method to ensure datetime serialization"""
        data = super().dict(**kwargs)
        if 'timestamp' in data and isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors"""
    field_errors: Dict[str, List[str]]
    
    def dict(self, **kwargs):
        """Override dict method to ensure datetime serialization"""
        data = super().dict(**kwargs)
        if 'timestamp' in data and isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data


# HTTP Exception Classes with proper status codes
class HTTPValidationError(HTTPException):
    """HTTP exception for validation errors"""
    
    def __init__(
        self, 
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field_errors = field_errors or {}
        self.details = details or {}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )


class HTTPBusinessLogicError(HTTPException):
    """HTTP exception for business logic errors"""
    
    def __init__(
        self, 
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code or "BUSINESS_LOGIC_ERROR"
        self.details = details or {}
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


class HTTPNotFoundError(HTTPException):
    """HTTP exception for not found errors"""
    
    def __init__(
        self, 
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        self.details = details
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class HTTPConflictError(HTTPException):
    """HTTP exception for conflict errors"""
    
    def __init__(
        self, 
        message: str = "Resource conflict",
        conflict_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.conflict_field = conflict_field
        self.details = details or {}
        if conflict_field:
            self.details["conflict_field"] = conflict_field
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


# Exception mapping for consistent HTTP responses
EXCEPTION_STATUS_MAP = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    BusinessLogicError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    MaintenanceError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def get_error_status_code(exception: Exception) -> int:
    """Get appropriate HTTP status code for exception"""
    exception_type = type(exception)
    return EXCEPTION_STATUS_MAP.get(exception_type, status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_error_response(
    exception: Exception,
    request_id: Optional[str] = None,
    include_details: bool = True
) -> ErrorResponse:
    """Create standardized error response from exception"""
    
    if isinstance(exception, QROrderingException):
        error_response = ErrorResponse(
            error_code=exception.error_code,
            message=exception.message,
            details=exception.details if include_details else None,
            request_id=request_id
        )
        
        # Add field errors for validation errors
        if isinstance(exception, ValidationError) and exception.field_errors:
            error_response.field_errors = exception.field_errors
            
        return error_response
    
    # Handle standard HTTP exceptions
    elif isinstance(exception, HTTPException):
        return ErrorResponse(
            error_code="HTTP_ERROR",
            message=str(exception.detail),
            details={"status_code": exception.status_code} if include_details else None,
            request_id=request_id
        )
    
    # Handle unexpected exceptions
    else:
        logger.error(f"Unexpected exception: {type(exception).__name__}: {str(exception)}")
        return ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred" if not include_details else str(exception),
            request_id=request_id
        )


# Utility functions for common error scenarios
def raise_validation_error(
    message: str,
    field_errors: Optional[Dict[str, List[str]]] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Raise a validation error with optional field-specific errors"""
    raise ValidationError(
        message=message,
        field_errors=field_errors,
        details=details
    )


def raise_not_found_error(
    resource_type: str,
    resource_id: Optional[str] = None,
    message: Optional[str] = None
):
    """Raise a not found error for a specific resource"""
    if not message:
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"
    
    raise NotFoundError(
        message=message,
        details={
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    )


def raise_authorization_error(
    message: str = "Access denied",
    required_permission: Optional[str] = None,
    resource_type: Optional[str] = None
):
    """Raise an authorization error with context"""
    details = {}
    if required_permission:
        details["required_permission"] = required_permission
    if resource_type:
        details["resource_type"] = resource_type
    
    raise AuthorizationError(
        message=message,
        details=details
    )


def raise_business_logic_error(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Raise a business logic error"""
    raise BusinessLogicError(
        message=message,
        error_code=error_code,
        details=details
    )


def raise_conflict_error(
    message: str,
    conflict_field: Optional[str] = None,
    existing_value: Optional[str] = None
):
    """Raise a conflict error for duplicate resources"""
    details = {}
    if conflict_field:
        details["conflict_field"] = conflict_field
    if existing_value:
        details["existing_value"] = existing_value
    
    raise ConflictError(
        message=message,
        details=details
    )