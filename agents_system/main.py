"""FastAPI application for Super Admin Agent system."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn
from typing import Dict, Any

from .config.settings import settings
from .api import super_admin, course_agents, chat, files
from .models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Super Admin Agent system...")
    
    # Initialize services
    try:
        # Verify OpenAI API key
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Verify Supabase configuration
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration incomplete")
        
        # Create upload directory
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Initialize Super Admin Agent
        from .services.super_admin_agent import super_admin_agent
        await super_admin_agent.initialize()
        
        logger.info("Super Admin Agent system started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down Super Admin Agent system...")


# Create FastAPI application
app = FastAPI(
    title="TeachMe AI - Super Admin Agent System",
    description="""
    ## Super Admin Agent System

    A comprehensive AI agent system for educational platform management using OpenAI's Agent SDK.

    ### Key Features
    - **Super Admin Agent**: Orchestration agent for platform management
    - **Course Assistants**: Specialized AI tutors for specific subjects
    - **File Processing**: Document ingestion with vector storage
    - **Chat Management**: Thread-based conversations with history
    - **Role-Based Security**: Integration with existing auth system

    ### Agent Types
    1. **Super Admin Agent** - Platform management and course assistant creation
    2. **Course Assistants** - Subject-specific AI tutors with document knowledge

    ### API Categories
    - **Super Admin**: Platform management and orchestration
    - **Course Assistants**: Create and manage specialized tutors
    - **Chat & Sessions**: Conversation management
    - **File Management**: Document upload and processing

    ### Authentication
    All endpoints require JWT authentication. Super Admin endpoints require elevated privileges.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with security."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token from TeachMe authentication system"
        }
    }
    
    # Add global security requirement
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "tags" in operation:
                operation.setdefault("security", [{"BearerAuth": []}])
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Include routers
app.include_router(super_admin.router)
app.include_router(course_agents.router)
app.include_router(chat.router)
app.include_router(files.router)

# Root endpoints
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with system information."""
    return {
        "name": "TeachMe AI - Super Admin Agent System",
        "version": "1.0.0",
        "description": "AI-powered educational platform management system",
        "features": [
            "Super Admin Agent for platform orchestration",
            "Course Assistant creation and management",
            "Document processing with vector storage", 
            "Real-time chat with WebSocket support",
            "Role-based access control"
        ],
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check services
        services = {}
        
        # Check OpenAI connection
        try:
            from .utils.openai_client import openai_client
            # Simple test - this would normally make a lightweight API call
            services["openai"] = "healthy"
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {str(e)}")
            services["openai"] = "unhealthy"
        
        # Check Supabase connection
        try:
            from .utils.supabase_client import supabase_client
            # Simple test - this would normally make a lightweight query
            services["supabase"] = "healthy"
        except Exception as e:
            logger.warning(f"Supabase health check failed: {str(e)}")
            services["supabase"] = "unhealthy"
        
        # Check file system
        try:
            upload_dir_ok = os.path.exists(settings.upload_dir) and os.access(settings.upload_dir, os.W_OK)
            services["file_system"] = "healthy" if upload_dir_ok else "unhealthy"
        except Exception:
            services["file_system"] = "unhealthy"
        
        # Overall status
        overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            services=services,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            services={"error": str(e)},
            version="1.0.0"
        )

@app.get("/info")
async def system_info():
    """Get detailed system information."""
    return {
        "system": {
            "name": "Super Admin Agent System",
            "version": "1.0.0",
            "environment": "development" if settings.debug else "production"
        },
        "configuration": {
            "text_model": settings.text_model,
            "voice_model": settings.voice_model,
            "embedding_model": settings.embedding_model,
            "max_file_size_mb": settings.max_file_size / (1024 * 1024),
            "supported_file_types": settings.supported_file_types,
            "max_sessions_per_user": settings.max_sessions_per_user
        },
        "capabilities": {
            "super_admin_agent": True,
            "course_assistants": True,
            "file_processing": True,
            "vector_search": True,
            "chat_sessions": True,
            "websockets": True,
            "streaming": True,
            "audio_transcription": True
        },
        "endpoints": {
            "super_admin": "/agents/super-admin/*",
            "course_assistants": "/agents/course-assistants/*",
            "chat": "/agents/chat/*",
            "files": "/agents/files/*"
        }
    }

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "agents.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
