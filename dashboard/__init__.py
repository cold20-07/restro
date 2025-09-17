"""Restaurant Dashboard Package

This package contains the Reflex-based dashboard UI components
for the QR Code Ordering System.
"""

# Import from the correct dashboard.py file in the root of this package
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dashboard import app
except ImportError:
    # Fallback to direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location("dashboard", os.path.join(os.path.dirname(__file__), "dashboard.py"))
    dashboard_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dashboard_module)
    app = dashboard_module.app

__all__ = ["app"]