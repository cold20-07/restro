"""Analytics API endpoints for dashboard reporting"""

from typing import Optional, Dict, Any
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_restaurant_id
from app.database.service_factory import get_analytics_service
from app.models.analytics import AnalyticsResponse, AnalyticsRequest
from app.services.analytics_service import AnalyticsService
from app.database.base import DatabaseError

router = APIRouter()


@router.get("/", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analytics period (YYYY-MM-DD)"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive analytics for restaurant dashboard
    
    This endpoint provides:
    - Sales calculations and revenue metrics
    - Order volume and performance statistics
    - Best-selling items analysis
    - Time-based analytics (hourly and daily breakdowns)
    - Order and payment status breakdowns
    
    Query Parameters:
    - start_date: Start date for analytics period (defaults to 30 days ago)
    - end_date: End date for analytics period (defaults to today)
    
    Requirements covered: 8.1, 8.2, 8.3, 8.4
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Set reasonable limits on date range (max 1 year)
        if start_date and end_date:
            date_diff = (end_date - start_date).days
            if date_diff > 365:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date range cannot exceed 365 days"
                )
        
        # Generate comprehensive analytics
        analytics = await analytics_service.get_comprehensive_analytics(
            restaurant_id=restaurant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return analytics
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.post("/", response_model=AnalyticsResponse)
async def get_analytics_with_filters(
    analytics_request: AnalyticsRequest,
    restaurant_id: str = Depends(get_current_restaurant_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get analytics with POST request for complex filtering
    
    This endpoint allows for more complex analytics requests through POST body.
    Useful for future extensions with additional filtering options.
    
    Requirements covered: 8.1, 8.2, 8.3, 8.4
    """
    try:
        # Validate date range
        if (analytics_request.start_date and analytics_request.end_date and 
            analytics_request.start_date > analytics_request.end_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate analytics with request parameters
        analytics = await analytics_service.get_comprehensive_analytics(
            restaurant_id=restaurant_id,
            start_date=analytics_request.start_date,
            end_date=analytics_request.end_date
        )
        
        return analytics
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.get("/quick-metrics", response_model=Dict[str, Any])
async def get_quick_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days for quick metrics (1-90)"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get quick metrics for dashboard overview
    
    This endpoint provides a lightweight summary of key metrics:
    - Total orders and revenue
    - Average order value
    - Order completion rate
    
    Optimized for dashboard widgets and quick loading.
    
    Query Parameters:
    - days: Number of days to include in metrics (default: 7, max: 90)
    
    Requirements covered: 8.1, 8.2
    """
    try:
        metrics = await analytics_service.get_quick_metrics(
            restaurant_id=restaurant_id,
            days=days
        )
        
        return metrics
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quick metrics: {str(e)}"
        )


@router.get("/revenue-summary")
async def get_revenue_summary(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="Time period: 7d, 30d, 90d, or 1y"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get revenue summary for specific time periods
    
    This endpoint provides revenue-focused analytics for common time periods.
    Useful for revenue charts and financial reporting.
    
    Query Parameters:
    - period: Time period (7d, 30d, 90d, 1y)
    
    Requirements covered: 8.1, 8.2
    """
    try:
        # Map period strings to days
        period_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }
        
        days = period_days.get(period, 30)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics for the period
        analytics = await analytics_service.get_comprehensive_analytics(
            restaurant_id=restaurant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Return revenue-focused summary
        return {
            "period": period,
            "total_revenue": float(analytics.total_revenue),
            "total_orders": analytics.total_orders,
            "average_order_value": float(analytics.average_order_value),
            "revenue_by_day": [
                {
                    "date": day.date.isoformat(),
                    "revenue": float(day.revenue),
                    "order_count": day.order_count
                }
                for day in analytics.revenue_by_day
            ],
            "date_range": {
                "start_date": analytics.date_range.start_date.isoformat(),
                "end_date": analytics.date_range.end_date.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue summary: {str(e)}"
        )


@router.get("/best-sellers")
async def get_best_selling_items(
    limit: int = Query(10, ge=1, le=50, description="Number of top items to return (1-50)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get best-selling menu items analysis
    
    This endpoint provides detailed analysis of top-performing menu items:
    - Items ranked by quantity sold
    - Revenue contribution per item
    - Order frequency statistics
    
    Query Parameters:
    - limit: Number of top items to return (default: 10, max: 50)
    - days: Number of days to analyze (default: 30, max: 365)
    
    Requirements covered: 8.3, 8.4
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get best-selling items
        best_sellers = await analytics_service._get_best_selling_items(
            restaurant_id=restaurant_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "best_selling_items": [
                {
                    "menu_item_id": item.menu_item_id,
                    "menu_item_name": item.menu_item_name,
                    "total_quantity_sold": item.total_quantity_sold,
                    "total_revenue": float(item.total_revenue),
                    "order_count": item.order_count,
                    "average_quantity_per_order": float(item.average_quantity_per_order)
                }
                for item in best_sellers
            ],
            "period_days": days,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get best-selling items: {str(e)}"
        )