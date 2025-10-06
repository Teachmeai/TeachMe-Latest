from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import logging
import tempfile
import os
from datetime import datetime, timezone
import openai
from openai import OpenAI

from core.supabase import get_supabase_admin
from core.redis_client import get_redis
from middleware.auth_middleware import get_user_id
from service.session_service import get_session
from service.user_service import build_session_payload

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

@router.get("/test-auth")
async def test_auth(user_id: str = Depends(get_user_id)):
    """Test authentication endpoint"""
    return {"ok": True, "user_id": user_id, "message": "Authentication working"}

@router.post("/temp-file")
async def store_temp_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id)
):
    """Store a temporary file for assistant processing (Teacher only)"""
    try:
        logger.info(f"📁 STORE TEMP FILE: user_id={user_id}, filename={file.filename}, content_type={file.content_type}")
        
        # Check if user is a teacher or org admin
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Check user role - must be teacher or org admin
        user_role = session.get("role")
        active_role = session.get("active_role")
        roles = session.get("roles", [])
        
        # Check if user has teacher or org admin role in any context
        has_teacher_role = False
        has_org_admin_role = False
        
        # Check global role
        if user_role in ["teacher", "organization_admin"]:
            has_teacher_role = user_role == "teacher"
            has_org_admin_role = user_role == "organization_admin"
        
        # Check active role
        if active_role in ["teacher", "organization_admin"]:
            has_teacher_role = active_role == "teacher" or has_teacher_role
            has_org_admin_role = active_role == "organization_admin" or has_org_admin_role
        
        # Check all roles in session
        for role in roles:
            role_name = role.get("role")
            if role_name == "teacher":
                has_teacher_role = True
            elif role_name == "organization_admin":
                has_org_admin_role = True
        
        if not (has_teacher_role or has_org_admin_role):
            raise HTTPException(status_code=403, detail="Only teachers and organization admins can upload files")
        
        # Read file content
        content = await file.read()
        
        # Generate unique file ID
        import uuid
        file_id = str(uuid.uuid4())
        
        # Store file in temporary storage (fallback to file system if Redis unavailable)
        import json
        import tempfile
        
        file_data = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "content": content.decode('utf-8', errors='ignore') if file.content_type and file.content_type.startswith('text/') else content.hex(),  # Store text as string, binary as hex
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Try Redis first, fallback to file system
        try:
            redis = get_redis()
            await redis.setex(f"temp_file:{file_id}", 3600, json.dumps(file_data, default=str))
            logger.info(f"📁 STORE TEMP FILE: Stored in Redis")
        except Exception as redis_error:
            logger.warning(f"⚠️ Redis unavailable, using file system: {str(redis_error)}")
            # Fallback: store in temporary file
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"temp_file_{file_id}.json")
            with open(temp_file_path, 'w') as f:
                json.dump(file_data, f, default=str)
            logger.info(f"📁 STORE TEMP FILE: Stored in file system: {temp_file_path}")
        
        logger.info(f"📁 STORE TEMP FILE: Stored file {file_id} ({len(content)} bytes)")
        
        return {
            "ok": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "message": f"File '{file.filename}' stored temporarily for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ STORE TEMP FILE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

@router.get("/temp-file/{file_id}")
async def get_temp_file(file_id: str, user_id: str = Depends(get_user_id)):
    """Retrieve a temporary file (Teacher only)"""
    try:
        logger.info(f"📁 GET TEMP FILE: file_id={file_id}, user_id={user_id}")
        
        # Check if user is a teacher or org admin
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Check user role - must be teacher or org admin
        user_role = session.get("role")
        active_role = session.get("active_role")
        roles = session.get("roles", [])
        
        # Check if user has teacher or org admin role in any context
        has_teacher_role = False
        has_org_admin_role = False
        
        # Check global role
        if user_role in ["teacher", "organization_admin"]:
            has_teacher_role = user_role == "teacher"
            has_org_admin_role = user_role == "organization_admin"
        
        # Check active role
        if active_role in ["teacher", "organization_admin"]:
            has_teacher_role = active_role == "teacher" or has_teacher_role
            has_org_admin_role = active_role == "organization_admin" or has_org_admin_role
        
        # Check all roles in session
        for role in roles:
            role_name = role.get("role")
            if role_name == "teacher":
                has_teacher_role = True
            elif role_name == "organization_admin":
                has_org_admin_role = True
        
        if not (has_teacher_role or has_org_admin_role):
            raise HTTPException(status_code=403, detail="Only teachers and organization admins can access files")
        
        # Get file from Redis or file system fallback
        import json
        import tempfile
        
        file_data = None
        
        # Try Redis first
        try:
            redis = get_redis()
            file_data_str = await redis.get(f"temp_file:{file_id}")
            if file_data_str:
                file_data = json.loads(file_data_str)
                logger.info(f"📁 GET TEMP FILE: Retrieved from Redis")
        except Exception as redis_error:
            logger.warning(f"⚠️ Redis unavailable, trying file system: {str(redis_error)}")
        
        # Fallback to file system
        if not file_data:
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"temp_file_{file_id}.json")
            try:
                with open(temp_file_path, 'r') as f:
                    file_data = json.load(f)
                logger.info(f"📁 GET TEMP FILE: Retrieved from file system")
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="File not found or expired")
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        # Verify file belongs to user
        if file_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"📁 GET TEMP FILE: Retrieved file {file_id}")
        
        return {
            "ok": True,
            "file_id": file_id,
            "filename": file_data["filename"],
            "content_type": file_data["content_type"],
            "size": file_data["size"],
            "content": file_data["content"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GET TEMP FILE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

@router.post("/course-content")
async def upload_course_file(
    course_name: str = Form(...),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user_id: str = Depends(get_user_id)
):
    """Upload a file to course vector store (Teacher only)"""
    try:
        logger.info(f"📚 UPLOAD COURSE FILE: user_id={user_id}, course_name={course_name}")
        
        # Check if user is a teacher or org admin
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Check user role - must be teacher or org admin
        user_role = session.get("role")
        active_role = session.get("active_role")
        roles = session.get("roles", [])
        
        logger.info(f"📚 UPLOAD COURSE FILE: user_role={user_role}, active_role={active_role}, roles_count={len(roles)}")
        
        # Check if user has teacher or org admin role in any context
        has_teacher_role = False
        has_org_admin_role = False
        
        # Check global role
        if user_role in ["teacher", "organization_admin"]:
            has_teacher_role = user_role == "teacher"
            has_org_admin_role = user_role == "organization_admin"
        
        # Check active role
        if active_role in ["teacher", "organization_admin"]:
            has_teacher_role = active_role == "teacher" or has_teacher_role
            has_org_admin_role = active_role == "organization_admin" or has_org_admin_role
        
        # Check all roles in session
        for role in roles:
            role_name = role.get("role")
            if role_name == "teacher":
                has_teacher_role = True
            elif role_name == "organization_admin":
                has_org_admin_role = True
        
        if not (has_teacher_role or has_org_admin_role):
            logger.error(f"📚 UPLOAD COURSE FILE: Access denied - user_role={user_role}, active_role={active_role}, roles={[r.get('role') for r in roles]}")
            raise HTTPException(status_code=403, detail="Only teachers and organization admins can upload course content")
        
        org_id = session.get("org_id") or session.get("active_org_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No active organization found")
        
        # Find course by name in user's org
        supabase = get_supabase_admin()
        logger.info(f"📚 UPLOAD COURSE FILE: Looking for course '{course_name}' in org_id={org_id}")
        
        # First, let's see what courses exist in this org
        all_courses_resp = supabase.table("courses").select("id, title").eq("org_id", org_id).execute()
        logger.info(f"📚 UPLOAD COURSE FILE: Available courses in org: {[c['title'] for c in all_courses_resp.data]}")
        
        course_resp = supabase.table("courses").select("*").eq("title", course_name).eq("org_id", org_id).limit(1).execute()
        if not course_resp.data:
            logger.error(f"📚 UPLOAD COURSE FILE: Course '{course_name}' not found in org_id={org_id}")
            raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found in your organization")
        
        course = course_resp.data[0]
        
        # Check if course has an assistant with vector store
        if not course.get("assistant_id"):
            raise HTTPException(status_code=400, detail=f"Course '{course_name}' does not have an assistant. Create one first.")
        
        # Get assistant info
        assistant_resp = supabase.table("assistants").select("*").eq("id", course["assistant_id"]).single().execute()
        if not assistant_resp.data:
            raise HTTPException(status_code=404, detail="Course assistant not found")
        
        assistant = assistant_resp.data
        
        # Validate file type
        allowed_types = ["text/plain", "text/markdown", "application/pdf", "text/csv"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not supported. Allowed types: {allowed_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create OpenAI file from uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, 'rb') as f:
                    openai_file = client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                
                logger.info(f"📚 UPLOAD COURSE FILE: OpenAI file created: {openai_file.id}")
                
                # Try to add to vector store if available
                vector_store_id = course.get("vector_store_id")
                if vector_store_id:
                    try:
                        client.beta.vector_stores.files.create(
                            vector_store_id=vector_store_id,
                            file_id=openai_file.id
                        )
                        logger.info(f"📚 UPLOAD COURSE FILE: File added to vector store: {vector_store_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ UPLOAD COURSE FILE: Failed to add to vector store: {str(e)}")
                        # Continue without vector store
                else:
                    logger.warning(f"⚠️ UPLOAD COURSE FILE: No vector store found for course")
                
                # Use title from form or filename
                file_title = title or file.filename or "Untitled"
                
                return {
                    "ok": True,
                    "message": f"File '{file_title}' uploaded successfully to '{course_name}' vector store",
                    "file_id": openai_file.id,
                    "vector_store_id": vector_store_id
                }
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FILE UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/course-content/text")
async def upload_course_text(
    course_name: str = Form(...),
    content: str = Form(...),
    title: str = Form(...),
    content_type: str = Form("text"),
    user_id: str = Depends(get_user_id)
):
    """Upload text content to course vector store (Teacher only)"""
    try:
        logger.info(f"📚 UPLOAD COURSE TEXT: user_id={user_id}, course_name={course_name}")
        
        # Check if user is a teacher or org admin
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Check user role - must be teacher or org admin
        user_role = session.get("role")
        active_role = session.get("active_role")
        roles = session.get("roles", [])
        
        logger.info(f"📚 UPLOAD COURSE TEXT: user_role={user_role}, active_role={active_role}, roles_count={len(roles)}")
        
        # Check if user has teacher or org admin role in any context
        has_teacher_role = False
        has_org_admin_role = False
        
        # Check global role
        if user_role in ["teacher", "organization_admin"]:
            has_teacher_role = user_role == "teacher"
            has_org_admin_role = user_role == "organization_admin"
        
        # Check active role
        if active_role in ["teacher", "organization_admin"]:
            has_teacher_role = active_role == "teacher" or has_teacher_role
            has_org_admin_role = active_role == "organization_admin" or has_org_admin_role
        
        # Check all roles in session
        for role in roles:
            role_name = role.get("role")
            if role_name == "teacher":
                has_teacher_role = True
            elif role_name == "organization_admin":
                has_org_admin_role = True
        
        if not (has_teacher_role or has_org_admin_role):
            logger.error(f"📚 UPLOAD COURSE TEXT: Access denied - user_role={user_role}, active_role={active_role}, roles={[r.get('role') for r in roles]}")
            raise HTTPException(status_code=403, detail="Only teachers and organization admins can upload course content")
        
        org_id = session.get("org_id") or session.get("active_org_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No active organization found")
        
        # Find course by name in user's org
        supabase = get_supabase_admin()
        course_resp = supabase.table("courses").select("*").eq("title", course_name).eq("org_id", org_id).limit(1).execute()
        if not course_resp.data:
            raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found in your organization")
        
        course = course_resp.data[0]
        
        # Check if course has an assistant with vector store
        if not course.get("assistant_id"):
            raise HTTPException(status_code=400, detail=f"Course '{course_name}' does not have an assistant. Create one first.")
        
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create temporary file with content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            
            try:
                with open(temp_file.name, 'rb') as f:
                    openai_file = client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                
                logger.info(f"📚 UPLOAD COURSE TEXT: OpenAI file created: {openai_file.id}")
                
                # Try to add to vector store if available
                vector_store_id = course.get("vector_store_id")
                if vector_store_id:
                    try:
                        client.beta.vector_stores.files.create(
                            vector_store_id=vector_store_id,
                            file_id=openai_file.id
                        )
                        logger.info(f"📚 UPLOAD COURSE TEXT: File added to vector store: {vector_store_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ UPLOAD COURSE TEXT: Failed to add to vector store: {str(e)}")
                        # Continue without vector store
                else:
                    logger.warning(f"⚠️ UPLOAD COURSE TEXT: No vector store found for course")
                
                return {
                    "ok": True,
                    "message": f"Content '{title}' uploaded successfully to '{course_name}' vector store",
                    "file_id": openai_file.id,
                    "vector_store_id": vector_store_id
                }
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TEXT UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
