"""
Template schemas - matches templates.json structure
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AllocationItem(BaseModel):
    """Single allocation entry"""
    category: str = Field(..., description="Asset category, e.g., 'A股大盘'")
    region: str = Field(..., description="Geographic region, e.g., '中国'")
    weight: float = Field(..., description="Weight as decimal, e.g., 0.2 for 20%")


class TemplateMetrics(BaseModel):
    """Template performance metrics"""
    expected_return: float = Field(..., description="Expected annual return in %")
    volatility: float = Field(..., description="Annual volatility in %")
    max_drawdown: float = Field(..., description="Maximum drawdown in %")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    data_period: str = Field(..., description="Data period description")


class TemplateBase(BaseModel):
    """Base template schema"""
    id: str = Field(..., description="Template ID, e.g., 'global_balanced'")
    name: str = Field(..., description="Template name")
    tagline: str = Field(..., description="Short tagline")
    description: str = Field(..., description="Detailed description")
    target_audience: str = Field(..., description="Target investor type")
    risk_level: str = Field(..., description="Risk level: 低/中/中高/高")


class TemplateCreate(TemplateBase):
    """Schema for creating a template"""
    allocations: List[AllocationItem] = Field(..., description="Detailed allocations")
    allocation: Optional[Dict[str, float]] = Field(None, description="Simple allocation dict")
    metrics: TemplateMetrics = Field(..., description="Performance metrics")
    personality_tags: List[str] = Field(default_factory=list, description="Personality tags")
    original_data: Optional[Dict[str, Any]] = Field(None, description="Original data backup")


class TemplateResponse(TemplateBase):
    """Full template response - matches templates.json"""
    allocations: List[AllocationItem]
    allocation: Optional[Dict[str, float]]
    metrics: TemplateMetrics
    personality_tags: List[str]
    original_data: Optional[Dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateListItem(BaseModel):
    """Lightweight template for list views"""
    id: str
    name: str
    tagline: str
    risk_level: str
    metrics: TemplateMetrics
    personality_tags: List[str]

    class Config:
        from_attributes = True
