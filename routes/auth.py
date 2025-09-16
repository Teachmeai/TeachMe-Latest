from fastapi import APIRouter, Depends, Header
from datetime import datetime, timezone

from middleware.auth_middleware import get_user_id
from service.session_service import get_session, set_session, delete_session
from service.user_service import build_session_payload, set_profile_active_role

def log_auth_operation(operation: str, user_id: str, additional_info: str = "", data: dict = None):
    """Log authentication operations with detailed information"""
    print(f"🔑 AUTH {operation.upper()}: user_id={user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    if data:
        print(f"   📋 Response Data: {data}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


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


