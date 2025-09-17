"""
Global exception handlers for the FastAPI application

This module provides centralized exception handling for all API endpoints,
ensuring consistent error responses and proper logging.
"""

import logging
import traceback
import uuid
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    QROrderingException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessLogicError,
    DatabaseError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    RateLimitError,
    MaintenanceError,
    ErrorResponse,
    ValidationErrorResponse,
    create_error_response,
    get_error_status_code
)

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """Generate a unique request ID for error tracking"""
    return str(uuid.uuid4())


async def qr_ordering_exception_handler(
    request: Request, 
    exc: QROrderingException
) -> JSONResponse:
    """Handle custom QR ordering system exceptions"""
    request_id = generate_request_id()
    
    # Log the error with context
    logger.error(
        f"QR Ordering Exception [{request_id}]: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "error_type": type(exc).__name__,
            "url": str(request.url),
            "method": request.method,
            "details": exc.details,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Create error response
    error_response = create_error_response(exc, request_id=request_id)
    status_code = get_error_status_code(exc)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
        headers={"Content-Type": "application/json"}
    )


async def authentication_error_handler(
    request: Request, 
    exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors with security considerations"""
    request_id = generate_request_id()
    
    # Log authentication failures for security monitoring
    logger.warning(
        f"Authentication Error [{request_id}]: {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "security_event": "authentication_failure"
        }
    )
    
    error_response = ErrorResponse(
        error_code="AUTHENTICATION_FAILED",
        message="Authentication required or invalid credentials",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.dict(),
        headers={"WWW-Authenticate": "Bearer"}
    )


async def authorization_error_handler(
    request: Request, 
    exc: AuthorizationError
) -> JSONResponse:
    """Handle authorization errors"""
    request_id = generate_request_id()
    
    # Log authorization failures for security monitoring
    logger.warning(
        f"Authorization Error [{request_id}]: {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "security_event": "authorization_failure"
        }
    )
    
    error_response = create_error_response(exc, request_id=request_id)
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response.dict()
    )


async def validation_error_handler(
    request: Request, 
    exc: Union[ValidationError, RequestValidationError, PydanticValidationError]
) -> JSONResponse:
    """Handle validation errors with detailed field information"""
    request_id = generate_request_id()
    
    # Extract field errors from different validation error types
    field_errors = {}
    error_message = "Validation failed"
    
    if isinstance(exc, ValidationError):
        # Our custom validation error
        field_errors = exc.field_errors
        error_message = exc.message
    elif isinstance(exc, RequestValidationError):
        # FastAPI request validation error
        error_message = "Request validation failed"
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            if field_path not in field_errors:
                field_errors[field_path] = []
            field_errors[field_path].append(error["msg"])
    elif isinstance(exc, PydanticValidationError):
        # Pydantic validation error
        error_message = "Data validation failed"
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            if field_path not in field_errors:
                field_errors[field_path] = []
            field_errors[field_path].append(error["msg"])
    
    # Log validation errors
    logger.info(
        f"Validation Error [{request_id}]: {error_message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "field_errors": field_errors,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = ValidationErrorResponse(
        error_code="VALIDATION_ERROR",
        message=error_message,
        field_errors=field_errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


async def http_exception_handler(
    request: Request, 
    exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """Handle standard HTTP exceptions"""
    request_id = generate_request_id()
    
    # Log HTTP exceptions
    logger.info(
        f"HTTP Exception [{request_id}]: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = ErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        details={"status_code": exc.status_code},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def database_error_handler(
    request: Request, 
    exc: DatabaseError
) -> JSONResponse:
    """Handle database errors with appropriate logging"""
    request_id = generate_request_id()
    
    # Log database errors as errors since they indicate system issues
    logger.error(
        f"Database Error [{request_id}]: {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "error_details": exc.details,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Don't expose internal database details to clients
    error_response = ErrorResponse(
        error_code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


async def external_service_error_handler(
    request: Request, 
    exc: ExternalServiceError
) -> JSONResponse:
    """Handle external service errors"""
    request_id = generate_request_id()
    
    logger.error(
        f"External Service Error [{request_id}]: {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "error_details": exc.details,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    error_response = ErrorResponse(
        error_code="EXTERNAL_SERVICE_ERROR",
        message="An external service is temporarily unavailable. Please try again later.",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=error_response.dict()
    )


async def rate_limit_error_handler(
    request: Request, 
    exc: RateLimitError
) -> JSONResponse:
    """Handle rate limiting errors"""
    request_id = generate_request_id()
    
    logger.warning(
        f"Rate Limit Error [{request_id}]: {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "security_event": "rate_limit_exceeded"
        }
    )
    
    error_response = create_error_response(exc, request_id=request_id)
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.dict(),
        headers={"Retry-After": "60"}  # Suggest retry after 60 seconds
    )


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = generate_request_id()
    
    # Log unexpected exceptions with full traceback
    logger.error(
        f"Unexpected Exception [{request_id}]: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "traceback": traceback.format_exc()
        }
    )
    
    # Don't expose internal error details in production
    from app.core.config import settings
    error_message = str(exc) if settings.debug else "An unexpected error occurred"
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message=error_message,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


# Exception handler registry for easy registration
EXCEPTION_HANDLERS = {
    QROrderingException: qr_ordering_exception_handler,
    AuthenticationError: authentication_error_handler,
    AuthorizationError: authorization_error_handler,
    ValidationError: validation_error_handler,
    RequestValidationError: validation_error_handler,
    PydanticValidationError: validation_error_handler,
    HTTPException: http_exception_handler,
    StarletteHTTPException: http_exception_handler,
    DatabaseError: database_error_handler,
    ExternalServiceError: external_service_error_handler,
    RateLimitError: rate_limit_error_handler,
    Exception: generic_exception_handler,  # Catch-all for unexpected exceptions
}


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    for exception_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)
    
    logger.info("Registered global exception handlers")