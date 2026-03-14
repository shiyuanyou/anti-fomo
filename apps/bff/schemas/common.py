"""
Common response schemas
"""
from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response"""
    message: str
    data: Optional[dict] = None
