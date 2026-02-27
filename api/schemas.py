"""
Pydantic schemas for FastAPI request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TemplateBase(BaseModel):
    """Base schema for Template"""
    id: str = Field(..., description="Template ID (e.g., AF-T001)")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Detailed description")
    allocation: Dict[str, float] = Field(..., description="Asset allocation (symbol: weight)")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    tags: Optional[List[str]] = Field(None, description="Template tags")


class TemplateCreate(TemplateBase):
    """Schema for creating a new template"""
    pass


class TemplateResponse(TemplateBase):
    """Response schema for Template"""
    created_at: datetime

    class Config:
        from_attributes = True


class ShareCreate(BaseModel):
    """Schema for creating a new share"""
    name: str = Field(..., description="User-defined configuration name")
    author: Optional[str] = Field("", description="Author name")
    config_json: Dict[str, Any] = Field(..., description="Full configuration data")


class ShareResponse(BaseModel):
    """Response schema for Share"""
    id: str = Field(..., description="Share ID (e.g., AF-SHARE-A1B2C3)")
    name: str = Field(..., description="Configuration name")
    author: str = Field(..., description="Author name")
    config_json: Dict[str, Any] = Field(..., description="Configuration data")
    created_at: datetime

    class Config:
        from_attributes = True


# For config.asset.yaml operations
class AssetConfig(BaseModel):
    """Asset configuration from YAML file"""
    portfolio: Dict[str, Any]


class SaveAssetRequest(BaseModel):
    """Request schema for saving asset config"""
    portfolio: Dict[str, Any]
