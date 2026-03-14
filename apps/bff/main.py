#!/usr/bin/env python3
"""
Entry point for BFF FastAPI server
Usage: python3 -m uvicorn apps.bff.main:app --reload --port 8001
"""
from apps.bff.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.bff.main:app", host="127.0.0.1", port=8001, reload=True)
