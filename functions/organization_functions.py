"""
Organization-related functions for assistant tool calls.
These functions replicate the logic from the API endpoints but work as direct function calls.
"""

import os
import logging
from datetime import datetime, timezone

from core.supabase import get_supabase_admin
from service.session_service import get_session, set_session
from service.user_service import build_session_payload
from service.opa_service import check_permission
from core.email_service import send_invite_email

logger = logging.getLogger("uvicorn.error")


async def create_organization(user_id: str, name: str) -> dict:
    """
    Create a new organization.
    
    Args:
        user_id: ID of the user creating the organization
        name: Name of the organization
        
    Returns:
        dict: Result with organization data or error
    """
    try:
        logger.info(f"🔧 CREATE ORG: user_id={user_id}, name={name}")
        
        # Check if user is super_admin and has OPA permission
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            return {"error": "Session not found"}
        
        user_role = session.get("active_role")
        if not user_role:
            return {"error": "No active role"}
        
        # OPA authorization check
        try:
            allowed = await check_permission(user_id, user_role, "create", "organization")
            if not allowed:
                return {"error": "Forbidden: insufficient permissions to create organization"}
        except Exception as opa_error:
            logger.warning(f"⚠️ OPA CHECK FAILED: {str(opa_error)} - Proceeding without OPA check")
        
        # Additional role check for super_admin
        if user_role != "super_admin":
            return {"error": "Only super_admin can create organizations"}
        
        # Create organization
        supabase = get_supabase_admin()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            resp = supabase.table("organizations").insert({
                "name": name,
                "created_by": user_id,
                "created_at": now_iso,
            }).execute()
            org = (resp.data or [None])[0]
            if not org:
                return {"error": "Failed to create organization"}
            return {"ok": True, "organization": org}
        except Exception as e:
            logger.error(f"❌ CREATE ORG ERROR: {str(e)}")
            return {"error": f"Failed to create organization: {str(e)}"}
            
    except Exception as e:
        logger.error(f"❌ CREATE ORG ERROR: {str(e)}")
        return {"error": f"Failed to create organization: {str(e)}"}


async def invite_organization_admin(user_id: str, org_id: str, invitee_email: str, role: str = "organization_admin") -> dict:
    """
    Invite an organization admin to an organization.
    
    Args:
        user_id: ID of the user making the invite
        org_id: ID of the organization
        invitee_email: Email of the person being invited
        role: Role to assign (default: organization_admin)
        
    Returns:
        dict: Result with invite data and email status or error
    """
    try:
        logger.info(f"🔧 INVITE ORG ADMIN: user_id={user_id}, org_id={org_id}, invitee_email={invitee_email}, role={role}")
        
        if not invitee_email:
            logger.error(f"❌ INVITE ERROR: invitee_email is required")
            return {"error": "invitee_email is required"}
        
        # Check permissions with OPA authorization
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            return {"error": "Session not found"}
        
        user_role = session.get("active_role")
        if not user_role:
            return {"error": "No active role"}
        
        # OPA authorization check for inviting to organization
        try:
            allowed = await check_permission(user_id, user_role, "invite", f"organization:{org_id}")
            if not allowed:
                return {"error": "Forbidden: insufficient permissions to invite to this organization"}
        except Exception as opa_error:
            logger.warning(f"⚠️ OPA CHECK FAILED: {str(opa_error)} - Proceeding without OPA check")
        
        is_super_admin = user_role == "super_admin"
        
        # Check if user is org admin for this org
        supabase = get_supabase_admin()
        is_org_admin = False
        if not is_super_admin:
            logger.info(f"🔧 INVITE DEBUG: Checking org admin membership for user {user_id} in org {org_id}")
            try:
                resp = (
                    supabase
                    .table("organization_memberships")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("org_id", org_id)
                    .eq("role", "organization_admin")
                    .limit(1)
                    .execute()
                )
                logger.info(f"🔧 INVITE DEBUG: Org membership query result: {resp.data}")
                is_org_admin = bool(resp.data)
                logger.info(f"🔧 INVITE DEBUG: is_org_admin = {is_org_admin}")
            except Exception as e:
                logger.error(f"❌ INVITE ERROR: Org membership check failed: {str(e)}")
                is_org_admin = False
        
        # Check allowed roles
        allowed_roles = ["organization_admin"] if is_super_admin else ["organization_admin", "teacher"] if is_org_admin else []
        logger.info(f"🔧 INVITE DEBUG: user_role={user_role}, is_super_admin={is_super_admin}, is_org_admin={is_org_admin}, allowed_roles={allowed_roles}, invitee_role={role}")
        if role not in allowed_roles:
            logger.error(f"❌ INVITE ERROR: Role {role} not in allowed roles {allowed_roles}")
            return {"error": "Invalid role for organization invite"}
        
        # Create invite
        now_iso = datetime.now(timezone.utc).isoformat()
        logger.info(f"🔧 INVITE DEBUG: About to create invite in database")
        try:
            invite_resp = supabase.table("invites").insert({
                "inviter": user_id,
                "invitee_email": str(invitee_email).lower(),
                "role": role,
                "org_id": org_id,
                "status": "pending",
                "created_at": now_iso,
            }).execute()
            logger.info(f"🔧 INVITE DEBUG: Database insert response: {invite_resp.data}")
            invite = (invite_resp.data or [None])[0]
            if not invite:
                logger.error(f"❌ INVITE ERROR: Failed to create invite - no data returned")
                return {"error": "Failed to create invite"}
            logger.info(f"🔧 INVITE DEBUG: Invite created successfully: {invite.get('id')}")
            
            # Send invitation email
            email_sent = False
            try:
                logger.info(f"📧 STARTING EMAIL SEND: invitee={invitee_email}, org_id={org_id}, invite_id={invite.get('id')}")
                
                # Debug environment variables
                logger.info(f"📧 ENV CHECK: MAIL_USERNAME={os.getenv('MAIL_USERNAME', 'NOT_SET')}")
                logger.info(f"📧 ENV CHECK: MAIL_PASSWORD={'SET' if os.getenv('MAIL_PASSWORD') else 'NOT_SET'}")
                logger.info(f"📧 ENV CHECK: MAIL_FROM={os.getenv('MAIL_FROM', 'NOT_SET')}")

                org_resp = supabase.table("organizations").select("name").eq("id", org_id).single().execute()
                org_name = (org_resp.data or {}).get("name") or "Your Organization"
                logger.info(f"📧 ORG NAME: {org_name}")
                
                # Try to send email and catch any specific errors
                try:
                    email_sent = await send_invite_email(str(invitee_email), org_name, invite.get("id"), role)
                    logger.info(f"📧 EMAIL SEND RESULT: {email_sent} for invite {invite.get('id')}")
                except Exception as email_error:
                    logger.error(f"❌ EMAIL SERVICE ERROR: {str(email_error)}")
                    import traceback
                    logger.error(f"❌ EMAIL SERVICE TRACEBACK: {traceback.format_exc()}")
                    email_sent = False
                
                if not email_sent:
                    logger.error(f"❌ EMAIL SEND FAILED: send_invite_email returned False")
            except Exception as e:
                logger.error(f"❌ EMAIL ERROR: {str(e)}")
                import traceback
                logger.error(f"❌ EMAIL TRACEBACK: {traceback.format_exc()}")
                email_sent = False
            
            return {"ok": True, "invite": invite, "email_sent": email_sent}
        except Exception as e:
            logger.error(f"❌ INVITE ORG ERROR: {str(e)}")
            return {"error": f"Failed to invite organization admin: {str(e)}"}
            
    except Exception as e:
        logger.error(f"❌ INVITE ORG ERROR: {str(e)}")
        return {"error": f"Failed to invite organization admin: {str(e)}"}
