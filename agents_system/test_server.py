#!/usr/bin/env python3
"""Simple test server to verify agent system functionality."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Simple test app
app = FastAPI(title="Super Admin Agent Test", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Super Admin Agent Test Server is running!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "super_admin_agent_test",
        "version": "1.0.0"
    }

@app.get("/test")
async def test_imports():
    """Test if we can import all the agent modules."""
    try:
        # Test basic imports
        from agents_system.config.settings import settings
        from agents_system.models.schemas import ChatRequest
        
        return {
            "imports": "success",
            "openai_configured": bool(settings.openai_api_key),
            "supabase_configured": bool(settings.supabase_url),
            "jwt_configured": bool(settings.jwt_secret)
        }
    except Exception as e:
        return {
            "imports": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
