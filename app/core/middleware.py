"""
Middleware for comprehensive request validation and error handling

This module provides middleware for request validation, rate limiting,
and security checks across all API endpoints.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.exceptions import (
    ValidationError,
    RateLimitError,
    MaintenanceError,
    ErrorResponse,
    create_error_response
)
from app.core.logging_config import log_request_info, log_security_event

logger = logging.getLogger("app.middleware")


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request validation"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_json_depth = 10
        self.blocked_user_agents = [
            "bot", "crawler", "spider", "scraper"
        ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            # Validate request size
            await self._validate_request_size(request)
            
            # Validate user agent
            await self._validate_user_agent(request)
            
            # Validate JSON payload if present
            if request.headers.get("content-type", "").startswith("application/json"):
                await self._validate_json_payload(request)
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            duration_ms = (time.time() - start_time) * 1000
            log_request_info(
                logger,
                request.method,
                str(request.url),
                response.status_code,
                duration_ms,
                user_agent=request.headers.get("user-agent"),
                client_ip=request.client.host if request.client else None
            )
            
            return response
            
        except Exception as exc:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request validation failed: {str(exc)}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": duration_ms,
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": request.client.host if request.client else None,
                    "error": str(exc)
                }
            )
            
            # Return error response
            if isinstance(exc, (ValidationError, RateLimitError, MaintenanceError)):
                error_response = create_error_response(exc)
                return JSONResponse(
                    status_code=400 if isinstance(exc, ValidationError) else 429,
                    content=error_response.dict()
                )
            else:
                error_response = ErrorResponse(
                    error_code="REQUEST_VALIDATION_ERROR",
                    message="Request validation failed"
                )
                return JSONResponse(
                    status_code=400,
                    content=error_response.dict()
                )
    
    async def _validate_request_size(self, request: Request):
        """Validate request size limits"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise ValidationError(
                "Request too large",
                details={"max_size": self.max_request_size, "actual_size": int(content_length)}
            )
    
    async def _validate_user_agent(self, request: Request):
        """Validate user agent for security"""
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Block suspicious user agents
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent in user_agent:
                log_security_event(
                    "blocked_user_agent",
                    f"Blocked request from suspicious user agent: {user_agent}",
                    ip_address=request.client.host if request.client else None,
                    user_agent=user_agent
                )
                raise ValidationError(
                    "Invalid user agent",
                    error_code="BLOCKED_USER_AGENT"
                )
    
    async def _validate_json_payload(self, request: Request):
        """Validate JSON payload structure and depth"""
        try:
            # Get raw body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    "Invalid JSON format",
                    details={"json_error": str(e)}
                )
            
            # Validate JSON depth
            self._validate_json_depth(json_data, 0)
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                "JSON validation failed",
                details={"error": str(e)}
            )
    
    def _validate_json_depth(self, obj: Any, current_depth: int):
        """Recursively validate JSON depth"""
        if current_depth > self.max_json_depth:
            raise ValidationError(
                "JSON structure too deep",
                details={"max_depth": self.max_json_depth}
            )
        
        if isinstance(obj, dict):
            for value in obj.values():
                self._validate_json_depth(value, current_depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self._validate_json_depth(item, current_depth + 1)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            log_security_event(
                "rate_limit_exceeded",
                f"Rate limit exceeded for IP: {client_ip}",
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent")
            )
            
            error_response = ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
            )
            
            return JSONResponse(
                status_code=429,
                content=error_response.dict(),
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _clean_old_entries(self, current_time: float):
        """Remove old entries outside the time window"""
        cutoff_time = current_time - self.window_size
        
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip]["requests"] = [
                req_time for req_time in self.request_counts[ip]["requests"]
                if req_time > cutoff_time
            ]
            
            if not self.request_counts[ip]["requests"]:
                del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.request_counts:
            return False
        
        request_count = len(self.request_counts[client_ip]["requests"])
        return request_count >= self.requests_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {"requests": []}
        
        self.request_counts[client_ip]["requests"].append(current_time)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Middleware to handle maintenance mode"""
    
    def __init__(self, app: ASGIApp, maintenance_mode: bool = False):
        super().__init__(app)
        self.maintenance_mode = maintenance_mode
        self.allowed_paths = ["/health", "/"]
    
    async def dispatch(self, request: Request, call_next):
        if self.maintenance_mode and request.url.path not in self.allowed_paths:
            error_response = ErrorResponse(
                error_code="MAINTENANCE_MODE",
                message="System is currently under maintenance. Please try again later."
            )
            
            return JSONResponse(
                status_code=503,
                content=error_response.dict(),
                headers={"Retry-After": "3600"}  # Retry after 1 hour
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request/response logging"""
    
    def __init__(self, app: ASGIApp, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
        }
        
        # Optionally log request body
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_data["body_size"] = len(body)
                    # Don't log sensitive data
                    if "password" not in str(body).lower():
                        request_data["body"] = body.decode("utf-8")[:1000]  # Limit size
            except Exception:
                request_data["body"] = "Could not read body"
        
        logger.info("Request received", extra=request_data)
        
        # Process request
        response = await call_next(request)
        
        # Log response details
        duration_ms = (time.time() - start_time) * 1000
        response_data = {
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "response_headers": dict(response.headers),
        }
        
        # Optionally log response body
        if self.log_response_body and hasattr(response, 'body'):
            try:
                response_data["response_body"] = str(response.body)[:1000]  # Limit size
            except Exception:
                response_data["response_body"] = "Could not read response body"
        
        logger.info("Request completed", extra=response_data)
        
        return response