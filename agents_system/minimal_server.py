#!/usr/bin/env python3
"""Minimal server for testing Super Admin Agent APIs."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents_system.config.settings import settings
from agents_system.api import super_admin, course_agents, chat, files

# Create minimal FastAPI app
app = FastAPI(
    title="Super Admin Agent - Minimal",
    description="Minimal version for testing",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(super_admin.router)
app.include_router(course_agents.router)
app.include_router(chat.router)
app.include_router(files.router)

@app.get("/")
async def root():
    return {
        "name": "Super Admin Agent - Minimal",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "super_admin": "/agents/super-admin/*",
            "course_assistants": "/agents/course-assistants/*",
            "chat": "/agents/chat/*",
            "files": "/agents/files/*"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "super_admin_agent",
        "version": "1.0.0",
        "config": {
            "openai_configured": bool(settings.openai_api_key),
            "supabase_configured": bool(settings.supabase_url),
            "jwt_configured": bool(settings.jwt_secret)
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Super Admin Agent - Minimal Server")
    print(f"📡 Server will be available at: http://localhost:8002")
    print(f"📚 API Documentation: http://localhost:8002/docs")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
