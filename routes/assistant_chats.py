from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import time
import logging
from datetime import datetime, timezone

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
        
        if endpoint == "/organizations" and method.upper() == "POST":
            # Create organization using dedicated function
            name = (json_data or {}).get("name")
            if not name:
                return {"error": "name is required"}
            
            return await create_organization(user_id, name)
            
        elif "/organizations/" in endpoint and "/invites" in endpoint and method.upper() == "POST":
            # Invite organization admin logic
            org_id = endpoint.split("/organizations/")[1].split("/invites")[0]
            invitee_email = (json_data or {}).get("invitee_email")
            role = (json_data or {}).get("role", "organization_admin")
            
            logger.info(f"🔧 INVITE DEBUG: org_id={org_id}, invitee_email={invitee_email}, role={role}")
            
            if not invitee_email:
                logger.error(f"❌ INVITE ERROR: invitee_email is required")
                return {"error": "invitee_email is required"}
            
            return await invite_organization_admin(user_id, org_id, invitee_email, role)
        
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

    rec = {
        "user_id": user_id,
        "assistant_id": payload.assistant_id,
        "course_id": payload.course_id,
        "org_id": a.get("org_id"),
        "role": None,
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


@router.get("")
async def list_threads(course_id: Optional[str] = None, page: int = 1, page_size: int = 20, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    q = supabase.table("chat_threads").select("*").eq("user_id", user_id)
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
                        elif norm in ("switch_role", "switchrole"):
                            new_role = (fargs or {}).get("role")
                            if new_role:
                                supabase.table("profiles").update({"active_role": new_role}).eq("id", user_id).execute()
                            result_obj = {"ok": True, "active_role": new_role}
                        elif norm in ("create_course", "createcourse"):
                            org_id = (fargs or {}).get("org_id")
                            title = (fargs or {}).get("title")
                            description = (fargs or {}).get("description")
                            if not (org_id and title):
                                raise Exception("org_id and title required")
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
    msgs = supabase.table("chat_messages").select("*").eq("thread_id", thread_id).order("created_at").range(offset, offset + page_size - 1).execute().data or []
    return {"ok": True, "messages": msgs}


