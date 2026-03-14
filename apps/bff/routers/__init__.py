"""
Routers package initialization
"""
from fastapi import APIRouter

# Import all routers
from .templates import router as templates_router
from .shares import router as shares_router
from .assets import router as assets_router

__all__ = [
    "templates_router",
    "shares_router",
    "assets_router",
]
