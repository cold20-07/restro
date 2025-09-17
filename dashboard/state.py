"""Global state management for the restaurant dashboard"""

import reflex as rx
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, date, timedelta
import asyncio
import logging
from dashboard.websocket_client import get_websocket_client

logger = logging.getLogger(__name__)


class WebSocketState(rx.State):
    """State management for WebSocket real-time connections"""
    
    is_connected: bool = False
    is_connecting: bool = False
    connection_error: str = ""
    last_message_time: str = ""
    reconnect_attempts: int = 0
    
    # Connection status indicators
    connection_status: str = "disconnected"  # disconnected, connecting, connected, error
    
    async def connect_websocket(self, access_token: str, restaurant_id: str):
        """Connect to WebSocket for real-time updates"""
        if self.is_connected or self.is_connecting:
            return
        
        self.is_connecting = True
        self.connection_status = "connecting"
        self.connection_error = ""
        
        try:
            ws_client = get_websocket_client()
            ws_client.set_auth(access_token, restaurant_id)
            
            # Set event handlers
            ws_client.set_event_handlers(
                on_order_created=self._handle_order_created,
                on_order_status_changed=self._handle_order_status_changed,
                on_connection_established=self._handle_connection_established,
                on_connection_lost=self._handle_connection_lost,
                on_error=self._handle_connection_error
            )
            
            # Attempt connection
            success = await ws_client.connect()
            
            if success:
                self.is_connected = True
                self.is_connecting = False
                self.connection_status = "connected"
                self.reconnect_attempts = 0
                logger.info("WebSocket connected successfully")
            else:
                self.is_connecting = False
                self.connection_status = "error"
                self.connection_error = "Failed to connect"
                
        except Exception as e:
            self.is_connecting = False
            self.is_connected = False
            self.connection_status = "error"
            self.connection_error = f"Connection failed: {str(e)}"
            logger.error(f"WebSocket connection error: {e}")
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        try:
            ws_client = get_websocket_client()
            await ws_client.disconnect()
            
            self.is_connected = False
            self.is_connecting = False
            self.connection_status = "disconnected"
            self.connection_error = ""
            
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {e}")
    
    def _handle_order_created(self, data: Dict[str, Any]):
        """Handle new order WebSocket message"""
        try:
            order = data.get("order", {})
            self.last_message_time = datetime.now().isoformat()
            
            # Update dashboard state with new order
            dashboard_state = self.get_state(DashboardState)
            if dashboard_state:
                # Add to recent orders list
                new_order = {
                    "id": order.get("id"),
                    "order_number": order.get("order_number"),
                    "table_number": order.get("table_number"),
                    "customer_name": order.get("customer_name"),
                    "customer_phone": order.get("customer_phone"),
                    "total": order.get("total_price"),
                    "status": order.get("order_status"),
                    "created_at": order.get("created_at"),
                    "items_count": len(order.get("items", [])),
                    "estimated_time": order.get("estimated_time"),
                    "payment_method": order.get("payment_method")
                }
                
                # Insert at beginning of recent orders
                dashboard_state.recent_orders.insert(0, new_order)
                
                # Keep only last 10 orders
                if len(dashboard_state.recent_orders) > 10:
                    dashboard_state.recent_orders = dashboard_state.recent_orders[:10]
                
                # Update metrics
                dashboard_state.total_orders += 1
                dashboard_state.total_revenue += order.get("total_price", 0)
                
                # Trigger UI update by modifying state
                pass
            
            # Update orders page state if available
            orders_state = self.get_state(OrdersState)
            if orders_state:
                orders_state.orders.insert(0, new_order)
                if len(orders_state.orders) > orders_state.orders_per_page:
                    orders_state.orders = orders_state.orders[:orders_state.orders_per_page]
                orders_state.total_orders += 1
            
            logger.info(f"Processed new order: {order.get('id')}")
            
        except Exception as e:
            logger.error(f"Error handling order created: {e}")
    
    def _handle_order_status_changed(self, data: Dict[str, Any]):
        """Handle order status change WebSocket message"""
        try:
            order = data.get("order", {})
            order_id = order.get("id")
            new_status = order.get("order_status")
            self.last_message_time = datetime.now().isoformat()
            
            # Update dashboard state
            dashboard_state = self.get_state(DashboardState)
            if dashboard_state:
                # Update order in recent orders
                for i, existing_order in enumerate(dashboard_state.recent_orders):
                    if existing_order.get("id") == order_id:
                        dashboard_state.recent_orders[i]["status"] = new_status
                        break
                
                # Trigger UI update by modifying state
                pass
            
            # Update orders page state
            orders_state = self.get_state(OrdersState)
            if orders_state:
                # Update order in orders list
                for i, existing_order in enumerate(orders_state.orders):
                    if existing_order.get("id") == order_id:
                        orders_state.orders[i]["status"] = new_status
                        break
                
                # Update selected order if it matches
                if orders_state.selected_order and orders_state.selected_order.get("id") == order_id:
                    orders_state.selected_order["status"] = new_status
            
            logger.info(f"Updated order status: {order_id} -> {new_status}")
            
        except Exception as e:
            logger.error(f"Error handling order status change: {e}")
    
    def _handle_connection_established(self, data: Dict[str, Any]):
        """Handle WebSocket connection established"""
        self.is_connected = True
        self.is_connecting = False
        self.connection_status = "connected"
        self.connection_error = ""
        self.last_message_time = datetime.now().isoformat()
        logger.info("WebSocket connection established")
    
    def _handle_connection_lost(self):
        """Handle WebSocket connection lost"""
        self.is_connected = False
        self.connection_status = "disconnected"
        self.connection_error = "Connection lost"
        logger.warning("WebSocket connection lost")
    
    def _handle_connection_error(self, error: str):
        """Handle WebSocket connection error"""
        self.is_connected = False
        self.is_connecting = False
        self.connection_status = "error"
        self.connection_error = error
        logger.error(f"WebSocket error: {error}")
    
    def get_connection_indicator_color(self) -> str:
        """Get color for connection status indicator"""
        status_colors = {
            "connected": "green",
            "connecting": "yellow",
            "disconnected": "gray",
            "error": "red"
        }
        return status_colors.get(self.connection_status, "gray")
    
    def get_connection_indicator_text(self) -> str:
        """Get text for connection status indicator"""
        status_texts = {
            "connected": "Connected",
            "connecting": "Connecting...",
            "disconnected": "Disconnected",
            "error": "Connection Error"
        }
        return status_texts.get(self.connection_status, "Unknown")
    
    @property
    def connection_indicator_color(self) -> str:
        """Get color for connection status indicator"""
        return self.get_connection_indicator_color()
    
    @property
    def connection_indicator_text(self) -> str:
        """Get text for connection status indicator"""
        return self.get_connection_indicator_text()


class NavigationState(rx.State):
    """State for navigation and routing"""
    
    current_page: str = "dashboard"
    sidebar_collapsed: bool = False
    
    def set_page(self, page: str):
        """Set the current page"""
        self.current_page = page
        return rx.redirect(f"/{page}")
    
    def toggle_sidebar(self):
        """Toggle sidebar collapsed state"""
        self.sidebar_collapsed = not self.sidebar_collapsed


class AuthState(rx.State):
    """Authentication state management"""
    
    is_authenticated: bool = False
    restaurant_id: str = ""
    restaurant_name: str = ""
    access_token: str = ""
    user_email: str = ""
    user_id: str = ""
    
    # Session management
    token_expires_at: str = ""
    last_activity: str = ""
    
    # Form state for login/registration
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    
    # UI state
    is_loading: bool = False
    is_checking_auth: bool = False
    error_message: str = ""
    success_message: str = ""
    
    def set_email(self, email: str):
        """Set email field"""
        self.email = email
        self.error_message = ""
    
    def set_password(self, password: str):
        """Set password field"""
        self.password = password
        self.error_message = ""
    
    def set_confirm_password(self, confirm_password: str):
        """Set confirm password field"""
        self.confirm_password = confirm_password
        self.error_message = ""
    
    def set_restaurant_name(self, name: str):
        """Set restaurant name field"""
        self.restaurant_name = name
        self.error_message = ""
    
    async def login(self):
        """Handle user login"""
        if not self.email or not self.password:
            self.error_message = "Email and password are required"
            return
        
        self.is_loading = True
        self.error_message = ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={
                        "email": self.email,
                        "password": self.password
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    self.restaurant_id = data["restaurant_id"]
                    self.user_email = self.email
                    self.is_authenticated = True
                    self.last_activity = datetime.now().isoformat()
                    
                    # Connect to WebSocket for real-time updates
                    websocket_state = self.get_state(WebSocketState)
                    if websocket_state:
                        await websocket_state.connect_websocket(self.access_token, self.restaurant_id)
                    
                    # Clear form fields
                    self.email = ""
                    self.password = ""
                    
                    return rx.redirect("/dashboard")
                else:
                    error_data = response.json()
                    self.error_message = error_data.get("message", "Login failed")
                    
        except httpx.TimeoutException:
            self.error_message = "Login request timed out. Please try again."
        except httpx.ConnectError:
            self.error_message = "Unable to connect to server. Please check your connection."
        except Exception as e:
            self.error_message = f"Login failed: {str(e)}"
        finally:
            self.is_loading = False
    
    async def register(self):
        """Handle user registration"""
        if not self.email or not self.password or not self.restaurant_name:
            self.error_message = "All fields are required"
            return
        
        if len(self.password) < 8:
            self.error_message = "Password must be at least 8 characters long"
            return
        
        if self.password != self.confirm_password:
            self.error_message = "Passwords do not match"
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/register",
                    json={
                        "email": self.email,
                        "password": self.password,
                        "restaurant_name": self.restaurant_name
                    },
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    data = response.json()
                    self.success_message = "Account created successfully! You can now log in."
                    
                    # Clear form fields
                    self.email = ""
                    self.password = ""
                    self.confirm_password = ""
                    self.restaurant_name = ""
                    
                    # Redirect to login after a short delay
                    await asyncio.sleep(2)
                    return rx.redirect("/login")
                else:
                    error_data = response.json()
                    self.error_message = error_data.get("message", "Registration failed")
                    
        except httpx.TimeoutException:
            self.error_message = "Registration request timed out. Please try again."
        except httpx.ConnectError:
            self.error_message = "Unable to connect to server. Please check your connection."
        except Exception as e:
            self.error_message = f"Registration failed: {str(e)}"
        finally:
            self.is_loading = False

    async def logout(self):
        """Handle user logout"""
        try:
            # Call logout API endpoint if token exists
            if self.access_token:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "http://localhost:8000/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        timeout=5.0
                    )
        except Exception as e:
            print(f"Logout API call failed: {e}")
        finally:
            # Disconnect WebSocket
            try:
                websocket_state = self.get_state(WebSocketState)
                if websocket_state:
                    await websocket_state.disconnect_websocket()
            except Exception as e:
                print(f"WebSocket disconnect failed: {e}")
            
            # Clear all auth state regardless of API call result
            self.is_authenticated = False
            self.access_token = ""
            self.user_email = ""
            self.user_id = ""
            self.restaurant_id = ""
            self.restaurant_name = ""
            self.token_expires_at = ""
            self.last_activity = ""
            self.email = ""
            self.password = ""
            self.confirm_password = ""
            self.error_message = ""
            self.success_message = ""
            
            return rx.redirect("/login")
    
    async def verify_token(self) -> bool:
        """Verify if current token is still valid"""
        if not self.access_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/verify-token",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    # Update last activity
                    self.last_activity = datetime.now().isoformat()
                    return True
                else:
                    # Token is invalid, clear auth state
                    await self.logout()
                    return False
                    
        except Exception as e:
            print(f"Token verification failed: {e}")
            return False
    
    async def get_user_info(self):
        """Get current user information"""
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.user_id = user_data["user"]["id"]
                    self.user_email = user_data["user"]["email"]
                    self.restaurant_id = user_data["restaurant_id"]
                    return user_data
                else:
                    await self.logout()
                    return None
                    
        except Exception as e:
            print(f"Failed to get user info: {e}")
            return None
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        return self.is_authenticated and bool(self.access_token)
    
    def require_auth(self):
        """Redirect to login if not authenticated"""
        if not self.is_session_valid():
            return rx.redirect("/login")
        return None
    
    async def check_auth_status(self):
        """Check authentication status on app initialization"""
        self.is_checking_auth = True
        
        try:
            # Check if we have a stored token (in real app, this would be from localStorage/cookies)
            if self.access_token:
                is_valid = await self.verify_token()
                if is_valid:
                    await self.get_user_info()
                else:
                    self.is_authenticated = False
            else:
                self.is_authenticated = False
        except Exception as e:
            print(f"Auth check failed: {e}")
            self.is_authenticated = False
        finally:
            self.is_checking_auth = False


class OrdersState(rx.State):
    """State management for the orders page"""
    
    # Orders data
    orders: List[Dict[str, Any]] = []
    selected_order: Optional[Dict[str, Any]] = None
    total_orders: int = 0
    orders_per_page: int = 20
    current_page: int = 1
    
    # Filters
    status_filter: str = "all"
    search_query: str = ""
    date_filter: str = "today"
    
    # Loading and error states
    is_loading: bool = False
    error_message: str = ""
    
    async def load_orders(self):
        """Load orders from API"""
        self.is_loading = True
        self.error_message = ""
        
        try:
            # Mock data for now - in real implementation, this would call the API
            self.orders = [
                {
                    "id": "ord_001",
                    "order_number": "ORD-240114-A1B2",
                    "table_number": 5,
                    "customer_name": "John Doe",
                    "customer_phone": "+1234567890",
                    "total": 45.50,
                    "status": "completed",
                    "created_at": "2024-01-14T14:30:00",
                    "items_count": 3,
                    "estimated_time": 15,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_002", 
                    "order_number": "ORD-240114-C3D4",
                    "table_number": 12,
                    "customer_name": "Jane Smith",
                    "customer_phone": "+1234567891",
                    "total": 32.75,
                    "status": "in_progress",
                    "created_at": "2024-01-14T14:25:00",
                    "items_count": 2,
                    "estimated_time": 12,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_003",
                    "order_number": "ORD-240114-E5F6",
                    "table_number": 8,
                    "customer_name": "Mike Johnson",
                    "customer_phone": "+1234567892",
                    "total": 67.25,
                    "status": "ready",
                    "created_at": "2024-01-14T14:20:00",
                    "items_count": 4,
                    "estimated_time": 18,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_004",
                    "order_number": "ORD-240114-G7H8",
                    "table_number": 3,
                    "customer_name": "Sarah Wilson",
                    "customer_phone": "+1234567893",
                    "total": 28.50,
                    "status": "pending",
                    "created_at": "2024-01-14T14:15:00",
                    "items_count": 2,
                    "estimated_time": 10,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_005",
                    "order_number": "ORD-240114-I9J0",
                    "table_number": 15,
                    "customer_name": "David Brown",
                    "customer_phone": "+1234567894",
                    "total": 52.00,
                    "status": "confirmed",
                    "created_at": "2024-01-14T14:10:00",
                    "items_count": 3,
                    "estimated_time": 20,
                    "payment_method": "cash"
                }
            ]
            self.total_orders = len(self.orders)
            
        except Exception as e:
            self.error_message = f"Failed to load orders: {str(e)}"
        finally:
            self.is_loading = False
    
    async def update_order_status(self, order_id: str, new_status: str):
        """Update order status"""
        try:
            # Find and update the order
            for i, order in enumerate(self.orders):
                if order["id"] == order_id:
                    self.orders[i]["status"] = new_status
                    break
            
            # Update selected order if it matches
            if self.selected_order and self.selected_order["id"] == order_id:
                self.selected_order["status"] = new_status
            
            # In real implementation, this would call the API
            # await self.api_client.update_order_status(order_id, new_status)
            
        except Exception as e:
            self.error_message = f"Failed to update order status: {str(e)}"
    
    def view_order_details(self, order_id: str):
        """View order details"""
        for order in self.orders:
            if order["id"] == order_id:
                self.selected_order = order
                break
    
    def set_status_filter(self, status: str):
        """Set status filter"""
        self.status_filter = status
        # In real implementation, this would trigger a new API call
    
    def set_search_query(self, query: str):
        """Set search query"""
        self.search_query = query
        # In real implementation, this would trigger a new API call
    
    def set_date_filter(self, date_filter: str):
        """Set date filter"""
        self.date_filter = date_filter
        # In real implementation, this would trigger a new API call


class DashboardState(rx.State):
    """State management for the main dashboard"""
    
    # Dashboard metrics
    total_revenue: float = 4287.50
    total_orders: int = 127
    total_customers: int = 89
    average_rating: float = 4.8
    
    # Revenue chart data
    revenue_period: str = "7d"
    revenue_data: List[Dict[str, Any]] = []
    
    # Order status data
    order_status_data: Dict[str, int] = {
        "completed": 85,
        "in_progress": 12,
        "pending": 8
    }
    
    # Recent orders
    recent_orders: List[Dict[str, Any]] = []
    
    # Popular items
    popular_items: List[Dict[str, Any]] = []
    
    # Table status data
    table_status: Dict[str, Dict[str, Any]] = {}
    
    # Loading states
    is_loading_analytics: bool = False
    is_loading_orders: bool = False
    is_loading_tables: bool = False
    
    # Error states
    orders_error: str = ""
    analytics_error: str = ""
    tables_error: str = ""
    
    async def load_dashboard_data(self):
        """Load all dashboard data from API"""
        self.is_loading_analytics = True
        self.is_loading_orders = True
        self.is_loading_tables = True
        
        # Clear previous errors
        self.orders_error = ""
        self.analytics_error = ""
        self.tables_error = ""
        
        try:
            await self.load_analytics_data()
            await self.load_recent_orders()
            await self.load_popular_items()
            await self.load_table_status()
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
        finally:
            self.is_loading_analytics = False
            self.is_loading_orders = False
            self.is_loading_tables = False
    
    async def load_analytics_data(self):
        """Load analytics data from API"""
        # Mock data that would come from /api/v1/analytics/quick-metrics
        self.total_revenue = 4287.50
        self.total_orders = 127
        self.total_customers = 89
        self.average_rating = 4.8
        
        # Mock revenue chart data
        self.revenue_data = [
            {"date": "2024-01-08", "revenue": 580.25, "orders": 18},
            {"date": "2024-01-09", "revenue": 720.50, "orders": 23},
            {"date": "2024-01-10", "revenue": 650.75, "orders": 21},
            {"date": "2024-01-11", "revenue": 890.00, "orders": 28},
            {"date": "2024-01-12", "revenue": 760.25, "orders": 24},
            {"date": "2024-01-13", "revenue": 920.50, "orders": 29},
            {"date": "2024-01-14", "revenue": 765.25, "orders": 25},
        ]
        
        # Mock order status data
        self.order_status_data = {
            "completed": 85,
            "in_progress": 12,
            "pending": 8
        }
    
    async def load_recent_orders(self):
        """Load recent orders data"""
        try:
            # Mock data that would come from orders API
            self.recent_orders = [
                {
                    "id": "ord_001",
                    "order_number": "ORD-240114-A1B2",
                    "table_number": 5,
                    "customer_name": "John Doe",
                    "customer_phone": "+1234567890",
                    "total": 45.50,
                    "status": "completed",
                    "created_at": "2024-01-14T14:30:00",
                    "items_count": 3,
                    "estimated_time": 15,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_002", 
                    "order_number": "ORD-240114-C3D4",
                    "table_number": 12,
                    "customer_name": "Jane Smith",
                    "customer_phone": "+1234567891",
                    "total": 32.75,
                    "status": "in_progress",
                    "created_at": "2024-01-14T14:25:00",
                    "items_count": 2,
                    "estimated_time": 12,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_003",
                    "order_number": "ORD-240114-E5F6",
                    "table_number": 8,
                    "customer_name": "Mike Johnson",
                    "customer_phone": "+1234567892",
                    "total": 67.25,
                    "status": "ready",
                    "created_at": "2024-01-14T14:20:00",
                    "items_count": 4,
                    "estimated_time": 18,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_004",
                    "order_number": "ORD-240114-G7H8",
                    "table_number": 3,
                    "customer_name": "Sarah Wilson",
                    "customer_phone": "+1234567893",
                    "total": 28.50,
                    "status": "pending",
                    "created_at": "2024-01-14T14:15:00",
                    "items_count": 2,
                    "estimated_time": 10,
                    "payment_method": "cash"
                },
                {
                    "id": "ord_005",
                    "order_number": "ORD-240114-I9J0",
                    "table_number": 15,
                    "customer_name": "David Brown",
                    "customer_phone": "+1234567894",
                    "total": 52.00,
                    "status": "confirmed",
                    "created_at": "2024-01-14T14:10:00",
                    "items_count": 3,
                    "estimated_time": 20,
                    "payment_method": "cash"
                }
            ]
        except Exception as e:
            self.orders_error = f"Failed to load recent orders: {str(e)}"
    
    async def load_popular_items(self):
        """Load popular items data"""
        try:
            # Mock data that would come from /api/v1/analytics/best-sellers
            self.popular_items = [
                {
                    "id": "item_001",
                    "name": "Margherita Pizza",
                    "sales_count": 45,
                    "revenue": 675.00,
                    "percentage": 35.4,
                    "category": "Pizza",
                    "price": 15.00,
                    "avg_rating": 4.8,
                    "trend": "up"
                },
                {
                    "id": "item_002",
                    "name": "Caesar Salad",
                    "sales_count": 32,
                    "revenue": 384.00,
                    "percentage": 25.2,
                    "category": "Salads",
                    "price": 12.00,
                    "avg_rating": 4.6,
                    "trend": "up"
                },
                {
                    "id": "item_003",
                    "name": "Grilled Chicken",
                    "sales_count": 28,
                    "revenue": 560.00,
                    "percentage": 22.0,
                    "category": "Main Course",
                    "price": 20.00,
                    "avg_rating": 4.7,
                    "trend": "stable"
                },
                {
                    "id": "item_004",
                    "name": "Pasta Carbonara",
                    "sales_count": 22,
                    "revenue": 330.00,
                    "percentage": 17.3,
                    "category": "Pasta",
                    "price": 15.00,
                    "avg_rating": 4.5,
                    "trend": "down"
                },
                {
                    "id": "item_005",
                    "name": "Fish & Chips",
                    "sales_count": 18,
                    "revenue": 270.00,
                    "percentage": 14.2,
                    "category": "Main Course",
                    "price": 15.00,
                    "avg_rating": 4.3,
                    "trend": "up"
                }
            ]
        except Exception as e:
            self.analytics_error = f"Failed to load popular items: {str(e)}"
    
    async def load_table_status(self):
        """Load table status data"""
        try:
            # Mock data that would come from table management API
            self.table_status = {
                "1": {"status": "available", "capacity": 2, "last_cleaned": "14:00"},
                "2": {"status": "occupied", "capacity": 4, "order_id": "ord_001", "occupied_since": "13:45"},
                "3": {"status": "occupied", "capacity": 2, "order_id": "ord_004", "occupied_since": "14:15"},
                "4": {"status": "available", "capacity": 6, "last_cleaned": "13:30"},
                "5": {"status": "occupied", "capacity": 4, "order_id": "ord_001", "occupied_since": "14:30"},
                "6": {"status": "reserved", "capacity": 2, "reserved_until": "15:00", "customer": "Alice"},
                "7": {"status": "available", "capacity": 4, "last_cleaned": "14:15"},
                "8": {"status": "occupied", "capacity": 6, "order_id": "ord_003", "occupied_since": "14:20"},
                "9": {"status": "out_of_service", "capacity": 2, "reason": "Maintenance"},
                "10": {"status": "available", "capacity": 4, "last_cleaned": "13:45"},
                "11": {"status": "available", "capacity": 2, "last_cleaned": "14:10"},
                "12": {"status": "occupied", "capacity": 4, "order_id": "ord_002", "occupied_since": "14:25"},
                "13": {"status": "available", "capacity": 6, "last_cleaned": "13:20"},
                "14": {"status": "reserved", "capacity": 4, "reserved_until": "15:30", "customer": "Bob"},
                "15": {"status": "occupied", "capacity": 2, "order_id": "ord_005", "occupied_since": "14:10"},
                "16": {"status": "available", "capacity": 4, "last_cleaned": "14:00"}
            }
        except Exception as e:
            self.tables_error = f"Failed to load table status: {str(e)}"
    
    def set_revenue_period(self, period: str):
        """Set the revenue chart time period"""
        self.revenue_period = period
        # In real implementation, this would trigger a new API call
        asyncio.create_task(self.load_analytics_data())
    
    async def update_order_status(self, order_id: str, new_status: str):
        """Update order status"""
        try:
            # Find and update the order in recent_orders
            for order in self.recent_orders:
                if order["id"] == order_id:
                    order["status"] = new_status
                    break
            
            # In real implementation, this would call the API
            # await api_client.put(f"/api/v1/orders/{order_id}", {"status": new_status})
            
        except Exception as e:
            print(f"Error updating order status: {e}")


class MenuState(rx.State):
    """State management for menu page"""
    
    menu_items: List[Dict[str, Any]] = []
    selected_item: Optional[Dict[str, Any]] = None
    is_loading: bool = False
    error_message: str = ""
    
    # Form state for adding/editing items
    form_name: str = ""
    form_description: str = ""
    form_price: str = ""
    form_category: str = ""
    form_is_available: bool = True
    form_image_url: str = ""
    is_editing: bool = False
    editing_item_id: str = ""
    
    # Filters
    filter_category: str = "all"
    filter_availability: str = "all"
    search_query: str = ""
    category_filter: str = "all"
    availability_filter: str = "all"
    show_item_modal: bool = False
    is_saving: bool = False
    
    async def load_menu_items(self):
        """Load menu items"""
        self.is_loading = True
        self.error_message = ""
        
        try:
            # Mock menu items - in real implementation, this would call the API
            self.menu_items = [
                {
                    "id": "item_001",
                    "name": "Margherita Pizza",
                    "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                    "price": 15.00,
                    "category": "Pizza",
                    "is_available": True,
                    "image_url": "/images/margherita.jpg",
                    "created_at": "2024-01-01T10:00:00"
                },
                {
                    "id": "item_002",
                    "name": "Caesar Salad",
                    "description": "Fresh romaine lettuce with Caesar dressing, croutons, and parmesan",
                    "price": 12.00,
                    "category": "Salads",
                    "is_available": True,
                    "image_url": "/images/caesar.jpg",
                    "created_at": "2024-01-01T10:00:00"
                },
                {
                    "id": "item_003",
                    "name": "Grilled Chicken",
                    "description": "Tender grilled chicken breast with herbs and spices",
                    "price": 20.00,
                    "category": "Main Course",
                    "is_available": True,
                    "image_url": "/images/chicken.jpg",
                    "created_at": "2024-01-01T10:00:00"
                },
                {
                    "id": "item_004",
                    "name": "Pasta Carbonara",
                    "description": "Creamy pasta with bacon, eggs, and parmesan cheese",
                    "price": 15.00,
                    "category": "Pasta",
                    "is_available": False,
                    "image_url": "/images/carbonara.jpg",
                    "created_at": "2024-01-01T10:00:00"
                },
                {
                    "id": "item_005",
                    "name": "Fish & Chips",
                    "description": "Beer-battered fish with crispy fries and tartar sauce",
                    "price": 15.00,
                    "category": "Main Course",
                    "is_available": True,
                    "image_url": "/images/fish.jpg",
                    "created_at": "2024-01-01T10:00:00"
                }
            ]
        except Exception as e:
            self.error_message = f"Failed to load menu items: {str(e)}"
        finally:
            self.is_loading = False
    
    def set_filter_category(self, category: str):
        """Set category filter"""
        self.filter_category = category
    
    def set_filter_availability(self, availability: str):
        """Set availability filter"""
        self.filter_availability = availability
    
    def get_filtered_items(self) -> List[Dict[str, Any]]:
        """Get filtered menu items"""
        filtered = self.menu_items
        
        if self.filter_category != "all":
            filtered = [item for item in filtered if item["category"] == self.filter_category]
        
        if self.filter_availability != "all":
            is_available = self.filter_availability == "available"
            filtered = [item for item in filtered if item["is_available"] == is_available]
        
        return filtered
    
    def start_add_item(self):
        """Start adding a new menu item"""
        self.is_editing = False
        self.editing_item_id = ""
        self.form_name = ""
        self.form_description = ""
        self.form_price = ""
        self.form_category = ""
        self.form_is_available = True
        self.form_image_url = ""
    
    def start_edit_item(self, item_id: str):
        """Start editing an existing menu item"""
        item = next((item for item in self.menu_items if item["id"] == item_id), None)
        if item:
            self.is_editing = True
            self.editing_item_id = item_id
            self.form_name = item["name"]
            self.form_description = item["description"]
            self.form_price = str(item["price"])
            self.form_category = item["category"]
            self.form_is_available = item["is_available"]
            self.form_image_url = item.get("image_url", "")
    
    async def save_menu_item(self):
        """Save menu item (add or update)"""
        try:
            if not self.form_name or not self.form_price:
                self.error_message = "Name and price are required"
                return
            
            item_data = {
                "name": self.form_name,
                "description": self.form_description,
                "price": float(self.form_price),
                "category": self.form_category,
                "is_available": self.form_is_available,
                "image_url": self.form_image_url
            }
            
            if self.is_editing:
                # Update existing item
                for i, item in enumerate(self.menu_items):
                    if item["id"] == self.editing_item_id:
                        self.menu_items[i].update(item_data)
                        break
            else:
                # Add new item
                new_item = {
                    "id": f"item_{len(self.menu_items) + 1:03d}",
                    "created_at": datetime.now().isoformat(),
                    **item_data
                }
                self.menu_items.append(new_item)
            
            # Clear form
            self.start_add_item()
            self.error_message = ""
            
        except ValueError:
            self.error_message = "Invalid price format"
        except Exception as e:
            self.error_message = f"Failed to save item: {str(e)}"
    
    async def delete_menu_item(self, item_id: str):
        """Delete a menu item"""
        try:
            self.menu_items = [item for item in self.menu_items if item["id"] != item_id]
            self.error_message = ""
        except Exception as e:
            self.error_message = f"Failed to delete item: {str(e)}"
    
    async def toggle_item_availability(self, item_id: str, is_available: bool = None):
        """Toggle menu item availability"""
        try:
            for item in self.menu_items:
                if item["id"] == item_id:
                    if is_available is not None:
                        item["is_available"] = is_available
                    else:
                        item["is_available"] = not item["is_available"]
                    break
        except Exception as e:
            self.error_message = f"Failed to update availability: {str(e)}"
    
    def set_search_query(self, query: str):
        """Set search query"""
        self.search_query = query
    
    def set_category_filter(self, category: str):
        """Set category filter"""
        self.category_filter = category
    
    def set_availability_filter(self, availability: str):
        """Set availability filter"""
        self.availability_filter = availability
    
    def open_add_item_modal(self):
        """Open modal for adding new item"""
        self.start_add_item()
        self.show_item_modal = True
    
    def open_edit_item_modal(self, item_id: str):
        """Open modal for editing item"""
        self.start_edit_item(item_id)
        self.show_item_modal = True
    
    def set_show_item_modal(self, show: bool):
        """Set modal visibility"""
        self.show_item_modal = show
    
    def set_form_name(self, name: str):
        """Set form name"""
        self.form_name = name
    
    def set_form_description(self, description: str):
        """Set form description"""
        self.form_description = description
    
    def set_form_price(self, price: str):
        """Set form price"""
        self.form_price = price
    
    def set_form_category(self, category: str):
        """Set form category"""
        self.form_category = category
    
    def set_form_image_url(self, url: str):
        """Set form image URL"""
        self.form_image_url = url
    
    def set_form_is_available(self, available: bool):
        """Set form availability"""
        self.form_is_available = available
    
    @property
    def filtered_menu_items(self) -> List[Dict[str, Any]]:
        """Get filtered menu items"""
        filtered = self.menu_items
        
        # Apply search filter
        if self.search_query:
            filtered = [
                item for item in filtered 
                if self.search_query.lower() in item["name"].lower() 
                or self.search_query.lower() in item["description"].lower()
            ]
        
        # Apply category filter
        if self.category_filter != "all":
            filtered = [item for item in filtered if item["category"].lower() == self.category_filter]
        
        # Apply availability filter
        if self.availability_filter != "all":
            is_available = self.availability_filter == "available"
            filtered = [item for item in filtered if item["is_available"] == is_available]
        
        return filtered
    
    @property
    def total_items(self) -> int:
        """Total number of menu items"""
        return len(self.menu_items)
    
    @property
    def available_items(self) -> int:
        """Number of available menu items"""
        return len([item for item in self.menu_items if item["is_available"]])
    
    @property
    def total_categories(self) -> int:
        """Number of unique categories"""
        categories = set(item["category"] for item in self.menu_items)
        return len(categories)