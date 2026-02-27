"""
Share schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ShareCreate(BaseModel):
    """Schema for creating a share"""
    name: str = Field(..., description="Configuration name")
    author: Optional[str] = Field("Anonymous", description="Author name")
    description: Optional[str] = Field("", description="Description")
    config_json: Dict[str, Any] = Field(..., description="Full portfolio configuration")


class ShareResponse(BaseModel):
    """Full share response"""
    id: str = Field(..., description="Share ID")
    name: str
    author: str
    description: Optional[str]
    config_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ShareListItem(BaseModel):
    """Lightweight share for list views"""
    id: str
    name: str
    author: str
    created_at: datetime

    class Config:
        from_attributes = True
