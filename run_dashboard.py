"""Entry point for running the Reflex dashboard application."""

import reflex as rx
from dashboard.app import app

if __name__ == "__main__":
    # Run the Reflex app
    rx.run(app)