"""Test configuration and fixtures"""

import pytest
from unittest.mock import Mock, patch
import os

# Set test environment variables before any imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_key"

@pytest.fixture(autouse=True)
def mock_database():
    """Auto-use fixture to mock database connections for all tests"""
    mock_client = Mock()
    
    # Mock the entire supabase_client module
    with patch('app.database.supabase_client.create_client', return_value=mock_client):
        with patch('app.database.supabase_client.SupabaseClient') as mock_supabase_class:
            # Create a mock instance
            mock_instance = Mock()
            mock_instance.client = mock_client
            mock_instance.service_client = mock_client
            mock_supabase_class.return_value = mock_instance
            
            # Mock the global instance
            with patch('app.database.supabase_client.supabase_client', mock_instance):
                yield mock_client