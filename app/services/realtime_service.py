"""Supabase real-time service for order notifications"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from supabase import Client
from app.database.supabase_client import supabase_client
from app.services.websocket_service import connection_manager
from app.services.order_service import OrderService
from app.models.order import Order

logger = logging.getLogger(__name__)


class RealtimeService:
    """Service for handling Supabase real-time subscriptions"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or supabase_client.service_client
        self.order_service = OrderService(self.client)
        self.subscriptions: Dict[str, Any] = {}
        self._is_running = False
    
    async def start_order_subscription(self):
        """Start listening to real-time order changes"""
        if self._is_running:
            logger.warning("Real-time service is already running")
            return
        
        try:
            # Subscribe to order table changes
            self._is_running = True
            logger.info("Starting real-time order subscription")
            
            # Note: Supabase Python client real-time is limited
            # For production, consider using Supabase Edge Functions or webhooks
            # For now, we'll implement a polling mechanism as a fallback
            await self._start_polling_mechanism()
            
        except Exception as e:
            logger.error(f"Error starting real-time subscription: {e}")
            self._is_running = False
            raise
    
    async def stop_order_subscription(self):
        """Stop listening to real-time order changes"""
        self._is_running = False
        
        # Unsubscribe from all subscriptions
        for subscription_id, subscription in self.subscriptions.items():
            try:
                # Clean up subscriptions if needed
                logger.info(f"Stopping subscription {subscription_id}")
            except Exception as e:
                logger.error(f"Error stopping subscription {subscription_id}: {e}")
        
        self.subscriptions.clear()
        logger.info("Stopped real-time order subscription")
    
    async def _start_polling_mechanism(self):
        """
        Fallback polling mechanism for real-time updates
        This is a temporary solution until Supabase Python client supports better real-time
        """
        last_check_timestamps: Dict[str, str] = {}
        
        while self._is_running:
            try:
                # Get all connected restaurants
                connected_restaurants = connection_manager.get_connected_restaurants()
                
                for restaurant_id in connected_restaurants:
                    await self._check_restaurant_orders(restaurant_id, last_check_timestamps)
                
                # Wait before next poll (adjust interval as needed)
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in polling mechanism: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _check_restaurant_orders(self, restaurant_id: str, last_check_timestamps: Dict[str, str]):
        """Check for new or updated orders for a specific restaurant"""
        try:
            # Get the last check timestamp for this restaurant
            last_timestamp = last_check_timestamps.get(restaurant_id)
            
            # Query for recent orders
            if last_timestamp:
                # Get orders updated since last check
                response = (
                    self.client.table("orders")
                    .select("*")
                    .eq("restaurant_id", restaurant_id)
                    .gt("updated_at", last_timestamp)
                    .order("updated_at", desc=False)
                    .execute()
                )
            else:
                # First time check - get recent orders from last 5 minutes
                response = (
                    self.client.table("orders")
                    .select("*")
                    .eq("restaurant_id", restaurant_id)
                    .gte("created_at", "now() - interval '5 minutes'")
                    .order("created_at", desc=False)
                    .execute()
                )
            
            if response.data:
                for order_data in response.data:
                    await self._handle_order_change(order_data)
                
                # Update last check timestamp
                last_check_timestamps[restaurant_id] = response.data[-1]["updated_at"]
        
        except Exception as e:
            logger.error(f"Error checking orders for restaurant {restaurant_id}: {e}")
    
    async def _handle_order_change(self, order_data: Dict[str, Any]):
        """Handle order change event"""
        try:
            # Convert to Order model
            order = Order(**order_data)
            
            # Get order items
            order_with_items = await self.order_service.get_order_with_items(order.id)
            if order_with_items:
                order = order_with_items
            
            # Determine event type based on timestamps
            created_at = order.created_at
            updated_at = order.updated_at
            
            if updated_at and updated_at > created_at:
                # Order was updated
                await connection_manager.broadcast_order_status_changed(order)
            else:
                # New order
                await connection_manager.broadcast_order_created(order)
        
        except Exception as e:
            logger.error(f"Error handling order change: {e}")
    
    def is_running(self) -> bool:
        """Check if the real-time service is running"""
        return self._is_running


# Global real-time service instance (lazy initialization)
_realtime_service = None


def get_realtime_service() -> RealtimeService:
    """Get or create the global real-time service instance"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service


async def start_realtime_service():
    """Start the real-time service"""
    try:
        service = get_realtime_service()
        await service.start_order_subscription()
    except Exception as e:
        logger.error(f"Failed to start real-time service: {e}")


async def stop_realtime_service():
    """Stop the real-time service"""
    try:
        service = get_realtime_service()
        await service.stop_order_subscription()
    except Exception as e:
        logger.error(f"Failed to stop real-time service: {e}")