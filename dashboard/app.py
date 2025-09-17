"""Main application file with authentication integration."""

import reflex as rx
from dashboard.pages.auth import login_page, register_page
from dashboard.pages.dashboard import dashboard_page
from dashboard.pages.orders import orders_page
from dashboard.pages.menu import menu_page


# Create the main app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%",
    )
)

# Public routes (login/register)
app.add_page(
    login_page(),
    route="/login",
    title="Login - QR Order System"
)

app.add_page(
    register_page(),
    route="/register", 
    title="Register - QR Order System"
)

# Protected routes (dashboard pages)
app.add_page(
    dashboard_page(),
    route="/",
    title="Dashboard - QR Order System"
)

app.add_page(
    dashboard_page(),
    route="/dashboard",
    title="Dashboard - QR Order System"
)

app.add_page(
    orders_page(),
    route="/orders",
    title="Orders - QR Order System"
)

app.add_page(
    menu_page(),
    route="/menu",
    title="Menu Management - QR Order System"
)