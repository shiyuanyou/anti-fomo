"""
FastAPI application factory
Anti-FOMO Backend v3.5+
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Anti-FOMO Backend",
        description="Backend services for portfolio analysis, AI, and scheduled jobs",
        version="3.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    def root():
        return {
            "message": "Anti-FOMO Backend v3.5",
            "docs": "/docs",
            "version": "3.5.0",
        }
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
