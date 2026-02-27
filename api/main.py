#!/usr/bin/env python3
"""
Entry point for FastAPI server
Usage: python3 -m api.main
Or: uvicorn api.main:app --reload --port 8000
"""
from api.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
