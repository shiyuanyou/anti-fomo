"""
Template CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from api.models import Template
from api.schemas import TemplateCreate


def get_template(db: Session, template_id: str) -> Optional[Template]:
    """Get a template by ID"""
    return db.execute(
        select(Template).where(Template.id == template_id)
    ).scalar_one_or_none()


def get_templates(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Template]:
    """Get all templates"""
    result = db.execute(
        select(Template).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


def create_template(db: Session, template: TemplateCreate) -> Template:
    """Create a new template"""
    db_template = Template(
        id=template.id,
        name=template.name,
        tagline=template.tagline,
        description=template.description,
        target_audience=template.target_audience,
        risk_level=template.risk_level,
        allocations=[item.model_dump() for item in template.allocations],
        allocation=template.allocation,
        metrics=template.metrics.model_dump(),
        personality_tags=template.personality_tags,
        original_data=template.original_data,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: str) -> bool:
    """Delete a template"""
    template = get_template(db, template_id)
    if template:
        db.delete(template)
        db.commit()
        return True
    return False


def delete_all_templates(db: Session) -> int:
    """Delete all templates, return count"""
    count = db.query(Template).delete()
    db.commit()
    return count
