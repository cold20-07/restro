import reflex as rx
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, date, timedelta
import asyncio
from dashboard.state import DashboardState


def sidebar_nav() -> rx.Component:
    """Sidebar navigation component"""
    return rx.box(
        rx.vstack(
            # Logo/Brand section
            rx.hstack(
                rx.icon(tag="utensils", size=24, color="#FF6B35"),
                rx.text("QR Order", font_weight="bold", font_size="lg", color="white"),
                spacing="2",
                align="center",
                padding_bottom="4"
            ),
            
            rx.divider(color_scheme="gray"),
            
            # Navigation items
            rx.vstack(
                nav_item("layout_dashboard", "Dashboard", "/", True),
                nav_item("shopping_cart", "Orders", "/orders", False),
                nav_item("menu", "Menu", "/menu", False),
                nav_item("users", "Customers", "#", False),
                nav_item("grid_3x3", "Tables", "#", False),
                nav_item("user_check", "Staff", "#", False),
                spacing="1",
                width="100%",
                padding_y="4"
            ),
            
            rx.divider(color_scheme="gray"),
            
            # Analytics section
            rx.text("Analytics", font_size="sm", color="gray.400", font_weight="semibold", padding_y="2"),
            rx.vstack(
                nav_item("bar_chart_3", "Sales Reports", "#", False),
                nav_item("package", "Inventory", "#", False),
                nav_item("trending_up", "Revenue", "#", False),
                spacing="1",
                width="100%"
            ),
            
            rx.divider(color_scheme="gray"),
            
            # Management section
            rx.text("Management", font_size="sm", color="gray.400", font_weight="semibold", padding_y="2"),
            rx.vstack(
                nav_item("settings", "Settings", "#", False),
                nav_item("percent", "Promotions", "#", False),
                spacing="1",
                width="100%"
            ),
            
            spacing="2",
            align="start",
            width="100%"
        ),
        background="linear-gradient(180deg, #2D3748 0%, #1A202C 100%)",
        width="250px",
        height="100vh",
        padding="6",
        position="fixed",
        left="0",
        top="0",
        overflow_y="auto"
    )


def nav_item(icon: str, label: str, route: str = "/", is_active: bool = False) -> rx.Component:
    """Navigation item component with routing"""
    return rx.link(
        rx.hstack(
            rx.icon(tag=icon, size=18, color="white" if is_active else "gray.400"),
            rx.text(
                label, 
                color="white" if is_active else "gray.400",
                font_weight="medium" if is_active else "normal"
            ),
            spacing="3",
            align="center",
            padding="3",
            border_radius="md",
            background="#FF6B35" if is_active else "transparent",
            _hover={"background": "#FF6B35" if not is_active else "#FF6B35", "cursor": "pointer"},
            width="100%"
        ),
        href=route,
        text_decoration="none",
        width="100%"
    )


def metric_card(title: str, value, change: str, change_type: str = "positive", icon: str = "dollar_sign") -> rx.Component:
    """Metric card component for dashboard KPIs"""
    change_color = "green.500" if change_type == "positive" else "red.500"
    change_icon = "trending_up" if change_type == "positive" else "trending_down"
    
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=20, color="#FF6B35"),
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


def revenue_chart() -> rx.Component:
    """Revenue chart component with time period selection"""
    
    return rx.card(
        rx.vstack(
            # Chart header
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
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
    )


def period_button(label: str, period: str) -> rx.Component:
    """Time period selection button"""
    return rx.button(
        label,
        size="2",
        variant="outline",
        color_scheme="orange"
    )


def order_status_chart() -> rx.Component:
    """Order status visualization with circular progress"""
    
    return rx.card(
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
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
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


def recent_orders_table() -> rx.Component:
    """Enhanced recent orders table component with real-time updates"""
    return rx.card(
        rx.vstack(
            # Header with refresh button
            rx.hstack(
                rx.text("Recent Orders", font_size="lg", font_weight="semibold", color="gray.900"),
                rx.hstack(
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        size="2",
                        variant="ghost",
                        color_scheme="gray"
                    ),
                    rx.button(
                        "View All",
                        size="2",
                        variant="ghost",
                        color_scheme="orange"
                    ),
                    spacing="2"
                ),
                justify="between",
                width="100%"
            ),
            
            # Table content
            rx.vstack(
                # Table header
                rx.hstack(
                    rx.text("Order #", font_size="sm", font_weight="medium", color="gray.600", width="18%"),
                    rx.text("Table", font_size="sm", font_weight="medium", color="gray.600", width="12%"),
                    rx.text("Customer", font_size="sm", font_weight="medium", color="gray.600", width="20%"),
                    rx.text("Items", font_size="sm", font_weight="medium", color="gray.600", width="12%"),
                    rx.text("Total", font_size="sm", font_weight="medium", color="gray.600", width="15%"),
                    rx.text("Status", font_size="sm", font_weight="medium", color="gray.600", width="15%"),
                    rx.text("Actions", font_size="sm", font_weight="medium", color="gray.600", width="8%"),
                    spacing="2",
                    width="100%",
                    padding_y="3",
                    border_bottom="1px solid #E2E8F0"
                ),
                
                # Table rows - using static data for demo
                rx.vstack(
                    simple_order_row("ORD-A1B2", "5", "John Doe", "3", "$45.50", "completed"),
                    simple_order_row("ORD-C3D4", "12", "Jane Smith", "2", "$32.75", "in_progress"),
                    simple_order_row("ORD-E5F6", "8", "Mike Johnson", "4", "$67.25", "ready"),
                    simple_order_row("ORD-G7H8", "3", "Sarah Wilson", "2", "$28.50", "pending"),
                    simple_order_row("ORD-I9J0", "15", "David Brown", "3", "$52.00", "confirmed"),
                    spacing="0",
                    width="100%"
                ),
                
                spacing="0",
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
    )


def simple_order_row(order_number: str, table: str, customer: str, items: str, total: str, status: str) -> rx.Component:
    """Simplified order row component that works with Reflex"""
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
        rx.text(order_number, font_size="sm", color="gray.900", font_weight="medium", width="18%"),
        
        # Table number
        rx.text(f"T{table}", font_size="sm", color="gray.900", width="12%"),
        
        # Customer name
        rx.text(customer, font_size="sm", color="gray.900", width="20%"),
        
        # Items count
        rx.text(f"{items} items", font_size="sm", color="gray.600", width="12%"),
        
        # Total
        rx.text(total, font_size="sm", font_weight="medium", color="gray.900", width="15%"),
        
        # Status badge
        rx.badge(
            status.replace("_", " ").title(),
            color_scheme=status_colors.get(status, "gray"),
            size="2"
        ),
        
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
            width="8%"
        ),
        
        spacing="2",
        width="100%",
        padding_y="3",
        border_bottom="1px solid #F7FAFC",
        _hover={"background": "#F7FAFC"},
        align="center"
    )


def enhanced_order_row(order) -> rx.Component:
    """Enhanced order table row component with interactive elements"""
    status_colors = {
        "pending": "yellow",
        "confirmed": "blue", 
        "in_progress": "orange",
        "ready": "purple",
        "completed": "green",
        "canceled": "red"
    }
    
    # Format time - simplified for Reflex state variables
    created_time = "14:30"  # Simplified for demo
    
    return rx.hstack(
        # Order number with tooltip
        rx.tooltip(
            rx.text(
                order["order_number"],
                font_size="sm", 
                color="gray.900", 
                font_weight="medium",
                width="18%"
            ),
            content=f"Order Details"
        ),
        
        # Table number
        rx.text(f"T{order['table_number']}", font_size="sm", color="gray.900", width="12%"),
        
        # Customer info with phone tooltip
        rx.tooltip(
            rx.text(order["customer_name"], font_size="sm", color="gray.900", width="20%"),
            content="Customer Details"
        ),
        
        # Items count
        rx.text(f"{order['items_count']} items", font_size="sm", color="gray.600", width="12%"),
        
        # Total with currency
        rx.text(f"${order['total']:.2f}", font_size="sm", font_weight="medium", color="gray.900", width="15%"),
        
        # Status badge with dropdown for updates
        rx.menu.root(
            rx.menu.trigger(
                rx.badge(
                    order["status"].replace("_", " ").title(),
                    color_scheme=status_colors.get(order["status"], "gray"),
                    size="2",
                    cursor="pointer"
                )
            ),
            rx.menu.content(
                rx.menu.item("Confirm Order"),
                rx.menu.item("Start Preparation"),
                rx.menu.item("Mark Ready"),
                rx.menu.item("Complete Order"),
                rx.menu.separator(),
                rx.menu.item("Cancel Order", color="red")
            ),
            width="15%"
        ),
        
        # Quick actions
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
                rx.menu.item("Print Receipt"),
                rx.menu.item("Contact Customer"),
                rx.menu.separator(),
                rx.menu.item("Refund Order", color="red")
            ),
            width="8%"
        ),
        
        spacing="2",
        width="100%",
        padding_y="3",
        border_bottom="1px solid #F7FAFC",
        _hover={"background": "#F7FAFC"},
        align="center"
    )


def popular_items_list() -> rx.Component:
    """Enhanced popular items list component with sales data"""
    return rx.card(
        rx.vstack(
            # Header with time period selector
            rx.hstack(
                rx.text("Popular Items Today", font_size="lg", font_weight="semibold", color="gray.900"),
                rx.hstack(
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        size="2",
                        variant="ghost",
                        color_scheme="gray"
                    ),
                    rx.menu.root(
                        rx.menu.trigger(
                            rx.button(
                                "Today",
                                rx.icon(tag="chevron_down", size=14),
                                size="2",
                                variant="ghost",
                                color_scheme="orange"
                            )
                        ),
                        rx.menu.content(
                            rx.menu.item("Today"),
                            rx.menu.item("This Week"),
                            rx.menu.item("This Month")
                        )
                    ),
                    spacing="2"
                ),
                justify="between",
                width="100%"
            ),
            
            # Loading/Error states
            rx.vstack(
                simple_popular_item("Margherita Pizza", "45 sold", "35.4%", "Pizza", "4.8"),
                simple_popular_item("Caesar Salad", "32 sold", "25.2%", "Salads", "4.6"),
                simple_popular_item("Grilled Chicken", "28 sold", "22.0%", "Main Course", "4.7"),
                simple_popular_item("Pasta Carbonara", "22 sold", "17.3%", "Pasta", "4.5"),
                simple_popular_item("Fish & Chips", "18 sold", "14.2%", "Main Course", "4.3"),
                spacing="3",
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
    )


def simple_popular_item(name: str, sales: str, percentage: str, category: str, rating: str) -> rx.Component:
    """Simplified popular item component that works with Reflex"""
    return rx.hstack(
        # Item icon
        rx.box(
            rx.icon(tag="utensils", size=24, color="#FF6B35"),
            width="48px",
            height="48px",
            display="flex",
            align_items="center",
            justify_content="center",
            background="linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%)",
            border_radius="lg",
            border="1px solid #FEB2B2"
        ),
        
        # Item details
        rx.vstack(
            rx.hstack(
                rx.text(name, font_size="sm", font_weight="semibold", color="gray.900"),
                rx.badge(category, size="1", color_scheme="gray", variant="soft"),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.text(sales, font_size="xs", color="gray.600"),
                rx.text("|", font_size="xs", color="gray.400"),
                rx.text("$675 revenue", font_size="xs", color="gray.600"),
                rx.text("|", font_size="xs", color="gray.400"),
                rx.hstack(
                    rx.icon(tag="star", size=12, color="yellow.400"),
                    rx.text(rating, font_size="xs", color="gray.600"),
                    spacing="1",
                    align="center"
                ),
                spacing="1",
                align="center"
            ),
            spacing="1",
            align="start",
            flex="1"
        ),
        
        # Performance metrics
        rx.vstack(
            rx.hstack(
                rx.text(percentage, font_size="sm", font_weight="bold", color="#FF6B35"),
                rx.icon(tag="trending_up", size=14, color="green.500"),
                spacing="1",
                align="center"
            ),
            rx.text("$15.00", font_size="xs", color="gray.500"),
            spacing="1",
            align="end"
        ),
        
        spacing="3",
        align="center",
        width="100%",
        padding="3",
        border_radius="lg",
        _hover={"background": "gray.50", "cursor": "pointer"},
        border="1px solid transparent",
        _hover_border="1px solid #E2E8F0"
    )


def enhanced_popular_item(item) -> rx.Component:
    """Enhanced popular item component with detailed sales data"""
    # Use a default icon for simplicity with Reflex state variables
    icon = "utensils"
    
    # Simplified trend for Reflex state variables
    trend = {"color": "green.500", "icon": "trending_up"}
    
    return rx.hstack(
        # Item image/icon
        rx.box(
            rx.icon(tag=icon, size=24, color="#FF6B35"),
            width="48px",
            height="48px",
            display="flex",
            align_items="center",
            justify_content="center",
            background="linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%)",
            border_radius="lg",
            border="1px solid #FEB2B2"
        ),
        
        # Item details
        rx.vstack(
            rx.hstack(
                rx.text(item["name"], font_size="sm", font_weight="semibold", color="gray.900"),
                rx.badge(item["category"], size="1", color_scheme="gray", variant="soft"),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.text(f"{item['sales_count']} sold", font_size="xs", color="gray.600"),
                rx.text("|", font_size="xs", color="gray.400"),
                rx.text(f"${item['revenue']:.0f} revenue", font_size="xs", color="gray.600"),
                rx.text("|", font_size="xs", color="gray.400"),
                rx.hstack(
                    rx.icon(tag="star", size=12, color="yellow.400"),
                    rx.text(item["avg_rating"], font_size="xs", color="gray.600"),
                    spacing="1",
                    align="center"
                ),
                spacing="1",
                align="center"
            ),
            spacing="1",
            align="start",
            flex="1"
        ),
        
        # Performance metrics
        rx.vstack(
            rx.hstack(
                rx.text(f"{item['percentage']:.1f}%", font_size="sm", font_weight="bold", color="#FF6B35"),
                rx.icon(tag=trend["icon"], size=14, color=trend["color"]),
                spacing="1",
                align="center"
            ),
            rx.text(item["price"], font_size="xs", color="gray.500"),
            spacing="1",
            align="end"
        ),
        
        spacing="3",
        align="center",
        width="100%",
        padding="3",
        border_radius="lg",
        _hover={"background": "gray.50", "cursor": "pointer"},
        border="1px solid transparent",
        _hover_border="1px solid #E2E8F0"
    )


def table_status_grid() -> rx.Component:
    """Table status grid with color-coded availability"""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text("Table Status", font_size="lg", font_weight="semibold", color="gray.900"),
                rx.hstack(
                    rx.button(
                        rx.icon(tag="refresh_cw", size=16),
                        size="2",
                        variant="ghost",
                        color_scheme="gray"
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
            
            # Loading/Error states
            rx.cond(
                DashboardState.is_loading_tables,
                rx.center(
                    rx.text("Loading table status...", color="gray.500"),
                    height="200px",
                    width="100%"
                ),
                rx.cond(
                    DashboardState.tables_error != "",
                    rx.center(
                        rx.vstack(
                            rx.icon(tag="alert_circle", size=32, color="red.400"),
                            rx.text(DashboardState.tables_error, color="red.600", font_size="sm"),
                            rx.button(
                                "Retry",
                                size="2",
                                color_scheme="red",
                                on_click=DashboardState.load_table_status
                            ),
                            spacing="3",
                            align="center"
                        ),
                        height="200px",
                        width="100%"
                    ),
                    # Table grid
                    rx.box(
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
                        ),
                        width="100%",
                        overflow_x="auto"
                    )
                )
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="6",
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
    )


def table_status_card(table_number: str, table_data) -> rx.Component:
    """Individual table status card with interactive elements"""
    status = table_data["status"]
    capacity = table_data["capacity"]
    
    # Status colors and configurations
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
    
    # Additional info based on status - simplified for demo
    additional_info = "Ready"
    
    return rx.menu.root(
        rx.menu.trigger(
            rx.box(
                rx.vstack(
                    # Table number and icon
                    rx.hstack(
                        rx.text(f"T{table_number}", font_weight="bold", font_size="lg", color=config["text"]),
                        rx.icon(tag=config["icon"], size=16, color=config["icon_color"]),
                        justify="between",
                        width="100%"
                    ),
                    
                    # Capacity
                    rx.text(f"{capacity} seats", font_size="xs", color="gray.600"),
                    
                    # Additional info
                    rx.text(
                        additional_info,
                        font_size="xs",
                        color="gray.500",
                        text_align="center",
                        height="2em",
                        overflow="hidden"
                    ),
                    
                    spacing="1",
                    align="center",
                    width="100%"
                ),
                
                background=config["bg"],
                border=f"2px solid",
                border_color=config["border"],
                border_radius="lg",
                padding="3",
                min_height="80px",
                cursor="pointer",
                _hover={
                    "transform": "translateY(-2px)",
                    "box_shadow": "md",
                    "border_color": config["icon_color"]
                },
                transition="all 0.2s"
            )
        ),
        rx.menu.content(
            rx.menu.item("Mark Available"),
            rx.menu.item("Mark Occupied"),
            rx.menu.item("Reserve Table"),
            rx.menu.separator(),
            rx.menu.item("Out of Service", color="red"),
            rx.menu.separator(),
            rx.menu.item("View Details"),
            rx.menu.item("Clean Table")
        )
    )


def dashboard_header() -> rx.Component:
    """Dashboard header component"""
    return rx.hstack(
        rx.vstack(
            rx.text("Welcome back!", font_size="sm", color="gray.600"),
            rx.text("Restaurant Dashboard", font_size="xl", font_weight="bold", color="gray.900"),
            spacing="1",
            align="start"
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon(tag="download", size=16),
                "Export Data",
                size="2",
                variant="outline",
                color_scheme="gray"
            ),
            rx.button(
                rx.icon(tag="refresh_cw", size=16),
                "Refresh",
                size="2",
                color_scheme="orange"
            ),
            spacing="2"
        ),
        justify="between",
        align="center",
        width="100%",
        padding_bottom="6"
    )


def main_content() -> rx.Component:
    """Main dashboard content area"""
    return rx.box(
        rx.vstack(
            dashboard_header(),
            
            # Key metrics row
            rx.hstack(
                metric_card("Revenue", "$4,287.50", "+12.5%", "positive", "dollar_sign"),
                metric_card("Orders", "127", "+8.2%", "positive", "shopping_cart"),
                metric_card("Customers", "89", "+15.3%", "positive", "users"),
                metric_card("Rating", "4.8", "+0.3", "positive", "star"),
                spacing="6",
                width="100%"
            ),
            
            # Charts row
            rx.hstack(
                revenue_chart(),
                order_status_chart(),
                spacing="6",
                width="100%"
            ),
            
            # Tables row
            rx.hstack(
                recent_orders_table(),
                popular_items_list(),
                spacing="6",
                width="100%"
            ),
            
            # Table status grid
            table_status_grid(),
            
            spacing="6",
            width="100%"
        ),
        margin_left="250px",  # Account for fixed sidebar
        padding="6",
        min_height="100vh",
        background="gray.50"
    )


def index() -> rx.Component:
    """Main dashboard page"""
    from dashboard.pages.dashboard import dashboard_page
    return dashboard_page()


def orders_page_wrapper() -> rx.Component:
    """Orders management page wrapper"""
    from dashboard.pages.orders import orders_page
    return rx.fragment(
        sidebar_nav(),
        rx.box(
            orders_page(),
            margin_left="250px",
            min_height="100vh",
            background="gray.50"
        )
    )


def menu_page_wrapper() -> rx.Component:
    """Menu management page wrapper"""
    from dashboard.pages.menu import menu_page
    return rx.fragment(
        sidebar_nav(),
        rx.box(
            menu_page(),
            margin_left="250px",
            min_height="100vh",
            background="gray.50"
        )
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="orange"
    )
)
# Import authentication components
from dashboard.pages.auth import login_page, register_page
from dashboard.auth_wrapper import protected_page, public_only_page, with_auth_check

# Wrap protected pages
protected_dashboard = protected_page(index)
protected_orders = protected_page(orders_page_wrapper)
protected_menu = protected_page(menu_page_wrapper)

# Wrap public pages
public_login = public_only_page(login_page())
public_register = public_only_page(register_page())

# Add pages with authentication
app.add_page(protected_dashboard, route="/", title="Restaurant Dashboard")
app.add_page(protected_orders, route="/orders", title="Orders Management")
app.add_page(protected_menu, route="/menu", title="Menu Management")
app.add_page(public_login, route="/login", title="Login")
app.add_page(public_register, route="/register", title="Register")