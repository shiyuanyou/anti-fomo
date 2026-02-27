"""
Share CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
import uuid
from api.models import Share
from api.schemas import ShareCreate


def generate_share_id() -> str:
    """Generate a unique share ID"""
    return f"AF-SHARE-{uuid.uuid4().hex[:8].upper()}"


def get_share(db: Session, share_id: str) -> Optional[Share]:
    """Get a share by ID"""
    return db.execute(
        select(Share).where(Share.id == share_id)
    ).scalar_one_or_none()


def get_shares(
    db: Session, skip: int = 0, limit: int = 50
) -> List[Share]:
    """Get recent shares"""
    result = db.execute(
        select(Share).order_by(Share.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


def create_share(db: Session, share: ShareCreate) -> Share:
    """Create a new share"""
    share_id = generate_share_id()
    
    db_share = Share(
        id=share_id,
        name=share.name,
        author=share.author or "Anonymous",
        description=share.description,
        config_json=share.config_json,
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def delete_share(db: Session, share_id: str) -> bool:
    """Delete a share"""
    share = get_share(db, share_id)
    if share:
        db.delete(share)
        db.commit()
        return True
    return False
