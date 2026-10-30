"""Pydantic schemas for collections."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique collection name")
    description: Optional[str] = Field(None, max_length=1000)


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionResponse(CollectionBase):
    id: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
