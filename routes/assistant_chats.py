from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import time
import logging
from datetime import datetime, timezone, timedelta

from core.supabase import get_supabase_admin
from core.redis_client import get_redis
from middleware.auth_middleware import get_user_id


router = APIRouter(prefix="/assistant/chats", tags=["assistant-chats"])

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
logger = logging.getLogger("uvicorn.error")


async def _make_internal_api_call(user_id: str, endpoint: str, method: str = "POST", json_data: dict = None):
    """Helper function to call endpoint logic directly without FastAPI dependencies"""
    try:
        logger.info(f"🔗 DIRECT FUNCTION CALL: endpoint={endpoint}, method={method}, user_id={user_id}")
        
        # Import organization functions
        from functions.organization_functions import create_organization, invite_organization_admin
        # Teacher functions
        from functions.teacher_functions import create_course as teacher_create_course
        from functions.teacher_functions import send_course_invite_email_function as teacher_send_course_invite_email
        # Course functions
        from functions.course_functions import create_course_assistant, upload_course_content, update_course_assistant_instructions
        
        if endpoint == "/organizations" and method.upper() == "POST":
            # Create organization using dedicated function
            name = (json_data or {}).get("name")
            if not name:
                return {"error": "name is required"}
            
            return await create_organization(user_id, name)
            
        elif "/organizations/" in endpoint and "/invites/teacher" in endpoint and method.upper() == "POST":
            # Invite teacher via org assistant
            org_id = endpoint.split("/organizations/")[1].split("/invites")[0]
            invitee_email = (json_data or {}).get("invitee_email")
            role = "teacher"
            
            logger.info(f"🔧 INVITE DEBUG: org_id={org_id}, invitee_email={invitee_email}, role={role}")
            
            if not invitee_email:
                logger.error(f"❌ INVITE ERROR: invitee_email is required")
                return {"error": "invitee_email is required"}
            
            return await invite_organization_admin(user_id, org_id, invitee_email, role)

        elif "/organizations/" in endpoint and "/invites" in endpoint and method.upper() == "POST":
            # Super admin: invite organization_admin (or explicit role) to organization
            org_id = endpoint.split("/organizations/")[1].split("/invites")[0]
            invitee_email = (json_data or {}).get("invitee_email")
            role = (json_data or {}).get("role", "organization_admin")

            logger.info(f"🔧 INVITE DEBUG: org_id={org_id}, invitee_email={invitee_email}, role={role}")

            if not invitee_email:
                logger.error(f"❌ INVITE ERROR: invitee_email is required")
                return {"error": "invitee_email is required"}

            return await invite_organization_admin(user_id, org_id, invitee_email, role)

        elif endpoint == "/courses" and method.upper() == "POST":
            # Teacher creates a course
            org_id = (json_data or {}).get("org_id")
            name = (json_data or {}).get("name") or (json_data or {}).get("title")
            description = (json_data or {}).get("description")
            return await teacher_create_course(user_id, org_id, name, description)

        elif "/courses/" in endpoint and "/invite-email" in endpoint and method.upper() == "POST":
            # Teacher sends course invite email
            course_id = endpoint.split("/courses/")[1].split("/invite-email")[0]
            email = (json_data or {}).get("invitee_email") or (json_data or {}).get("email")
            expires_in_minutes = (json_data or {}).get("expires_in_minutes", 60)
            return await teacher_send_course_invite_email(user_id, course_id, email, expires_in_minutes)
        
        elif endpoint == "/courses/create-assistant" and method.upper() == "POST":
            # Create course assistant using dedicated function
            course_name = (json_data or {}).get("course_name")
            custom_instructions = (json_data or {}).get("custom_instructions", "")
            
            if not course_name:
                return {"error": "course_name is required"}
            
            return await create_course_assistant(user_id, course_name, custom_instructions)
            
        elif endpoint == "/courses/upload-content" and method.upper() == "POST":
            # Upload course content using dedicated function
            course_name = (json_data or {}).get("course_name")
            content_type = (json_data or {}).get("content_type")
            content = (json_data or {}).get("content")
            title = (json_data or {}).get("title", "Untitled")
            
            if not (course_name and content_type and content):
                return {"error": "course_name, content_type, and content are required"}
            
            return await upload_course_content(user_id, course_name, content_type, content, title)
            
        elif endpoint == "/courses/update-assistant-instructions" and method.upper() == "PATCH":
            # Update course assistant instructions using dedicated function
            course_name = (json_data or {}).get("course_name")
            instructions = (json_data or {}).get("instructions")
            
            if not (course_name and instructions):
                return {"error": "course_name and instructions are required"}
            
            return await update_course_assistant_instructions(user_id, course_name, instructions)
        
        else:
            return {"error": f"Endpoint {endpoint} not implemented for direct calls"}
                
    except Exception as e:
        logger.error(f"❌ DIRECT CALL ERROR: {str(e)}")
        return {"error": f"Failed to call function: {str(e)}"}


class CreateThreadRequest(BaseModel):
    assistant_id: str
    course_id: Optional[str] = None
    title: Optional[str] = None


@router.post("")
async def create_thread(payload: CreateThreadRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()

    a_resp = supabase.table("assistants").select("*").eq("id", payload.assistant_id).single().execute()
    a = a_resp.data
    if not a:
        raise HTTPException(status_code=404, detail="Assistant not found")

    if payload.course_id:
        c_resp = supabase.table("courses").select("id,org_id,assistant_id").eq("id", payload.course_id).single().execute()
        c = c_resp.data
        if not c:
            raise HTTPException(status_code=404, detail="Course not found")
        # RBAC: allow if teacher/org admin in course org, otherwise require enrollment
        mem = supabase.table("organization_memberships").select("role").eq("user_id", user_id).eq("org_id", c.get("org_id")).limit(1).execute()
        role = (mem.data or [{}])[0].get("role")
        if role not in ("teacher", "organization_admin"):
            enr = supabase.table("enrollments").select("id").eq("user_id", user_id).eq("course_id", payload.course_id).limit(1).execute()
            if not (enr.data or []):
                raise HTTPException(status_code=403, detail="Must be enrolled in course to create a course chat")

    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        th = openai.beta.threads.create()
        openai_thread_id = th.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create OpenAI thread: {str(e)}")

    # For org-context threads (non-course), capture org_id on the thread and add a system message
    org_id_ctx = a.get("org_id")
    if not payload.course_id:
        try:
            # Load session to get active org context
            from service.session_service import get_session
            from service.user_service import build_session_payload
            session = await get_session(user_id) or await build_session_payload(user_id)
            active_org_id = (session or {}).get("org_id")
            if active_org_id:
                # Persist org context on the thread
                org_id_ctx = org_id_ctx or active_org_id
                # Attach a system message to the OpenAI thread with org context
                openai.beta.threads.messages.create(
                    thread_id=openai_thread_id,
                    role="system",
                    content=f"active_org_id: {active_org_id}. When org_id is omitted, use this value."
                )
        except Exception:
            # Best-effort; do not fail thread creation if system message fails
            pass

    # Finalize org id for thread record (prefer session-derived)
    org_id_final = org_id_ctx
    if not org_id_final:
        try:
            from service.session_service import get_session
            from service.user_service import build_session_payload
            _s = await get_session(user_id) or await build_session_payload(user_id)
            _org_from_session = (_s or {}).get("org_id")
            if _org_from_session:
                org_id_final = _org_from_session
        except Exception:
            pass

    # Final fallback: lookup organization_memberships for an org where user is org admin
    if not org_id_final:
        try:
            mem = supabase.table("organization_memberships").select("org_id").eq("user_id", user_id).eq("role", "organization_admin").order("created_at", desc=True).limit(1).execute()
            if mem.data:
                org_id_final = mem.data[0].get("org_id") or org_id_final
        except Exception:
            pass

    # Get current user's role from session
    current_role = None
    try:
        from service.session_service import get_session
        from service.user_service import build_session_payload
        session = await get_session(user_id) or await build_session_payload(user_id)
        current_role = (session or {}).get("active_role")
    except Exception:
        pass

    rec = {
        "user_id": user_id,
        "assistant_id": payload.assistant_id,
        "course_id": payload.course_id,
        "org_id": org_id_final,
        "role": current_role,
        "openai_thread_id": openai_thread_id,
        "title": payload.title or "New Chat",
    }
    ins = supabase.table("chat_threads").insert(rec).execute()
    row = (ins.data or [None])[0]
    if not row:
        # Fallback: fetch by openai_thread_id
        fetched = supabase.table("chat_threads").select("*").eq("openai_thread_id", openai_thread_id).limit(1).execute()
        row = (fetched.data or [None])[0]
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create chat thread")
    # If org_id is still null and we have a session org id, backfill
    try:
        if not (row.get("org_id") or None) and org_id_final:
            supabase.table("chat_threads").update({"org_id": org_id_final}).eq("id", row.get("id")).execute()
            row["org_id"] = org_id_final
    except Exception:
        pass
    return {"ok": True, "thread": row}


@router.post("/{thread_id}/archive")
async def archive_thread(thread_id: str, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    th = supabase.table("chat_threads").select("id,user_id").eq("id", thread_id).single().execute().data
    if not th or th.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    supabase.table("chat_threads").update({"archived_at": "now()"}).eq("id", thread_id).execute()
    return {"ok": True}


@router.post("/{thread_id}/unarchive")
async def unarchive_thread(thread_id: str, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    th = supabase.table("chat_threads").select("id,user_id").eq("id", thread_id).single().execute().data
    if not th or th.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    supabase.table("chat_threads").update({"archived_at": None}).eq("id", thread_id).execute()
    return {"ok": True}


class RenameThreadRequest(BaseModel):
    title: str


@router.patch("/{thread_id}")
async def rename_thread(thread_id: str, payload: RenameThreadRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    # Prefer ownership check; if no row, fallback to id-only update
    th = supabase.table("chat_threads").select("id,user_id").eq("id", thread_id).limit(1).execute().data
    if not (th or []):
        # Fallback blindly updates by id (handles legacy rows missing user id)
        supabase.table("chat_threads").update({"title": payload.title, "updated_at": "now()"}).eq("id", thread_id).execute()
        return {"ok": True}
    if th[0].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    supabase.table("chat_threads").update({"title": payload.title, "updated_at": "now()"}).eq("id", thread_id).eq("user_id", user_id).execute()
    return {"ok": True}


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    th = supabase.table("chat_threads").select("id,user_id").eq("id", thread_id).limit(1).execute().data
    if not (th or []):
        # Fallback: delete by id even if ownership meta missing
        supabase.table("chat_threads").delete().eq("id", thread_id).execute()
        return {"ok": True}
    if th[0].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Hard delete scoped by id + user for safety
    supabase.table("chat_threads").delete().eq("id", thread_id).eq("user_id", user_id).execute()
    return {"ok": True}


# Method override helper to support frontend POST-only client
class MethodOverrideRequest(BaseModel):
    _method: str | None = None
    title: str | None = None


@router.post("/{thread_id}/_method")
async def post_method_override(thread_id: str, payload: MethodOverrideRequest, user_id: str = Depends(get_user_id)):
    method = (payload._method or "").upper()
    if method == "PATCH":
        if not payload.title:
            raise HTTPException(status_code=400, detail="title is required for rename")
        return await rename_thread(thread_id, RenameThreadRequest(title=payload.title), user_id)  # type: ignore
    if method == "DELETE":
        return await delete_thread(thread_id, user_id)  # type: ignore
    raise HTTPException(status_code=405, detail="Unsupported method override")


# Explicit endpoints to avoid method override issues
@router.post("/{thread_id}/rename")
async def rename_thread_post(thread_id: str, payload: RenameThreadRequest, user_id: str = Depends(get_user_id)):
    return await rename_thread(thread_id, payload, user_id)  # type: ignore


@router.post("/{thread_id}/delete")
async def delete_thread_post(thread_id: str, user_id: str = Depends(get_user_id)):
    return await delete_thread(thread_id, user_id)  # type: ignore


@router.get("")
async def list_threads(course_id: Optional[str] = None, page: int = 1, page_size: int = 20, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    # Get current user's role from session
    current_role = None
    try:
        from service.session_service import get_session
        from service.user_service import build_session_payload
        session = await get_session(user_id) or await build_session_payload(user_id)
        current_role = (session or {}).get("active_role")
    except Exception:
        pass
    
    q = supabase.table("chat_threads").select("*").eq("user_id", user_id)
    
    # Filter by current role if available
    if current_role:
        q = q.eq("role", current_role)
    
    if course_id:
        q = q.eq("course_id", course_id)
    # PostgREST pagination: range headers are not exposed in python client; emulate by limit/offset
    offset = (page - 1) * page_size
    resp = q.order("last_message_at", desc=True).range(offset, offset + page_size - 1).execute()
    return {"ok": True, "threads": resp.data or []}


class SendMessageRequest(BaseModel):
    thread_id: str
    message: str


@router.post("/send")
async def send_message(payload: SendMessageRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    redis = get_redis()
    try:
        logger.info("📨 CHAT SEND START: %s", {"user_id": user_id, "thread_id": payload.thread_id})
    except Exception:
        pass
    # simple rate limit: 1 message per second, burst 5
    key = f"rl:send:{user_id}"
    try:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 1)
        elif current > 5:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except Exception:
        pass
    th = supabase.table("chat_threads").select("*").eq("id", payload.thread_id).single().execute().data
    if not th or th.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    a = supabase.table("assistants").select("*").eq("id", th.get("assistant_id")).single().execute().data
    if not a:
        raise HTTPException(status_code=404, detail="Assistant not found")

    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        m = openai.beta.threads.messages.create(
            thread_id=th["openai_thread_id"],
            role="user",
            content=payload.message
        )
        try:
            logger.info("🧵 MESSAGE APPENDED: %s", {"openai_thread_id": th["openai_thread_id"], "message_id": m.id})
        except Exception:
            pass
        supabase.table("chat_messages").insert({
            "thread_id": th["id"],
            "role": "user",
            "content": payload.message,
            "openai_message_id": m.id
        }).execute()

        run = openai.beta.threads.runs.create(
            thread_id=th["openai_thread_id"],
            assistant_id=a["openai_assistant_id"]
        )
        try:
            logger.info("🏃 RUN STARTED: %s", {"thread_id": th["openai_thread_id"], "run_id": run.id, "assistant_id": a["openai_assistant_id"]})
        except Exception:
            pass

        # Tool-call loop
        # exponential backoff polling up to ~10s
        delay = 0.5
        max_delay = 2.0
        total = 0.0
        forced_assistant_message = None
        while True:
            status = openai.beta.threads.runs.retrieve(thread_id=th["openai_thread_id"], run_id=run.id)
            try:
                logger.info("🤖 ASSISTANT RUN: %s", {"thread_id": th["openai_thread_id"], "run_id": run.id, "status": status.status})
            except Exception:
                pass
            if status.status == "requires_action":
                tool_calls = status.required_action.submit_tool_outputs.tool_calls
                try:
                    logger.info("🛠 TOOLS REQUIRED: %s", [
                        {"id": tc.id, "name": getattr(tc.function, "name", None), "args": getattr(tc.function, "arguments", None)}
                        for tc in tool_calls
                    ])
                except Exception:
                    pass
                outputs = []
                for tc in tool_calls:
                    fname = getattr(tc.function, "name", "") or ""
                    try:
                        import json as _json, re as _re
                        fargs = _json.loads(getattr(tc.function, "arguments", "") or "{}")
                        norm = _re.sub(r"[^a-z0-9]+", "_", str(fname).strip().lower())
                    except Exception:
                        fargs = {}
                        norm = ""

                    # Minimal built-in tool handlers mapped to backend data/actions
                    result_obj = None
                    try:
                        if norm in ("create_organization", "createorganisation", "create_org", "createorganization"):
                            name = (fargs or {}).get("name")
                            if not name:
                                raise Exception("name is required")
                            
                            # Call the existing POST /organizations API
                            result_obj = await _make_internal_api_call(
                                user_id=user_id,
                                endpoint="/organizations",
                                method="POST",
                                json_data={"name": name}
                            )
                        elif norm in ("get_me", "me"):
                            profile = supabase.table("profiles").select("id,full_name,active_role").eq("id", user_id).single().execute().data or {}
                            roles = supabase.table("user_roles").select("role").eq("user_id", user_id).execute().data or []
                            result_obj = {"user_id": user_id, "profile": profile, "roles": roles}
                        elif norm in ("list_courses", "listcourses", "get_courses", "getcourses"):
                            # Get user's org_id from session
                            try:
                                from service.session_service import get_session
                                from service.user_service import build_session_payload
                                session = await get_session(user_id) or await build_session_payload(user_id)
                                org_id = (session or {}).get("org_id") or (session or {}).get("active_org_id")
                                
                                if not org_id:
                                    # Fallback to database lookup
                                    mem_resp = supabase.table("organization_memberships").select("org_id").eq("user_id", user_id).eq("role", "teacher").limit(1).execute()
                                    org_id = mem_resp.data[0].get("org_id") if mem_resp.data else None
                                
                                if org_id:
                                    courses_resp = supabase.table("courses").select("*").eq("org_id", org_id).order("created_at", desc=True).execute()
                                    result_obj = {"ok": True, "courses": courses_resp.data or []}
                                else:
                                    result_obj = {"ok": False, "error": "No organization found"}
                            except Exception as e:
                                logger.error(f"❌ LIST COURSES ERROR: {str(e)}")
                                result_obj = {"ok": False, "error": f"Failed to list courses: {str(e)}"}
                        # Old upload_course_content handler removed - using new one below
                        elif norm in ("switch_role", "switchrole"):
                            new_role = (fargs or {}).get("role")
                            if new_role:
                                supabase.table("profiles").update({"active_role": new_role}).eq("id", user_id).execute()
                            result_obj = {"ok": True, "active_role": new_role}
                        elif norm in ("create_course", "createcourse"):
                            # Get org_id from session if not provided
                            org_id = (fargs or {}).get("org_id")
                            if not org_id:
                                # Try multiple approaches to get org_id
                                try:
                                    # Approach 1: Direct session service
                                    from service.session_service import get_session
                                    from service.user_service import build_session_payload
                                    session = await get_session(user_id) or await build_session_payload(user_id)
                                    logger.info(f"🔧 CREATE COURSE DEBUG: session={session}")
                                    org_id = (session or {}).get("org_id")
                                    logger.info(f"🔧 CREATE COURSE DEBUG: org_id from session={org_id}")
                                    
                                    # Approach 2: If still no org_id, try direct database lookup
                                    if not org_id:
                                        logger.info(f"🔧 CREATE COURSE DEBUG: Trying database lookup for user {user_id}")
                                        mem_resp = supabase.table("organization_memberships").select("org_id").eq("user_id", user_id).eq("role", "teacher").limit(1).execute()
                                        if mem_resp.data:
                                            org_id = mem_resp.data[0].get("org_id")
                                            logger.info(f"🔧 CREATE COURSE DEBUG: org_id from database={org_id}")
                                    
                                    # Approach 3: Use thread's org_id as fallback
                                    if not org_id:
                                        try:
                                            thread_org_id = th.get("org_id")
                                            if thread_org_id:
                                                org_id = thread_org_id
                                                logger.info(f"🔧 CREATE COURSE DEBUG: org_id from thread={org_id}")
                                        except Exception:
                                            pass
                                        
                                except Exception as e:
                                    logger.error(f"❌ CREATE COURSE SESSION ERROR: {str(e)}")
                                    pass
                            
                            # Support both 'name' and 'title' parameters
                            title = (fargs or {}).get("title") or (fargs or {}).get("name")
                            description = (fargs or {}).get("description")
                            
                            if not title:
                                raise Exception("Course name/title is required")
                            if not org_id:
                                logger.error(f"❌ CREATE COURSE: No org_id found. fargs={fargs}, session_org_id={org_id}")
                                raise Exception("Organization not found in session. Please ensure you're logged in as a teacher in an organization.")
                            
                            # Check if course already exists
                            existing_course = supabase.table("courses").select("id").eq("title", title).eq("org_id", org_id).limit(1).execute()
                            if existing_course.data:
                                logger.info(f"🔧 CREATE COURSE: Course '{title}' already exists")
                                raise Exception(f"Course '{title}' already exists in your organization")
                            
                            logger.info(f"🔧 CREATE COURSE: org_id={org_id}, title={title}, user_id={user_id}")
                            
                            mem = supabase.table("organization_memberships").select("role").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
                            role = (mem.data or [{}])[0].get("role")
                            if role not in ("teacher", "organization_admin"):
                                raise Exception("Only teachers or org admins can create courses")
                            ins = supabase.table("courses").insert({
                                "org_id": org_id,
                                "created_by": user_id,
                                "title": title,
                                "description": description,
                                "status": "draft"
                            }).execute()
                            course_row = (ins.data or [None])[0]
                            if not course_row:
                                fetch = supabase.table("courses").select("*").eq("created_by", user_id).eq("title", title).order("created_at", desc=True).limit(1).execute()
                                course_row = (fetch.data or [None])[0]
                            result_obj = {"ok": True, "course": course_row}
                            
                            # Deterministic assistant response for successful creation
                            if isinstance(result_obj, dict) and result_obj.get("ok"):
                                forced_assistant_message = f"Course '{title}' created successfully!"
                        elif norm in ("invite_student", "invitestudent"):
                            course_id = (fargs or {}).get("course_id")
                            email = (fargs or {}).get("email")
                            
                            if not (course_id and email):
                                raise Exception("course_id and email are required")
                            
                            logger.info(f"🔧 INVITE STUDENT: course_id={course_id}, email={email}, user_id={user_id}")
                            
                            # Check if user is teacher/org admin for this course
                            course_resp = supabase.table("courses").select("org_id, created_by, title").eq("id", course_id).single().execute()
                            if not course_resp.data:
                                raise Exception("Course not found")
                            
                            course_org_id = course_resp.data.get("org_id")
                            course_creator = course_resp.data.get("created_by")
                            course_title = course_resp.data.get("title", "Unknown Course")
                            
                            # Check permissions - user must be course creator or org admin
                            is_course_creator = course_creator == user_id
                            is_org_admin = False
                            
                            if not is_course_creator:
                                mem_resp = supabase.table("organization_memberships").select("role").eq("user_id", user_id).eq("org_id", course_org_id).eq("role", "organization_admin").limit(1).execute()
                                is_org_admin = bool(mem_resp.data)
                            
                            if not (is_course_creator or is_org_admin):
                                raise Exception("Only course creators or organization admins can invite students")
                            
                            # Generate JWT token for enrollment (old method)
                            try:
                                import jwt
                                from core.config import config
                                
                                token_data = {
                                    "scope": "course_invite",
                                    "course_id": course_id,
                                    "org_id": course_org_id,
                                    "exp": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
                                }
                                
                                token = jwt.encode(token_data, config.jwt.SECRET, algorithm=config.jwt.ALGORITHM)
                                
                                # Send enrollment email with token (old method)
                                try:
                                    from core.email_service import send_course_invite_email
                                    import os
                                    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
                                    
                                    # Get organization name
                                    org_resp = supabase.table("organizations").select("name").eq("id", course_org_id).single().execute()
                                    org_name = org_resp.data.get("name", "Unknown Organization") if org_resp.data else "Unknown Organization"
                                    
                                    email_sent = await send_course_invite_email(
                                        email=email,
                                        org_name=org_name,
                                        course_title=course_title,
                                        token=token,
                                        frontend_url=frontend_url
                                    )
                                    logger.info(f"📧 Course enrollment email sent: {email_sent}")
                                except Exception as email_error:
                                    logger.error(f"❌ EMAIL ERROR: {str(email_error)}")
                                    import traceback
                                    logger.error(f"❌ EMAIL ERROR TRACEBACK: {traceback.format_exc()}")
                                    email_sent = False
                                
                                enrollment_link = f"{frontend_url}/courses/enroll?token={token}"
                                
                                result_obj = {
                                    "ok": True,
                                    "message": f"Course enrollment invitation sent to {email}" if email_sent else f"Failed to send email to {email}",
                                    "course_id": course_id,
                                    "course_name": course_title,
                                    "email": email,
                                    "email_sent": email_sent,
                                    "enrollment_link": enrollment_link
                                }
                                
                            except Exception as token_error:
                                logger.error(f"❌ TOKEN GENERATION ERROR: {str(token_error)}")
                                raise Exception(f"Failed to generate enrollment token: {str(token_error)}")
                            
                            # Deterministic assistant response for successful invite
                            if isinstance(result_obj, dict) and result_obj.get("ok"):
                                forced_assistant_message = f"Student invitation sent to {email}! They can now accept the invitation to enroll in the course."
                        elif norm in ("invite_org_admin", "inviteorgadmin"):
                            org_id = (fargs or {}).get("org_id")
                            invitee_email = (fargs or {}).get("invitee_email")
                            if not (org_id and invitee_email):
                                raise Exception("org_id and invitee_email required")
                            
                            # Call the existing POST /organizations/{org_id}/invites API
                            result_obj = await _make_internal_api_call(
                                user_id=user_id,
                                endpoint=f"/organizations/{org_id}/invites",
                                method="POST",
                                json_data={
                                    "invitee_email": invitee_email,
                                    "role": "organization_admin"
                                }
                            )
                        elif norm in ("invite_teacher", "inviteteacher", "invite_org_teacher", "inviteorgteacher"):
                            org_id = (fargs or {}).get("org_id")
                            invitee_email = (fargs or {}).get("invitee_email") or (fargs or {}).get("email")
                            # Resolution order: explicit arg → thread.org_id → session.org_id
                            if not org_id:
                                try:
                                    org_id = th.get("org_id")
                                except Exception:
                                    org_id = None
                            if not org_id:
                                try:
                                    from service.session_service import get_session
                                    from service.user_service import build_session_payload
                                    session = await get_session(user_id) or await build_session_payload(user_id)
                                    org_id = (session or {}).get("org_id")
                                except Exception:
                                    org_id = None
                            if not (org_id and invitee_email):
                                raise Exception("org_id and invitee_email required")
                            # Route to internal invite-teacher endpoint which maps to role=teacher
                            result_obj = await _make_internal_api_call(
                                user_id=user_id,
                                endpoint=f"/organizations/{org_id}/invites/teacher",
                                method="POST",
                                json_data={
                                    "invitee_email": invitee_email,
                                    "role": "teacher"
                                }
                            )
                            # Deterministic assistant response to avoid LLM asking for org_id after success
                            if isinstance(result_obj, dict) and result_obj.get("ok"):
                                forced_assistant_message = f"Invitation sent to {invitee_email} for org {org_id} as Teacher."
                        elif norm in ("create_course_assistant", "createcourseassistant"):
                            course_name = (fargs or {}).get("course_name")
                            custom_instructions = (fargs or {}).get("custom_instructions", "")
                            
                            if not course_name:
                                raise Exception("course_name is required")
                            
                            result_obj = await _make_internal_api_call(
                                user_id=user_id,
                                endpoint="/courses/create-assistant",
                                method="POST",
                                json_data={"course_name": course_name, "custom_instructions": custom_instructions}
                            )
                            
                            # Deterministic assistant response for successful creation
                            if isinstance(result_obj, dict) and result_obj.get("ok"):
                                forced_assistant_message = f"Course assistant created successfully for '{course_name}'!"
                        elif norm in ("upload_course_content", "uploadcoursecontent"):
                            logger.info(f"🔧 TOOL HANDLER: upload_course_content called with args: {fargs}")
                            course_name = (fargs or {}).get("course_name")
                            content_type = (fargs or {}).get("content_type")
                            content = (fargs or {}).get("content")
                            title = (fargs or {}).get("title", "Untitled")
                            file_ids = (fargs or {}).get("file_ids", [])  # New parameter for file IDs
                            
                            logger.info(f"🔧 TOOL HANDLER: course_name={course_name}, file_ids={file_ids}, content_type={content_type}")
                            
                            if not course_name:
                                raise Exception("course_name is required")
                            
                            # If file_ids are provided, use them to get file content
                            if file_ids:
                                logger.info(f"🔧 TOOL HANDLER: Processing file_ids: {file_ids}")
                                import json
                                import tempfile
                                
                                uploaded_files = []
                                
                                for file_id in file_ids:
                                    try:
                                        file_data = None
                                        
                                        # Try Redis first
                                        try:
                                            redis_client = get_redis()
                                            file_data_str = await redis_client.get(f"temp_file:{file_id}")
                                            if file_data_str:
                                                file_data = json.loads(file_data_str)
                                        except Exception as redis_error:
                                            logger.warning(f"⚠️ Redis unavailable for file {file_id}: {str(redis_error)}")
                                        
                                        # Fallback to file system
                                        if not file_data:
                                            temp_dir = tempfile.gettempdir()
                                            temp_file_path = os.path.join(temp_dir, f"temp_file_{file_id}.json")
                                            try:
                                                with open(temp_file_path, 'r') as f:
                                                    file_data = json.load(f)
                                            except FileNotFoundError:
                                                logger.warning(f"⚠️ File {file_id} not found in file system")
                                                continue
                                        
                                        if file_data and file_data.get("user_id") == user_id:
                                            uploaded_files.append({
                                                "filename": file_data["filename"],
                                                "content_type": file_data["content_type"],
                                                "content": file_data["content"]
                                            })
                                            logger.info(f"🔧 TOOL HANDLER: Retrieved file {file_id}: {file_data['filename']} ({len(file_data['content'])} chars)")
                                        else:
                                            logger.warning(f"🔧 TOOL HANDLER: File {file_id} not found or user mismatch")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Failed to retrieve file {file_id}: {str(e)}")
                                
                                # Upload each file to the course using internal function
                                results = []
                                for file_info in uploaded_files:
                                    # Call the internal function directly instead of API endpoint
                                    from functions.course_functions import upload_course_content
                                    result_obj = await upload_course_content(
                                        user_id=user_id,
                                        course_name=course_name,
                                        content_type="document",
                                        content=file_info["content"],
                                        title=file_info["filename"]
                                    )
                                    results.append(result_obj)
                                
                                # Deterministic assistant response for successful upload
                                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("ok"))
                                if success_count > 0:
                                    forced_assistant_message = f"Successfully uploaded {success_count} file(s) to '{course_name}' course!"
                                else:
                                    forced_assistant_message = f"Failed to upload files to '{course_name}' course."
                            else:
                                # Original behavior for text content
                                if not (content_type and content):
                                    raise Exception("content_type and content are required")
                                
                                result_obj = await _make_internal_api_call(
                                    user_id=user_id,
                                    endpoint="/courses/upload-content",
                                    method="POST",
                                    json_data={
                                        "course_name": course_name,
                                        "content_type": content_type,
                                        "content": content,
                                        "title": title
                                    }
                                )
                                
                                # Deterministic assistant response for successful upload
                                if isinstance(result_obj, dict) and result_obj.get("ok"):
                                    forced_assistant_message = f"Content uploaded successfully to '{course_name}' course!"
                        elif norm in ("update_course_assistant_instructions", "updatecourseassistantinstructions"):
                            course_name = (fargs or {}).get("course_name")
                            instructions = (fargs or {}).get("instructions")
                            
                            if not (course_name and instructions):
                                raise Exception("course_name and instructions are required")
                            
                            result_obj = await _make_internal_api_call(
                                user_id=user_id,
                                endpoint="/courses/update-assistant-instructions",
                                method="PATCH",
                                json_data={"course_name": course_name, "instructions": instructions}
                            )
                            
                            # Deterministic assistant response for successful update
                            if isinstance(result_obj, dict) and result_obj.get("ok"):
                                forced_assistant_message = f"Assistant instructions updated successfully for '{course_name}' course!"
                        elif norm in ("generate_invite_link", "generateinvitelink"):
                            result_obj = {"ok": False, "error": "Not implemented in tool bridge; call API endpoint"}
                        elif norm in ("enroll_by_token", "enrollbytoken"):
                            result_obj = {"ok": False, "error": "Not implemented in tool bridge; call API endpoint"}
                        else:
                            result_obj = {"error": f"Unknown tool {fname}"}
                    except Exception as e:
                        result_obj = {"error": str(e)}

                    # Each output must be a string
                    try:
                        import json as _json
                        outputs.append({
                            "tool_call_id": tc.id,
                            "output": _json.dumps(result_obj)
                        })
                    except Exception:
                        outputs.append({
                            "tool_call_id": tc.id,
                            "output": str(result_obj)
                        })

                # Persist tool call details for audit
                try:
                    for tc, out in zip(tool_calls, outputs):
                        supabase.table("chat_messages").insert({
                            "thread_id": th["id"],
                            "role": "tool",
                            "content": None,
                            "tool_call": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                                "output": out.get("output")
                            }
                        }).execute()
                    # Log summary
                    logger.info("🧾 TOOLS SUBMITTED: %s", [
                        {"id": x[0].id, "name": getattr(x[0].function, "name", None)} for x in zip(tool_calls, outputs)
                    ])
                except Exception:
                    pass

                openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=th["openai_thread_id"],
                    run_id=run.id,
                    tool_outputs=outputs
                )
            elif status.status in ("completed", "failed", "cancelled", "expired"):
                try:
                    logger.info("✅ RUN ENDED: %s", {"status": status.status, "run_id": run.id})
                except Exception:
                    pass
                break
            time.sleep(delay)
            total += delay
            delay = min(max_delay, delay * 1.5)
            if total > 10:
                break

        # If we set a deterministic assistant message, save and return it immediately
        if forced_assistant_message:
            supabase.table("chat_messages").insert({
                "thread_id": th["id"],
                "role": "assistant",
                "content": forced_assistant_message,
            }).execute()
            supabase.table("chat_threads").update({"last_message_at": "now()"}).eq("id", th["id"]).execute()
            return {"ok": True, "messages": [{"openai_message_id": None, "content": forced_assistant_message}]}

        # Get messages in reverse chronological order (newest first)
        msgs = openai.beta.threads.messages.list(thread_id=th["openai_thread_id"], order="desc", limit=20)
        new_assistant_msgs = []
        
        # Find ONLY the most recent assistant message that's not a generic greeting
        for msg in msgs.data:
            if msg.role == "assistant":
                text_chunks = []
                for p in (msg.content or []):
                    if getattr(p, "type", None) == "text":
                        text_chunks.append(p.text.value)
                content = "\n".join(text_chunks).strip()
                if content:
                    try:
                        logger.info("🔍 CHECKING ASSISTANT MSG: id=%s, content_preview=%s, is_greeting=%s", 
                                  msg.id, content[:50] + "..." if len(content) > 50 else content, 
                                  "Hello! How can I assist you today?" in content)
                    except Exception:
                        pass
                    
                    # Skip generic greeting messages
                    if "Hello! How can I assist you today?" in content:
                        continue
                    # Take ONLY the first non-greeting assistant message and STOP
                    new_assistant_msgs.append({"openai_message_id": msg.id, "content": content})
                    break  # CRITICAL: Stop after finding the first non-greeting message
        
        # If no non-greeting message found, take the most recent assistant message
        if not new_assistant_msgs:
            for msg in msgs.data:
                if msg.role == "assistant":
                    text_chunks = []
                    for p in (msg.content or []):
                        if getattr(p, "type", None) == "text":
                            text_chunks.append(p.text.value)
                    content = "\n".join(text_chunks).strip()
                    if content:
                        new_assistant_msgs.append({"openai_message_id": msg.id, "content": content})
                        break  # CRITICAL: Stop after finding the first message
        try:
            logger.info("💬 ASSISTANT MESSAGES: %s", {"count": len(new_assistant_msgs)})
        except Exception:
            pass

        for am in reversed(new_assistant_msgs):
            try:
                logger.info("💾 SAVING ASSISTANT MSG: openai_id=%s, content_preview=%s", 
                          am["openai_message_id"], am["content"][:50] + "..." if len(am["content"]) > 50 else am["content"])
            except Exception:
                pass
            
            supabase.table("chat_messages").insert({
                "thread_id": th["id"],
                "role": "assistant",
                "content": am["content"],
                "openai_message_id": am["openai_message_id"]
            }).execute()

        supabase.table("chat_threads").update({"last_message_at": "now()"}).eq("id", th["id"]).execute()

        return {"ok": True, "messages": new_assistant_msgs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat send failed: {str(e)}")


@router.post("/send/stream")
async def send_message_stream(payload: SendMessageRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    th = supabase.table("chat_threads").select("*").eq("id", payload.thread_id).single().execute().data
    if not th or th.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    a = supabase.table("assistants").select("*").eq("id", th.get("assistant_id")).single().execute().data
    if not a:
        raise HTTPException(status_code=404, detail="Assistant not found")

    import openai
    openai.api_key = OPENAI_API_KEY

    # append user message
    m = openai.beta.threads.messages.create(
        thread_id=th["openai_thread_id"],
        role="user",
        content=payload.message
    )
    supabase.table("chat_messages").insert({
        "thread_id": th["id"],
        "role": "user",
        "content": payload.message,
        "openai_message_id": m.id
    }).execute()

    def event_stream():
        # naive stream of final message only; upgrade to token streaming with responses API if needed
        try:
            run = openai.beta.threads.runs.create(
                thread_id=th["openai_thread_id"],
                assistant_id=a["openai_assistant_id"]
            )
            while True:
                status = openai.beta.threads.runs.retrieve(thread_id=th["openai_thread_id"], run_id=run.id)
                if status.status == "requires_action":
                    # For simplicity, do not stream tool processing; handle synchronously like non-stream
                    break
                if status.status in ("completed", "failed", "cancelled", "expired"):
                    break
                yield f"data: {{\"status\": \"{status.status}\"}}\n\n"
                time.sleep(0.5)
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            return

        # fetch messages and emit last assistant text
        msgs = openai.beta.threads.messages.list(thread_id=th["openai_thread_id"])
        last_text = None
        last_id = None
        for msg in msgs.data:
            if msg.role == "assistant":
                chunks = []
                for p in (msg.content or []):
                    if getattr(p, "type", None) == "text":
                        chunks.append(p.text.value)
                text = "\n".join(chunks).strip()
                if text:
                    last_text = text
                    last_id = msg.id
                    break
        if last_text:
            supabase.table("chat_messages").insert({
                "thread_id": th["id"],
                "role": "assistant",
                "content": last_text,
                "openai_message_id": last_id
            }).execute()
            supabase.table("chat_threads").update({"last_message_at": "now()"}).eq("id", th["id"]).execute()
            yield f"data: {{\"message\": {last_text!r}}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{thread_id}/messages")
async def get_messages(thread_id: str, page: int = 1, page_size: int = 50, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    th = supabase.table("chat_threads").select("id,user_id").eq("id", thread_id).single().execute().data
    if not th or th.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    offset = (page - 1) * page_size
    # Exclude tool messages from history to avoid empty placeholders in UI
    msgs = (
        supabase
        .table("chat_messages")
        .select("*")
        .eq("thread_id", thread_id)
        .neq("role", "tool")
        .order("created_at")
        .range(offset, offset + page_size - 1)
        .execute()
        .data
        or []
    )
    return {"ok": True, "messages": msgs}


