"""
Asset configuration API routes (for Local Mode)
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml

from apps.bff.schemas import SaveAssetRequest, SaveAssetResponse

router = APIRouter(
    prefix="/api",
    tags=["assets"],
)

# Config file path - use environment variable or default to mounted config
import os
CONFIG_FILE = Path(os.getenv("CONFIG_FILE", "/app/configs/config.asset.yaml"))


@router.get("/assets")
def get_asset_config():
    """
    Get current asset configuration (Local Mode only).
    
    Reads from the local config.asset.yaml file.
    Returns empty portfolio if file doesn't exist.
    """
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


@router.post("/save", response_model=SaveAssetResponse)
def save_asset_config(config: SaveAssetRequest):
    """
    Save asset configuration (Local Mode only).
    
    Writes to the local config.asset.yaml file.
    """
    # Clean up _localId if present
    if "holdings" in config.portfolio:
        for holding in config.portfolio["holdings"]:
            if "_localId" in holding:
                del holding["_localId"]

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config.portfolio, f, allow_unicode=True, sort_keys=False)
        return SaveAssetResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
