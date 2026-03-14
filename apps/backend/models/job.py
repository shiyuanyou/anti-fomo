"""
Job model - scheduled task execution records
"""
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from apps.backend.models.database import Base


class Job(Base):
    """Scheduled job execution records"""
    __tablename__ = "jobs"

    id = Column(String(50), primary_key=True)
    job_type = Column(String(20), nullable=False)  # "daily_check", "weekly_report"
    status = Column(String(20), nullable=False)  # "pending", "running", "completed", "failed"
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    result = Column(JSON)  # {portfolio_result, alert_result, decision}
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Job(id='{self.id}', type='{self.job_type}', status='{self.status}')>"
