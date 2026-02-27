"""
Template API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.models import get_db
from api.schemas import TemplateResponse, TemplateListItem
from api.crud import get_template, get_templates

router = APIRouter(
    prefix="/api/templates",
    tags=["templates"],
)


@router.get("", response_model=List[TemplateResponse])
def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all official templates.
    
    Returns a list of all available asset allocation templates
    with complete details including allocations, metrics, and tags.
    """
    templates = get_templates(db, skip=skip, limit=limit)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template_by_id(template_id: str, db: Session = Depends(get_db)):
    """
    Get a specific template by ID.
    
    - **template_id**: Template identifier (e.g., "global_balanced")
    """
    template = get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template
