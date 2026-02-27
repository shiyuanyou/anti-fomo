"""
Share API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.models import get_db
from api.schemas import ShareCreate, ShareResponse
from api.crud import create_share, get_share

router = APIRouter(
    prefix="/api/shares",
    tags=["shares"],
)


@router.post("", response_model=ShareResponse)
def create_new_share(
    share: ShareCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio share.
    
    Returns the created share with its generated ID.
    """
    return create_share(db=db, share=share)


@router.get("/{share_id}", response_model=ShareResponse)
def get_share_by_id(share_id: str, db: Session = Depends(get_db)):
    """
    Get a shared portfolio configuration.
    
    - **share_id**: Share identifier (e.g., "AF-SHARE-A1B2C3D4")
    """
    share = get_share(db, share_id)
    if not share:
        raise HTTPException(status_code=404, detail=f"Share '{share_id}' not found")
    return share
