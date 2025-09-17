"""Analytics model definitions for dashboard reporting"""

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional, Dict, Any


class DateRange(BaseModel):
    """Date range model for analytics filtering"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MenuItemStats(BaseModel):
    """Statistics for individual menu items"""
    menu_item_id: str
    menu_item_name: str
    total_quantity_sold: int
    total_revenue: Decimal
    order_count: int
    average_quantity_per_order: Decimal


class OrderVolumeByHour(BaseModel):
    """Order volume statistics by hour of day"""
    hour: int
    order_count: int
    revenue: Decimal


class OrderStatusBreakdown(BaseModel):
    """Breakdown of orders by status"""
    pending: int = 0
    confirmed: int = 0
    in_progress: int = 0
    ready: int = 0
    completed: int = 0
    canceled: int = 0


class PaymentStatusBreakdown(BaseModel):
    """Breakdown of orders by payment status"""
    pending: int = 0
    paid: int = 0
    failed: int = 0
    refunded: int = 0


class RevenueByDay(BaseModel):
    """Daily revenue statistics"""
    date: date
    revenue: Decimal
    order_count: int
    average_order_value: Decimal


class AnalyticsResponse(BaseModel):
    """Complete analytics response model for dashboard"""
    # Summary metrics
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    
    # Best-selling items
    best_selling_items: List[MenuItemStats] = []
    
    # Time-based analytics
    orders_by_hour: List[OrderVolumeByHour] = []
    revenue_by_day: List[RevenueByDay] = []
    
    # Status breakdowns
    order_status_breakdown: OrderStatusBreakdown = OrderStatusBreakdown()
    payment_status_breakdown: PaymentStatusBreakdown = PaymentStatusBreakdown()
    
    # Metadata
    date_range: DateRange
    generated_at: datetime = datetime.utcnow()



class AnalyticsRequest(BaseModel):
    """Request model for analytics with optional date filtering"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None