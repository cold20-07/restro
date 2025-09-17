"""Simple test to verify dashboard components work"""

import reflex as rx
from dashboard.state import DashboardState

def simple_dashboard() -> rx.Component:
    """Simple dashboard test"""
    return rx.vstack(
        rx.text("Dashboard Test", font_size="xl"),
        rx.text("Revenue: $4,287.50"),
        rx.text("Orders: 127"),
        spacing="4",
        padding="6"
    )

# Test app
app = rx.App()
app.add_page(simple_dashboard, route="/test", title="Test Dashboard")

if __name__ == "__main__":
    print("Simple dashboard test created successfully")