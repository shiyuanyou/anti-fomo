"""
Template model - matches templates.json structure
"""
from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from .database import Base


class Template(Base):
    """Official template library - asset allocation templates"""
    __tablename__ = "templates"

    # Primary fields from templates.json
    id = Column(String(30), primary_key=True)  # e.g., "global_balanced"
    name = Column(String(100), nullable=False)
    tagline = Column(String(200))
    description = Column(Text, nullable=False)
    target_audience = Column(String(200))
    risk_level = Column(String(10))  # "低" / "中" / "中高" / "高"
    
    # Complex allocations structure
    allocations = Column(JSON, nullable=False)  # [{"category": "A股大盘", "region": "中国", "weight": 0.2}]
    
    # Simple allocation for quick lookup
    allocation = Column(JSON)  # {"A股大盘": 20, "债券": 30} - percentage format
    
    # Metrics
    metrics = Column(JSON, nullable=False)  # {expected_return, volatility, max_drawdown, sharpe_ratio, data_period}
    
    # Tags
    personality_tags = Column(JSON)  # ["无国界思维", "追求平稳"]
    
    # Full original data for compatibility
    original_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Template(id='{self.id}', name='{self.name}')>"
