"""Base model classes for the QR Code Ordering System"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class BaseDBModel(BaseModel):
    """Base model for database entities"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseCreateModel(BaseModel):
    """Base model for create operations"""
    
    class Config:
        from_attributes = True


class BaseUpdateModel(BaseModel):
    """Base model for update operations"""
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True