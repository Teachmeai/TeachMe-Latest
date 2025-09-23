from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import jwt

from middleware.auth_middleware import get_user_id
from core.supabase import get_supabase_admin
from service.session_service import get_session, set_session, delete_session
from service.user_service import build_session_payload, set_profile_active_role
from core.config import config

def log_auth_operation(operation: str, user_id: str, additional_info: str = "", data: dict = None):
    """Log authentication operations with detailed information"""
    print(f"🔑 AUTH {operation.upper()}: user_id={user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    if data:
        print(f"   📋 Response Data: {data}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


class AssignGlobalRoleRequest(BaseModel):
    role: str  # 'student' or 'teacher'

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(user_id: str = Depends(get_user_id), x_device_id: str | None = Header(default=None, alias="X-Device-Id")):
    log_auth_operation("GET_ME", user_id, f"Device ID: {x_device_id}")
    
    session = await get_session(user_id)
    if session is None:
        log_auth_operation("GET_ME", user_id, "No existing session found, creating new session")
        session = await build_session_payload(user_id, device_id=x_device_id)
        await set_session(user_id, session)
        log_auth_operation("GET_ME", user_id, "New session created successfully", {"active_role": session.get("active_role"), "roles_count": len(session.get("roles", []))})
    else:
        if x_device_id and session.get("device_id") != x_device_id:
            log_auth_operation("GET_ME", user_id, f"Updating device ID from {session.get('device_id')} to {x_device_id}")
            session["device_id"] = x_device_id
            await set_session(user_id, session)
        else:
            log_auth_operation("GET_ME", user_id, "Existing session found and returned")
    
    # Attach profile details for convenience
    try:
        supabase = get_supabase_admin()
        profile_resp = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        profile_data = profile_resp.data or None
        if profile_data is None:
            # lazily create a minimal profile row if missing
            now_iso = datetime.now(timezone.utc).isoformat()
            create_resp = supabase.table("profiles").insert({
                "id": user_id,
                "profile_completion_percentage": 0,
                "created_at": now_iso,
                "updated_at": now_iso,
            }).execute()
            profile_data = (create_resp.data or [None])[0]
        # attach auth email for convenience
        try:
            auth_response = supabase.schema("auth").table("users").select("email").eq("id", user_id).single().execute()
            if auth_response.data and profile_data is not None:
                profile_data["email"] = auth_response.data.get("email")
        except Exception:
            pass
        session["profile"] = profile_data
    except Exception:
        # do not fail /me if profile fetch fails
        pass

    # Generate token2 with user_id and active_role
    try:
        secret = config.jwt.SECRET
        algorithm = config.jwt.ALGORITHM or "HS256"
        if secret:
            now = datetime.now(timezone.utc)
            payload = {
                "sub": user_id,
                "active_role": session.get("active_role"),
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(days=1)).timestamp()),
                "aud": "agent",
                "iss": "teachme-backend"
            }
            token2 = jwt.encode(payload, secret, algorithm=algorithm)
            session["token2"] = token2
        else:
            # If no secret configured, omit token2 silently
            pass
    except Exception:
        # Do not break /me on token generation errors
        pass

    return session


@router.post("/switch-role")
async def switch_role(role: str, org_id: str | None = None, user_id: str = Depends(get_user_id)):
    log_auth_operation("SWITCH_ROLE", user_id, f"Requested role: {role}, org_id: {org_id}")
    
    session = await get_session(user_id) or await build_session_payload(user_id)
    
    # Check if role is valid for this user
    role_matches = False
    matched_role_data = None
    for r in session.get("roles", []):
        if r.get("role") == role and (org_id is None or r.get("org_id") == org_id):
            role_matches = True
            matched_role_data = r
            break
    
    if not role_matches:
        log_auth_operation("SWITCH_ROLE", user_id, f"Role switch failed: {role} not available for user")
        return {"ok": False, "error": "Role not assigned"}
    
    old_role = session.get("active_role")
    old_org_id = session.get("active_org_id")
    
    session["active_role"] = role
    if org_id:
        session["active_org_id"] = org_id
    else:
        session["active_org_id"] = matched_role_data.get("org_id")
    
    log_auth_operation("SWITCH_ROLE", user_id, f"Switching from {old_role} (org: {old_org_id}) to {role} (org: {session.get('active_org_id')})")
    
    await set_session(user_id, session)
    await set_profile_active_role(user_id, role)
    
    result = {"ok": True, "active_role": role, "active_org_id": session.get("active_org_id")}
    log_auth_operation("SWITCH_ROLE", user_id, "Role switch completed successfully", result)
    return result


@router.post("/logout")
async def logout(user_id: str = Depends(get_user_id), x_device_id: str | None = Header(default=None, alias="X-Device-Id")):
    log_auth_operation("LOGOUT", user_id, f"User logging out, device_id: {x_device_id}")
    
    try:
        await delete_session(user_id)
        log_auth_operation("LOGOUT", user_id, "Session deleted successfully")
    except Exception as e:
        log_auth_operation("LOGOUT", user_id, f"Error deleting session: {str(e)}", success=False)
        # Continue with logout even if session deletion fails
    
    result = {"ok": True}
    log_auth_operation("LOGOUT", user_id, "Logout completed successfully", result)
    return result


@router.post("/assign-global-role")
async def assign_global_role(
    request: AssignGlobalRoleRequest, 
    user_id: str = Depends(get_user_id)
):
    """
    Assign a global role (student or teacher) to the current user.
    This allows users without global roles to become global students or teachers.
    """
    log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, f"Requested role: {request.role}")
    
    # Validate role
    if request.role not in ['student', 'teacher']:
        log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, f"Invalid role: {request.role}", success=False)
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'teacher'")
    
    supabase = get_supabase_admin()
    
    try:
        # Check if user already has this global role
        existing_role_resp = supabase.table("user_roles").select("*").eq("user_id", user_id).eq("role", request.role).execute()
        
        if existing_role_resp.data:
            log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, f"User already has global role: {request.role}")
            return {"ok": True, "message": f"You already have the {request.role} role", "role": request.role}
        
        # Allow multiple global roles - removed the restriction
        
        # Assign the global role
        insert_resp = supabase.table("user_roles").insert({
            "user_id": user_id,
            "role": request.role
        }).execute()
        
        if not insert_resp.data:
            log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, "Failed to insert global role", success=False)
            raise HTTPException(status_code=500, detail="Failed to assign role")
        
        # Update profile active_role if user doesn't have one
        profile_resp = supabase.table("profiles").select("active_role").eq("id", user_id).single().execute()
        if profile_resp.data and not profile_resp.data.get("active_role"):
            supabase.table("profiles").update({"active_role": request.role}).eq("id", user_id).execute()
        
        # Refresh session to include new role
        session = await build_session_payload(user_id)
        await set_session(user_id, session)
        
        log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, f"Successfully assigned global role: {request.role}")
        return {"ok": True, "message": f"Successfully assigned {request.role} role", "role": request.role}
        
    except Exception as e:
        log_auth_operation("ASSIGN_GLOBAL_ROLE", user_id, f"Error assigning role: {str(e)}", success=False)
        raise HTTPException(status_code=500, detail="Failed to assign role")


@router.post("/logout/force")
async def force_logout(user_id: str, x_device_id: str | None = Header(default=None, alias="X-Device-Id")):
    """
    Force logout endpoint that doesn't require JWT authentication.
    Used when JWT has expired but we still need to clear the session.
    """
    log_auth_operation("FORCE_LOGOUT", user_id, f"Force logout, device_id: {x_device_id}")
    
    try:
        await delete_session(user_id)
        log_auth_operation("FORCE_LOGOUT", user_id, "Session deleted successfully")
    except Exception as e:
        log_auth_operation("FORCE_LOGOUT", user_id, f"Error deleting session: {str(e)}", success=False)
    
    result = {"ok": True}
    log_auth_operation("FORCE_LOGOUT", user_id, "Force logout completed", result)
    return result


