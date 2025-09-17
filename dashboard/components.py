"""Reusable UI components for the restaurant dashboard"""

import reflex as rx
from typing import List, Dict, Any, Optional


def loading_spinner(size: str = "md") -> rx.Component:
    """Loading spinner component"""
    return rx.center(
        rx.text("Loading...", color="#FF6B35", font_weight="medium"),
        height="100px",
        width="100%"
    )


def empty_state(
    icon: str,
    title: str,
    description: str,
    action_text: Optional[str] = None,
    action_handler: Optional[callable] = None
) -> rx.Component:
    """Empty state component for when no data is available"""
    return rx.center(
        rx.vstack(
            rx.icon(tag=icon, size=48, color="gray.400"),
            rx.text(title, font_size="lg", font_weight="semibold", color="gray.900"),
            rx.text(description, font_size="sm", color="gray.600", text_align="center"),
            rx.cond(
                action_text is not None,
                rx.button(
                    action_text or "Action",
                    color_scheme="orange",
                    size="2"
                )
            ),
            spacing="4",
            align="center",
            max_width="300px"
        ),
        height="200px",
        width="100%"
    )


def error_message(message: str, retry_handler: Optional[callable] = None) -> rx.Component:
    """Error message component with optional retry button"""
    return rx.center(
        rx.vstack(
            rx.icon(tag="alert_circle", size=48, color="red.400"),
            rx.text("Error", font_size="lg", font_weight="semibold", color="red.600"),
            rx.text(message, font_size="sm", color="red.600", text_align="center"),
            spacing="4",
            align="center",
            max_width="300px"
        ),
        height="200px",
        width="100%"
    )


def stat_card(title: str, value: str, icon: str, color: str = "blue") -> rx.Component:
    """Simple stat card component"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=20, color=f"{color}.500"),
                rx.spacer(),
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
        width="100%"
    )


def progress_ring(percentage: int, color: str = "blue") -> rx.Component:
    """Progress ring component"""
    return rx.center(
        rx.vstack(
            rx.text(f"{percentage}%", font_size="xl", font_weight="bold", color=f"{color}.600"),
            rx.text("Complete", font_size="sm", color="gray.600"),
            spacing="1",
            align="center"
        ),
        width="100px",
        height="100px",
        border_radius="full",
        border=f"4px solid",
        border_color=f"{color}.200",
        background=f"{color}.50"
    )


def status_badge(status: str, size: str = "2") -> rx.Component:
    """Status badge with appropriate colors"""
    status_colors = {
        "pending": "yellow",
        "confirmed": "blue", 
        "in_progress": "orange",
        "ready": "purple",
        "completed": "green",
        "canceled": "red"
    }
    
    return rx.badge(
        status.replace("_", " ").title(),
        color_scheme=status_colors.get(status, "gray"),
        size=size
    )


def connection_status_indicator() -> rx.Component:
    """Real-time connection status indicator"""
    from dashboard.state import WebSocketState
    
    return rx.hstack(
        rx.cond(
            WebSocketState.connection_status == "connected",
            rx.icon(tag="wifi", size=16, color="green.500"),
            rx.cond(
                WebSocketState.connection_status == "connecting",
                rx.icon(tag="loader", size=16, color="yellow.500"),
                rx.cond(
                    WebSocketState.connection_status == "error",
                    rx.icon(tag="wifi_off", size=16, color="red.500"),
                    rx.icon(tag="wifi_off", size=16, color="gray.400")
                )
            )
        ),
        rx.cond(
            WebSocketState.connection_status == "connected",
            rx.text("Connected", font_size="sm", color="green.600"),
            rx.cond(
                WebSocketState.connection_status == "connecting",
                rx.text("Connecting...", font_size="sm", color="yellow.600"),
                rx.cond(
                    WebSocketState.connection_status == "error",
                    rx.text("Connection Error", font_size="sm", color="red.600"),
                    rx.text("Disconnected", font_size="sm", color="gray.600")
                )
            )
        ),
        rx.cond(
            WebSocketState.connection_error != "",
            rx.tooltip(
                rx.icon(tag="info", size=14, color="gray.400"),
                content=WebSocketState.connection_error
            )
        ),
        spacing="2",
        align="center"
    )


def real_time_indicator() -> rx.Component:
    """Compact real-time status indicator for headers"""
    from dashboard.state import WebSocketState
    
    return rx.hstack(
        rx.box(
            width="8px",
            height="8px",
            border_radius="full",
            background=rx.cond(
                WebSocketState.connection_status == "connected",
                "green.500",
                rx.cond(
                    WebSocketState.connection_status == "connecting",
                    "yellow.500",
                    "red.500"
                )
            )
        ),
        rx.text(
            "Live",
            font_size="xs",
            color="gray.600",
            font_weight="medium"
        ),
        spacing="1",
        align="center"
    )