"""
Teacher-related functions for assistant tool calls.
These can be wired to tools: create_course, invite_student, enroll_student.

Note: Some endpoints may not exist yet. The functions below include
basic scaffolding and should be completed against your real course APIs.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from core.supabase import get_supabase_admin
from core.email_service import send_course_invite_email
from core.config import config
import jwt

logger = logging.getLogger("uvicorn.error")


async def create_course(user_id: str, org_id: str, name: str, description: Optional[str] = None) -> dict:
    """Create a course within the specified organization.

    Expects a table public.courses with (id, org_id, name, description, created_by, created_at).
    Add/adjust columns to match your schema.
    """
    try:
        if not org_id or not name:
            return {"error": "org_id and name are required"}

        supabase = get_supabase_admin()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "org_id": org_id,
            "name": name,
            "description": description or "",
            "created_by": user_id,
            "created_at": now_iso,
        }
        resp = supabase.table("courses").insert(payload).execute()
        course = (resp.data or [None])[0]
        if not course:
            return {"error": "Failed to create course"}
        return {"ok": True, "course": course}
    except Exception as e:
        logger.error(f"❌ CREATE COURSE ERROR: {str(e)}")
        return {"error": f"Failed to create course: {str(e)}"}


async def invite_student(user_id: str, course_id: str, email: str) -> dict:
    """Invite a student to a course by email.

    Expects a table public.course_invites (id, course_id, email, inviter, status, created_at).
    Adjust as per your schema; sending email can reuse core.email_service if needed.
    """
    try:
        if not course_id or not email:
            return {"error": "course_id and email are required"}

        supabase = get_supabase_admin()
        now_iso = datetime.now(timezone.utc).isoformat()
        invite_resp = supabase.table("course_invites").insert({
            "course_id": course_id,
            "email": str(email).lower(),
            "inviter": user_id,
            "status": "pending",
            "created_at": now_iso,
        }).execute()
        invite = (invite_resp.data or [None])[0]
        if not invite:
            return {"error": "Failed to create course invite"}
        return {"ok": True, "invite": invite}
    except Exception as e:
        logger.error(f"❌ INVITE STUDENT ERROR: {str(e)}")
        return {"error": f"Failed to invite student: {str(e)}"}


async def send_course_invite_email_function(user_id: str, course_id: str, email: str, expires_in_minutes: int = 60) -> dict:
    """Generate an enroll token for a course and send invite email to the student.

    Mirrors logic from routes.courses.generate_invite_link + send_course_invite_email endpoint.
    """
    try:
        if not course_id or not email:
            return {"error": "course_id and email are required"}

        supabase = get_supabase_admin()
        # load course and org
        course_resp = supabase.table("courses").select("id,org_id,title").eq("id", course_id).single().execute()
        course = course_resp.data
        if not course:
            return {"error": "Course not found"}

        # generate token
        secret = config.jwt.SECRET
        if not secret:
            return {"error": "Server not configured for token issuance"}
        now = datetime.now(timezone.utc)
        exp = now + (timezone.utc.utcoffset(now) or (exp := None))  # placeholder to keep style
        # Proper expiration:
        from datetime import timedelta
        exp = now + timedelta(minutes=max(5, min(1440, int(expires_in_minutes or 60))))
        token = jwt.encode({
            "sub": str(user_id),
            "course_id": course.get("id"),
            "org_id": course.get("org_id"),
            "scope": "course_invite",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }, secret, algorithm=config.jwt.ALGORITHM)

        # fetch org name for email
        org_resp = supabase.table("organizations").select("name").eq("id", course.get("org_id")).single().execute()
        org_name = (org_resp.data or {}).get("name") or "Your Organization"

        sent = await send_course_invite_email(str(email).lower(), org_name, course.get("title") or "Course", token)
        return {"ok": True, "email_sent": bool(sent)}
    except Exception as e:
        logger.error(f"❌ SEND COURSE INVITE EMAIL ERROR: {str(e)}")
        return {"error": f"Failed to send course invite email: {str(e)}"}

async def enroll_student(user_id: str, course_id: str, student_id: Optional[str] = None, email: Optional[str] = None) -> dict:
    """Enroll a student into a course by user_id or email.

    Expects a table public.course_enrollments (id, course_id, user_id, created_at).
    If only email is provided, resolve to user_id via your users/profiles table first.
    """
    try:
        if not course_id:
            return {"error": "course_id is required"}

        supabase = get_supabase_admin()

        resolved_user_id: Optional[str] = student_id
        if not resolved_user_id and email:
            try:
                # Adjust table/column names to your auth/profiles
                u = supabase.table("profiles").select("user_id").eq("email", str(email).lower()).limit(1).execute()
                if u.data:
                    resolved_user_id = u.data[0].get("user_id")
            except Exception:
                resolved_user_id = None

        if not resolved_user_id:
            return {"error": "student_id or resolvable email is required"}

        now_iso = datetime.now(timezone.utc).isoformat()
        enr = supabase.table("course_enrollments").insert({
            "course_id": course_id,
            "user_id": resolved_user_id,
            "created_at": now_iso,
        }).execute()
        enrollment = (enr.data or [None])[0]
        if not enrollment:
            return {"error": "Failed to enroll student"}
        return {"ok": True, "enrollment": enrollment}
    except Exception as e:
        logger.error(f"❌ ENROLL STUDENT ERROR: {str(e)}")
        return {"error": f"Failed to enroll student: {str(e)}"}


