"""Order and order item database service"""

import random
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from supabase import Client
from app.database.base import BaseDatabaseService, DatabaseError, NotFoundError
from app.models.order import Order, OrderCreate, OrderUpdate, OrderItem, OrderItemCreate
from app.models.enums import OrderStatus, PaymentStatus


class OrderItemService(BaseDatabaseService[OrderItem, OrderItemCreate, None]):
    """Service for order item database operations"""
    
    def __init__(self, client: Optional[Client] = None):
        super().__init__(OrderItem, "order_items", client)
    
    async def create_order_items(self, order_id: str, items: List[OrderItemCreate]) -> List[OrderItem]:
        """Create multiple order items for an order"""
        try:
            order_items = []
            for item_data in items:
                # Add order_id to each item
                item_dict = item_data.dict()
                item_dict["order_id"] = order_id
                
                response = self.client.table(self.table_name).insert(item_dict).execute()
                result = self._handle_response(response)
                
                if result:
                    order_items.append(self.model(**result[0]))
            
            return order_items
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to create order items: {str(e)}")
    
    async def get_items_for_order(self, order_id: str) -> List[OrderItem]:
        """Get all items for a specific order"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("order_id", order_id)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get order items: {str(e)}")


class OrderService(BaseDatabaseService[Order, OrderCreate, OrderUpdate]):
    """Service for order database operations"""
    
    def __init__(self, client: Optional[Client] = None):
        super().__init__(Order, "orders", client)
        self.order_item_service = OrderItemService(client)
    
    def _generate_order_number(self, restaurant_id: str) -> str:
        """Generate a unique order number for customer reference"""
        # Use current timestamp with microseconds and random suffix for uniqueness
        timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.digits + string.ascii_uppercase, k=4))
        return f"ORD-{timestamp}-{random_suffix}"
    
    def _calculate_estimated_time(self, items_count: int) -> int:
        """Calculate estimated preparation time based on order complexity"""
        # Base time of 10 minutes + 2 minutes per item (minimum 10, maximum 45)
        base_time = 10
        item_time = items_count * 2
        estimated = base_time + item_time
        return min(max(estimated, 10), 45)
    
    async def create_order_with_items(self, order_data: OrderCreate, notify_realtime: bool = True) -> Order:
        """Create an order with its items in a transaction-like manner"""
        try:
            # Extract items from order data
            items_data = order_data.items
            order_dict = order_data.dict(exclude={"items"})
            
            # Generate order number and estimated time
            order_dict["order_number"] = self._generate_order_number(order_data.restaurant_id)
            order_dict["estimated_time"] = self._calculate_estimated_time(len(items_data))
            
            # Set default payment method to cash
            order_dict["payment_method"] = "cash"
            
            # Create the order first
            response = self.client.table(self.table_name).insert(order_dict).execute()
            result = self._handle_response(response)
            
            if not result:
                raise DatabaseError("Failed to create order")
            
            order = self.model(**result[0])
            
            # Create order items
            if items_data:
                order_items = await self.order_item_service.create_order_items(order.id, items_data)
                # Add items to the order object
                order.items = order_items
            
            # Trigger real-time notification
            if notify_realtime:
                try:
                    # Import here to avoid circular imports
                    from app.services.websocket_service import connection_manager
                    await connection_manager.broadcast_order_created(order)
                except Exception as e:
                    # Log error but don't fail the order creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to broadcast order creation: {e}")
            
            return order
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to create order with items: {str(e)}")
    
    async def get_order_with_items(self, order_id: str) -> Optional[Order]:
        """Get an order with its items"""
        try:
            # Get the order
            order = await self.get(order_id)
            if not order:
                return None
            
            # Get the order items
            order_items = await self.order_item_service.get_items_for_order(order_id)
            order.items = order_items
            
            return order
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get order with items: {str(e)}")
    
    async def get_orders_for_restaurant(
        self,
        restaurant_id: str,
        status_filter: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
        include_items: bool = False
    ) -> List[Order]:
        """Get orders for a specific restaurant"""
        try:
            query = self.client.table(self.table_name).select("*").eq("restaurant_id", restaurant_id)
            
            # Filter by status if provided
            if status_filter:
                query = query.eq("order_status", status_filter.value)
            
            # Apply pagination and ordering
            query = query.range(skip, skip + limit - 1).order("created_at", desc=True)
            
            response = query.execute()
            result = self._handle_response(response)
            
            orders = [self.model(**item) for item in result]
            
            # Include items if requested
            if include_items:
                for order in orders:
                    order_items = await self.order_item_service.get_items_for_order(order.id)
                    order.items = order_items
            
            return orders
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get orders for restaurant: {str(e)}")
    
    async def update_order_status(
        self,
        order_id: str,
        restaurant_id: str,
        new_status: OrderStatus,
        notify_realtime: bool = True
    ) -> Order:
        """Update order status for a specific restaurant's order"""
        try:
            # First verify the order belongs to the restaurant
            existing_order = await self.get_order_for_restaurant(order_id, restaurant_id)
            if not existing_order:
                raise NotFoundError(f"Order {order_id} not found for restaurant {restaurant_id}")
            
            # Update the order status
            update_data = OrderUpdate(order_status=new_status)
            updated_order = await self.update(order_id, update_data)
            
            if not updated_order:
                raise NotFoundError("Order not found after update")
            
            # Get the full order with items for broadcasting
            full_order = await self.get_order_with_items(updated_order.id)
            if not full_order:
                full_order = updated_order
            
            # Trigger real-time notification
            if notify_realtime:
                try:
                    # Import here to avoid circular imports
                    from app.services.websocket_service import connection_manager
                    await connection_manager.broadcast_order_status_changed(full_order)
                except Exception as e:
                    # Log error but don't fail the status update
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to broadcast order status change: {e}")
            
            return updated_order
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to update order status: {str(e)}")
    
    async def get_order_for_restaurant(
        self,
        order_id: str,
        restaurant_id: str,
        include_items: bool = True
    ) -> Optional[Order]:
        """Get a specific order that belongs to a restaurant"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", order_id)
                .eq("restaurant_id", restaurant_id)
                .execute()
            )
            result = self._handle_response(response)
            
            if not result:
                return None
            
            order = self.model(**result[0])
            
            # Include items if requested
            if include_items:
                order_items = await self.order_item_service.get_items_for_order(order_id)
                order.items = order_items
            
            return order
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get order for restaurant: {str(e)}")
    
    async def get_recent_orders(
        self,
        restaurant_id: str,
        hours: int = 24,
        limit: int = 50
    ) -> List[Order]:
        """Get recent orders for a restaurant within specified hours"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .gte("created_at", since_time.isoformat())
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get recent orders: {str(e)}")
    
    async def get_order_analytics(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get order analytics for a restaurant"""
        try:
            query = self.client.table(self.table_name).select("*").eq("restaurant_id", restaurant_id)
            
            # Apply date filters
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            if end_date:
                query = query.lte("created_at", end_date.isoformat())
            
            response = query.execute()
            result = self._handle_response(response)
            
            orders = [self.model(**item) for item in result]
            
            # Calculate analytics
            total_orders = len(orders)
            total_revenue = sum(order.total_price for order in orders)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
            
            # Order status breakdown
            status_counts = {}
            for status in OrderStatus:
                status_counts[status.value] = sum(1 for order in orders if order.order_status == status)
            
            # Payment status breakdown
            payment_counts = {}
            for status in PaymentStatus:
                payment_counts[status.value] = sum(1 for order in orders if order.payment_status == status)
            
            return {
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "average_order_value": float(avg_order_value),
                "order_status_breakdown": status_counts,
                "payment_status_breakdown": payment_counts,
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get order analytics: {str(e)}")
    
    async def get_orders_by_table(
        self,
        restaurant_id: str,
        table_number: int,
        active_only: bool = True
    ) -> List[Order]:
        """Get orders for a specific table"""
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .eq("table_number", table_number)
            )
            
            # Filter for active orders only
            if active_only:
                query = query.not_.in_("order_status", [OrderStatus.COMPLETED.value, OrderStatus.CANCELED.value])
            
            query = query.order("created_at", desc=True)
            
            response = query.execute()
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get orders by table: {str(e)}")