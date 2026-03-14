#!/usr/bin/env python3
"""
Entry point for Backend FastAPI server
Usage: python3 -m uvicorn apps.backend.main:app --reload --port 8002
"""
from apps.backend.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.backend.main:app", host="127.0.0.1", port=8002, reload=True)
