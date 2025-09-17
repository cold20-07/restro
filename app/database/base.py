"""Base database service class with common CRUD operations"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from pydantic import BaseModel
from supabase import Client
from app.database.supabase_client import supabase_client
from app.core.exceptions import DatabaseError, NotFoundError, ValidationError
from app.core.logging_config import get_logger, LogOperationTime

# Type variables for generic CRUD operations
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = get_logger("database")


class BaseDatabaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base database service with common CRUD operations"""
    
    def __init__(
        self,
        model: Type[ModelType],
        table_name: str,
        client: Optional[Client] = None
    ):
        self.model = model
        self.table_name = table_name
        self.client = client or supabase_client.client
    
    def _handle_response(self, response) -> Any:
        """Handle Supabase response and raise appropriate exceptions"""
        if hasattr(response, 'error') and response.error:
            logger.error(f"Database operation failed on {self.table_name}: {response.error}")
            raise DatabaseError(f"Database operation failed: {response.error}")
        return response.data
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        with LogOperationTime(logger, f"create {self.table_name}"):
            try:
                data = obj_in.dict(exclude_unset=True)
                response = self.client.table(self.table_name).insert(data).execute()
                result = self._handle_response(response)
                
                if not result:
                    raise DatabaseError("Failed to create record")
                
                created_record = self.model(**result[0])
                logger.info(f"Created {self.table_name} record", extra={"record_id": created_record.id})
                return created_record
            except Exception as e:
                if isinstance(e, DatabaseError):
                    raise
                logger.error(f"Failed to create {self.table_name}: {str(e)}")
                raise DatabaseError(f"Failed to create {self.table_name}: {str(e)}")
    
    async def get(self, id: str) -> Optional[ModelType]:
        """Get a record by ID"""
        try:
            response = self.client.table(self.table_name).select("*").eq("id", id).execute()
            result = self._handle_response(response)
            
            if not result:
                return None
            
            return self.model(**result[0])
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get {self.table_name}: {str(e)}")
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get multiple records with optional filtering and pagination"""
        try:
            query = self.client.table(self.table_name).select("*")
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply ordering
            if order_by:
                query = query.order(order_by)
            
            # Apply pagination
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            result = self._handle_response(response)
            
            return [self.model(**item) for item in result]
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to get {self.table_name} list: {str(e)}")
    
    async def update(self, id: str, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record by ID"""
        try:
            data = obj_in.dict(exclude_unset=True)
            if not data:
                # No fields to update
                return await self.get(id)
            
            response = self.client.table(self.table_name).update(data).eq("id", id).execute()
            result = self._handle_response(response)
            
            if not result:
                return None
            
            return self.model(**result[0])
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to update {self.table_name}: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete a record by ID"""
        try:
            response = self.client.table(self.table_name).delete().eq("id", id).execute()
            result = self._handle_response(response)
            
            return len(result) > 0
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to delete {self.table_name}: {str(e)}")
    
    async def exists(self, id: str) -> bool:
        """Check if a record exists by ID"""
        try:
            response = self.client.table(self.table_name).select("id").eq("id", id).execute()
            result = self._handle_response(response)
            
            return len(result) > 0
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to check existence in {self.table_name}: {str(e)}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        try:
            query = self.client.table(self.table_name).select("id", count="exact")
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.count or 0
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to count {self.table_name}: {str(e)}")