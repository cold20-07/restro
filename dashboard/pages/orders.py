"""Orders management page for restaurant dashboard"""

import reflex as rx
from typing import List, Dict, Any, Optional
from dashboard.state import OrdersState, WebSocketState, AuthState
from dashboard.components import status_badge, loading_spinner, empty_state, error_message, real_time_indicator, connection_status_indicator


def orders_page() -> rx.Component:
    """Orders management page with filtering and status controls"""
    from dashboard.layout import base_layout
    
    # Set current page for navigation
    from dashboard.state import NavigationState
    NavigationState.current_page = "orders"
    
    return base_layout(
        content=rx.vstack(
            # Load orders data on page mount
            rx.script("window.addEventListener('load', () => { OrdersState.load_orders(); });"),
            
            # Real-time connection status
            orders_connection_status(),
            
            # Filters and search
            orders_filters(),
            
            # Orders table
            orders_table(),
            
            # Pagination
            orders_pagination(),
            
            spacing="6",
            width="100%"
        ),
        page_title="Orders Management"
    )


def orders_filters() -> rx.Component:
    """Filters and search controls for orders"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                # Search input
                rx.input(
                    placeholder="Search by order number, customer name, or phone...",
                    size="3",
                    width="400px"
                ),
                
                # Status filter
                rx.select(
                    ["All Orders", "Pending", "Confirmed", "In Progress", "Ready", "Completed", "Canceled"],
                    placeholder="Filter by status",
                    size="3"
                ),
                
                # Date range filter
                rx.select(
                    ["Today", "Yesterday", "Last 7 days", "Last 30 days", "This month"],
                    placeholder="Date range",
                    size="3"
                ),
                
                spacing="4",
                align="center"
            ),
            
            # Quick stats
            rx.hstack(
                quick_stat("Total Orders", "127"),
                quick_stat("Pending", "8"),
                quick_stat("In Progress", "12"),
                quick_stat("Completed Today", "85"),
                spacing="6"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def orders_connection_status() -> rx.Component:
    """Orders page connection status"""
    return rx.card(
        rx.hstack(
            rx.hstack(
                rx.icon(tag="wifi", size=18, color="#FF6B35"),
                rx.text("Live Order Updates", font_weight="medium", color="gray.900"),
                spacing="2",
                align="center"
            ),
            
            rx.spacer(),
            
            connection_status_indicator(),
            
            rx.cond(
                WebSocketState.connection_error != "",
                rx.button(
                    rx.icon(tag="refresh_cw", size=14),
                    "Reconnect",
                    size="2",
                    variant="outline",
                    color_scheme="orange",
                    on_click=lambda: WebSocketState.connect_websocket(
                        AuthState.access_token, 
                        AuthState.restaurant_id
                    )
                )
            ),
            
            justify="between",
            align="center",
            width="100%"
        ),
        padding="3",
        width="100%",
        background=rx.cond(
            WebSocketState.connection_status == "connected",
            "green.25",
            "yellow.25"
        )
    )


def quick_stat(label: str, value) -> rx.Component:
    """Quick stat component for orders overview"""
    return rx.vstack(
        rx.text(value, font_size="xl", font_weight="bold", color="gray.900"),
        rx.text(label, font_size="sm", color="gray.600"),
        spacing="1",
        align="center"
    )


def orders_table() -> rx.Component:
    """Main orders table with status controls"""
    return rx.card(
        rx.vstack(
            # Table header
            rx.hstack(
                rx.hstack(
                    rx.text("Recent Orders", font_size="lg", font_weight="semibold", color="gray.900"),
                    real_time_indicator(),
                    spacing="3",
                    align="center"
                ),
                rx.text("Showing 5 orders", color="gray.500", font_size="sm"),
                justify="between",
                width="100%"
            ),
            
            # Loading/Error states
            rx.cond(
                OrdersState.is_loading,
                rx.center(
                    loading_spinner("lg"),
                    height="300px",
                    width="100%"
                ),
                rx.cond(
                    OrdersState.error_message != "",
                    rx.center(
                        error_message(OrdersState.error_message),
                        height="300px",
                        width="100%"
                    ),
                    rx.cond(
                        False,
                        rx.center(
                            empty_state(
                                "inbox",
                                "No orders found",
                                "Orders matching your filters will appear here"
                            ),
                            height="300px",
                            width="100%"
                        ),
                        # Orders table content
                        rx.vstack(
                            # Table header row
                            rx.hstack(
                                rx.text("Order #", font_size="sm", font_weight="medium", color="gray.600", width="15%"),
                                rx.text("Table", font_size="sm", font_weight="medium", color="gray.600", width="8%"),
                                rx.text("Customer", font_size="sm", font_weight="medium", color="gray.600", width="20%"),
                                rx.text("Items", font_size="sm", font_weight="medium", color="gray.600", width="12%"),
                                rx.text("Total", font_size="sm", font_weight="medium", color="gray.600", width="12%"),
                                rx.text("Status", font_size="sm", font_weight="medium", color="gray.600", width="15%"),
                                rx.text("Time", font_size="sm", font_weight="medium", color="gray.600", width="12%"),
                                rx.text("Actions", font_size="sm", font_weight="medium", color="gray.600", width="6%"),
                                spacing="2",
                                width="100%",
                                padding_y="3",
                                border_bottom="1px solid #E2E8F0"
                            ),
                            
                            # Table rows - static data for demo
                            rx.vstack(
                                simple_order_row_static("ORD-A1B2", "5", "John Doe", "3", "$45.50", "completed"),
                                simple_order_row_static("ORD-C3D4", "12", "Jane Smith", "2", "$32.75", "in_progress"),
                                simple_order_row_static("ORD-E5F6", "8", "Mike Johnson", "4", "$67.25", "ready"),
                                simple_order_row_static("ORD-G7H8", "3", "Sarah Wilson", "2", "$28.50", "pending"),
                                simple_order_row_static("ORD-I9J0", "15", "David Brown", "3", "$52.00", "confirmed"),
                                spacing="0",
                                width="100%"
                            ),
                            
                            spacing="0",
                            width="100%"
                        )
                    )
                )
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def simple_order_row_static(order_number: str, table: str, customer: str, items: str, total: str, status: str) -> rx.Component:
    """Simple static order row for demo"""
    status_colors = {
        "pending": "yellow",
        "confirmed": "blue", 
        "in_progress": "orange",
        "ready": "purple",
        "completed": "green",
        "canceled": "red"
    }
    
    return rx.hstack(
        # Order number
        rx.text(order_number, font_size="sm", color="gray.900", font_weight="medium", width="15%"),
        
        # Table number
        rx.badge(f"T{table}", color_scheme="blue", size="2", width="8%"),
        
        # Customer info
        rx.vstack(
            rx.text(customer, font_size="sm", color="gray.900", font_weight="medium"),
            rx.text("+1234567890", font_size="xs", color="gray.500"),
            spacing="1",
            align="start",
            width="20%"
        ),
        
        # Items count
        rx.text(f"{items} items", font_size="sm", color="gray.600", width="12%"),
        
        # Total
        rx.text(total, font_size="sm", font_weight="medium", color="gray.900", width="12%"),
        
        # Status badge
        rx.badge(
            status.replace("_", " ").title(),
            color_scheme=status_colors.get(status, "gray"),
            size="2",
            width="15%"
        ),
        
        # Time
        rx.text("14:30", font_size="sm", color="gray.600", width="12%"),
        
        # Actions menu
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon(tag="more_horizontal", size=16),
                    size="1",
                    variant="ghost",
                    color_scheme="gray"
                )
            ),
            rx.menu.content(
                rx.menu.item("View Details"),
                rx.menu.item("Update Status"),
                rx.menu.item("Print Receipt")
            ),
            width="6%"
        ),
        
        spacing="2",
        width="100%",
        padding_y="3",
        border_bottom="1px solid #F7FAFC",
        _hover={"background": "#F7FAFC"},
        align="center"
    )


def order_table_row(order) -> rx.Component:
    """Individual order row with status controls"""
    return rx.hstack(
        # Order number
        rx.text(order["order_number"], font_size="sm", color="gray.900", font_weight="medium", width="15%"),
        
        # Table number
        rx.badge(f"T{order['table_number']}", color_scheme="blue", size="2", width="8%"),
        
        # Customer info
        rx.vstack(
            rx.text(order["customer_name"], font_size="sm", color="gray.900", font_weight="medium"),
            rx.text(order["customer_phone"], font_size="xs", color="gray.500"),
            spacing="1",
            align="start",
            width="20%"
        ),
        
        # Items count
        rx.text(f"{order['items_count']} items", font_size="sm", color="gray.600", width="12%"),
        
        # Total
        rx.text(f"${order['total']:.2f}", font_size="sm", font_weight="medium", color="gray.900", width="12%"),
        
        # Status with update controls
        rx.vstack(
            status_badge(order["status"]),
            rx.cond(
                order["status"] != "completed",
                status_update_menu(order["id"], order["status"]),
                rx.box()
            ),
            spacing="1",
            width="15%"
        ),
        
        # Time
        rx.text(order["created_at"], font_size="sm", color="gray.600", width="12%"),
        
        # Actions menu
        order_actions_menu(order["id"]),
        
        spacing="2",
        width="100%",
        padding_y="3",
        border_bottom="1px solid #F7FAFC",
        _hover={"background": "#F7FAFC"},
        align="center"
    )


def status_update_menu(order_id: str, current_status: str) -> rx.Component:
    """Status update dropdown menu"""
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon(tag="chevron_down", size=12),
                size="1",
                variant="ghost",
                color_scheme="gray"
            )
        ),
        rx.menu.content(
            rx.cond(
                current_status == "pending",
                rx.menu.item(
                    "Confirm Order",
                    on_click=lambda: OrdersState.update_order_status(order_id, "confirmed")
                )
            ),
            rx.cond(
                current_status == "confirmed",
                rx.menu.item(
                    "Start Preparing",
                    on_click=lambda: OrdersState.update_order_status(order_id, "in_progress")
                )
            ),
            rx.cond(
                current_status == "in_progress",
                rx.menu.item(
                    "Mark Ready",
                    on_click=lambda: OrdersState.update_order_status(order_id, "ready")
                )
            ),
            rx.cond(
                current_status == "ready",
                rx.menu.item(
                    "Complete Order",
                    on_click=lambda: OrdersState.update_order_status(order_id, "completed")
                )
            ),
            rx.menu.separator(),
            rx.menu.item(
                "Cancel Order",
                color="red",
                on_click=lambda: OrdersState.update_order_status(order_id, "canceled")
            )
        )
    )


def order_actions_menu(order_id: str) -> rx.Component:
    """Order actions dropdown menu"""
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon(tag="more_horizontal", size=16),
                size="1",
                variant="ghost",
                color_scheme="gray"
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon(tag="eye", size=14),
                "View Details",
                on_click=lambda: OrdersState.view_order_details(order_id)
            ),
            rx.menu.item(
                rx.icon(tag="printer", size=14),
                "Print Receipt"
            ),
            rx.menu.item(
                rx.icon(tag="phone", size=14),
                "Call Customer"
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon(tag="trash_2", size=14),
                "Delete Order",
                color="red"
            )
        ),
        width="6%"
    )


def orders_pagination() -> rx.Component:
    """Pagination controls for orders table"""
    return rx.hstack(
        rx.text(
            "Showing 1 to 10 of 50 orders",
            font_size="sm",
            color="gray.600"
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon(tag="chevron_left", size=16),
                size="2",
                variant="outline"
            ),
            rx.text("Page 1", font_size="sm", color="gray.600"),
            rx.button(
                rx.icon(tag="chevron_right", size=16),
                size="2",
                variant="outline"
            ),
            spacing="2"
        ),
        justify="between",
        width="100%",
        padding_top="4"
    )