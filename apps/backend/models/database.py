"""
Database configuration for Jobs service
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

Base = declarative_base()


def get_database_url() -> str:
    """Get SQLite database URL from environment or default"""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db_dir = os.path.join(project_root, "data", "jobs")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "anti-fomo-jobs.db")
    return f"sqlite:///{db_path}"


engine = create_engine(get_database_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session (FastAPI dependency)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
