"""WebSocket client integration for real-time dashboard updates"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class DashboardWebSocketClient:
    """WebSocket client for connecting to real-time order updates"""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.is_connecting = False
        self.access_token: Optional[str] = None
        self.restaurant_id: Optional[str] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Event handlers
        self.on_order_created: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_order_status_changed: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection_established: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection_lost: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def set_auth(self, access_token: str, restaurant_id: str):
        """Set authentication credentials"""
        self.access_token = access_token
        self.restaurant_id = restaurant_id
    
    def set_event_handlers(self, 
                          on_order_created: Optional[Callable[[Dict[str, Any]], None]] = None,
                          on_order_status_changed: Optional[Callable[[Dict[str, Any]], None]] = None,
                          on_connection_established: Optional[Callable[[Dict[str, Any]], None]] = None,
                          on_connection_lost: Optional[Callable[[], None]] = None,
                          on_error: Optional[Callable[[str], None]] = None):
        """Set event handler callbacks"""
        if on_order_created:
            self.on_order_created = on_order_created
        if on_order_status_changed:
            self.on_order_status_changed = on_order_status_changed
        if on_connection_established:
            self.on_connection_established = on_connection_established
        if on_connection_lost:
            self.on_connection_lost = on_connection_lost
        if on_error:
            self.on_error = on_error
    
    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        if self.is_connected or self.is_connecting:
            return self.is_connected
        
        if not self.access_token:
            logger.error("No access token provided for WebSocket connection")
            if self.on_error:
                self.on_error("Authentication required")
            return False
        
        self.is_connecting = True
        
        try:
            # Construct WebSocket URL with token
            ws_url = f"{self.base_url}/api/v1/ws/orders/live?token={self.access_token}"
            
            logger.info(f"Connecting to WebSocket: {ws_url}")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10   # Wait 10 seconds for close
            )
            
            self.is_connected = True
            self.is_connecting = False
            self.reconnect_attempts = 0
            
            logger.info("WebSocket connected successfully")
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
            return True
            
        except Exception as e:
            self.is_connecting = False
            self.is_connected = False
            logger.error(f"Failed to connect to WebSocket: {e}")
            if self.on_error:
                self.on_error(f"Connection failed: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        self.is_connected = False
        self.is_connecting = False
        self.websocket = None
        
        logger.info("WebSocket disconnected")
    
    async def send_ping(self):
        """Send ping message to keep connection alive"""
        if self.is_connected and self.websocket:
            try:
                await self.websocket.send("ping")
            except Exception as e:
                logger.error(f"Failed to send ping: {e}")
                await self._handle_connection_lost()
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                    if self.on_error:
                        self.on_error(f"Invalid message format: {str(e)}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    if self.on_error:
                        self.on_error(f"Message handling error: {str(e)}")
        
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self._handle_connection_lost()
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            await self._handle_connection_lost()
        except Exception as e:
            logger.error(f"Unexpected error in message handler: {e}")
            await self._handle_connection_lost()
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle parsed WebSocket message"""
        message_type = data.get("type")
        
        if message_type == "connection_established":
            logger.info("WebSocket connection established")
            if self.on_connection_established:
                self.on_connection_established(data)
        
        elif message_type == "order_created":
            logger.info(f"New order received: {data.get('order', {}).get('id')}")
            if self.on_order_created:
                self.on_order_created(data)
        
        elif message_type == "order_status_changed":
            logger.info(f"Order status changed: {data.get('order', {}).get('id')}")
            if self.on_order_status_changed:
                self.on_order_status_changed(data)
        
        elif message_type == "pong":
            logger.debug("Received pong response")
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_connection_lost(self):
        """Handle connection loss and attempt reconnection"""
        self.is_connected = False
        
        if self.on_connection_lost:
            self.on_connection_lost()
        
        # Attempt reconnection if within retry limits
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            # Exponential backoff for reconnection delay
            delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 60)
            await asyncio.sleep(delay)
            await self.connect()
        else:
            logger.error("Max reconnection attempts reached")
            if self.on_error:
                self.on_error("Connection lost and max reconnection attempts reached")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "is_connected": self.is_connected,
            "is_connecting": self.is_connecting,
            "reconnect_attempts": self.reconnect_attempts,
            "has_auth": bool(self.access_token),
            "restaurant_id": self.restaurant_id
        }


# Global WebSocket client instance
_websocket_client = None


def get_websocket_client() -> DashboardWebSocketClient:
    """Get or create the global WebSocket client instance"""
    global _websocket_client
    if _websocket_client is None:
        _websocket_client = DashboardWebSocketClient()
    return _websocket_client