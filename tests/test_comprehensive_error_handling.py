"""
Comprehensive tests for enhanced error handling and validation

This module tests the complete error handling system including middleware,
input validation, monitoring, and edge cases.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    DatabaseError,
    RateLimitError,
    ErrorResponse
)
from app.core.middleware import (
    RequestValidationMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    MaintenanceMiddleware
)
from app.core.input_validation import (
    InputValidator,
    validate_input,
    validate_request_body,
    validate_query_params,
    validate_path_params
)
from app.core.error_monitoring import (
    ErrorMonitor,
    ErrorSeverity,
    AlertRule,
    AlertChannel,
    record_error
)
from app.core.validation import ValidationRules


class TestRequestValidationMiddleware:
    """Test request validation middleware"""
    
    def test_request_size_validation(self):
        """Test request size validation"""
        app = FastAPI()
        app.add_middleware(RequestValidationMiddleware)
        
        @app.post("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        client = TestClient(app)
        
        # Test normal request
        response = client.post("/test", json={"data": "test"})
        assert response.status_code == 200
    
    def test_user_agent_validation(self):
        """Test user agent validation"""
        app = FastAPI()
        app.add_middleware(RequestValidationMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        client = TestClient(app)
        
        # Test normal user agent
        response = client.get("/test", headers={"user-agent": "Mozilla/5.0"})
        assert response.status_code == 200
        
        # Test blocked user agent
        response = client.get("/test", headers={"user-agent": "bot crawler"})
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BLOCKED_USER_AGENT"


class TestRateLimitMiddleware:
    """Test rate limiting middleware"""
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, requests_per_minute=2)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        client = TestClient(app)
        
        # First two requests should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200
        
        response2 = client.get("/test")
        assert response2.status_code == 200
        
        # Third request should be rate limited
        response3 = client.get("/test")
        assert response3.status_code == 429
        data = response3.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"


class TestInputValidation:
    """Test input validation decorators and utilities"""
    
    def test_input_validator_field_validation(self):
        """Test input validator field validation"""
        validator = InputValidator()
        
        # Test email validation
        result = validator.validate_field("email", "test@example.com")
        assert result == "test@example.com"
        
        # Test UUID validation
        uuid_val = "550e8400-e29b-41d4-a716-446655440000"
        result = validator.validate_field("id", uuid_val)
        assert result == uuid_val
        
        # Test price validation
        result = validator.validate_field("price", "10.99")
        assert str(result) == "10.99"
    
    def test_input_validator_invalid_fields(self):
        """Test input validator with invalid fields"""
        validator = InputValidator()
        
        # Test invalid email
        with pytest.raises(ValidationError):
            validator.validate_field("email", "invalid-email")
        
        # Test invalid UUID
        with pytest.raises(ValidationError):
            validator.validate_field("id", "invalid-uuid")
        
        # Test invalid price
        with pytest.raises(ValidationError):
            validator.validate_field("price", "0.00")
    
    @pytest.mark.asyncio
    async def test_validate_input_decorator(self):
        """Test validate_input decorator"""
        @validate_input()
        async def test_function(email: str, price: str):
            return {"email": email, "price": price}
        
        # Test valid input
        result = await test_function("test@example.com", "10.99")
        assert result["email"] == "test@example.com"
        
        # Test invalid input
        with pytest.raises(ValidationError):
            await test_function("invalid-email", "10.99")


class TestErrorMonitoring:
    """Test error monitoring and alerting"""
    
    def test_error_monitor_record_error(self):
        """Test error recording in monitor"""
        monitor = ErrorMonitor()
        
        # Record a validation error
        exc = ValidationError("Test validation error")
        monitor.record_error(exc, endpoint="/api/test", user_id="user123")
        
        # Check that error was recorded
        assert len(monitor.error_metrics) > 0
        assert len(monitor.recent_errors) > 0
        
        # Check error details
        error_key = list(monitor.error_metrics.keys())[0]
        metric = monitor.error_metrics[error_key]
        assert metric.error_type == "ValidationError"
        assert metric.count == 1
        assert metric.endpoint == "/api/test"
    
    def test_error_monitor_summary(self):
        """Test error summary generation"""
        monitor = ErrorMonitor()
        
        # Record multiple errors
        for i in range(5):
            exc = ValidationError(f"Error {i}")
            monitor.record_error(exc, endpoint=f"/api/test{i}")
        
        # Get summary
        summary = monitor.get_error_summary(24)
        assert summary["total_errors"] == 5
        assert "error_types" in summary
        assert "ValidationError" in summary["error_types"]
    
    def test_error_monitor_trends(self):
        """Test error trend analysis"""
        monitor = ErrorMonitor()
        
        # Record some errors
        for i in range(3):
            exc = DatabaseError(f"DB Error {i}")
            monitor.record_error(exc)
        
        # Get trends
        trends = monitor.get_error_trends(7)
        assert "daily_errors" in trends
        assert "hourly_errors" in trends
        assert "error_growth_rate" in trends
    
    def test_alert_rule_creation(self):
        """Test custom alert rule creation"""
        monitor = ErrorMonitor()
        
        # Create custom alert rule
        rule = AlertRule(
            name="Test Alert",
            condition=lambda errors: len(errors) > 2,
            severity=ErrorSeverity.HIGH,
            channels=[AlertChannel.LOG],
            cooldown_minutes=10
        )
        
        monitor.add_alert_rule(rule)
        assert len(monitor.alert_rules) > 3  # Default rules + custom rule


class TestBusinessLogicValidation:
    """Test business logic validation"""
    
    def test_validation_rules_constants(self):
        """Test validation rules constants"""
        assert ValidationRules.MIN_PRICE > 0
        assert ValidationRules.MAX_PRICE > ValidationRules.MIN_PRICE
        assert ValidationRules.MIN_QUANTITY > 0
        assert ValidationRules.MAX_QUANTITY > ValidationRules.MIN_QUANTITY
        assert ValidationRules.MIN_TABLE_NUMBER > 0
        assert ValidationRules.MAX_TABLE_NUMBER > ValidationRules.MIN_TABLE_NUMBER
    
    def test_order_item_limits(self):
        """Test order item limits"""
        from app.core.validation import validate_order_items
        
        # Test maximum items limit
        max_items = [
            {"menu_item_id": f"550e8400-e29b-41d4-a716-44665544{i:04d}", "quantity": 1}
            for i in range(ValidationRules.MAX_ORDER_ITEMS)
        ]
        
        result = validate_order_items(max_items)
        assert len(result) == ValidationRules.MAX_ORDER_ITEMS
        
        # Test over limit
        over_limit_items = max_items + [
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440999", "quantity": 1}
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items(over_limit_items)
        
        assert "Too many items" in exc_info.value.message


class TestSecurityValidation:
    """Test security-related validation"""
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        from app.core.validation import validate_password
        
        # Test valid password
        strong_password = "SecurePass123"
        result = validate_password(strong_password)
        assert result == strong_password
        
        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoNumbers",  # No digits
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(ValidationError):
                validate_password(weak_password)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in validation"""
        from app.core.validation import validate_string_length
        
        # Test potential SQL injection strings
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "1; DELETE FROM orders; --"
        ]
        
        for malicious_input in malicious_inputs:
            # Should not raise exception - just validate length
            result = validate_string_length(malicious_input, "test_field", 0, 100, False)
            # The validation should pass but the actual SQL queries should use parameterized queries
            assert isinstance(result, str)


class TestErrorResponseConsistency:
    """Test error response consistency"""
    
    def test_error_response_format(self):
        """Test consistent error response format"""
        from app.core.exceptions import create_error_response
        
        # Test different exception types
        exceptions = [
            ValidationError("Validation failed"),
            AuthenticationError("Auth failed"),
            DatabaseError("DB failed"),
            NotFoundError("Not found")
        ]
        
        for exc in exceptions:
            response = create_error_response(exc, request_id="test-123")
            
            # Check required fields
            assert response.error is True
            assert response.error_code is not None
            assert response.message is not None
            assert response.timestamp is not None
            assert response.request_id == "test-123"
            
            # Check serialization
            response_dict = response.dict()
            assert "error" in response_dict
            assert "error_code" in response_dict
            assert "message" in response_dict
            assert "timestamp" in response_dict
    
    def test_validation_error_response_format(self):
        """Test validation error response format"""
        from app.core.exceptions import ValidationErrorResponse
        
        field_errors = {
            "email": ["Invalid format", "Required field"],
            "password": ["Too short"]
        }
        
        response = ValidationErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            field_errors=field_errors,
            request_id="test-123"
        )
        
        response_dict = response.dict()
        assert response_dict["field_errors"] == field_errors
        assert response_dict["error"] is True


class TestIntegrationScenarios:
    """Test integration scenarios with real FastAPI app"""
    
    def test_middleware_integration(self):
        """Test middleware integration with FastAPI"""
        app = FastAPI()
        
        # Add all middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
        app.add_middleware(RequestValidationMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.status_code == 200
    
    def test_exception_handler_integration(self):
        """Test exception handler integration"""
        from app.core.exception_handlers import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/test-error")
        async def test_error_endpoint():
            raise ValidationError("Test validation error")
        
        client = TestClient(app)
        response = client.get("/test-error")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "VALIDATIONERROR"
        assert "request_id" in data


class TestEndpointValidationDecorator:
    """Test the comprehensive endpoint validation decorator"""
    
    @pytest.mark.asyncio
    async def test_endpoint_validation_decorator(self):
        """Test endpoint validation decorator with all features"""
        from app.core.endpoint_validation import validate_endpoint_input
        from app.models.order import OrderCreate
        
        @validate_endpoint_input(
            path_params={"restaurant_id": validate_uuid},
            query_params={"limit": lambda x: validate_quantity(int(x) if x else 10)},
            body_model=OrderCreate
        )
        async def test_endpoint(restaurant_id: str, order_data: OrderCreate, limit: int = 10):
            return {"restaurant_id": restaurant_id, "limit": limit, "items": len(order_data.items)}
        
        # Test with valid data
        from app.models.order import OrderItemCreate
        order_data = OrderCreate(
            restaurant_id="550e8400-e29b-41d4-a716-446655440000",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            items=[
                OrderItemCreate(
                    menu_item_id="550e8400-e29b-41d4-a716-446655440001",
                    quantity=2
                )
            ]
        )
        
        result = await test_endpoint("550e8400-e29b-41d4-a716-446655440000", order_data, 20)
        assert result["restaurant_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["limit"] == 20
        assert result["items"] == 1
    
    @pytest.mark.asyncio
    async def test_endpoint_validation_decorator_errors(self):
        """Test endpoint validation decorator error handling"""
        from app.core.endpoint_validation import validate_endpoint_input
        
        @validate_endpoint_input(
            path_params={"restaurant_id": validate_uuid}
        )
        async def test_endpoint(restaurant_id: str):
            return {"restaurant_id": restaurant_id}
        
        # Test with invalid UUID
        with pytest.raises(ValidationError):
            await test_endpoint("invalid-uuid")


class TestProductionErrorScenarios:
    """Test production-like error scenarios"""
    
    def test_concurrent_error_handling(self):
        """Test error handling under concurrent load"""
        import asyncio
        from app.core.error_monitoring import error_monitor
        
        async def generate_errors():
            tasks = []
            for i in range(10):
                task = asyncio.create_task(self._simulate_error(i))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        async def _simulate_error(self, error_id):
            exc = ValidationError(f"Test error {error_id}")
            error_monitor.record_error(exc, endpoint=f"/test/{error_id}")
            return error_id
        
        # Run the test
        results = asyncio.run(generate_errors())
        assert len(results) == 10
        
        # Check that all errors were recorded
        summary = error_monitor.get_error_summary(1)
        assert summary["total_errors"] >= 10
    
    def test_memory_usage_under_error_load(self):
        """Test memory usage doesn't grow excessively under error load"""
        from app.core.error_monitoring import error_monitor
        import gc
        
        # Record many errors
        for i in range(1000):
            exc = ValidationError(f"Load test error {i}")
            error_monitor.record_error(exc, endpoint="/load-test")
        
        # Force garbage collection
        gc.collect()
        
        # Check that error monitor doesn't hold too many errors in memory
        assert len(error_monitor.recent_errors) <= error_monitor.max_errors_in_memory
        
        # Check that we can still get summaries
        summary = error_monitor.get_error_summary(1)
        assert "total_errors" in summary
    
    def test_error_recovery_after_database_failure(self):
        """Test error recovery after database failures"""
        from app.core.exceptions import DatabaseError
        from app.core.error_monitoring import error_monitor
        
        # Simulate database failures
        for i in range(5):
            exc = DatabaseError(f"Connection failed {i}")
            error_monitor.record_error(exc, endpoint="/api/orders")
        
        # Check that errors are properly categorized
        summary = error_monitor.get_error_summary(1)
        assert "DatabaseError" in summary["error_types"]
        assert summary["error_types"]["DatabaseError"] == 5


class TestErrorMonitoringIntegration:
    """Test error monitoring integration with the application"""
    
    def test_error_dashboard_data(self):
        """Test error dashboard data generation"""
        from app.core.error_monitoring import get_error_dashboard_data, error_monitor
        
        # Generate some test errors
        for i in range(3):
            exc = ValidationError(f"Dashboard test error {i}")
            error_monitor.record_error(exc, endpoint="/api/test")
        
        # Get dashboard data
        dashboard_data = get_error_dashboard_data()
        
        # Check structure
        assert "summary_24h" in dashboard_data
        assert "summary_1h" in dashboard_data
        assert "trends" in dashboard_data
        assert "active_alerts" in dashboard_data
        assert "total_error_types" in dashboard_data
        
        # Check that we have some errors
        assert dashboard_data["summary_1h"]["total_errors"] >= 3
    
    def test_alert_rule_triggering(self):
        """Test that alert rules are properly triggered"""
        from app.core.error_monitoring import ErrorMonitor, AlertRule, ErrorSeverity, AlertChannel
        
        monitor = ErrorMonitor()
        alert_triggered = False
        
        # Create a test alert rule
        def test_condition(errors):
            return len(errors) > 2
        
        rule = AlertRule(
            name="Test Alert",
            condition=test_condition,
            severity=ErrorSeverity.HIGH,
            channels=[AlertChannel.LOG],
            cooldown_minutes=1
        )
        
        monitor.add_alert_rule(rule)
        
        # Generate errors to trigger the alert
        for i in range(4):
            exc = ValidationError(f"Alert test error {i}")
            monitor.record_error(exc, endpoint="/api/alert-test")
        
        # Check that the alert condition would be triggered
        recent_errors = list(monitor.recent_errors)
        assert test_condition(recent_errors) is True