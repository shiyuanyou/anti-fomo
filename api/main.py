"""
FastAPI backend for Anti-FOMO v3.3+
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import yaml
from typing import Optional
import os

import models, schemas, crud
from models import get_db

# Create FastAPI app
app = FastAPI(
    title="Anti-FOMO API",
    description="Backend API for asset allocation comparison and sharing",
    version="3.3.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://anti-fomo.yoyoostone.cn",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config file path
CONFIG_FILE = Path(__file__).parent.parent / "config.asset.yaml"


@app.get("/")
def root():
    return {"message": "Anti-FOMO API v3.3", "docs": "/docs"}


# Template endpoints
@app.get("/api/templates", response_model=list[schemas.TemplateResponse])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all official templates"""
    templates = crud.get_templates(db, skip=skip, limit=limit)
    return templates


@app.get("/api/templates/{template_id}", response_model=schemas.TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a specific template by ID"""
    template = crud.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# Share endpoints
@app.post("/api/shares", response_model=schemas.ShareResponse)
def create_share(share: schemas.ShareCreate, db: Session = Depends(get_db)):
    """Create a new share"""
    return crud.create_share(db=db, share=share)


@app.get("/api/shares/{share_id}", response_model=schemas.ShareResponse)
def get_share(share_id: str, db: Session = Depends(get_db)):
    """Get a shared configuration"""
    share = crud.get_share(db, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    return share


# Asset config endpoints (for Local Mode)
@app.get("/api/assets")
def get_asset_config():
    """Get current asset configuration (Local Mode)"""
    if not CONFIG_FILE.exists():
        return {"portfolio": {"total_amount": 0, "holdings": []}}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                data = {"portfolio": {"total_amount": 0, "holdings": []}}
            return data
    except yaml.YAMLError:
        return {"portfolio": {"total_amount": 0, "holdings": []}}


@app.post("/api/save")
def save_asset_config(config: schemas.SaveAssetRequest):
    """Save asset configuration (Local Mode)"""
    # Clean up _localId if present
    if "portfolio" in config.portfolio and "holdings" in config.portfolio["portfolio"]:
        for holding in config.portfolio["portfolio"]["holdings"]:
            if "_localId" in holding:
                del holding["_localId"]

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config.portfolio, f, allow_unicode=True, sort_keys=False)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
