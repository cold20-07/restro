"""Authentication wrapper for protected routes."""

import reflex as rx
from dashboard.state import AuthState


def auth_wrapper(component: rx.Component) -> rx.Component:
    """
    Wrapper component that protects routes requiring authentication.
    
    Args:
        component: The component to protect
        
    Returns:
        Protected component that redirects to login if not authenticated
    """
    return rx.cond(
        AuthState.is_authenticated,
        component,
        rx.center(
            rx.text("Redirecting to login...", color="gray"),
            min_height="100vh"
        )
    )


def loading_spinner() -> rx.Component:
    """Loading spinner component for authentication checks."""
    return rx.center(
        rx.vstack(
            rx.icon(tag="loader", size=48, color="orange"),
            rx.text("Loading...", color="gray"),
            spacing="4"
        ),
        min_height="100vh"
    )


def auth_check_wrapper(component: rx.Component) -> rx.Component:
    """
    Wrapper that shows loading while checking authentication status.
    
    Args:
        component: The component to show after auth check
        
    Returns:
        Component with loading state during auth check
    """
    return rx.cond(
        AuthState.is_checking_auth,
        loading_spinner(),
        rx.cond(
            AuthState.is_authenticated,
            component,
            rx.center(
                rx.text("Redirecting to login...", color="gray"),
                min_height="100vh"
            )
        )
    )


def public_route_wrapper(component: rx.Component) -> rx.Component:
    """
    Wrapper for public routes that redirects authenticated users to dashboard.
    
    Args:
        component: The public component (login/register page)
        
    Returns:
        Component that redirects to dashboard if already authenticated
    """
    return rx.cond(
        AuthState.is_checking_auth,
        loading_spinner(),
        rx.cond(
            AuthState.is_authenticated,
            rx.center(
                rx.text("Redirecting to dashboard...", color="gray"),
                min_height="100vh"
            ),
            component
        )
    )