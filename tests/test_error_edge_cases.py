"""
Tests for error handling edge cases and complex scenarios

This module tests edge cases, error recovery, and complex error scenarios
that might occur in production environments.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.exceptions import (
    ValidationError,
    DatabaseError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    BusinessLogicError
)
from app.core.validation import (
    validate_order_items,
    validate_date_range,
    validate_price,
    validate_email,
    validate_phone_number
)
from main import app


class TestValidationEdgeCases:
    """Test validation edge cases and boundary conditions"""
    
    def test_email_validation_edge_cases(self):
        """Test email validation with edge cases"""
        # Test empty string
        with pytest.raises(ValidationError):
            validate_email("")
        
        # Test None
        with pytest.raises(ValidationError):
            validate_email(None)
        
        # Test whitespace only
        with pytest.raises(ValidationError):
            validate_email("   ")
        
        # Test very long email
        long_email = "a" * 100 + "@" + "b" * 100 + ".com"
        result = validate_email(long_email)
        assert result == long_email.lower()
        
        # Test email with special characters
        special_email = "test+tag@example-domain.co.uk"
        result = validate_email(special_email)
        assert result == special_email.lower()
    
    def test_phone_number_validation_edge_cases(self):
        """Test phone number validation with edge cases"""
        # Test international formats
        assert validate_phone_number("+44 20 7946 0958") == "+442079460958"
        assert validate_phone_number("+1 (555) 123-4567") == "+15551234567"
        
        # Test minimum length
        assert validate_phone_number("1234567890") == "1234567890"
        
        # Test maximum length
        long_number = "+" + "1" * 15
        assert validate_phone_number(long_number) == long_number
        
        # Test too short
        with pytest.raises(ValidationError):
            validate_phone_number("123456789")
        
        # Test too long
        with pytest.raises(ValidationError):
            validate_phone_number("+" + "1" * 16)
    
    def test_price_validation_edge_cases(self):
        """Test price validation with edge cases"""
        # Test minimum valid price
        assert validate_price("0.01") == Decimal("0.01")
        
        # Test maximum valid price
        assert validate_price("999.99") == Decimal("999.99")
        
        # Test scientific notation
        assert validate_price("1e2") == Decimal("100")
        
        # Test negative numbers
        with pytest.raises(ValidationError):
            validate_price("-10.00")
        
        # Test invalid decimal formats
        with pytest.raises(ValidationError):
            validate_price("10.999")  # Too many decimal places
        
        # Test string that looks like number but isn't
        with pytest.raises(ValidationError):
            validate_price("10.99.99")
    
    def test_order_items_validation_edge_cases(self):
        """Test order items validation with edge cases"""
        # Test empty list
        with pytest.raises(ValidationError):
            validate_order_items([])
        
        # Test None
        with pytest.raises(ValidationError):
            validate_order_items(None)
        
        # Test maximum items
        max_items = [
            {"menu_item_id": f"550e8400-e29b-41d4-a716-44665544{i:04d}", "quantity": 1}
            for i in range(50)  # Maximum allowed
        ]
        result = validate_order_items(max_items)
        assert len(result) == 50
        
        # Test over maximum items
        over_max_items = [
            {"menu_item_id": f"550e8400-e29b-41d4-a716-44665544{i:04d}", "quantity": 1}
            for i in range(51)  # Over maximum
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items(over_max_items)
        assert "Too many items" in exc_info.value.message
        
        # Test mixed valid and invalid items
        mixed_items = [
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 1},  # Valid
            {"menu_item_id": "invalid-uuid", "quantity": 2},  # Invalid UUID
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440001", "quantity": 0},  # Invalid quantity
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_order_items(mixed_items)
        
        # Should have errors for items 1 and 2
        assert "items.1" in exc_info.value.field_errors
        assert "items.2" in exc_info.value.field_errors
    
    def test_date_range_validation_edge_cases(self):
        """Test date range validation with edge cases"""
        # Test same date
        same_date = "2024-01-01"
        with pytest.raises(ValidationError):
            validate_date_range(same_date, same_date)
        
        # Test very large date range (over 1 year)
        start_date = "2024-01-01"
        end_date = "2025-01-02"  # Over 1 year
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(start_date, end_date)
        assert "cannot exceed 1 year" in str(exc_info.value.field_errors)
        
        # Test invalid date formats
        with pytest.raises(ValidationError):
            validate_date_range("invalid-date", "2024-01-01")
        
        # Test None values (should be allowed)
        start, end = validate_date_range(None, None)
        assert start is None
        assert end is None
        
        # Test timezone handling
        start_tz = "2024-01-01T00:00:00Z"
        end_tz = "2024-01-02T00:00:00+05:00"
        start, end = validate_date_range(start_tz, end_tz)
        assert start is not None
        assert end is not None


class TestConcurrentErrorHandling:
    """Test error handling under concurrent conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_errors(self):
        """Test handling multiple validation errors concurrently"""
        async def validate_item(item_data):
            try:
                validate_order_items([item_data])
                return True
            except ValidationError:
                return False
        
        # Test multiple invalid items concurrently
        invalid_items = [
            {"menu_item_id": "invalid", "quantity": 1},
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 0},
            {"menu_item_id": "", "quantity": -1},
        ]
        
        tasks = [validate_item(item) for item in invalid_items]
        results = await asyncio.gather(*tasks)
        
        # All should fail validation
        assert all(result is False for result in results)
    
    @pytest.mark.asyncio
    async def test_database_error_recovery(self):
        """Test database error recovery scenarios"""
        from app.database.base import BaseDatabaseService
        from app.models.restaurant import Restaurant, RestaurantCreate
        
        # Mock a database service
        mock_client = Mock()
        service = BaseDatabaseService(Restaurant, "restaurants", mock_client)
        
        # Test connection failure recovery
        mock_client.table.return_value.insert.return_value.execute.side_effect = [
            Exception("Connection failed"),  # First attempt fails
            Mock(data=[{"id": "123", "name": "Test", "owner_id": "owner123"}])  # Second attempt succeeds
        ]
        
        # First call should raise DatabaseError
        with pytest.raises(DatabaseError):
            await service.create(RestaurantCreate(name="Test", owner_id="owner123"))


class TestErrorRecoveryScenarios:
    """Test error recovery and graceful degradation"""
    
    def test_partial_validation_failure_recovery(self):
        """Test recovery from partial validation failures"""
        # Test scenario where some fields are valid, others are not
        try:
            validate_email("invalid-email")
        except ValidationError as e:
            # Should be able to extract specific field errors
            assert "email" in e.field_errors
            assert len(e.field_errors["email"]) > 0
            
            # Error message should be user-friendly
            assert "Invalid email format" in e.message
    
    def test_cascading_validation_errors(self):
        """Test handling of cascading validation errors"""
        # Test order with multiple validation issues
        invalid_order_data = {
            "restaurant_id": "invalid-uuid",
            "table_number": 0,
            "customer_name": "",
            "customer_phone": "123",
            "items": []
        }
        
        errors = []
        
        # Validate each field and collect errors
        try:
            from app.core.validation import validate_uuid
            validate_uuid(invalid_order_data["restaurant_id"], "restaurant_id")
        except ValidationError as e:
            errors.extend(e.field_errors.get("restaurant_id", []))
        
        try:
            from app.core.validation import validate_table_number
            validate_table_number(invalid_order_data["table_number"])
        except ValidationError as e:
            errors.extend(e.field_errors.get("table_number", []))
        
        try:
            validate_order_items(invalid_order_data["items"])
        except ValidationError as e:
            errors.extend(e.field_errors.get("items", []))
        
        # Should have collected multiple errors
        assert len(errors) >= 3


class TestErrorLoggingAndMonitoring:
    """Test error logging and monitoring functionality"""
    
    @patch('app.core.logging_config.get_logger')
    def test_error_logging_integration(self, mock_get_logger):
        """Test that errors are properly logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Import after mocking to ensure mock is used
        from app.core.exception_handlers import qr_ordering_exception_handler
        
        # Create a test exception
        exc = ValidationError("Test validation error", field_errors={"field": ["error"]})
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.__str__ = Mock(return_value="http://test.com/api/test")
        mock_request.method = "POST"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"
        
        # Test that handler logs the error
        asyncio.run(qr_ordering_exception_handler(mock_request, exc))
        
        # Verify logging was called
        mock_logger.error.assert_called_once()
    
    def test_security_event_logging(self):
        """Test security event logging for authentication failures"""
        from app.core.logging_config import log_security_event
        
        with patch('app.core.logging_config.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            log_security_event(
                "authentication_failure",
                "Invalid login attempt",
                user_id="test-user",
                ip_address="192.168.1.1"
            )
            
            mock_logger.warning.assert_called_once()


class TestProductionErrorScenarios:
    """Test error scenarios that might occur in production"""
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        client = TestClient(app)
        
        # Test malformed JSON
        response = client.post(
            "/api/auth/register",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
    
    def test_oversized_request_handling(self):
        """Test handling of oversized requests"""
        client = TestClient(app)
        
        # Test very large restaurant name
        large_data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "restaurant_name": "A" * 10000  # Very large name
        }
        
        response = client.post("/api/auth/register", json=large_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "field_errors" in data
    
    def test_special_character_handling(self):
        """Test handling of special characters in input"""
        client = TestClient(app)
        
        # Test special characters in restaurant name
        special_data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "restaurant_name": "Test 🍕 Restaurant & Café"
        }
        
        response = client.post("/api/auth/register", json=special_data)
        
        # Should handle special characters gracefully
        # (This might succeed or fail depending on validation rules)
        assert response.status_code in [200, 201, 422]
        data = response.json()
        assert "error" in data
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters"""
        # Test Unicode in validation functions
        unicode_name = "Ресторан Москва"  # Russian text
        
        from app.core.validation import validate_string_length
        result = validate_string_length(unicode_name, "name", 2, 100)
        assert result == unicode_name
        
        # Test Unicode email
        unicode_email = "тест@example.com"
        with pytest.raises(ValidationError):
            validate_email(unicode_email)  # Should fail as it's not valid email format


class TestErrorResponseConsistency:
    """Test consistency of error responses across different scenarios"""
    
    def test_error_response_structure_consistency(self):
        """Test that all error responses have consistent structure"""
        from app.core.exceptions import create_error_response
        
        # Test different exception types
        exceptions = [
            ValidationError("Validation failed", field_errors={"field": ["error"]}),
            NotFoundError("Not found"),
            DatabaseError("DB error"),
            BusinessLogicError("Business rule violated")
        ]
        
        for exc in exceptions:
            response = create_error_response(exc, request_id="test-123")
            
            # All responses should have these fields
            assert hasattr(response, 'error')
            assert hasattr(response, 'error_code')
            assert hasattr(response, 'message')
            assert hasattr(response, 'timestamp')
            assert hasattr(response, 'request_id')
            
            assert response.error is True
            assert response.request_id == "test-123"
            assert response.timestamp is not None
    
    def test_field_error_format_consistency(self):
        """Test that field errors are consistently formatted"""
        # Test validation error with field errors
        from app.core.exceptions import create_error_response
        
        exc = ValidationError(
            "Multiple validation errors",
            field_errors={
                "email": ["Invalid format", "Required field"],
                "password": ["Too short"],
                "nested.field": ["Invalid value"]
            }
        )
        
        response = create_error_response(exc)
        
        assert response.field_errors is not None
        assert "email" in response.field_errors
        assert "password" in response.field_errors
        assert "nested.field" in response.field_errors
        
        # Each field should have a list of errors
        assert isinstance(response.field_errors["email"], list)
        assert len(response.field_errors["email"]) == 2
        assert len(response.field_errors["password"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])