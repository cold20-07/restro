"""Order management API endpoints"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import traceback
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse

from app.core.auth import get_current_restaurant_id
from app.database.service_factory import get_order_service, get_menu_item_service, get_customer_service
from app.models.order import Order, OrderCreate, OrderUpdate, OrderItemCreate, OrderConfirmationResponse
from app.models.enums import OrderStatus, PaymentStatus
from app.services.order_service import OrderService
from app.services.menu_item_service import MenuItemService
from app.services.customer_service import CustomerService
from app.database.base import DatabaseError, NotFoundError
from app.core.input_validation import (
    validate_request_body, 
    validate_path_params, 
    validate_query_params,
    validate_restaurant_endpoint,
    validate_order_endpoint
)
from app.core.exceptions import ValidationError, raise_validation_error, raise_not_found_error
from app.core.validation import validate_order_items, validate_uuid, validate_table_number
from app.core.error_monitoring import record_error
from app.core.logging_config import get_logger

logger = get_logger("order_endpoints")

router = APIRouter()


class OrderCalculationService:
    """Service for order calculations and validation"""
    
    @staticmethod
    async def validate_and_calculate_order(
        order_data: OrderCreate,
        menu_service: MenuItemService
    ) -> tuple[Decimal, List[OrderItemCreate]]:
        """
        Validate order items and calculate total price
        Returns: (total_price, validated_items)
        """
        if not order_data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item"
            )
        
        # Get menu item IDs from order
        menu_item_ids = [item.menu_item_id for item in order_data.items]
        
        # Fetch menu items from database
        menu_items = await menu_service.get_menu_items_by_ids(
            menu_item_ids, 
            order_data.restaurant_id
        )
        
        # Create a lookup dict for menu items
        menu_items_dict = {item.id: item for item in menu_items}
        
        # Validate all items exist and are available
        validated_items = []
        calculated_total = Decimal('0')
        
        for order_item in order_data.items:
            menu_item = menu_items_dict.get(order_item.menu_item_id)
            
            if not menu_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item {order_item.menu_item_id} not found or not available"
                )
            
            if not menu_item.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item '{menu_item.name}' is currently unavailable"
                )
            
            # Create validated order item with correct price
            validated_item = OrderItemCreate(
                menu_item_id=order_item.menu_item_id,
                quantity=order_item.quantity,
                unit_price=menu_item.price
            )
            validated_items.append(validated_item)
            
            # Add to total
            item_total = menu_item.price * order_item.quantity
            calculated_total += item_total
        
        return calculated_total, validated_items


@router.post("/", response_model=OrderConfirmationResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    menu_service: MenuItemService = Depends(get_menu_item_service),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """
    Create a new order for a restaurant
    
    This endpoint handles:
    - Order validation and item verification
    - Price calculation and validation
    - Customer profile creation/update
    - Order creation with items
    """
    try:
        # Validate and calculate order
        calculated_total, validated_items = await OrderCalculationService.validate_and_calculate_order(
            order_data, menu_service
        )
        
        # Verify the submitted total matches calculated total
        if abs(calculated_total - order_data.total_price) > Decimal('0.01'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Price mismatch. Expected: {calculated_total}, Received: {order_data.total_price}"
            )
        
        # Create or update customer profile
        customer = await customer_service.create_or_update_customer(
            restaurant_id=order_data.restaurant_id,
            phone_number=order_data.customer_phone,
            name=order_data.customer_name
        )
        
        # Create order with validated items
        validated_order_data = OrderCreate(
            restaurant_id=order_data.restaurant_id,
            table_number=order_data.table_number,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            total_price=calculated_total,
            items=validated_items
        )
        
        # Create the order
        order = await order_service.create_order_with_items(validated_order_data)
        
        # Update customer's last order time
        await customer_service.update_last_order_time(customer.id, datetime.utcnow())
        
        # Create confirmation response with customer-friendly messaging
        confirmation_response = OrderConfirmationResponse(
            **order.dict(),
            confirmation_message="Your order has been sent to the kitchen and is being prepared!",
            payment_message="Payment will be collected by our staff when your order is ready. We accept cash payments.",
            kitchen_notification_sent=True
        )
        
        return confirmation_response
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    restaurant_id: str = Depends(get_current_restaurant_id),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get a specific order by ID (restaurant owners only)
    """
    try:
        order = await order_service.get_order_for_restaurant(
            order_id=order_id,
            restaurant_id=restaurant_id,
            include_items=True
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}"
        )


@router.put("/{order_id}", response_model=Order)
async def update_order_status(
    order_id: str,
    order_update: OrderUpdate,
    restaurant_id: str = Depends(get_current_restaurant_id),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Update order status (restaurant owners only)
    
    Allows updating order status and payment status for order management
    """
    try:
        # Validate status transitions if needed
        if order_update.order_status:
            await _validate_order_status_transition(
                order_id, order_update.order_status, restaurant_id, order_service
            )
        
        # Get current order to verify it exists and belongs to restaurant
        current_order = await order_service.get_order_for_restaurant(
            order_id=order_id,
            restaurant_id=restaurant_id,
            include_items=False
        )
        
        if not current_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Update the order
        updated_order = await order_service.update(order_id, order_update)
        
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found after update"
            )
        
        # Get the updated order with items
        final_order = await order_service.get_order_for_restaurant(
            order_id=order_id,
            restaurant_id=restaurant_id,
            include_items=True
        )
        
        return final_order
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}"
        )


@router.get("/", response_model=List[Order])
async def get_orders_for_restaurant(
    restaurant_id: str = Depends(get_current_restaurant_id),
    status_filter: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 100,
    include_items: bool = True,
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get orders for the authenticated restaurant
    
    Query parameters:
    - status_filter: Filter by order status
    - skip: Number of orders to skip (pagination)
    - limit: Maximum number of orders to return
    - include_items: Whether to include order items in response
    """
    try:
        orders = await order_service.get_orders_for_restaurant(
            restaurant_id=restaurant_id,
            status_filter=status_filter,
            skip=skip,
            limit=limit,
            include_items=include_items
        )
        
        return orders
        
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )


@router.get("/table/{table_number}", response_model=List[Order])
async def get_orders_by_table(
    table_number: int,
    restaurant_id: str = Depends(get_current_restaurant_id),
    active_only: bool = True,
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get orders for a specific table (restaurant owners only)
    
    Parameters:
    - table_number: The table number to get orders for
    - active_only: If true, only returns non-completed/non-canceled orders
    """
    try:
        if table_number <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table number must be positive"
            )
        
        orders = await order_service.get_orders_by_table(
            restaurant_id=restaurant_id,
            table_number=table_number,
            active_only=active_only
        )
        
        return orders
        
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders by table: {str(e)}"
        )


async def _validate_order_status_transition(
    order_id: str,
    new_status: OrderStatus,
    restaurant_id: str,
    order_service: OrderService
) -> None:
    """
    Validate that the order status transition is allowed
    """
    # Get current order status
    current_order = await order_service.get_order_for_restaurant(
        order_id=order_id,
        restaurant_id=restaurant_id,
        include_items=False
    )
    
    if not current_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    current_status = current_order.order_status
    
    # Define valid status transitions
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELED],
        OrderStatus.CONFIRMED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELED],
        OrderStatus.IN_PROGRESS: [OrderStatus.READY, OrderStatus.CANCELED],
        OrderStatus.READY: [OrderStatus.COMPLETED],
        OrderStatus.COMPLETED: [],  # No transitions from completed
        OrderStatus.CANCELED: []    # No transitions from canceled
    }
    
    # Check if transition is valid
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current_status.value} to {new_status.value}"
        )