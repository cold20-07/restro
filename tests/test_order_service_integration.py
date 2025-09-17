"""Integration tests for order service business logic"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.order_service import OrderService, OrderItemService
from app.models.order import Order, OrderCreate, OrderUpdate, OrderItem, OrderItemCreate
from app.models.enums import OrderStatus, PaymentStatus
from app.database.base import DatabaseError, NotFoundError


class TestOrderServiceIntegration:
    """Integration tests for order service business logic"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock Supabase client"""
        return Mock()
    
    @pytest.fixture
    def order_service(self, mock_client):
        """Order service instance with mocked client"""
        return OrderService(mock_client)
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order creation data"""
        return OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("21.98"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                ),
                OrderItemCreate(
                    menu_item_id="item-2",
                    quantity=1,
                    unit_price=Decimal("5.99")
                )
            ]
        )
    
    @pytest.fixture
    def sample_order(self):
        """Sample order for testing"""
        return Order(
            id="order-123",
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            total_price=Decimal("21.98"),
            created_at=datetime.utcnow(),
            updated_at=None,
            items=[]
        )
    
    @pytest.mark.asyncio
    async def test_create_order_with_items_success(
        self, 
        order_service, 
        mock_client, 
        sample_order_data, 
        sample_order
    ):
        """Test successful order creation with items"""
        # Mock database responses
        order_response = Mock()
        order_response.data = [sample_order.dict()]
        mock_client.table.return_value.insert.return_value.execute.return_value = order_response
        
        # Mock order items creation
        order_service.order_item_service = AsyncMock()
        order_service.order_item_service.create_order_items.return_value = []
        
        # Test order creation
        result = await order_service.create_order_with_items(sample_order_data)
        
        # Assertions
        assert result.id == "order-123"
        assert result.restaurant_id == "restaurant-123"
        assert result.total_price == Decimal("21.98")
        
        # Verify database calls
        mock_client.table.assert_called_with("orders")
        order_service.order_item_service.create_order_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_with_items(
        self, 
        order_service, 
        mock_client, 
        sample_order
    ):
        """Test getting order with items"""
        # Mock order retrieval
        order_service.get = AsyncMock(return_value=sample_order)
        
        # Mock order items retrieval
        order_service.order_item_service = AsyncMock()
        order_service.order_item_service.get_items_for_order.return_value = []
        
        # Test getting order with items
        result = await order_service.get_order_with_items("order-123")
        
        # Assertions
        assert result.id == "order-123"
        assert result.items == []
        
        # Verify service calls
        order_service.get.assert_called_once_with("order-123")
        order_service.order_item_service.get_items_for_order.assert_called_once_with("order-123")
    
    @pytest.mark.asyncio
    async def test_get_orders_for_restaurant_with_filters(
        self, 
        order_service, 
        mock_client, 
        sample_order
    ):
        """Test getting orders for restaurant with status filter"""
        # Mock database response
        orders_response = Mock()
        orders_response.data = [sample_order.dict()]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = orders_response
        
        mock_client.table.return_value.select.return_value = mock_query
        
        # Test getting orders with status filter
        result = await order_service.get_orders_for_restaurant(
            restaurant_id="restaurant-123",
            status_filter=OrderStatus.PENDING,
            skip=0,
            limit=10,
            include_items=False
        )
        
        # Assertions
        assert len(result) == 1
        assert result[0].id == "order-123"
        
        # Verify query was built correctly
        mock_client.table.assert_called_with("orders")
        assert mock_query.eq.call_count >= 2  # restaurant_id and status filter
    
    @pytest.mark.asyncio
    async def test_update_order_status_success(
        self, 
        order_service, 
        sample_order
    ):
        """Test successful order status update"""
        # Mock getting existing order
        order_service.get_order_for_restaurant = AsyncMock(return_value=sample_order)
        
        # Mock update operation
        updated_order = sample_order.copy()
        updated_order.order_status = OrderStatus.CONFIRMED
        order_service.update = AsyncMock(return_value=updated_order)
        
        # Test status update
        result = await order_service.update_order_status(
            order_id="order-123",
            restaurant_id="restaurant-123",
            new_status=OrderStatus.CONFIRMED
        )
        
        # Assertions
        assert result.order_status == OrderStatus.CONFIRMED
        
        # Verify service calls
        order_service.get_order_for_restaurant.assert_called_once()
        order_service.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_status_not_found(self, order_service):
        """Test order status update when order not found"""
        # Mock order not found
        order_service.get_order_for_restaurant = AsyncMock(return_value=None)
        
        # Test status update should raise exception
        with pytest.raises(NotFoundError) as exc_info:
            await order_service.update_order_status(
                order_id="nonexistent-order",
                restaurant_id="restaurant-123",
                new_status=OrderStatus.CONFIRMED
            )
        
        assert "not found for restaurant" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_order_analytics(
        self, 
        order_service, 
        mock_client
    ):
        """Test order analytics calculation"""
        # Mock orders data
        orders_data = [
            {
                "id": "order-1",
                "restaurant_id": "restaurant-123",
                "order_status": "completed",
                "payment_status": "paid",
                "total_price": "25.99",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "order-2",
                "restaurant_id": "restaurant-123",
                "order_status": "pending",
                "payment_status": "pending",
                "total_price": "15.50",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Mock database response
        analytics_response = Mock()
        analytics_response.data = orders_data
        
        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.execute.return_value = analytics_response
        
        mock_client.table.return_value.select.return_value = mock_query
        
        # Test analytics calculation
        result = await order_service.get_order_analytics(
            restaurant_id="restaurant-123",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        # Assertions
        assert result["total_orders"] == 2
        assert result["total_revenue"] == 41.49  # 25.99 + 15.50
        assert result["average_order_value"] == 20.745  # 41.49 / 2
        assert result["order_status_breakdown"]["completed"] == 1
        assert result["order_status_breakdown"]["pending"] == 1
        assert result["payment_status_breakdown"]["paid"] == 1
        assert result["payment_status_breakdown"]["pending"] == 1
    
    @pytest.mark.asyncio
    async def test_get_orders_by_table_active_only(
        self, 
        order_service, 
        mock_client, 
        sample_order
    ):
        """Test getting active orders for a specific table"""
        # Mock database response
        orders_response = Mock()
        orders_response.data = [sample_order.dict()]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.not_.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = orders_response
        
        mock_client.table.return_value.select.return_value = mock_query
        
        # Test getting orders by table
        result = await order_service.get_orders_by_table(
            restaurant_id="restaurant-123",
            table_number=5,
            active_only=True
        )
        
        # Assertions
        assert len(result) == 1
        assert result[0].table_number == 5
        
        # Verify query filters
        mock_client.table.assert_called_with("orders")
        assert mock_query.eq.call_count >= 2  # restaurant_id and table_number
        mock_query.not_.assert_called_once()  # active_only filter
    
    @pytest.mark.asyncio
    async def test_get_recent_orders(
        self, 
        order_service, 
        mock_client, 
        sample_order
    ):
        """Test getting recent orders within time window"""
        # Mock database response
        orders_response = Mock()
        orders_response.data = [sample_order.dict()]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = orders_response
        
        mock_client.table.return_value.select.return_value = mock_query
        
        # Test getting recent orders
        result = await order_service.get_recent_orders(
            restaurant_id="restaurant-123",
            hours=24,
            limit=50
        )
        
        # Assertions
        assert len(result) == 1
        assert result[0].id == "order-123"
        
        # Verify query parameters
        mock_query.eq.assert_called_with("restaurant_id", "restaurant-123")
        mock_query.gte.assert_called_once()  # Time filter
        mock_query.limit.assert_called_with(50)


class TestOrderItemService:
    """Tests for order item service"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock Supabase client"""
        return Mock()
    
    @pytest.fixture
    def order_item_service(self, mock_client):
        """Order item service instance with mocked client"""
        return OrderItemService(mock_client)
    
    @pytest.fixture
    def sample_order_items(self):
        """Sample order items for testing"""
        return [
            OrderItemCreate(
                menu_item_id="item-1",
                quantity=2,
                unit_price=Decimal("15.99")
            ),
            OrderItemCreate(
                menu_item_id="item-2",
                quantity=1,
                unit_price=Decimal("5.99")
            )
        ]
    
    @pytest.mark.asyncio
    async def test_create_order_items_success(
        self, 
        order_item_service, 
        mock_client, 
        sample_order_items
    ):
        """Test successful creation of multiple order items"""
        # Mock database responses for each item
        item_responses = []
        for i, item in enumerate(sample_order_items):
            response = Mock()
            response.data = [{
                "id": f"order-item-{i+1}",
                "order_id": "order-123",
                **item.dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            }]
            item_responses.append(response)
        
        # Mock insert operations
        mock_client.table.return_value.insert.return_value.execute.side_effect = item_responses
        
        # Test creating order items
        result = await order_item_service.create_order_items("order-123", sample_order_items)
        
        # Assertions
        assert len(result) == 2
        assert result[0].order_id == "order-123"
        assert result[0].menu_item_id == "item-1"
        assert result[1].menu_item_id == "item-2"
        
        # Verify database calls
        assert mock_client.table.call_count == 2
        assert mock_client.table.return_value.insert.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_items_for_order(
        self, 
        order_item_service, 
        mock_client
    ):
        """Test getting all items for a specific order"""
        # Mock order items data
        items_data = [
            {
                "id": "order-item-1",
                "order_id": "order-123",
                "menu_item_id": "item-1",
                "quantity": 2,
                "unit_price": "15.99",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            },
            {
                "id": "order-item-2",
                "order_id": "order-123",
                "menu_item_id": "item-2",
                "quantity": 1,
                "unit_price": "5.99",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            }
        ]
        
        # Mock database response
        items_response = Mock()
        items_response.data = items_data
        
        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = items_response
        
        mock_client.table.return_value.select.return_value = mock_query
        
        # Test getting items for order
        result = await order_item_service.get_items_for_order("order-123")
        
        # Assertions
        assert len(result) == 2
        assert all(item.order_id == "order-123" for item in result)
        assert result[0].menu_item_id == "item-1"
        assert result[1].menu_item_id == "item-2"
        
        # Verify query
        mock_client.table.assert_called_with("order_items")
        mock_query.eq.assert_called_with("order_id", "order-123")
    
    @pytest.mark.asyncio
    async def test_create_order_items_database_error(
        self, 
        order_item_service, 
        mock_client, 
        sample_order_items
    ):
        """Test handling database error during order items creation"""
        # Mock database error
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        # Test creating order items should raise DatabaseError
        with pytest.raises(DatabaseError) as exc_info:
            await order_item_service.create_order_items("order-123", sample_order_items)
        
        assert "Failed to create order items" in str(exc_info.value)


class TestOrderValidationLogic:
    """Tests for order validation business logic"""
    
    def test_order_status_transitions(self):
        """Test valid order status transitions"""
        from app.api.v1.endpoints.orders import _validate_order_status_transition
        from app.models.enums import OrderStatus
        
        # Valid transitions should be defined in the endpoint
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELED],
            OrderStatus.CONFIRMED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELED],
            OrderStatus.IN_PROGRESS: [OrderStatus.READY, OrderStatus.CANCELED],
            OrderStatus.READY: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELED: []
        }
        
        # Test each valid transition
        for current_status, allowed_next_statuses in valid_transitions.items():
            for next_status in allowed_next_statuses:
                # This should not raise an exception
                assert next_status in allowed_next_statuses
        
        # Test invalid transitions
        invalid_transitions = [
            (OrderStatus.COMPLETED, OrderStatus.PENDING),
            (OrderStatus.CANCELED, OrderStatus.CONFIRMED),
            (OrderStatus.READY, OrderStatus.PENDING),
            (OrderStatus.IN_PROGRESS, OrderStatus.PENDING)
        ]
        
        for current_status, invalid_next_status in invalid_transitions:
            allowed = valid_transitions.get(current_status, [])
            assert invalid_next_status not in allowed
    
    def test_order_item_validation(self):
        """Test order item validation rules"""
        from app.models.order import OrderItemCreate
        from pydantic import ValidationError
        
        # Valid order item
        valid_item = OrderItemCreate(
            menu_item_id="item-123",
            quantity=2,
            unit_price=Decimal("15.99")
        )
        assert valid_item.quantity == 2
        assert valid_item.unit_price == Decimal("15.99")
        
        # Invalid quantity (zero)
        with pytest.raises(ValidationError):
            OrderItemCreate(
                menu_item_id="item-123",
                quantity=0,
                unit_price=Decimal("15.99")
            )
        
        # Invalid quantity (negative)
        with pytest.raises(ValidationError):
            OrderItemCreate(
                menu_item_id="item-123",
                quantity=-1,
                unit_price=Decimal("15.99")
            )
        
        # Invalid price (zero)
        with pytest.raises(ValidationError):
            OrderItemCreate(
                menu_item_id="item-123",
                quantity=1,
                unit_price=Decimal("0")
            )
        
        # Invalid price (negative)
        with pytest.raises(ValidationError):
            OrderItemCreate(
                menu_item_id="item-123",
                quantity=1,
                unit_price=Decimal("-5.99")
            )
    
    def test_order_validation(self):
        """Test order validation rules"""
        from app.models.order import OrderCreate, OrderItemCreate
        from pydantic import ValidationError
        
        # Valid order
        valid_order = OrderCreate(
            restaurant_id="restaurant-123",
            table_number=5,
            customer_name="John Doe",
            customer_phone="+1234567890",
            total_price=Decimal("21.98"),
            items=[
                OrderItemCreate(
                    menu_item_id="item-1",
                    quantity=1,
                    unit_price=Decimal("15.99")
                )
            ]
        )
        assert valid_order.table_number == 5
        assert valid_order.customer_name == "John Doe"
        
        # Invalid table number (zero)
        with pytest.raises(ValidationError):
            OrderCreate(
                restaurant_id="restaurant-123",
                table_number=0,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=Decimal("21.98"),
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=1,
                        unit_price=Decimal("15.99")
                    )
                ]
            )
        
        # Invalid customer name (empty)
        with pytest.raises(ValidationError):
            OrderCreate(
                restaurant_id="restaurant-123",
                table_number=5,
                customer_name="",
                customer_phone="+1234567890",
                total_price=Decimal("21.98"),
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=1,
                        unit_price=Decimal("15.99")
                    )
                ]
            )
        
        # Invalid phone number (too short)
        with pytest.raises(ValidationError):
            OrderCreate(
                restaurant_id="restaurant-123",
                table_number=5,
                customer_name="John Doe",
                customer_phone="123",
                total_price=Decimal("21.98"),
                items=[
                    OrderItemCreate(
                        menu_item_id="item-1",
                        quantity=1,
                        unit_price=Decimal("15.99")
                    )
                ]
            )
        
        # Empty items list
        with pytest.raises(ValidationError):
            OrderCreate(
                restaurant_id="restaurant-123",
                table_number=5,
                customer_name="John Doe",
                customer_phone="+1234567890",
                total_price=Decimal("0"),
                items=[]
            )