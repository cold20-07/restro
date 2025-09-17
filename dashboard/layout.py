"""Layout components for the restaurant dashboard"""

import reflex as rx
from typing import Optional
from dashboard.state import NavigationState, AuthState


def base_layout(content: rx.Component, page_title: str = "Dashboard") -> rx.Component:
    """Base layout with sidebar navigation and main content area"""
    return rx.fragment(
        # Sidebar navigation
        sidebar_nav(),
        
        # Main content area
        rx.box(
            rx.vstack(
                # Page header
                page_header(page_title),
                
                # Page content
                content,
                
                spacing="6",
                width="100%"
            ),
            margin_left="250px",  # Account for fixed sidebar
            padding="6",
            min_height="100vh",
            background="gray.50"
        )
    )


def sidebar_nav() -> rx.Component:
    """Sidebar navigation component with active state management"""
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
                nav_item("layout_dashboard", "Dashboard", "/", NavigationState.current_page == "dashboard"),
                nav_item("shopping_cart", "Orders", "/orders", NavigationState.current_page == "orders"),
                nav_item("menu", "Menu", "/menu", NavigationState.current_page == "menu"),
                nav_item("users", "Customers", "/customers", NavigationState.current_page == "customers"),
                nav_item("grid_3x3", "Tables", "/tables", NavigationState.current_page == "tables"),
                nav_item("user_check", "Staff", "/staff", NavigationState.current_page == "staff"),
                spacing="1",
                width="100%",
                padding_y="4"
            ),
            
            rx.divider(color_scheme="gray"),
            
            # Analytics section
            rx.text("Analytics", font_size="sm", color="gray.400", font_weight="semibold", padding_y="2"),
            rx.vstack(
                nav_item("bar_chart_3", "Sales Reports", "/analytics/sales", NavigationState.current_page == "sales"),
                nav_item("package", "Inventory", "/analytics/inventory", NavigationState.current_page == "inventory"),
                nav_item("trending_up", "Revenue", "/analytics/revenue", NavigationState.current_page == "revenue"),
                spacing="1",
                width="100%"
            ),
            
            rx.divider(color_scheme="gray"),
            
            # Management section
            rx.text("Management", font_size="sm", color="gray.400", font_weight="semibold", padding_y="2"),
            rx.vstack(
                nav_item("settings", "Settings", "/settings", NavigationState.current_page == "settings"),
                nav_item("percent", "Promotions", "/promotions", NavigationState.current_page == "promotions"),
                spacing="1",
                width="100%"
            ),
            
            rx.spacer(),
            
            # User section at bottom
            rx.vstack(
                rx.divider(color_scheme="gray"),
                rx.hstack(
                    rx.avatar(
                        fallback=rx.cond(
                            AuthState.restaurant_name != "",
                            AuthState.restaurant_name[0].upper(),
                            "R"
                        ),
                        size="2",
                        color_scheme="orange"
                    ),
                    rx.vstack(
                        rx.text(
                            rx.cond(
                                AuthState.restaurant_name != "",
                                AuthState.restaurant_name,
                                "Restaurant"
                            ),
                            font_size="sm", 
                            font_weight="medium", 
                            color="white"
                        ),
                        rx.text(
                            rx.cond(
                                AuthState.user_email != "",
                                AuthState.user_email,
                                "user@restaurant.com"
                            ),
                            font_size="xs", 
                            color="gray.400"
                        ),
                        spacing="0",
                        align="start"
                    ),
                    rx.spacer(),
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
                            rx.menu.item("Profile"),
                            rx.menu.item("Settings"),
                            rx.menu.separator(),
                            rx.menu.item(
                                "Logout",
                                color="red",
                                on_click=AuthState.logout
                            )
                        )
                    ),
                    spacing="3",
                    align="center",
                    width="100%"
                ),
                spacing="3",
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
        overflow_y="auto",
        z_index="1000"
    )


def nav_item(icon: str, label: str, route: str = "/", is_active: bool = False) -> rx.Component:
    """Navigation item component with routing and active state"""
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


def page_header(title: str, subtitle: Optional[str] = None, actions: Optional[rx.Component] = None) -> rx.Component:
    """Page header component with title, subtitle, and optional actions"""
    from dashboard.components import connection_status_indicator
    
    header_content = [rx.text(title, font_size="2xl", font_weight="bold", color="gray.900")]
    if subtitle:
        header_content.append(rx.text(subtitle, color="gray.600"))
    
    return rx.hstack(
        rx.vstack(
            *header_content,
            spacing="1",
            align="start"
        ),
        rx.spacer(),
        rx.hstack(
            connection_status_indicator(),
            actions if actions else rx.fragment(),
            spacing="4",
            align="center"
        ),
        justify="between",
        width="100%",
        padding_bottom="6"
    )


def content_card(content: rx.Component, title: Optional[str] = None, padding: str = "6") -> rx.Component:
    """Content card wrapper component"""
    card_content = [content]
    if title:
        card_content.insert(0, rx.text(title, font_size="lg", font_weight="semibold", color="gray.900"))
    
    return rx.card(
        rx.vstack(
            *card_content,
            spacing="4" if title else "0",
            width="100%"
        ),
        padding=padding,
        border_radius="lg",
        box_shadow="sm",
        border="1px solid #E2E8F0",
        width="100%"
    )


def metric_grid(metrics: list) -> rx.Component:
    """Grid layout for metric cards"""
    return rx.grid(
        *metrics,
        columns=str(len(metrics)),
        spacing="6",
        width="100%"
    )


def two_column_layout(left_content: rx.Component, right_content: rx.Component) -> rx.Component:
    """Two column layout for dashboard sections"""
    return rx.hstack(
        left_content,
        right_content,
        spacing="6",
        width="100%"
    )


def responsive_grid(items: list, columns: int = 4) -> rx.Component:
    """Responsive grid layout for items"""
    return rx.grid(
        *items,
        columns=str(columns),
        spacing="6",
        width="100%"
    )