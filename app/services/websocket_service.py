"""WebSocket service for real-time order notifications"""

import json
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.models.order import Order
from app.models.enums import OrderStatus

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time order notifications"""
    
    def __init__(self):
        # Dictionary to store active connections by restaurant_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Dictionary to store restaurant_id for each connection
        self.connection_restaurant_map: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, restaurant_id: str):
        """Accept a WebSocket connection and associate it with a restaurant"""
        await websocket.accept()
        
        # Initialize restaurant connections if not exists
        if restaurant_id not in self.active_connections:
            self.active_connections[restaurant_id] = set()
        
        # Add connection to restaurant's set
        self.active_connections[restaurant_id].add(websocket)
        self.connection_restaurant_map[websocket] = restaurant_id
        
        logger.info(f"WebSocket connected for restaurant {restaurant_id}")
        
        # Send connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "restaurant_id": restaurant_id,
            "message": "Connected to real-time order updates"
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        restaurant_id = self.connection_restaurant_map.get(websocket)
        
        if restaurant_id and restaurant_id in self.active_connections:
            self.active_connections[restaurant_id].discard(websocket)
            
            # Clean up empty restaurant sets
            if not self.active_connections[restaurant_id]:
                del self.active_connections[restaurant_id]
        
        # Remove from connection map
        self.connection_restaurant_map.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected for restaurant {restaurant_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            # Remove the connection if it's broken
            self.disconnect(websocket)
    
    async def broadcast_to_restaurant(self, restaurant_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a specific restaurant"""
        if restaurant_id not in self.active_connections:
            logger.debug(f"No active connections for restaurant {restaurant_id}")
            return
        
        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections[restaurant_id].copy()
        disconnected_connections = []
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast_order_update(self, order: Order, event_type: str = "order_update"):
        """Broadcast order update to restaurant's connections"""
        message = {
            "type": event_type,
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "restaurant_id": order.restaurant_id,
                "table_number": order.table_number,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "order_status": order.order_status.value,
                "payment_status": order.payment_status.value,
                "payment_method": order.payment_method,
                "total_price": float(order.total_price),
                "estimated_time": order.estimated_time,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "items": [
                    {
                        "id": item.id,
                        "menu_item_id": item.menu_item_id,
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price)
                    }
                    for item in (order.items or [])
                ]
            },
            "timestamp": order.updated_at.isoformat() if order.updated_at else order.created_at.isoformat()
        }
        
        await self.broadcast_to_restaurant(order.restaurant_id, message)
        logger.info(f"Broadcasted {event_type} for order {order.id} to restaurant {order.restaurant_id}")
    
    async def broadcast_order_created(self, order: Order):
        """Broadcast new order creation"""
        await self.broadcast_order_update(order, "order_created")
    
    async def broadcast_order_status_changed(self, order: Order):
        """Broadcast order status change"""
        await self.broadcast_order_update(order, "order_status_changed")
    
    def get_connection_count(self, restaurant_id: str) -> int:
        """Get the number of active connections for a restaurant"""
        return len(self.active_connections.get(restaurant_id, set()))
    
    def get_total_connections(self) -> int:
        """Get the total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_restaurants(self) -> List[str]:
        """Get list of restaurant IDs with active connections"""
        return list(self.active_connections.keys())


# Global connection manager instance
connection_manager = ConnectionManager()