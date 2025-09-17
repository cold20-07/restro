"""Main dashboard page integrating all metric and chart components"""

import reflex as rx
from typing import List, Dict, Any
from dashboard.state import DashboardState, NavigationState, WebSocketState, AuthState
from dashboard.layout import base_layout, metric_grid, two_column_layout, content_card
from dashboard.components import loading_spinner, error_message, stat_card, progress_ring, real_time_indicator, connection_status_indicator


def dashboard_page() -> rx.Component:
    """Main dashboard page with integrated metrics, charts, and real-time data"""
    
    # Set current page for navigation
    NavigationState.current_page = "dashboard"
    
    return base_layout(
        content=rx.vstack(
            # Load dashboard data on page mount and connect WebSocket
            rx.script("""
                window.addEventListener('load', () => { 
                    DashboardState.load_dashboard_data();
                    // WebSocket connection is handled by AuthState.login()
                });
            """),
            
            # Connection status header
            dashboard_connection_status(),
            
            # Key metrics section
            dashboard_metrics(),
            
            # Charts and analytics section
            dashboard_charts(),
            
            # Recent activity section
            dashboard_activity(),
            
            # Table status section
            dashboard_table_status(),
            
            spacing="6",
            width="100%"
        ),
        page_title="Dashboard"
    )


def dashboard_metrics() -> rx.Component:
    """Key performance metrics cards"""
    return content_card(
        rx.cond(
            DashboardState.is_loading_analytics,
            rx.center(
                loading_spinner("lg"),
                height="120px",
                width="100%"
            ),
            rx.cond(
                DashboardState.analytics_error != "",
                rx.center(
                    error_message(DashboardState.analytics_error),
                    height="120px",
                    width="100%"
                ),
                metric_grid([
                    enhanced_metric_card(
                        "Total Revenue",
                        "$4,287.50",
                        "+12.5%",
                        "dollar_sign",
                        "green"
                    ),
                    enhanced_metric_card(
                        "Total Orders",
                        "127",
                        "+8.2%",
                        "shopping_cart",
                        "blue"
                    ),
                    enhanced_metric_card(
                        "Customers",
                        "89",
                        "+15.3%",
                        "users",
                        "purple"
                    ),
                    enhanced_metric_card(
                        "Avg Rating",
                        "4.8",
                        "+0.3",
                        "star",
                        "orange"
                    )
                ])
            )
        ),
        title="Key Metrics"
    )


def dashboard_connection_status() -> rx.Component:
    """Dashboard connection status header"""
    return rx.card(
        rx.hstack(
            rx.hstack(
                rx.icon(tag="activity", size=20, color="#FF6B35"),
                rx.text("Real-time Status", font_weight="semibold", color="gray.900"),
                spacing="2",
                align="center"
            ),
            
            rx.spacer(),
            
            connection_status_indicator(),
            
            rx.cond(
                WebSocketState.last_message_time != "",
                rx.text(
                    f"Last update: {WebSocketState.last_message_time}",
                    font_size="xs",
                    color="gray.500"
                )
            ),
            
            justify="between",
            align="center",
            width="100%"
        ),
        padding="4",
        width="100%",
        background=rx.cond(
            WebSocketState.connection_status == "connected",
            "green.50",
            rx.cond(
                WebSocketState.connection_status == "connecting",
                "yellow.50",
                "red.50"
            )
        ),
        border=rx.cond(
            WebSocketState.connection_status == "connected",
            "1px solid #10B981",
            rx.cond(
                WebSocketState.connection_status == "connecting",
                "1px solid #F59E0B",
                "1px solid #EF4444"
            )
        )
    )


def enhanced_metric_card(title: str, value: str, change: str, icon: str, color: str) -> rx.Component:
    """Enhanced metric card with improved styling"""
    change_color = "green.500" if change.startswith("+") else "red.500"
    change_icon = "trending_up" if change.startswith("+") else "trending_down"
    
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=20, color=f"{color}.500"),
                rx.hstack(
                    rx.icon(tag=change_icon, size=14, color=change_color),
                    rx.text(change, color=change_color, font_size="sm", font_weight="medium"),
                    spacing="1",
                    align="center"
                ),
                justify="between",
                width="100%"
            ),
            rx.text(value, font_size="2xl", font_weight="bold", color="gray.900"),
            rx.text(title, color="gray.600", font_size="sm"),
            spacing="2",
            align="start",
            width="100%"
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%",
        _hover={"box_shadow": "md", "transform": "translateY(-1px)", "transition": "all 0.2s"}
    )


def dashboard_charts() -> rx.Component:
    """Charts and analytics section"""
    return two_column_layout(
        # Revenue chart
        content_card(
            rx.vstack(
                rx.hstack(
                    rx.text("Revenue Overview", font_size="lg", font_weight="semibold", color="gray.900"),
                    rx.hstack(
                        period_button("7D", "7d"),
                        period_button("30D", "30d"),
                        period_button("90D", "90d"),
                        spacing="1"
                    ),
                    justify="between",
                    width="100%"
                ),
                
                # Revenue chart placeholder
                rx.box(
                    rx.vstack(
                        rx.icon(tag="trending_up", size=48, color="#FF6B35"),
                        rx.text("Revenue Chart", font_weight="medium", color="gray.600"),
                        rx.text("Period: 7d", font_size="sm", color="gray.500"),
                        rx.text("Revenue: $4,287.50", font_size="lg", font_weight="bold", color="#FF6B35"),
                        spacing="2",
                        align="center"
                    ),
                    height="300px",
                    width="100%",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    background="linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%)",
                    border_radius="md",
                    border="2px dashed",
                    border_color="#FF6B35"
                ),
                
                spacing="4",
                width="100%"
            )
        ),
        
        # Order status chart
        content_card(
            rx.vstack(
                rx.text("Order Status", font_size="lg", font_weight="semibold", color="gray.900"),
                
                # Order status visualization
                rx.center(
                    rx.vstack(
                        rx.icon(tag="pie_chart", size=48, color="green.500"),
                        rx.text("85% Complete", font_size="xl", font_weight="bold", color="green.600"),
                        rx.text("Order Status Overview", font_size="sm", color="gray.600"),
                        spacing="2",
                        align="center"
                    ),
                    height="200px",
                    width="100%",
                    background="linear-gradient(135deg, #F0FFF4 0%, #C6F6D5 100%)",
                    border_radius="md",
                    border="2px dashed",
                    border_color="green.400"
                ),
                
                # Status legend
                rx.vstack(
                    status_legend_item("Completed", "85", "green"),
                    status_legend_item("In Progress", "12", "orange"),
                    status_legend_item("Pending", "8", "red"),
                    spacing="2",
                    width="100%"
                ),
                
                spacing="4",
                width="100%"
            )
        )
    )


def period_button(label: str, period: str) -> rx.Component:
    """Time period selection button"""
    return rx.button(
        label,
        size="2",
        variant="outline",
        color_scheme="orange"
    )


def status_legend_item(label: str, count: str, color: str) -> rx.Component:
    """Status legend item component"""
    color_map = {
        "green": "#10B981",
        "orange": "#F59E0B", 
        "red": "#EF4444"
    }
    
    return rx.hstack(
        rx.box(
            width="12px",
            height="12px",
            background=color_map.get(color, "#6B7280"),
            border_radius="full"
        ),
        rx.text(label, font_size="sm", color="gray.700"),
        rx.spacer(),
        rx.text(count, font_size="sm", font_weight="medium", color="gray.900"),
        spacing="2",
        align="center",
        width="100%"
    )


def dashboard_activity() -> rx.Component:
    """Recent activity section with orders and popular items"""
    return two_column_layout(
        # Recent orders
        content_card(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.text("Recent Orders", font_size="lg", font_weight="semibold", color="gray.900"),
                        real_time_indicator(),
                        spacing="3",
                        align="center"
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="refresh_cw", size=16),
                            size="2",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=DashboardState.load_recent_orders
                        ),
                        rx.link(
                            rx.button(
                                "View All",
                                size="2",
                                variant="ghost",
                                color_scheme="orange"
                            ),
                            href="/orders"
                        ),
                        spacing="2"
                    ),
                    justify="between",
                    width="100%"
                ),
                
                rx.cond(
                    DashboardState.is_loading_orders,
                    rx.center(
                        loading_spinner("md"),
                        height="200px",
                        width="100%"
                    ),
                    rx.cond(
                        DashboardState.orders_error != "",
                        rx.center(
                            error_message(DashboardState.orders_error),
                            height="200px",
                            width="100%"
                        ),
                        rx.vstack(
                            simple_order_row({"order_number": "ORD-001", "table_number": 5, "customer_name": "John Doe", "total": 45.50, "status": "completed"}),
                            simple_order_row({"order_number": "ORD-002", "table_number": 12, "customer_name": "Jane Smith", "total": 32.75, "status": "in_progress"}),
                            simple_order_row({"order_number": "ORD-003", "table_number": 8, "customer_name": "Mike Johnson", "total": 67.25, "status": "ready"}),
                            spacing="1",
                            width="100%"
                        )
                    )
                ),
                
                spacing="4",
                width="100%"
            )
        ),
        
        # Popular items
        content_card(
            rx.vstack(
                rx.hstack(
                    rx.text("Popular Items Today", font_size="lg", font_weight="semibold", color="gray.900"),
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        size="2",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=DashboardState.load_popular_items
                    ),
                    justify="between",
                    width="100%"
                ),
                
                rx.vstack(
                    simple_popular_item({"name": "Margherita Pizza", "sales_count": 45, "revenue": 675.0, "percentage": 35.4}),
                    simple_popular_item({"name": "Caesar Salad", "sales_count": 32, "revenue": 384.0, "percentage": 25.2}),
                    simple_popular_item({"name": "Grilled Chicken", "sales_count": 28, "revenue": 560.0, "percentage": 22.0}),
                    spacing="3",
                    width="100%"
                ),
                
                spacing="4",
                width="100%"
            )
        )
    )


def simple_order_row(order) -> rx.Component:
    """Simple order row for recent orders display"""
    status_colors = {
        "pending": "yellow",
        "confirmed": "blue", 
        "in_progress": "orange",
        "ready": "purple",
        "completed": "green",
        "canceled": "red"
    }
    
    return rx.hstack(
        rx.text(order["order_number"], font_size="sm", color="gray.900", font_weight="medium", width="25%"),
        rx.text(f"T{order['table_number']}", font_size="sm", color="gray.900", width="15%"),
        rx.text(order["customer_name"], font_size="sm", color="gray.900", width="25%"),
        rx.text(f"${order['total']:.2f}", font_size="sm", font_weight="medium", color="gray.900", width="15%"),
        rx.badge(
            order["status"].replace("_", " ").title(),
            color_scheme=status_colors.get(order["status"], "gray"),
            size="2",
            width="20%"
        ),
        spacing="2",
        width="100%",
        padding_y="2",
        border_bottom="1px solid #F7FAFC",
        _hover={"background": "#F7FAFC"},
        align="center"
    )


def simple_popular_item(item) -> rx.Component:
    """Simple popular item display"""
    return rx.hstack(
        rx.box(
            rx.icon(tag="utensils", size=20, color="#FF6B35"),
            width="40px",
            height="40px",
            display="flex",
            align_items="center",
            justify_content="center",
            background="linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%)",
            border_radius="lg",
            border="1px solid #FEB2B2"
        ),
        
        rx.vstack(
            rx.text(item["name"], font_size="sm", font_weight="semibold", color="gray.900"),
            rx.text(f"{item['sales_count']} sold • ${item['revenue']:.0f}", font_size="xs", color="gray.600"),
            spacing="1",
            align="start",
            flex="1"
        ),
        
        rx.text(f"{item['percentage']:.1f}%", font_size="sm", font_weight="bold", color="#FF6B35"),
        
        spacing="3",
        align="center",
        width="100%",
        padding="2",
        border_radius="lg",
        _hover={"background": "gray.50"}
    )


def dashboard_table_status() -> rx.Component:
    """Table status grid section"""
    return content_card(
        rx.vstack(
            rx.hstack(
                rx.text("Table Status", font_size="lg", font_weight="semibold", color="gray.900"),
                rx.hstack(
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        size="2",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=DashboardState.load_table_status
                    ),
                    rx.button(
                        "Manage Tables",
                        size="2",
                        variant="ghost",
                        color_scheme="orange"
                    ),
                    spacing="2"
                ),
                justify="between",
                width="100%"
            ),
            
            # Status legend
            rx.hstack(
                status_legend_item("Available", "", "green"),
                status_legend_item("Occupied", "", "red"),
                status_legend_item("Reserved", "", "yellow"),
                status_legend_item("Out of Service", "", "gray"),
                spacing="6",
                width="100%",
                padding_y="2"
            ),
            
            rx.cond(
                DashboardState.is_loading_tables,
                rx.center(
                    loading_spinner("md"),
                    height="200px",
                    width="100%"
                ),
                rx.cond(
                    DashboardState.tables_error != "",
                    rx.center(
                        error_message(DashboardState.tables_error),
                        height="200px",
                        width="100%"
                    ),
                    # Table grid
                    rx.grid(
                        table_status_card("1", {"status": "available", "capacity": 2}),
                        table_status_card("2", {"status": "occupied", "capacity": 4}),
                        table_status_card("3", {"status": "reserved", "capacity": 2}),
                        table_status_card("4", {"status": "available", "capacity": 6}),
                        table_status_card("5", {"status": "occupied", "capacity": 4}),
                        table_status_card("6", {"status": "out_of_service", "capacity": 2}),
                        table_status_card("7", {"status": "available", "capacity": 4}),
                        table_status_card("8", {"status": "occupied", "capacity": 6}),
                        columns="8",
                        spacing="3",
                        width="100%"
                    )
                )
            ),
            
            spacing="4",
            width="100%"
        ),
        title="Table Management"
    )


def table_status_card(table_number: str, table_data) -> rx.Component:
    """Individual table status card"""
    status = table_data["status"]
    capacity = table_data["capacity"]
    
    status_config = {
        "available": {
            "bg": "green.50",
            "border": "green.200", 
            "text": "green.700",
            "icon": "check_circle",
            "icon_color": "green.500"
        },
        "occupied": {
            "bg": "red.50",
            "border": "red.200",
            "text": "red.700", 
            "icon": "user",
            "icon_color": "red.500"
        },
        "reserved": {
            "bg": "yellow.50",
            "border": "yellow.200",
            "text": "yellow.700",
            "icon": "clock",
            "icon_color": "yellow.500"
        },
        "out_of_service": {
            "bg": "gray.50",
            "border": "gray.200",
            "text": "gray.700",
            "icon": "x_circle",
            "icon_color": "gray.500"
        }
    }
    
    config = status_config.get(status, status_config["available"])
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(f"T{table_number}", font_weight="bold", font_size="lg", color=config["text"]),
                rx.icon(tag=config["icon"], size=16, color=config["icon_color"]),
                justify="between",
                width="100%"
            ),
            
            rx.text(f"{capacity} seats", font_size="xs", color="gray.600"),
            rx.text(status.replace("_", " ").title(), font_size="xs", color=config["text"], font_weight="medium"),
            
            spacing="2",
            align="center",
            width="100%"
        ),
        padding="3",
        border_radius="lg",
        background=config["bg"],
        border=f"1px solid",
        border_color=config["border"],
        width="80px",
        height="80px",
        cursor="pointer",
        _hover={"transform": "scale(1.05)", "transition": "all 0.2s"}
    )