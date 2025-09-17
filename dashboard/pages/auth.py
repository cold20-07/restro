"""Authentication pages for restaurant dashboard."""

import reflex as rx
from typing import Optional
from dashboard.state import AuthState


def login_form() -> rx.Component:
    """Login form component with validation."""
    return rx.card(
        rx.vstack(
            rx.heading("Restaurant Login", size="6", text_align="center"),
            rx.text(
                "Sign in to your restaurant dashboard",
                color="gray",
                text_align="center",
                margin_bottom="4"
            ),
            
            # Email input
            rx.vstack(
                rx.text("Email", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Enter your email",
                    type="email",
                    value=AuthState.email,
                    on_change=AuthState.set_email,
                    width="100%",
                    size="3"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Password input
            rx.vstack(
                rx.text("Password", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Enter your password",
                    type="password",
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    width="100%",
                    size="3"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Error message
            rx.cond(
                AuthState.error_message,
                rx.callout(
                    AuthState.error_message,
                    icon="alert_circle",
                    color_scheme="red",
                    size="1"
                )
            ),
            
            # Login button
            rx.button(
                rx.cond(
                    AuthState.is_loading,
                    rx.hstack(
                        rx.icon(tag="loader", size=16),
                        rx.text("Signing in..."),
                        spacing="2"
                    ),
                    rx.text("Sign In")
                ),
                on_click=AuthState.login,
                disabled=AuthState.is_loading,
                width="100%",
                size="3",
                color_scheme="orange"
            ),
            
            # Registration link
            rx.hstack(
                rx.text("Don't have an account?", color="gray", font_size="sm"),
                rx.link(
                    "Sign up here",
                    href="/register",
                    color="orange",
                    font_size="sm"
                ),
                spacing="1",
                justify="center"
            ),
            
            spacing="4",
            width="100%"
        ),
        max_width="400px",
        padding="6",
        margin="auto"
    )


def register_form() -> rx.Component:
    """Registration form component with validation."""
    return rx.card(
        rx.vstack(
            rx.heading("Create Restaurant Account", size="6", text_align="center"),
            rx.text(
                "Join our platform and start managing your restaurant",
                color="gray",
                text_align="center",
                margin_bottom="4"
            ),
            
            # Restaurant name input
            rx.vstack(
                rx.text("Restaurant Name", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Enter your restaurant name",
                    value=AuthState.restaurant_name,
                    on_change=AuthState.set_restaurant_name,
                    width="100%",
                    size="3"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Email input
            rx.vstack(
                rx.text("Email", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Enter your email",
                    type="email",
                    value=AuthState.email,
                    on_change=AuthState.set_email,
                    width="100%",
                    size="3"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Password input
            rx.vstack(
                rx.text("Password", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Create a password",
                    type="password",
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    width="100%",
                    size="3"
                ),
                rx.text(
                    "Password must be at least 8 characters",
                    color="gray",
                    font_size="xs"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Confirm password input
            rx.vstack(
                rx.text("Confirm Password", font_weight="medium", font_size="sm"),
                rx.input(
                    placeholder="Confirm your password",
                    type="password",
                    value=AuthState.confirm_password,
                    on_change=AuthState.set_confirm_password,
                    width="100%",
                    size="3"
                ),
                spacing="1",
                width="100%"
            ),
            
            # Error message
            rx.cond(
                AuthState.error_message,
                rx.callout(
                    AuthState.error_message,
                    icon="alert_circle",
                    color_scheme="red",
                    size="1"
                )
            ),
            
            # Success message
            rx.cond(
                AuthState.success_message,
                rx.callout(
                    AuthState.success_message,
                    icon="check_circle",
                    color_scheme="green",
                    size="1"
                )
            ),
            
            # Register button
            rx.button(
                rx.cond(
                    AuthState.is_loading,
                    rx.hstack(
                        rx.icon(tag="loader", size=16),
                        rx.text("Creating account..."),
                        spacing="2"
                    ),
                    rx.text("Create Account")
                ),
                on_click=AuthState.register,
                disabled=AuthState.is_loading,
                width="100%",
                size="3",
                color_scheme="orange"
            ),
            
            # Login link
            rx.hstack(
                rx.text("Already have an account?", color="gray", font_size="sm"),
                rx.link(
                    "Sign in here",
                    href="/login",
                    color="orange",
                    font_size="sm"
                ),
                spacing="1",
                justify="center"
            ),
            
            spacing="4",
            width="100%"
        ),
        max_width="400px",
        padding="6",
        margin="auto"
    )


def login_page() -> rx.Component:
    """Complete login page layout."""
    return rx.container(
        rx.vstack(
            rx.spacer(),
            login_form(),
            rx.spacer(),
            spacing="0",
            min_height="100vh",
            justify="center"
        ),
        max_width="100%",
        padding="4"
    )


def register_page() -> rx.Component:
    """Complete registration page layout."""
    return rx.container(
        rx.vstack(
            rx.spacer(),
            register_form(),
            rx.spacer(),
            spacing="0",
            min_height="100vh",
            justify="center"
        ),
        max_width="100%",
        padding="4"
    )