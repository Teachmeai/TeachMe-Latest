from typing import Dict, List, TypedDict
from datetime import datetime, timezone

from core.supabase import get_supabase_admin

def log_user_operation(operation: str, user_id: str, additional_info: str = "", data: dict = None):
    """Log user service operations with detailed information"""
    print(f"👤 USER {operation.upper()}: user_id={user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    if data:
        print(f"   📋 Data: {data}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


class RoleEntry(TypedDict, total=False):
    scope: str
    role: str
    org_id: str
    org_name: str


async def get_user_roles(user_id: str) -> List[RoleEntry]:
    supabase = get_supabase_admin()
    # Global roles
    global_resp = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
    global_roles: List[RoleEntry] = [
        {"scope": "global", "role": r["role"]} for r in (global_resp.data or [])
    ]

    # Org memberships: fetch memberships then org names in batch
    mem_resp = supabase.table("organization_memberships").select("role,org_id").eq("user_id", user_id).execute()
    memberships = mem_resp.data or []
    org_ids = sorted(list({m["org_id"] for m in memberships if m.get("org_id")}))
    org_map: Dict[str, str] = {}
    if org_ids:
        orgs_resp = supabase.table("organizations").select("id,name").in_("id", org_ids).execute()
        for o in (orgs_resp.data or []):
            org_map[o["id"]] = o.get("name")
    org_roles: List[RoleEntry] = []
    for m in memberships:
        org_id = m.get("org_id")
        org_roles.append({
            "scope": "org",
            "role": m.get("role"),
            "org_id": org_id,
            "org_name": org_map.get(org_id) if org_id else None,  # type: ignore
        })

    return global_roles + org_roles


async def get_profile_active_role(user_id: str) -> str | None:
    supabase = get_supabase_admin()
    resp = supabase.table("profiles").select("active_role").eq("id", user_id).single().execute()
    return (resp.data or {}).get("active_role") if resp.data else None


async def set_profile_active_role(user_id: str, role: str) -> None:
    log_user_operation("SET_ACTIVE_ROLE", user_id, f"Setting active role in profile to: {role}")
    supabase = get_supabase_admin()
    supabase.table("profiles").update({"active_role": role}).eq("id", user_id).execute()
    log_user_operation("SET_ACTIVE_ROLE", user_id, f"Successfully updated profile active role to: {role}")


async def build_session_payload(user_id: str, device_id: str | None = None) -> Dict:
    log_user_operation("BUILD_SESSION", user_id, f"Building session payload, device_id: {device_id}")
    
    roles = await get_user_roles(user_id)
    log_user_operation("BUILD_SESSION", user_id, f"Found {len(roles)} roles for user", {"roles": [f"{r['scope']}:{r['role']}" for r in roles]})
    
    saved_role = await get_profile_active_role(user_id)
    log_user_operation("BUILD_SESSION", user_id, f"Saved active role from profile: {saved_role}")
    
    # choose active role string for backward compatibility (e.g., "teacher")
    role_names = [r["role"] for r in roles]
    active_role = saved_role if saved_role in role_names else (role_names[0] if role_names else "student")
    
    log_user_operation("BUILD_SESSION", user_id, f"Selected active role: {active_role} (from saved: {saved_role}, available: {role_names})")
    
    payload: Dict = {
        "user_id": user_id,
        "roles": roles,
        "active_role": active_role,
    }
    if device_id:
        payload["device_id"] = device_id
    
    log_user_operation("BUILD_SESSION", user_id, "Session payload built successfully", {"active_role": active_role, "roles_count": len(roles), "has_device_id": bool(device_id)})
    return payload


