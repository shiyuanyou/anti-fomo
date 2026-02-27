"""
Asset configuration schemas
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class AssetConfig(BaseModel):
    """Asset configuration from YAML"""
    portfolio: Dict[str, Any]


class SaveAssetRequest(BaseModel):
    """Request to save asset config"""
    portfolio: Dict[str, Any]


class SaveAssetResponse(BaseModel):
    """Response after saving"""
    status: str
    message: Optional[str] = None
