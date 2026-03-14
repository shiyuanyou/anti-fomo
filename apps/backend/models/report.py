"""
Report model - generated reports
"""
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from apps.backend.models.database import Base


class Report(Base):
    """Generated reports storage"""
    __tablename__ = "reports"

    id = Column(String(50), primary_key=True)
    report_type = Column(String(20), nullable=False)  # "daily_digest", "weekly_report"
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON)  # {portfolio_summary, market_status, ai_analysis}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Report(id='{self.id}', type='{self.report_type}', title='{self.title}')>"
