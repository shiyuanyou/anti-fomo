"""
CRUD operations for database models
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
import models, schemas


# Template CRUD operations
def get_template(db: Session, template_id: str) -> Optional[models.Template]:
    """Get a template by ID"""
    return db.execute(
        select(models.Template).where(models.Template.id == template_id)
    ).scalar_one_or_none()


def get_templates(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Template]:
    """Get all templates with pagination"""
    result = db.execute(
        select(models.Template).offset(skip).limit(limit)
    )
    return result.scalars().all()


def create_template(
    db: Session, template: schemas.TemplateCreate
) -> models.Template:
    """Create a new template"""
    db_template = models.Template(
        id=template.id,
        name=template.name,
        description=template.description,
        allocation=template.allocation,
        metrics=template.metrics,
        tags=template.tags,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


# Share CRUD operations
def get_share(db: Session, share_id: str) -> Optional[models.Share]:
    """Get a share by ID"""
    return db.execute(
        select(models.Share).where(models.Share.id == share_id)
    ).scalar_one_or_none()


def create_share(db: Session, share: schemas.ShareCreate) -> models.Share:
    """Create a new share"""
    # Generate share ID if not provided
    import uuid

    share_id = f"AF-SHARE-{uuid.uuid4().hex[:8].upper()}"

    db_share = models.Share(
        id=share_id, name=share.name, author=share.author, config_json=share.config_json
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def get_recent_shares(
    db: Session, limit: int = 50
) -> List[models.Share]:
    """Get recent shares ordered by creation time"""
    result = db.execute(
        select(models.Share)
        .order_by(models.Share.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
