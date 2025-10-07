from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import jwt

from middleware.auth_middleware import get_user_id
from service.session_service import get_session
from core.supabase import get_supabase_admin
from core.config import config
from core.email_service import send_course_invite_email


router = APIRouter(prefix="/courses", tags=["courses"])


class CreateCourseRequest(BaseModel):
    org_id: str
    title: str
    description: str | None = None


def _require_teacher_in_org(supabase, user_id: str, org_id: str):
    # teacher must be a member of org with role 'teacher' OR 'organization_admin'
    mem = supabase.table("organization_memberships").select("role").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
    role = (mem.data or [{}])[0].get("role")
    if role not in ("teacher", "organization_admin"):
        raise HTTPException(status_code=403, detail="Only teachers/org admins of this org can perform this action")



class GenerateInviteLinkRequest(BaseModel):
    course_id: str
    expires_in_minutes: int = 60


@router.post("/invite-link")
async def generate_invite_link(payload: GenerateInviteLinkRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    # load course and check membership in org
    course_resp = supabase.table("courses").select("id,org_id,created_by").eq("id", payload.course_id).single().execute()
    course = course_resp.data
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_teacher_in_org(supabase, user_id, course.get("org_id"))

    # issue a short-lived token allowing enrollment into the course
    try:
        secret = config.jwt.SECRET
        if not secret:
            raise HTTPException(status_code=500, detail="Server not configured for token issuance")
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=max(5, min(1440, payload.expires_in_minutes)))
        token = jwt.encode({
            "sub": str(user_id),  # issuer user (teacher)
            "course_id": course.get("id"),
            "org_id": course.get("org_id"),
            "scope": "course_invite",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }, secret, algorithm=config.jwt.ALGORITHM)
        # frontend can build URL like /courses/enroll?token=...
        return {"ok": True, "token": token, "expires_at": int(exp.timestamp())}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate invite token")


class SendCourseInviteEmailRequest(BaseModel):
    invitee_email: str
    expires_in_minutes: int = 60



class EnrollByTokenRequest(BaseModel):
    token: str


@router.post("/enroll-by-token")
async def enroll_by_token(payload: EnrollByTokenRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    # verify token and extract course/org
    try:
        data = jwt.decode(payload.token, config.jwt.SECRET, algorithms=[config.jwt.ALGORITHM], options={
            "verify_signature": True,
            "verify_exp": True,
        })
        if data.get("scope") != "course_invite":
            raise HTTPException(status_code=400, detail="Invalid token scope")
        course_id = data.get("course_id")
        org_id = data.get("org_id")
        if not course_id or not org_id:
            raise HTTPException(status_code=400, detail="Token missing course/org")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # ensure org membership (student) exists, then create enrollment if not exists
    try:
        # 1) Upsert organization membership as student
        mem_exists = supabase.table("organization_memberships").select("id").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
        if not (mem_exists.data or []):
            supabase.table("organization_memberships").insert({
                "org_id": org_id,
                "user_id": user_id,
                "role": "student",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

        # 2) Create enrollment if not already enrolled
        existing = supabase.table("enrollments").select("id").eq("user_id", user_id).eq("course_id", course_id).limit(1).execute()
        if existing.data:
            return {"ok": True, "enrolled": True, "already": True}
        supabase.table("enrollments").insert({
            "user_id": user_id,
            "course_id": course_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return {"ok": True, "enrolled": True}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to enroll user")



class SetCourseAssistantRequest(BaseModel):
    assistant_id: str


@router.post("/{course_id}/assistant")
async def set_course_assistant(course_id: str, payload: SetCourseAssistantRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    # load course and check membership in org
    course_resp = supabase.table("courses").select("id,org_id").eq("id", course_id).single().execute()
    course = course_resp.data
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_teacher_in_org(supabase, user_id, course.get("org_id"))

    # ensure assistant exists
    a_resp = supabase.table("assistants").select("id").eq("id", payload.assistant_id).single().execute()
    if not (a_resp.data or None):
        raise HTTPException(status_code=404, detail="Assistant not found")

    supabase.table("courses").update({"assistant_id": payload.assistant_id}).eq("id", course_id).execute()
    return {"ok": True}


@router.get("/my")
async def my_courses(user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()
    enr = supabase.table("enrollments").select("course_id").eq("user_id", user_id).execute().data or []
    course_ids = [e.get("course_id") for e in enr]
    if not course_ids:
        return {"ok": True, "courses": []}
    courses_resp = supabase.table("courses").select("id,org_id,title,description,status,assistant_id,created_at,updated_at").in_("id", course_ids).execute()
    return {"ok": True, "courses": courses_resp.data or []}
