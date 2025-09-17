"""Public menu API endpoints for customer access"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import Optional, List
import traceback
from app.models.public_menu import (
    PublicMenuResponse, 
    PublicMenuItemResponse, 
    PublicMenuByCategory
)
from app.services.public_menu_service import PublicMenuService
from app.services.menu_item_service import MenuItemService
from app.services.restaurant_service import RestaurantService
from app.database.service_factory import get_menu_item_service, get_restaurant_service
from app.database.base import NotFoundError, DatabaseError
from app.core.input_validation import validate_path_params, validate_query_params
from app.core.exceptions import ValidationError, raise_not_found_error
from app.core.validation import validate_uuid
from app.core.error_monitoring import record_error
from app.core.logging_config import get_logger

logger = get_logger("menu_endpoints")


router = APIRouter()


def get_public_menu_service(
    menu_item_service: MenuItemService = Depends(get_menu_item_service),
    restaurant_service: RestaurantService = Depends(get_restaurant_service)
) -> PublicMenuService:
    """Dependency to get public menu service"""
    return PublicMenuService(menu_item_service, restaurant_service)


@router.get("/{restaurant_id}", response_model=PublicMenuResponse)
@validate_path_params(restaurant_id=validate_uuid)
@validate_query_params(
    category=lambda x: x.strip() if x and isinstance(x, str) else x
)
async def get_restaurant_menu(
    restaurant_id: str,
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    public_menu_service: PublicMenuService = Depends(get_public_menu_service)
):
    """
    Get public menu for a restaurant.
    
    This endpoint returns only available menu items for customer ordering.
    No authentication required as this is a public endpoint.
    
    - **restaurant_id**: The ID of the restaurant
    - **category**: Optional category filter to show only items from specific category
    
    Returns restaurant information along with available menu items.
    """
    try:
        # Additional validation for category
        if category and len(category.strip()) == 0:
            raise_validation_error(
                "Category cannot be empty",
                {"category": ["Category must be a non-empty string"]}
            )
        
        result = await public_menu_service.get_public_menu(restaurant_id, category)
        
        logger.info(
            "Public menu retrieved successfully",
            extra={
                "restaurant_id": restaurant_id,
                "category": category,
                "items_count": len(result.items),
                "endpoint": "/api/menus/{restaurant_id}"
            }
        )
        
        return result
        
    except ValidationError:
        raise
    except NotFoundError as e:
        logger.warning(
            f"Restaurant menu not found: {str(e)}",
            extra={
                "restaurant_id": restaurant_id,
                "endpoint": "/api/menus/{restaurant_id}",
                "error_type": "NotFoundError"
            }
        )
        record_error(e, endpoint="/api/menus/{restaurant_id}", request_data={"restaurant_id": restaurant_id})
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(
            f"Database error retrieving menu: {str(e)}",
            extra={
                "restaurant_id": restaurant_id,
                "endpoint": "/api/menus/{restaurant_id}",
                "error_type": "DatabaseError"
            }
        )
        record_error(e, endpoint="/api/menus/{restaurant_id}", request_data={"restaurant_id": restaurant_id}, stack_trace=traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve menu")
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving menu: {str(e)}",
            extra={
                "restaurant_id": restaurant_id,
                "endpoint": "/api/menus/{restaurant_id}",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        record_error(e, endpoint="/api/menus/{restaurant_id}", request_data={"restaurant_id": restaurant_id}, stack_trace=traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{restaurant_id}/by-category", response_model=PublicMenuByCategory)
async def get_restaurant_menu_by_category(
    restaurant_id: str,
    public_menu_service: PublicMenuService = Depends(get_public_menu_service)
):
    """
    Get public menu organized by categories.
    
    This endpoint returns available menu items grouped by their categories.
    Useful for displaying menu in a categorized layout.
    
    - **restaurant_id**: The ID of the restaurant
    
    Returns restaurant information with menu items organized by categories.
    """
    try:
        return await public_menu_service.get_public_menu_by_category(restaurant_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve menu")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{restaurant_id}/categories", response_model=List[str])
async def get_restaurant_menu_categories(
    restaurant_id: str,
    public_menu_service: PublicMenuService = Depends(get_public_menu_service)
):
    """
    Get available menu categories for a restaurant.
    
    Returns a list of categories that have available menu items.
    
    - **restaurant_id**: The ID of the restaurant
    
    Returns list of category names.
    """
    try:
        return await public_menu_service.get_menu_categories(restaurant_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{restaurant_id}/search", response_model=List[PublicMenuItemResponse])
async def search_restaurant_menu(
    restaurant_id: str,
    q: str = Query(..., description="Search query for menu items"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    public_menu_service: PublicMenuService = Depends(get_public_menu_service)
):
    """
    Search menu items by name or description.
    
    This endpoint allows customers to search for specific menu items.
    Only returns available items.
    
    - **restaurant_id**: The ID of the restaurant
    - **q**: Search query (searches in item name and description)
    - **category**: Optional category filter
    - **limit**: Maximum number of results (1-100, default 20)
    
    Returns list of matching menu items.
    """
    try:
        return await public_menu_service.search_public_menu(
            restaurant_id=restaurant_id,
            search_query=q,
            category=category,
            limit=limit
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to search menu")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")