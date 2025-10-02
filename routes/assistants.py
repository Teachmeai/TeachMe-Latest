from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Literal, Any

from middleware.auth_middleware import get_user_id
from core.supabase import get_supabase_admin
from core.redis_client import get_redis


router = APIRouter(prefix="/assistants", tags=["assistants"])

Scope = Literal["global","organization","course"]
Role = Literal["super_admin","organization_admin","teacher"]


class CreateAssistantRequest(BaseModel):
    scope: Scope
    name: str
    openai_assistant_id: str
    role: Optional[Role] = None
    org_id: Optional[str] = None
    course_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = True


@router.post("")
async def create_assistant(payload: CreateAssistantRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()

    if payload.scope == "global":
        if not payload.role:
            raise HTTPException(status_code=400, detail="role is required for global scope")
    if payload.scope == "organization":
        if not (payload.role and payload.org_id):
            raise HTTPException(status_code=400, detail="role and org_id are required for organization scope")
    if payload.scope == "course":
        if not payload.course_id:
            raise HTTPException(status_code=400, detail="course_id is required for course scope")

    data = {
        "scope": payload.scope,
        "role": payload.role,
        "org_id": payload.org_id,
        "course_id": payload.course_id,
        "name": payload.name,
        "openai_assistant_id": payload.openai_assistant_id,
        "is_active": payload.is_active,
        "metadata": payload.metadata or {},
        "created_by": user_id,
    }
    resp = supabase.table("assistants").insert(data).select("*").single().execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create assistant")
    return {"ok": True, "assistant": resp.data}


@router.get("")
async def list_assistants(
    scope: Optional[Scope] = Query(default=None),
    role: Optional[Role] = Query(default=None),
    org_id: Optional[str] = Query(default=None),
    course_id: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    user_id: str = Depends(get_user_id),
):
    supabase = get_supabase_admin()
    q = supabase.table("assistants").select("*")
    if scope:
        q = q.eq("scope", scope)
    if role:
        q = q.eq("role", role)
    if org_id:
        q = q.eq("org_id", org_id)
    if course_id:
        q = q.eq("course_id", course_id)
    if active_only:
        q = q.eq("is_active", True)
    resp = q.execute()
    return {"ok": True, "assistants": resp.data or []}


class UpdateAssistantRequest(BaseModel):
    name: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


@router.patch("/{assistant_id}")
async def update_assistant(assistant_id: str, payload: UpdateAssistantRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        return {"ok": True}
    resp = supabase.table("assistants").update(updates).eq("id", assistant_id).select("*").single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"ok": True, "assistant": resp.data}


@router.get("/resolve")
async def resolve_assistant(
    role: Role,
    org_id: Optional[str] = Query(default=None),
    course_id: Optional[str] = Query(default=None),
    user_id: str = Depends(get_user_id),
):
    supabase = get_supabase_admin()
    # try redis cache (60s)
    cache_key = None
    try:
        redis = get_redis()
        cache_key = f"assistant:resolve:{role}:{org_id or '-'}:{course_id or '-'}"
        cached = await redis.get(cache_key)
        if cached:
            import json as _json
            return {"ok": True, "assistant": _json.loads(cached)}
    except Exception:
        pass
    # precedence: course -> organization -> global
    if course_id:
        r = supabase.table("assistants").select("*").eq("scope", "course").eq("course_id", course_id).eq("is_active", True).limit(1).execute()
        if r.data:
            try:
                if cache_key:
                    import json as _json
                    redis = get_redis()
                    await redis.setex(cache_key, 60, _json.dumps(r.data[0]))
            except Exception:
                pass
            return {"ok": True, "assistant": r.data[0]}
    if org_id:
        r = supabase.table("assistants").select("*").eq("scope", "organization").eq("org_id", org_id).eq("role", role).eq("is_active", True).limit(1).execute()
        if r.data:
            try:
                if cache_key:
                    import json as _json
                    redis = get_redis()
                    await redis.setex(cache_key, 60, _json.dumps(r.data[0]))
            except Exception:
                pass
            return {"ok": True, "assistant": r.data[0]}
    r = supabase.table("assistants").select("*").eq("scope", "global").eq("role", role).eq("is_active", True).limit(1).execute()
    if r.data:
        try:
            if cache_key:
                import json as _json
                redis = get_redis()
                await redis.setex(cache_key, 60, _json.dumps(r.data[0]))
        except Exception:
            pass
        return {"ok": True, "assistant": r.data[0]}

    # Fallback: allow global assistant with null role
    r = supabase.table("assistants").select("*").eq("scope", "global").is_("role", None).eq("is_active", True).limit(1).execute()
    if r.data:
        try:
            if cache_key:
                import json as _json
                redis = get_redis()
                await redis.setex(cache_key, 60, _json.dumps(r.data[0]))
        except Exception:
            pass
        return {"ok": True, "assistant": r.data[0]}
    return {"ok": False, "error": "No assistant configured"}


