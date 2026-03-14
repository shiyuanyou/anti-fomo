"""
Notification model - notification records
"""
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from apps.backend.models.database import Base


class Notification(Base):
    """Notification delivery records"""
    __tablename__ = "notifications"

    id = Column(String(50), primary_key=True)
    notification_type = Column(String(20), nullable=False)  # "email", "webhook", "dingtalk"
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # "pending", "sent", "failed"
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    metadata = Column(JSON)  # {recipients, channel_config}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Notification(id='{self.id}', type='{self.notification_type}', status='{self.status}')>"
