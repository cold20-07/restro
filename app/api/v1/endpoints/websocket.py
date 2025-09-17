"""WebSocket endpoints for real-time order notifications"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.services.websocket_service import connection_manager
from app.services.realtime_service import get_realtime_service
from app.core.auth import get_current_user_from_token
from app.models.auth import User

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_current_user_websocket(websocket: WebSocket, token: str) -> User:
    """Get current user from WebSocket token parameter"""
    try:
        user = await get_current_user_from_token(token)
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


@router.websocket("/orders/live")
async def websocket_order_updates(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time order updates
    
    Query Parameters:
    - token: JWT authentication token
    
    Message Types Sent:
    - connection_established: Confirmation of successful connection
    - order_created: New order has been placed
    - order_status_changed: Order status has been updated
    
    Message Format:
    {
        "type": "order_created" | "order_status_changed" | "connection_established",
        "order": {
            "id": "order_id",
            "order_number": "ORD-240115103045-A1B2",
            "restaurant_id": "restaurant_id",
            "table_number": 5,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "order_status": "pending",
            "payment_status": "pending",
            "payment_method": "cash",
            "total_price": 25.50,
            "estimated_time": 15,
            "created_at": "2024-01-15T10:30:45Z",
            "updated_at": "2024-01-15T10:30:45Z",
            "items": [
                {
                    "id": "item_id",
                    "menu_item_id": "menu_item_id",
                    "quantity": 2,
                    "unit_price": 12.75
                }
            ]
        },
        "timestamp": "2024-01-15T10:30:45Z"
    }
    """
    try:
        # Authenticate user
        user = await get_current_user_websocket(websocket, token)
        
        # Get user's restaurant ID
        restaurant_id = user.restaurant_id
        if not restaurant_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="No restaurant associated")
            return
        
        # Connect to WebSocket manager
        await connection_manager.connect(websocket, restaurant_id)
        
        # Start real-time service if not already running
        realtime_service = get_realtime_service()
        if not realtime_service.is_running():
            await realtime_service.start_order_subscription()
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages if needed
                if data == "ping":
                    await connection_manager.send_personal_message(websocket, {
                        "type": "pong",
                        "message": "Connection is alive"
                    })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for restaurant {restaurant_id}")
        except Exception as e:
            logger.error(f"WebSocket error for restaurant {restaurant_id}: {e}")
        finally:
            connection_manager.disconnect(websocket)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.get("/orders/live/status")
async def websocket_status(current_user: User = Depends(get_current_user_from_token)):
    """
    Get WebSocket connection status for the current restaurant
    """
    restaurant_id = current_user.restaurant_id
    if not restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No restaurant associated with user"
        )
    
    connection_count = connection_manager.get_connection_count(restaurant_id)
    
    realtime_service = get_realtime_service()
    return {
        "restaurant_id": restaurant_id,
        "active_connections": connection_count,
        "realtime_service_running": realtime_service.is_running(),
        "total_system_connections": connection_manager.get_total_connections()
    }


@router.get("/orders/live/connections")
async def websocket_connections(current_user: User = Depends(get_current_user_from_token)):
    """
    Get detailed WebSocket connection information (admin endpoint)
    """
    restaurant_id = current_user.restaurant_id
    if not restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No restaurant associated with user"
        )
    
    realtime_service = get_realtime_service()
    return {
        "restaurant_connections": connection_manager.get_connection_count(restaurant_id),
        "connected_restaurants": connection_manager.get_connected_restaurants(),
        "total_connections": connection_manager.get_total_connections(),
        "realtime_service_status": {
            "running": realtime_service.is_running()
        }
    }