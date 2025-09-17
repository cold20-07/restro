"""
Tests for comprehensive error handling and validation

This module tests the global exception handlers, validation utilities,
and error response formats across the application.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError
from fastapi.exceptions import RequestValidationError

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
    get_error_status_code,
    raise_validation_error,
    raise_not_found_error,
    raise_authorization_error,
    raise_business_logic_error,
    raise_conflict_error
)

from app.core.exception_handlers import (
    qr_ordering_exception_handler,
    authentication_error_handler,
    authorization_error_handler,
    validation_error_handler,
    http_exception_handler,
    database_error_handler,
    external_service_error_handler,
    rate_limit_error_handler,
    generic_exception_handler
)

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
    ValidationRules
)

from main import app


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_qr_ordering_exception_base(self):
        """Test base QR ordering exception"""
        exc = QROrderingException("Test message", "TEST_CODE", {"key": "value"})
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test message"
    
    def test_authentication_error(self):
        """Test authentication error"""
        exc = AuthenticationError("Invalid credentials")
        assert exc.message == "Invalid credentials"
        assert exc.error_code == "AUTHENTICATIONERROR"
        assert isinstance(exc, QROrderingException)
    
    def test_validation_error_with_field_errors(self):
        """Test validation error with field-specific errors"""
        field_errors = {"email": ["Invalid format"], "password": ["Too short"]}
        exc = ValidationError("Validation failed", field_errors=field_errors)
        assert exc.message == "Validation failed"
        assert exc.field_errors == field_errors
        assert exc.details["field_errors"] == field_errors
    
    def test_not_found_error(self):
        """Test not found error"""
        exc = NotFoundError("Resource not found", details={"resource_id": "123"})
        assert exc.message == "Resource not found"
        assert exc.details["resource_id"] == "123"


class TestExceptionUtilities:
    """Test exception utility functions"""
    
    def test_get_error_status_code(self):
        """Test status code mapping for exceptions"""
        assert get_error_status_code(AuthenticationError("test")) == 401
        assert get_error_status_code(AuthorizationError("test")) == 403
        assert get_error_status_code(ValidationError("test")) == 422
        assert get_error_status_code(NotFoundError("test")) == 404
        assert get_error_status_code(ConflictError("test")) == 409
        assert get_error_status_code(DatabaseError("test")) == 500
        assert get_error_status_code(Exception("test")) == 500
    
    def test_create_error_response(self):
        """Test error response creation"""
        exc = ValidationError("Test error", field_errors={"field": ["error"]})
        response = create_error_response(exc, request_id="test-123")
        
        assert response.error is True
        assert response.error_code == "VALIDATIONERROR"
        assert response.message == "Test error"
        assert response.field_errors == {"field": ["error"]}
        assert response.request_id == "test-123"
        assert response.timestamp is not None
    
    def test_raise_validation_error(self):
        """Test validation error raising utility"""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("Test error", {"field": ["error"]})
        
        exc = exc_info.value
        assert exc.message == "Test error"
        assert exc.field_errors == {"field": ["error"]}
    
    def test_raise_not_found_error(self):
        """Test not found error raising utility"""
        with pytest.raises(NotFoundError) as exc_info:
            raise_not_found_error("User", "123")
        
        exc = exc_info.value
        assert "User with ID '123' not found" in exc.message
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "123"
    
    def test_raise_authorization_error(self):
        """Test authorization error raising utility"""
        with pytest.raises(AuthorizationError) as exc_info:
            raise_authorization_error("Access denied", "read", "Order")
        
        exc = exc_info.value
        assert exc.message == "Access denied"
        assert exc.details["required_permission"] == "read"
        assert exc.details["resource_type"] == "Order"


class TestValidationUtilities:
    """Test validation utility functions"""
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid-email")
        
        exc = exc_info.value
        assert "Invalid email format" in exc.message
        assert "email" in exc.field_errors
    
    def test_validate_phone_number_valid(self):
        """Test valid phone number validation"""
        assert validate_phone_number("+1234567890") == "+1234567890"
        assert validate_phone_number("(123) 456-7890") == "1234567890"
        assert validate_phone_number("123-456-7890") == "1234567890"
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_phone_number("123")
        
        exc = exc_info.value
        assert "Invalid phone number format" in exc.message
        assert "phone" in exc.field_errors
    
    def test_validate_uuid_valid(self):
        """Test valid UUID validation"""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid(valid_uuid) == valid_uuid
    
    def test_validate_uuid_invalid(self):
        """Test invalid UUID validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid("invalid-uuid")
        
        exc = exc_info.value
        assert "Invalid id format" in exc.message
        assert "id" in exc.field_errors
    
    def test_validate_price_valid(self):
        """Test valid price validation"""
        from decimal import Decimal
        assert validate_price("10.99") == Decimal("10.99")
        assert validate_price(10.99) == Decimal("10.99")
        assert validate_price(10) == Decimal("10")
    
    def test_validate_price_invalid(self):
        """Test invalid price validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_price("0.00")
        
        exc = exc_info.value
        assert "too low" in exc.message
        assert "price" in exc.field_errors
        
        with pytest.raises(ValidationError) as exc_info:
            validate_price("1000.00")
        
        exc = exc_info.value
        assert "too high" in exc.message
    
    def test_validate_quantity_valid(self):
        """Test valid quantity validation"""
        assert validate_quantity(5) == 5
        assert validate_quantity("10") == 10
    
    def test_validate_quantity_invalid(self):
        """Test invalid quantity validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_quantity(0)
        
        exc = exc_info.value
        assert "too low" in exc.message
        assert "quantity" in exc.field_errors
    
    def test_validate_table_number_valid(self):
        """Test valid table number validation"""
        assert validate_table_number(5) == 5
        assert validate_table_number("10") == 10
    
    def test_validate_table_number_invalid(self):
        """Test invalid table number validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_table_number(0)
        
        exc = exc_info.value
        assert "too low" in exc.message
        assert "table_number" in exc.field_errors
    
    def test_validate_string_length_valid(self):
        """Test valid string length validation"""
        assert validate_string_length("test", "name", 2, 10) == "test"
        assert validate_string_length("  test  ", "name", 2, 10) == "test"
    
    def test_validate_string_length_invalid(self):
        """Test invalid string length validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string_length("a", "name", 2, 10)
        
        exc = exc_info.value
        assert "too short" in exc.message
        assert "name" in exc.field_errors
    
    def test_validate_password_valid(self):
        """Test valid password validation"""
        assert validate_password("SecurePass123") == "SecurePass123"
    
    def test_validate_password_invalid(self):
        """Test invalid password validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_password("weak")
        
        exc = exc_info.value
        assert "too short" in exc.message
        
        with pytest.raises(ValidationError) as exc_info:
            validate_password("nouppercase123")
        
        exc = exc_info.value
        assert "uppercase letter" in str(exc.field_errors)
    
    def test_validate_order_items_valid(self):
        """Test valid order items validation"""
        items = [
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 2},
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440001", "quantity": 1}
        ]
        result = validate_order_items(items)
        assert len(result) == 2
        assert result[0]["quantity"] == 2
    
    def test_validate_order_items_invalid(self):
        """Test invalid order items validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items([])
        
        exc = exc_info.value
        assert "required" in exc.message
        assert "items" in exc.field_errors
        
        # Test invalid item
        items = [{"menu_item_id": "invalid", "quantity": 0}]
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items(items)
        
        exc = exc_info.value
        assert "items.0" in exc.field_errors
    
    def test_validate_date_range_valid(self):
        """Test valid date range validation"""
        from datetime import datetime
        start = "2024-01-01"
        end = "2024-01-31"
        start_dt, end_dt = validate_date_range(start, end)
        
        assert start_dt is not None
        assert end_dt is not None
        assert start_dt < end_dt
    
    def test_validate_date_range_invalid(self):
        """Test invalid date range validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range("2024-01-31", "2024-01-01")
        
        exc = exc_info.value
        assert "before end date" in str(exc.field_errors)


class TestExceptionHandlers:
    """Test global exception handlers"""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.__str__ = Mock(return_value="http://test.com/api/test")
        request.method = "POST"
        request.headers = {"user-agent": "test-agent"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.mark.asyncio
    async def test_qr_ordering_exception_handler(self, mock_request):
        """Test QR ordering exception handler"""
        exc = ValidationError("Test error", field_errors={"field": ["error"]})
        response = await qr_ordering_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        content = json.loads(response.body)
        assert content["error"] is True
        assert content["error_code"] == "VALIDATIONERROR"
        assert content["message"] == "Test error"
        assert content["field_errors"] == {"field": ["error"]}
        assert "request_id" in content
    
    @pytest.mark.asyncio
    async def test_authentication_error_handler(self, mock_request):
        """Test authentication error handler"""
        exc = AuthenticationError("Invalid token")
        response = await authentication_error_handler(mock_request, exc)
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        content = json.loads(response.body)
        assert content["error_code"] == "AUTHENTICATION_FAILED"
    
    @pytest.mark.asyncio
    async def test_validation_error_handler(self, mock_request):
        """Test validation error handler"""
        # Test with RequestValidationError
        from pydantic.error_wrappers import ErrorWrapper
        
        # Create a mock validation error
        errors = [ErrorWrapper(ValueError("field required"), ("field",))]
        exc = RequestValidationError(errors)
        
        response = await validation_error_handler(mock_request, exc)
        
        assert response.status_code == 422
        content = json.loads(response.body)
        assert content["error_code"] == "VALIDATION_ERROR"
        assert "field_errors" in content
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        """Test HTTP exception handler"""
        exc = HTTPException(status_code=400, detail="Bad request")
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 400
        content = json.loads(response.body)
        assert content["error_code"] == "HTTP_400"
        assert content["message"] == "Bad request"
    
    @pytest.mark.asyncio
    async def test_database_error_handler(self, mock_request):
        """Test database error handler"""
        exc = DatabaseError("Connection failed")
        response = await database_error_handler(mock_request, exc)
        
        assert response.status_code == 500
        content = json.loads(response.body)
        assert content["error_code"] == "DATABASE_ERROR"
        # Should not expose internal details
        assert "Connection failed" not in content["message"]
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handler(self, mock_request):
        """Test rate limit error handler"""
        exc = RateLimitError("Too many requests")
        response = await rate_limit_error_handler(mock_request, exc)
        
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        content = json.loads(response.body)
        assert content["error_code"] == "RATELIMITERROR"
    
    @pytest.mark.asyncio
    async def test_generic_exception_handler(self, mock_request):
        """Test generic exception handler"""
        exc = Exception("Unexpected error")
        response = await generic_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        content = json.loads(response.body)
        assert content["error_code"] == "INTERNAL_SERVER_ERROR"


class TestErrorHandlingIntegration:
    """Test error handling integration with FastAPI"""
    
    def test_validation_error_in_endpoint(self):
        """Test validation error handling in actual endpoint"""
        client = TestClient(app)
        
        # Test invalid registration data
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "password": "weak",
            "restaurant_name": ""
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "field_errors" in data
    
    def test_authentication_error_in_endpoint(self):
        """Test authentication error handling in protected endpoint"""
        client = TestClient(app)
        
        # Test accessing protected endpoint without token
        response = client.get("/api/dashboard/analytics")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "AUTHENTICATION_FAILED"
    
    def test_not_found_error_in_endpoint(self):
        """Test not found error handling"""
        client = TestClient(app)
        
        # Test accessing non-existent restaurant menu
        response = client.get("/api/menus/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
    
    def test_error_response_format_consistency(self):
        """Test that all error responses follow the same format"""
        client = TestClient(app)
        
        # Test different types of errors
        responses = [
            client.post("/api/auth/register", json={}),  # Validation error
            client.get("/api/dashboard/analytics"),       # Authentication error
            client.get("/api/menus/invalid-id"),         # Not found error
        ]
        
        for response in responses:
            data = response.json()
            # All error responses should have these fields
            assert "error" in data
            assert "error_code" in data
            assert "message" in data
            assert "timestamp" in data
            assert data["error"] is True


class TestBusinessLogicValidation:
    """Test business logic validation scenarios"""
    
    def test_order_validation_business_rules(self):
        """Test order validation with business rules"""
        # Test maximum items per order
        items = [{"menu_item_id": f"550e8400-e29b-41d4-a716-44665544000{i}", "quantity": 1} 
                for i in range(ValidationRules.MAX_ORDER_ITEMS + 1)]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items(items)
        
        exc = exc_info.value
        assert "Too many items" in exc.message
    
    def test_price_validation_business_rules(self):
        """Test price validation with business rules"""
        # Test minimum price
        with pytest.raises(ValidationError):
            validate_price("0.00")
        
        # Test maximum price
        with pytest.raises(ValidationError):
            validate_price("1000.00")
        
        # Test decimal precision
        with pytest.raises(ValidationError):
            validate_price("10.999")  # Too many decimal places
    
    def test_table_number_validation_business_rules(self):
        """Test table number validation with business rules"""
        # Test minimum table number
        with pytest.raises(ValidationError):
            validate_table_number(0)
        
        # Test maximum table number
        with pytest.raises(ValidationError):
            validate_table_number(1000)


if __name__ == "__main__":
    pytest.main([__file__])