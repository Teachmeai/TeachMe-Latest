from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime, timezone

from core.supabase import get_supabase_admin
from middleware.auth_middleware import get_user_id

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

class AcceptInviteRequest(BaseModel):
    invite_id: str

@router.post("/generate-enrollment-token")
async def generate_enrollment_token(
    payload: AcceptInviteRequest
):
    """Generate a JWT token for course enrollment (public endpoint for email links)"""
    try:
        import jwt
        from core.config import config
        
        supabase = get_supabase_admin()
        
        # Get the invite with course details
        invite_resp = supabase.table("course_invites").select("""
            *,
            courses(
                id,
                org_id
            )
        """).eq("id", payload.invite_id).single().execute()
        
        if not invite_resp.data:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        invite = invite_resp.data
        
        # Check if invite is still valid
        if invite["status"] != "pending":
            raise HTTPException(status_code=400, detail="Invitation is no longer valid")
        
        try:
            expires_str = invite["expires_at"]
            if expires_str.endswith('Z'):
                expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
            elif '+' in expires_str or expires_str.endswith('00:00'):
                expires_at = datetime.fromisoformat(expires_str)
            else:
                expires_at = datetime.fromisoformat(expires_str + '+00:00')
            
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Invitation has expired")
        except Exception as dt_error:
            logger.error(f"❌ DATETIME PARSING ERROR: {str(dt_error)}")
            raise HTTPException(status_code=400, detail="Invalid invitation expiration date")
        
        # Generate JWT token for enrollment (similar to old system)
        course = invite["courses"]
        token_data = {
            "scope": "course_invite",
            "course_id": course["id"],
            "org_id": course["org_id"],
            "invite_id": payload.invite_id,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
        }
        
        token = jwt.encode(token_data, config.jwt.SECRET, algorithm=config.jwt.ALGORITHM)
        
        return {
            "ok": True,
            "message": "Enrollment token generated successfully",
            "token": token,
            "invite": invite
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GENERATE ENROLLMENT TOKEN ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate enrollment token")

@router.post("/accept")
async def accept_course_invite(
    payload: AcceptInviteRequest,
    user_id: str = Depends(get_user_id)
):
    """Accept a course invitation and enroll the user"""
    try:
        supabase = get_supabase_admin()
        
        # Get the invite
        invite_resp = supabase.table("course_invites").select("*").eq("id", payload.invite_id).single().execute()
        if not invite_resp.data:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        invite = invite_resp.data
        
        # Check if invite is still valid
        if invite["status"] != "pending":
            raise HTTPException(status_code=400, detail="Invitation is no longer valid")
        
        try:
            expires_str = invite["expires_at"]
            if expires_str.endswith('Z'):
                expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
            elif '+' in expires_str or expires_str.endswith('00:00'):
                expires_at = datetime.fromisoformat(expires_str)
            else:
                expires_at = datetime.fromisoformat(expires_str + '+00:00')
            
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Invitation has expired")
        except Exception as dt_error:
            logger.error(f"❌ DATETIME PARSING ERROR: {str(dt_error)}")
            raise HTTPException(status_code=400, detail="Invalid invitation expiration date")
        
        # Get user's email to verify
        user_resp = supabase.table("profiles").select("id").eq("id", user_id).single().execute()
        if not user_resp.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get course info to get organization ID
        course_resp = supabase.table("courses").select("org_id").eq("id", invite["course_id"]).single().execute()
        if not course_resp.data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        org_id = course_resp.data["org_id"]
        
        # Ensure organization membership exists (as student)
        mem_exists = supabase.table("organization_memberships").select("id").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
        if not (mem_exists.data or []):
            supabase.table("organization_memberships").insert({
                "org_id": org_id,
                "user_id": user_id,
                "role": "student",
                "status": "active"
            }).execute()
        
        # Check if user is already enrolled
        existing_enrollment = supabase.table("enrollments").select("id").eq("user_id", user_id).eq("course_id", invite["course_id"]).limit(1).execute()
        if existing_enrollment.data:
            raise HTTPException(status_code=400, detail="Already enrolled in this course")
        
        # Update invite status
        supabase.table("course_invites").update({
            "status": "accepted",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", payload.invite_id).execute()
        
        # Create enrollment
        enrollment_resp = supabase.table("enrollments").insert({
            "user_id": user_id,
            "course_id": invite["course_id"]
        }).execute()
        
        enrollment = (enrollment_resp.data or [None])[0]
        if not enrollment:
            raise HTTPException(status_code=500, detail="Failed to create enrollment")
        
        # Get course info
        course_resp = supabase.table("courses").select("title, org_id").eq("id", invite["course_id"]).single().execute()
        course = course_resp.data if course_resp.data else {}
        
        return {
            "ok": True,
            "message": f"Successfully enrolled in course: {course.get('title', 'Unknown Course')}",
            "enrollment": enrollment,
            "course": course
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ACCEPT COURSE INVITE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept invitation")

@router.get("/{invite_id}")
async def get_invite_details(invite_id: str):
    """Get invitation details by ID (public endpoint for invitation links)"""
    try:
        supabase = get_supabase_admin()
        
        # Get the invite with course and organization details
        invite_resp = supabase.table("course_invites").select("""
            *,
            courses(
                id,
                title,
                description,
                org_id,
                organizations(
                    id,
                    name
                )
            )
        """).eq("id", invite_id).single().execute()
        
        if not invite_resp.data:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        invite = invite_resp.data
        
        # Check if invitation is expired
        if invite["status"] == "pending":
            try:
                # Handle different datetime formats
                expires_str = invite["expires_at"]
                
                # Try different parsing approaches
                if expires_str.endswith('Z'):
                    expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                elif '+' in expires_str or expires_str.endswith('00:00'):
                    expires_at = datetime.fromisoformat(expires_str)
                else:
                    # Assume UTC if no timezone info
                    expires_at = datetime.fromisoformat(expires_str + '+00:00')
                
                if datetime.now(timezone.utc) > expires_at:
                    # Update status to expired
                    supabase.table("course_invites").update({
                        "status": "expired",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", invite_id).execute()
                    invite["status"] = "expired"
            except Exception as dt_error:
                logger.error(f"❌ DATETIME PARSING ERROR: {str(dt_error)}")
                logger.error(f"❌ expires_at value: '{invite.get('expires_at', 'NOT_FOUND')}'")
                # Continue without expiring the invite if we can't parse the date
        
        return {
            "ok": True,
            "invite": invite
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GET INVITE DETAILS ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invitation details")

@router.get("/my")
async def get_my_invites(user_id: str = Depends(get_user_id)):
    """Get pending course invitations for the current user"""
    try:
        # Get user's email from profile or auth
        # For now, we'll need to get this from the user's auth data
        # This is a simplified version - you might need to get email from Supabase auth
        
        # Get all pending invites (this would need email matching in real implementation)
        supabase = get_supabase_admin()
        invites_resp = supabase.table("course_invites").select("*, courses(title, description)").eq("status", "pending").execute()
        
        return {
            "ok": True,
            "invites": invites_resp.data or []
        }
        
    except Exception as e:
        logger.error(f"❌ GET MY INVITES ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invitations")
