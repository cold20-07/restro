"""Tests for analytics API endpoints"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from app.models.analytics import (
    AnalyticsResponse, 
    DateRange, 
    MenuItemStats, 
    OrderVolumeByHour,
    OrderStatusBreakdown,
    PaymentStatusBreakdown
)
from app.database.base import DatabaseError


class TestAnalyticsEndpoints:
    """Test suite for analytics API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    

    
    @pytest.fixture
    def sample_analytics_response(self):
        """Sample analytics response for testing"""
        return AnalyticsResponse(
            total_orders=50,
            total_revenue=Decimal('1250.75'),
            average_order_value=Decimal('25.02'),
            best_selling_items=[
                MenuItemStats(
                    menu_item_id='item-1',
                    menu_item_name='Margherita Pizza',
                    total_quantity_sold=25,
                    total_revenue=Decimal('375.00'),
                    order_count=20,
                    average_quantity_per_order=Decimal('1.25')
                )
            ],
            orders_by_hour=[
                OrderVolumeByHour(hour=12, order_count=5, revenue=Decimal('125.50'))
            ],
            revenue_by_day=[],
            order_status_breakdown=OrderStatusBreakdown(
                completed=40, pending=5, confirmed=3, in_progress=2
            ),
            payment_status_breakdown=PaymentStatusBreakdown(
                paid=45, pending=5
            ),
            date_range=DateRange(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        )
    
    @patch('app.core.auth.get_current_user')
    @patch('app.api.v1.endpoints.analytics.get_analytics_service')
    def test_get_dashboard_analytics_success(self, mock_service, mock_auth, client, sample_analytics_response):
        """Test successful analytics retrieval"""
        # Mock authentication - return (user, restaurant_id) tuple
        from app.models.auth import User
        from datetime import datetime
        
        mock_user = User(
            id="user-123",
            email="test@restaurant.com",
            email_confirmed_at=datetime.utcnow(),
            created_at=datetime.utcnow().isoformat()
        )
        mock_auth.return_value = (mock_user, 'test-restaurant-id')
        
        # Mock the analytics service
        mock_analytics_service = Mock()
        mock_analytics_service.get_comprehensive_analytics = AsyncMock(return_value=sample_analytics_response)
        mock_service.return_value = mock_analytics_service
        
        # Make the request
        response = client.get(
            "/api/dashboard/analytics/",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['total_orders'] == 50
        assert data['total_revenue'] == '1250.75'
        assert data['average_order_value'] == '25.02'
        assert len(data['best_selling_items']) == 1
        assert data['best_selling_items'][0]['menu_item_name'] == 'Margherita Pizza'
        
        # Verify service was called correctly
        mock_analytics_service.get_comprehensive_analytics.assert_called_once_with(
            restaurant_id='test-restaurant-id',
            start_date=None,
            end_date=None
        )
    
    @patch('app.core.auth.get_current_user')
    @patch('app.api.v1.endpoints.analytics.get_analytics_service')
    def test_get_dashboard_analytics_with_date_range(self, mock_service, mock_auth, client, sample_analytics_response):
        """Test analytics retrieval with date range parameters"""
        # Mock authentication - return (user, restaurant_id) tuple
        from app.models.auth import User
        from datetime import datetime
        
        mock_user = User(
            id="user-123",
            email="test@restaurant.com",
            email_confirmed_at=datetime.utcnow(),
            created_at=datetime.utcnow().isoformat()
        )
        mock_auth.return_value = (mock_user, 'test-restaurant-id')
        
        # Mock the analytics service
        mock_analytics_service = Mock()
        mock_analytics_service.get_comprehensive_analytics = AsyncMock(return_value=sample_analytics_response)
        mock_service.return_value = mock_analytics_service
        
        # Make the request with date parameters
        response = client.get(
            "/api/dashboard/analytics/?start_date=2024-01-01&end_date=2024-01-31",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify the response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with correct dates
        mock_analytics_service.get_comprehensive_analytics.assert_called_once_with(
            restaurant_id='test-restaurant-id',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_invalid_date_range(self, client, mock_auth_dependency):
        """Test analytics with invalid date range"""
        response = client.get(
            "/api/v1/dashboard/analytics/?start_date=2024-01-31&end_date=2024-01-01",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Start date cannot be after end date" in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_date_range_too_large(self, client, mock_auth_dependency):
        """Test analytics with date range exceeding limit"""
        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)  # More than 365 days
        
        response = client.get(
            f"/api/v1/dashboard/analytics/?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Date range cannot exceed 365 days" in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_database_error(self, client, mock_auth_dependency):
        """Test analytics endpoint with database error"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_comprehensive_analytics = AsyncMock(
                side_effect=DatabaseError("Database connection failed")
            )
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Database error" in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_unauthorized(self, client):
        """Test analytics endpoint without authentication"""
        response = client.get("/api/v1/dashboard/analytics/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_post_analytics_with_filters(self, client, mock_auth_dependency, sample_analytics_response):
        """Test POST analytics endpoint with filters"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_comprehensive_analytics = AsyncMock(return_value=sample_analytics_response)
            mock_service.return_value = mock_analytics_service
            
            # Make POST request with filters
            request_data = {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
            
            response = client.post(
                "/api/v1/dashboard/analytics/",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['total_orders'] == 50
            
            # Verify service was called correctly
            mock_analytics_service.get_comprehensive_analytics.assert_called_once_with(
                restaurant_id='test-restaurant-id',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    @pytest.mark.asyncio
    async def test_post_analytics_invalid_date_range(self, client, mock_auth_dependency):
        """Test POST analytics with invalid date range"""
        request_data = {
            "start_date": "2024-01-31",
            "end_date": "2024-01-01"
        }
        
        response = client.post(
            "/api/v1/dashboard/analytics/",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Start date cannot be after end date" in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_get_quick_metrics_success(self, client, mock_auth_dependency):
        """Test successful quick metrics retrieval"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_quick_metrics = AsyncMock(return_value={
                "total_orders": 25,
                "total_revenue": 625.50,
                "average_order_value": 25.02,
                "completion_rate": 88.0,
                "period_days": 7
            })
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/quick-metrics",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data['total_orders'] == 25
            assert data['total_revenue'] == 625.50
            assert data['average_order_value'] == 25.02
            assert data['completion_rate'] == 88.0
            assert data['period_days'] == 7
            
            # Verify service was called with default days
            mock_analytics_service.get_quick_metrics.assert_called_once_with(
                restaurant_id='test-restaurant-id',
                days=7
            )
    
    @pytest.mark.asyncio
    async def test_get_quick_metrics_custom_days(self, client, mock_auth_dependency):
        """Test quick metrics with custom days parameter"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_quick_metrics = AsyncMock(return_value={
                "total_orders": 75,
                "total_revenue": 1875.25,
                "average_order_value": 25.00,
                "completion_rate": 92.0,
                "period_days": 30
            })
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/quick-metrics?days=30",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['period_days'] == 30
            
            # Verify service was called with custom days
            mock_analytics_service.get_quick_metrics.assert_called_once_with(
                restaurant_id='test-restaurant-id',
                days=30
            )
    
    @pytest.mark.asyncio
    async def test_get_quick_metrics_invalid_days(self, client, mock_auth_dependency):
        """Test quick metrics with invalid days parameter"""
        response = client.get(
            "/api/v1/dashboard/analytics/quick-metrics?days=0",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_success(self, client, mock_auth_dependency, sample_analytics_response):
        """Test successful revenue summary retrieval"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_comprehensive_analytics = AsyncMock(return_value=sample_analytics_response)
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/revenue-summary?period=30d",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data['period'] == '30d'
            assert data['total_revenue'] == 1250.75
            assert data['total_orders'] == 50
            assert data['average_order_value'] == 25.02
            assert 'revenue_by_day' in data
            assert 'date_range' in data
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_invalid_period(self, client, mock_auth_dependency):
        """Test revenue summary with invalid period"""
        response = client.get(
            "/api/v1/dashboard/analytics/revenue-summary?period=invalid",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_best_selling_items_success(self, client, mock_auth_dependency):
        """Test successful best-selling items retrieval"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service._get_best_selling_items = AsyncMock(return_value=[
                MenuItemStats(
                    menu_item_id='item-1',
                    menu_item_name='Margherita Pizza',
                    total_quantity_sold=25,
                    total_revenue=Decimal('375.00'),
                    order_count=20,
                    average_quantity_per_order=Decimal('1.25')
                ),
                MenuItemStats(
                    menu_item_id='item-2',
                    menu_item_name='Caesar Salad',
                    total_quantity_sold=15,
                    total_revenue=Decimal('225.00'),
                    order_count=15,
                    average_quantity_per_order=Decimal('1.00')
                )
            ])
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/best-sellers?limit=10&days=30",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert len(data['best_selling_items']) == 2
            assert data['best_selling_items'][0]['menu_item_name'] == 'Margherita Pizza'
            assert data['best_selling_items'][0]['total_quantity_sold'] == 25
            assert data['period_days'] == 30
            
            # Verify service was called correctly
            mock_analytics_service._get_best_selling_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_best_selling_items_custom_params(self, client, mock_auth_dependency):
        """Test best-selling items with custom parameters"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service._get_best_selling_items = AsyncMock(return_value=[])
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/best-sellers?limit=5&days=7",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data['period_days'] == 7
            assert len(data['best_selling_items']) == 0
    
    @pytest.mark.asyncio
    async def test_get_best_selling_items_invalid_params(self, client, mock_auth_dependency):
        """Test best-selling items with invalid parameters"""
        # Test invalid limit
        response = client.get(
            "/api/v1/dashboard/analytics/best-sellers?limit=0",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid days
        response = client.get(
            "/api/v1/dashboard/analytics/best-sellers?days=0",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_analytics_endpoints_general_error(self, client, mock_auth_dependency):
        """Test analytics endpoints with general error"""
        with patch('app.api.v1.endpoints.analytics.get_analytics_service') as mock_service:
            mock_analytics_service = Mock()
            mock_analytics_service.get_comprehensive_analytics = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_service.return_value = mock_analytics_service
            
            response = client.get(
                "/api/v1/dashboard/analytics/",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to generate analytics" in response.json()['detail']