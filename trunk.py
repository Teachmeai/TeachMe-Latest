# Apply websockets fix before any other imports
import fix_websockets

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from routes import auth
from routes import profiles
from routes import organizations
from routes import courses
from routes import assistants
from routes import assistant_chats
# from routes import course_invites  # Removed - using old JWT token method
from routes import file_upload
from core.supabase import init_supabase
from core.redis_client import init_redis
from middleware.cors import setup_cors

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_supabase()
    await init_redis()
    yield

# create fastapi instance
app = FastAPI(
    title="Teachme.ai",
    description="AI driven classrooms.",
    version="1.0",
    lifespan=lifespan
)

# custom openapi schema to add global security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT Bearer token"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi




# setup middleware
setup_cors(app)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(organizations.router)
app.include_router(courses.router)
# assistants and chat routers
app.include_router(assistants.router)
app.include_router(assistant_chats.router)
# app.include_router(course_invites.router, prefix="/course-invites", tags=["course-invites"])  # Removed - using old JWT token method
app.include_router(file_upload.router, prefix="/upload", tags=["file-upload"])
# Chat router disabled (switching to external HTTP agent)

# Debug endpoint to check session status
@app.get("/debug/session/{user_id}")
async def debug_session(user_id: str):
    from service.session_service import get_session
    session = await get_session(user_id)
    return {
        "user_id": user_id,
        "session_exists": session is not None,
        "session_data": session
    }

