"""Analytics service for dashboard reporting and business intelligence"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict
from supabase import Client

from app.database.base import BaseDatabaseService, DatabaseError
from app.models.analytics import (
    AnalyticsResponse, 
    DateRange, 
    MenuItemStats, 
    OrderVolumeByHour, 
    RevenueByDay,
    OrderStatusBreakdown,
    PaymentStatusBreakdown
)
from app.models.enums import OrderStatus, PaymentStatus


class AnalyticsService:
    """Service for generating analytics and business intelligence reports"""
    
    def __init__(self, client: Optional[Client] = None):
        from app.database.supabase_client import supabase_client
        self.client = client or supabase_client.client
    
    def _handle_response(self, response) -> List[Dict[str, Any]]:
        """Handle Supabase response and extract data"""
        if hasattr(response, 'data') and response.data is not None:
            return response.data
        return []
    
    async def get_comprehensive_analytics(
        self,
        restaurant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> AnalyticsResponse:
        """
        Generate comprehensive analytics report for a restaurant
        
        Args:
            restaurant_id: ID of the restaurant
            start_date: Start date for analytics period (defaults to 30 days ago)
            end_date: End date for analytics period (defaults to today)
        
        Returns:
            Complete analytics response with all metrics
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get all orders for the period
            orders_data = await self._get_orders_for_period(restaurant_id, start_date, end_date)
            
            # Calculate summary metrics
            total_orders = len(orders_data)
            total_revenue = sum(Decimal(str(order.get('total_price', 0))) for order in orders_data)
            average_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
            
            # Generate detailed analytics
            best_selling_items = await self._get_best_selling_items(restaurant_id, start_date, end_date)
            orders_by_hour = await self._get_orders_by_hour(orders_data)
            revenue_by_day = await self._get_revenue_by_day(orders_data, start_date, end_date)
            order_status_breakdown = self._get_order_status_breakdown(orders_data)
            payment_status_breakdown = self._get_payment_status_breakdown(orders_data)
            
            return AnalyticsResponse(
                total_orders=total_orders,
                total_revenue=total_revenue,
                average_order_value=average_order_value,
                best_selling_items=best_selling_items,
                orders_by_hour=orders_by_hour,
                revenue_by_day=revenue_by_day,
                order_status_breakdown=order_status_breakdown,
                payment_status_breakdown=payment_status_breakdown,
                date_range=DateRange(start_date=start_date, end_date=end_date),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to generate analytics: {str(e)}")
    
    async def _get_orders_for_period(
        self,
        restaurant_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get all orders for a restaurant within the specified date range"""
        try:
            # Convert dates to datetime strings for Supabase query
            start_datetime = datetime.combine(start_date, datetime.min.time()).isoformat()
            end_datetime = datetime.combine(end_date, datetime.max.time()).isoformat()
            
            response = (
                self.client.table('orders')
                .select('*')
                .eq('restaurant_id', restaurant_id)
                .gte('created_at', start_datetime)
                .lte('created_at', end_datetime)
                .execute()
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            raise DatabaseError(f"Failed to get orders for period: {str(e)}")
    
    async def _get_best_selling_items(
        self,
        restaurant_id: str,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[MenuItemStats]:
        """Get best-selling menu items with detailed statistics"""
        try:
            # Convert dates to datetime strings
            start_datetime = datetime.combine(start_date, datetime.min.time()).isoformat()
            end_datetime = datetime.combine(end_date, datetime.max.time()).isoformat()
            
            # Query to get order items with menu item details and order info
            response = (
                self.client.table('order_items')
                .select('''
                    quantity,
                    unit_price,
                    menu_item_id,
                    menu_items!inner(name),
                    orders!inner(restaurant_id, created_at)
                ''')
                .eq('orders.restaurant_id', restaurant_id)
                .gte('orders.created_at', start_datetime)
                .lte('orders.created_at', end_datetime)
                .execute()
            )
            
            order_items_data = self._handle_response(response)
            
            # Aggregate statistics by menu item
            item_stats = defaultdict(lambda: {
                'total_quantity': 0,
                'total_revenue': Decimal('0'),
                'order_count': 0,
                'name': '',
                'orders': set()
            })
            
            for item in order_items_data:
                menu_item_id = item['menu_item_id']
                quantity = item['quantity']
                unit_price = Decimal(str(item['unit_price']))
                item_revenue = quantity * unit_price
                
                stats = item_stats[menu_item_id]
                stats['total_quantity'] += quantity
                stats['total_revenue'] += item_revenue
                stats['name'] = item['menu_items']['name']
                stats['orders'].add(item['orders']['id'] if 'id' in item['orders'] else str(hash(str(item))))
            
            # Convert to MenuItemStats objects and sort by quantity
            menu_item_stats = []
            for menu_item_id, stats in item_stats.items():
                order_count = len(stats['orders'])
                avg_quantity = Decimal(str(stats['total_quantity'])) / order_count if order_count > 0 else Decimal('0')
                
                menu_item_stats.append(MenuItemStats(
                    menu_item_id=menu_item_id,
                    menu_item_name=stats['name'],
                    total_quantity_sold=stats['total_quantity'],
                    total_revenue=stats['total_revenue'],
                    order_count=order_count,
                    average_quantity_per_order=avg_quantity
                ))
            
            # Sort by total quantity sold (descending) and limit results
            menu_item_stats.sort(key=lambda x: x.total_quantity_sold, reverse=True)
            return menu_item_stats[:limit]
            
        except Exception as e:
            raise DatabaseError(f"Failed to get best-selling items: {str(e)}")
    
    async def _get_orders_by_hour(self, orders_data: List[Dict[str, Any]]) -> List[OrderVolumeByHour]:
        """Analyze order volume by hour of day"""
        try:
            hour_stats = defaultdict(lambda: {'count': 0, 'revenue': Decimal('0')})
            
            for order in orders_data:
                # Parse the created_at timestamp
                created_at_str = order.get('created_at', '')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        hour = created_at.hour
                        
                        hour_stats[hour]['count'] += 1
                        hour_stats[hour]['revenue'] += Decimal(str(order.get('total_price', 0)))
                    except (ValueError, TypeError):
                        continue
            
            # Convert to OrderVolumeByHour objects
            volume_by_hour = []
            for hour in range(24):  # Ensure all hours are represented
                stats = hour_stats[hour]
                volume_by_hour.append(OrderVolumeByHour(
                    hour=hour,
                    order_count=stats['count'],
                    revenue=stats['revenue']
                ))
            
            return volume_by_hour
            
        except Exception as e:
            raise DatabaseError(f"Failed to analyze orders by hour: {str(e)}")
    
    async def _get_revenue_by_day(
        self,
        orders_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date
    ) -> List[RevenueByDay]:
        """Calculate daily revenue statistics"""
        try:
            day_stats = defaultdict(lambda: {'revenue': Decimal('0'), 'count': 0})
            
            for order in orders_data:
                created_at_str = order.get('created_at', '')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        order_date = created_at.date()
                        
                        day_stats[order_date]['count'] += 1
                        day_stats[order_date]['revenue'] += Decimal(str(order.get('total_price', 0)))
                    except (ValueError, TypeError):
                        continue
            
            # Generate revenue by day for the entire date range
            revenue_by_day = []
            current_date = start_date
            while current_date <= end_date:
                stats = day_stats[current_date]
                avg_order_value = stats['revenue'] / stats['count'] if stats['count'] > 0 else Decimal('0')
                
                revenue_by_day.append(RevenueByDay(
                    date=current_date,
                    revenue=stats['revenue'],
                    order_count=stats['count'],
                    average_order_value=avg_order_value
                ))
                
                current_date += timedelta(days=1)
            
            return revenue_by_day
            
        except Exception as e:
            raise DatabaseError(f"Failed to calculate revenue by day: {str(e)}")
    
    def _get_order_status_breakdown(self, orders_data: List[Dict[str, Any]]) -> OrderStatusBreakdown:
        """Calculate breakdown of orders by status"""
        try:
            status_counts = {status.value: 0 for status in OrderStatus}
            
            for order in orders_data:
                order_status = order.get('order_status', '')
                if order_status in status_counts:
                    status_counts[order_status] += 1
            
            return OrderStatusBreakdown(
                pending=status_counts.get(OrderStatus.PENDING.value, 0),
                confirmed=status_counts.get(OrderStatus.CONFIRMED.value, 0),
                in_progress=status_counts.get(OrderStatus.IN_PROGRESS.value, 0),
                ready=status_counts.get(OrderStatus.READY.value, 0),
                completed=status_counts.get(OrderStatus.COMPLETED.value, 0),
                canceled=status_counts.get(OrderStatus.CANCELED.value, 0)
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to calculate order status breakdown: {str(e)}")
    
    def _get_payment_status_breakdown(self, orders_data: List[Dict[str, Any]]) -> PaymentStatusBreakdown:
        """Calculate breakdown of orders by payment status"""
        try:
            payment_counts = {status.value: 0 for status in PaymentStatus}
            
            for order in orders_data:
                payment_status = order.get('payment_status', '')
                if payment_status in payment_counts:
                    payment_counts[payment_status] += 1
            
            return PaymentStatusBreakdown(
                pending=payment_counts.get(PaymentStatus.PENDING.value, 0),
                paid=payment_counts.get(PaymentStatus.PAID.value, 0),
                failed=payment_counts.get(PaymentStatus.FAILED.value, 0),
                refunded=payment_counts.get(PaymentStatus.REFUNDED.value, 0)
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to calculate payment status breakdown: {str(e)}")
    
    async def get_quick_metrics(
        self,
        restaurant_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get quick metrics for dashboard overview"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            orders_data = await self._get_orders_for_period(restaurant_id, start_date, end_date)
            
            total_orders = len(orders_data)
            total_revenue = sum(Decimal(str(order.get('total_price', 0))) for order in orders_data)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
            
            # Calculate completion rate
            completed_orders = sum(1 for order in orders_data if order.get('order_status') == OrderStatus.COMPLETED.value)
            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            return {
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "average_order_value": float(avg_order_value),
                "completion_rate": round(completion_rate, 1),
                "period_days": days
            }
            
        except Exception as e:
            raise DatabaseError(f"Failed to get quick metrics: {str(e)}")