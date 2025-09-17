#!/usr/bin/env python3
"""
Simple test script to verify comprehensive error handling system
"""

import sys
import traceback
from app.core.exceptions import ValidationError, AuthenticationError, DatabaseError
from app.core.validation import validate_email, validate_uuid, validate_price, validate_order_items
from app.core.error_monitoring import record_error, get_error_dashboard_data
from app.core.input_validation import InputValidator

def test_validation_functions():
    """Test core validation functions"""
    print("Testing validation functions...")
    
    # Test email validation
    try:
        result = validate_email("test@example.com")
        assert result == "test@example.com"
        print("✓ Email validation works")
    except Exception as e:
        print(f"✗ Email validation failed: {e}")
        return False
    
    # Test invalid email
    try:
        validate_email("invalid-email")
        print("✗ Invalid email should have failed")
        return False
    except ValidationError:
        print("✓ Invalid email properly rejected")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test UUID validation
    try:
        uuid_val = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(uuid_val)
        assert result == uuid_val
        print("✓ UUID validation works")
    except Exception as e:
        print(f"✗ UUID validation failed: {e}")
        return False
    
    # Test price validation
    try:
        result = validate_price("10.99")
        assert str(result) == "10.99"
        print("✓ Price validation works")
    except Exception as e:
        print(f"✗ Price validation failed: {e}")
        return False
    
    # Test order items validation
    try:
        items = [
            {"menu_item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 2}
        ]
        result = validate_order_items(items)
        assert len(result) == 1
        print("✓ Order items validation works")
    except Exception as e:
        print(f"✗ Order items validation failed: {e}")
        return False
    
    return True

def test_input_validator():
    """Test input validator class"""
    print("\nTesting input validator...")
    
    try:
        validator = InputValidator()
        
        # Test field validation
        result = validator.validate_field("email", "test@example.com")
        assert result == "test@example.com"
        print("✓ Input validator field validation works")
        
        # Test invalid field
        try:
            validator.validate_field("email", "invalid")
            print("✗ Invalid field should have failed")
            return False
        except ValidationError:
            print("✓ Input validator properly rejects invalid fields")
        
        return True
        
    except Exception as e:
        print(f"✗ Input validator failed: {e}")
        return False

def test_error_monitoring():
    """Test error monitoring system"""
    print("\nTesting error monitoring...")
    
    try:
        # Record some errors
        exc1 = ValidationError("Test validation error")
        record_error(exc1, endpoint="/api/test")
        
        exc2 = AuthenticationError("Test auth error")
        record_error(exc2, endpoint="/api/auth")
        
        exc3 = DatabaseError("Test DB error")
        record_error(exc3, endpoint="/api/db")
        
        print("✓ Error recording works")
        
        # Get dashboard data
        dashboard_data = get_error_dashboard_data()
        assert "summary_24h" in dashboard_data
        assert "summary_1h" in dashboard_data
        assert "trends" in dashboard_data
        print("✓ Error dashboard data generation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Error monitoring failed: {e}")
        traceback.print_exc()
        return False

def test_exception_hierarchy():
    """Test exception hierarchy and error responses"""
    print("\nTesting exception hierarchy...")
    
    try:
        from app.core.exceptions import create_error_response, get_error_status_code
        
        # Test different exception types
        exceptions = [
            ValidationError("Validation failed"),
            AuthenticationError("Auth failed"),
            DatabaseError("DB failed")
        ]
        
        for exc in exceptions:
            # Test status code mapping
            status_code = get_error_status_code(exc)
            assert status_code > 0
            
            # Test error response creation
            response = create_error_response(exc, request_id="test-123")
            assert response.error is True
            assert response.error_code is not None
            assert response.message is not None
            assert response.request_id == "test-123"
        
        print("✓ Exception hierarchy and error responses work")
        return True
        
    except Exception as e:
        print(f"✗ Exception hierarchy test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=== Comprehensive Error Handling System Test ===\n")
    
    tests = [
        test_validation_functions,
        test_input_validator,
        test_error_monitoring,
        test_exception_hierarchy
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Comprehensive error handling system is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the error handling implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())