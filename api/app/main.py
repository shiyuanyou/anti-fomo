"""
FastAPI application factory
Anti-FOMO API v3.3+
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import templates_router, shares_router, assets_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Anti-FOMO API",
        description="Backend API for asset allocation comparison and sharing",
        version="3.3.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://anti-fomo.yoyoostone.cn",
            "http://localhost:5173",
            "http://localhost:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/")
    def root():
        return {
            "message": "Anti-FOMO API v3.3",
            "docs": "/docs",
            "version": "3.3.0",
        }
    
    # Health check
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    # Include routers
    app.include_router(templates_router)
    app.include_router(shares_router)
    app.include_router(assets_router)
    
    return app


# Create application instance
app = create_app()
