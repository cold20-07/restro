#!/usr/bin/env python3
"""
Demo script to test real-time WebSocket integration
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from app.services.websocket_service import connection_manager
from app.models.order import Order, OrderStatus, PaymentStatus
from dashboard.websocket_client import DashboardWebSocketClient


async def demo_backend_websocket():
    """Demo backend WebSocket functionality"""
    print("=== Backend WebSocket Demo ===")
    
    # Create test order
    test_order = Order(
        id="demo_order_001",
        order_number="ORD-240916-DEMO",
        restaurant_id="demo_restaurant_123",
        table_number=7,
        customer_name="Demo Customer",
        customer_phone="+1234567890",
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        payment_method="cash",
        total_price=Decimal("35.75"),
        estimated_time=18,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        items=[]
    )
    
    print(f"Created test order: {test_order.order_number}")
    
    # Test connection manager
    print(f"Total connections: {connection_manager.get_total_connections()}")
    print(f"Connected restaurants: {connection_manager.get_connected_restaurants()}")
    
    # Simulate order broadcast (would normally be triggered by order creation)
    print("Broadcasting order creation...")
    await connection_manager.broadcast_order_created(test_order)
    
    # Simulate status change
    test_order.order_status = OrderStatus.CONFIRMED
    test_order.updated_at = datetime.now()
    
    print("Broadcasting order status change...")
    await connection_manager.broadcast_order_status_changed(test_order)
    
    print("Backend demo completed!")


async def demo_frontend_websocket():
    """Demo frontend WebSocket client functionality"""
    print("\n=== Frontend WebSocket Client Demo ===")
    
    # Create WebSocket client
    ws_client = DashboardWebSocketClient("ws://localhost:8000")
    ws_client.set_auth("demo_token", "demo_restaurant_123")
    
    # Set up event handlers
    def on_order_created(data):
        print(f"📦 New order received: {data['order']['order_number']}")
        print(f"   Customer: {data['order']['customer_name']}")
        print(f"   Table: {data['order']['table_number']}")
        print(f"   Total: ${data['order']['total_price']}")
    
    def on_order_status_changed(data):
        print(f"🔄 Order status changed: {data['order']['id']}")
        print(f"   New status: {data['order']['order_status']}")
    
    def on_connection_established(data):
        print(f"✅ Connected to restaurant: {data['restaurant_id']}")
    
    def on_connection_lost():
        print("❌ Connection lost!")
    
    def on_error(error):
        print(f"🚨 Error: {error}")
    
    ws_client.set_event_handlers(
        on_order_created=on_order_created,
        on_order_status_changed=on_order_status_changed,
        on_connection_established=on_connection_established,
        on_connection_lost=on_connection_lost,
        on_error=on_error
    )
    
    # Test connection status
    status = ws_client.get_connection_status()
    print(f"Connection status: {status}")
    
    # Test message handling
    print("Testing message handling...")
    
    # Simulate connection established
    await ws_client._handle_message({
        "type": "connection_established",
        "restaurant_id": "demo_restaurant_123",
        "message": "Connected to real-time order updates"
    })
    
    # Simulate order created
    await ws_client._handle_message({
        "type": "order_created",
        "order": {
            "id": "demo_order_001",
            "order_number": "ORD-240916-DEMO",
            "restaurant_id": "demo_restaurant_123",
            "table_number": 7,
            "customer_name": "Demo Customer",
            "customer_phone": "+1234567890",
            "order_status": "pending",
            "payment_status": "pending",
            "payment_method": "cash",
            "total_price": 35.75,
            "estimated_time": 18,
            "created_at": "2024-09-16T09:15:00Z",
            "updated_at": "2024-09-16T09:15:00Z",
            "items": []
        },
        "timestamp": "2024-09-16T09:15:00Z"
    })
    
    # Simulate order status change
    await ws_client._handle_message({
        "type": "order_status_changed",
        "order": {
            "id": "demo_order_001",
            "order_status": "confirmed"
        },
        "timestamp": "2024-09-16T09:16:00Z"
    })
    
    print("Frontend demo completed!")


async def demo_state_integration():
    """Demo state integration"""
    print("\n=== State Integration Demo ===")
    
    from dashboard.state import WebSocketState, DashboardState, OrdersState
    
    # Create state instances
    ws_state = WebSocketState()
    dashboard_state = DashboardState()
    orders_state = OrdersState()
    
    print(f"Initial WebSocket state: {ws_state.connection_status}")
    print(f"Initial dashboard orders: {len(dashboard_state.recent_orders)}")
    print(f"Initial orders count: {len(orders_state.orders)}")
    
    # Mock get_state method for testing
    def mock_get_state(state_class):
        if state_class == DashboardState:
            return dashboard_state
        elif state_class == OrdersState:
            return orders_state
        return None
    
    ws_state.get_state = mock_get_state
    
    # Test connection status indicators
    ws_state.connection_status = "connected"
    print(f"Connected indicator color: {ws_state.get_connection_indicator_color()}")
    print(f"Connected indicator text: {ws_state.get_connection_indicator_text()}")
    
    ws_state.connection_status = "error"
    print(f"Error indicator color: {ws_state.get_connection_indicator_color()}")
    print(f"Error indicator text: {ws_state.get_connection_indicator_text()}")
    
    # Test order handling
    order_data = {
        "order": {
            "id": "demo_order_002",
            "order_number": "ORD-240916-STATE",
            "table_number": 12,
            "customer_name": "State Demo Customer",
            "customer_phone": "+1987654321",
            "total_price": 42.50,
            "order_status": "pending",
            "created_at": "2024-09-16T09:20:00Z",
            "items": [{"id": "item1"}, {"id": "item2"}],
            "estimated_time": 20,
            "payment_method": "cash"
        }
    }
    
    print("Processing new order...")
    ws_state._handle_order_created(order_data)
    
    print(f"Dashboard orders after creation: {len(dashboard_state.recent_orders)}")
    print(f"Orders count after creation: {len(orders_state.orders)}")
    
    if dashboard_state.recent_orders:
        print(f"Latest order: {dashboard_state.recent_orders[0]['order_number']}")
    
    # Test status change
    status_change_data = {
        "order": {
            "id": "demo_order_002",
            "order_status": "completed"
        }
    }
    
    print("Processing status change...")
    ws_state._handle_order_status_changed(status_change_data)
    
    if dashboard_state.recent_orders:
        print(f"Updated order status: {dashboard_state.recent_orders[0]['status']}")
    
    print("State integration demo completed!")


async def main():
    """Run all demos"""
    print("🚀 Real-time WebSocket Integration Demo")
    print("=" * 50)
    
    try:
        await demo_backend_websocket()
        await demo_frontend_websocket()
        await demo_state_integration()
        
        print("\n✅ All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())