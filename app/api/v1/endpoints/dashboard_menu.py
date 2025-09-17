"""Dashboard menu management API endpoints for restaurant owners"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, List
from app.models.menu_item import MenuItem, MenuItemCreate, MenuItemUpdate
from app.services.menu_item_service import MenuItemService
from app.database.service_factory import get_menu_item_service
from app.database.base import NotFoundError, DatabaseError
from app.core.auth import get_current_restaurant_id


router = APIRouter()


@router.get("", response_model=List[MenuItem])
async def get_restaurant_menu_items(
    include_unavailable: bool = Query(True, description="Include unavailable items"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Get all menu items for the authenticated restaurant.
    
    This endpoint returns menu items for restaurant management.
    Requires authentication and returns items only for the authenticated restaurant.
    
    - **include_unavailable**: Whether to include unavailable items (default: true)
    - **category**: Optional category filter
    - **skip**: Number of items to skip for pagination
    - **limit**: Maximum number of items to return (1-500, default 100)
    
    Returns list of menu items for the restaurant.
    """
    try:
        return await menu_service.get_by_restaurant(
            restaurant_id=restaurant_id,
            include_unavailable=include_unavailable,
            category=category,
            skip=skip,
            limit=limit
        )
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve menu items")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    menu_item_data: MenuItemCreate,
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Create a new menu item for the authenticated restaurant.
    
    This endpoint creates a new menu item and automatically associates it
    with the authenticated restaurant.
    
    - **menu_item_data**: Menu item information including name, price, category, etc.
    
    Returns the created menu item with generated ID and timestamps.
    """
    try:
        # Override restaurant_id with authenticated restaurant
        menu_item_data.restaurant_id = restaurant_id
        return await menu_service.create_menu_item(menu_item_data)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to create menu item")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{item_id}", response_model=MenuItem)
async def get_menu_item(
    item_id: str,
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Get a specific menu item by ID.
    
    This endpoint returns a menu item that belongs to the authenticated restaurant.
    
    - **item_id**: The ID of the menu item to retrieve
    
    Returns the menu item details.
    """
    try:
        menu_item = await menu_service.get_menu_item_for_restaurant(item_id, restaurant_id)
        if not menu_item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return menu_item
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve menu item")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{item_id}", response_model=MenuItem)
async def update_menu_item(
    item_id: str,
    menu_item_update: MenuItemUpdate,
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Update a menu item for the authenticated restaurant.
    
    This endpoint updates an existing menu item that belongs to the authenticated restaurant.
    Only provided fields will be updated.
    
    - **item_id**: The ID of the menu item to update
    - **menu_item_update**: Updated menu item information (partial update)
    
    Returns the updated menu item.
    """
    try:
        return await menu_service.update_menu_item_for_restaurant(
            item_id=item_id,
            restaurant_id=restaurant_id,
            menu_item_update=menu_item_update
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to update menu item")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: str,
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Delete a menu item from the authenticated restaurant.
    
    This endpoint permanently deletes a menu item that belongs to the authenticated restaurant.
    This action cannot be undone.
    
    - **item_id**: The ID of the menu item to delete
    
    Returns no content on successful deletion.
    """
    try:
        success = await menu_service.delete_menu_item_for_restaurant(item_id, restaurant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Menu item not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to delete menu item")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{item_id}/availability", response_model=MenuItem)
async def toggle_menu_item_availability(
    item_id: str,
    is_available: bool = Query(..., description="Set availability status"),
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Toggle menu item availability.
    
    This endpoint allows quick toggling of menu item availability without
    updating other fields.
    
    - **item_id**: The ID of the menu item to update
    - **is_available**: New availability status (true/false)
    
    Returns the updated menu item.
    """
    try:
        return await menu_service.toggle_availability(
            item_id=item_id,
            restaurant_id=restaurant_id,
            is_available=is_available
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to update menu item availability")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories/list", response_model=List[str])
async def get_menu_categories(
    restaurant_id: str = Depends(get_current_restaurant_id),
    menu_service: MenuItemService = Depends(get_menu_item_service)
):
    """
    Get all menu categories for the authenticated restaurant.
    
    This endpoint returns unique categories from the restaurant's menu items.
    Only categories with available items are returned.
    
    Returns list of category names.
    """
    try:
        return await menu_service.get_categories_for_restaurant(restaurant_id)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")