from fastapi import APIRouter
from app.api.v1.endpoints import auth, menus, orders, websocket, analytics, dashboard_menu

# Create main API router
api_router = APIRouter()

# Health check endpoint for API
@api_router.get("/health")
async def api_health():
    """API health check endpoint"""
    return {"status": "API is healthy"}

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include public menu routes (no authentication required)
api_router.include_router(menus.router, prefix="/menus", tags=["public-menus"])

# Include order management routes
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])

# Include WebSocket routes for real-time updates
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Include analytics routes for dashboard reporting
api_router.include_router(analytics.router, prefix="/dashboard/analytics", tags=["analytics"])

# Include dashboard menu management routes
api_router.include_router(dashboard_menu.router, prefix="/dashboard/menu", tags=["dashboard-menu"])