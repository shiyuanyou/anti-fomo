"""
Share model - user-shared portfolio configurations
"""
from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from .database import Base


class Share(Base):
    """User-shared portfolio configurations"""
    __tablename__ = "shares"

    id = Column(String(30), primary_key=True)  # e.g., "AF-SHARE-A1B2C3"
    name = Column(String(100), nullable=False)
    author = Column(String(50), default="Anonymous")
    description = Column(Text)
    config_json = Column(JSON, nullable=False)  # Full portfolio configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Share(id='{self.id}', name='{self.name}', author='{self.author}')>"
