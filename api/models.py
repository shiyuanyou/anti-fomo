"""
SQLAlchemy database models for Anti-FOMO v3.3+
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Base class for all models
Base = declarative_base()


class Template(Base):
    """Official template library - asset allocation templates"""
    __tablename__ = "templates"

    id = Column(String(20), primary_key=True)  # e.g., "AF-T001"
    name = Column(String(100), nullable=False)  # Template name
    description = Column(Text, nullable=False)  # Detailed description
    allocation = Column(JSON, nullable=False)  # {"SPY": 60, "TLT": 40}
    metrics = Column(JSON)  # {"expected_return": 0.08, "volatility": 0.12}
    tags = Column(JSON)  # ["全天候", "保守型"]
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Template(id='{self.id}', name='{self.name}')>"


class Share(Base):
    """User-shared portfolio configurations"""
    __tablename__ = "shares"

    id = Column(String(30), primary_key=True)  # e.g., "AF-SHARE-A1B2C3"
    name = Column(String(100), nullable=False)  # User-defined name
    author = Column(String(50), default="")  # Author name
    config_json = Column(JSON, nullable=False)  # Full configuration data
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Share(id='{self.id}', name='{self.name}', author='{self.author}')>"


# Database connection setup
def get_database_url() -> str:
    """Get SQLite database URL"""
    # Use project root for SQLite file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "anti-fomo.db")
    return f"sqlite:///{db_path}"


def create_tables():
    """Create all tables in the database"""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (for FastAPI dependency)"""
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
