from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from middleware.auth_middleware import get_user_id, auth_middleware
from service.session_service import get_session, set_session
from service.user_service import build_session_payload
from core.supabase import get_supabase_admin
from core.email_service import send_invite_email


router = APIRouter(prefix="/organizations", tags=["organizations"])


class CreateOrganizationRequest(BaseModel):
    name: str


class InviteRequest(BaseModel):
    invitee_email: EmailStr
    role: str = "organization_admin"  # one of: organization_admin, teacher, student


def _require_super_admin(session: dict):
    role = session.get("active_role")
    if role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super_admin can perform this action")


def _is_org_admin_for(supabase, user_id: str, org_id: str) -> bool:
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
        return bool(resp.data)
    except Exception:
        return False


@router.get("")
async def list_organizations(user_id: str = Depends(get_user_id)):
    session = await get_session(user_id) or await build_session_payload(user_id)
    _require_super_admin(session)

    supabase = get_supabase_admin()
    try:
        resp = supabase.table("organizations").select("id,name,created_by,created_at").order("created_at", desc=True).execute()
        return {"ok": True, "organizations": resp.data or []}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list organizations")

# COMMENTED OUT - Now using direct function calls in assistant_chats.py
# @router.post("")
# async def create_organization(payload: CreateOrganizationRequest, user_id: str = Depends(get_user_id)):
#     session = await get_session(user_id) or await build_session_payload(user_id)
#     _require_super_admin(session)
#
#     supabase = get_supabase_admin()
#     now_iso = datetime.now(timezone.utc).isoformat()
#     try:
#         resp = supabase.table("organizations").insert({
#             "name": payload.name,
#             "created_by": user_id,
#             "created_at": now_iso,
#         }).execute()
#         org = (resp.data or [None])[0]
#         if not org:
#             raise HTTPException(status_code=500, detail="Failed to create organization")
#         return {"ok": True, "organization": org}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Error creating organization")


# COMMENTED OUT - Now using direct function calls in assistant_chats.py
# @router.post("/{org_id}/invites")
# async def invite_org_role(org_id: str, request: InviteRequest, user_id: str = Depends(get_user_id)):
#     session = await get_session(user_id) or await build_session_payload(user_id)
#
#     # Permissions:
#     # - super_admin: may invite [organization_admin] only
#     # - org_admin of this org: may invite [organization_admin, teacher]
#     is_super_admin = session.get("active_role") == "super_admin"
#     supabase = get_supabase_admin()
#     is_org_admin = _is_org_admin_for(supabase, user_id, org_id)
#
#     allowed_roles = ["organization_admin"] if is_super_admin else ["organization_admin", "teacher"] if is_org_admin else []
#
#     if request.role not in allowed_roles:
#         raise HTTPException(status_code=400, detail="Invalid role for organization invite")
#
#     now_iso = datetime.now(timezone.utc).isoformat()
#     try:
#         # Create pending invite
#         invite_resp = supabase.table("invites").insert({
#             "inviter": user_id,
#             "invitee_email": str(request.invitee_email).lower(),
#             "role": request.role,
#             "org_id": org_id,
#             "status": "pending",
#             "created_at": now_iso,
#         }).execute()
#         invite = (invite_resp.data or [None])[0]
#         if not invite:
#             raise HTTPException(status_code=500, detail="Failed to create invite")
#         # Send invitation email (best-effort)
#         email_sent = False
#         try:
#             # Lookup org name for nicer email content
#             org_resp = supabase.table("organizations").select("name").eq("id", org_id).single().execute()
#             org_name = (org_resp.data or {}).get("name") or "Your Organization"
#             email_sent = await send_invite_email(str(request.invitee_email), org_name, invite.get("id"))
#         except Exception:
#             # Do not fail the endpoint if email sending fails
#             email_sent = False
#         return {"ok": True, "invite": invite, "email_sent": email_sent}
#     except Exception:
#         raise HTTPException(status_code=500, detail="Error creating invite")

class InviteTeacherRequest(BaseModel):
    invitee_email: EmailStr


# COMMENTED OUT - handled by assistant tool internal function
# @router.post("/{org_id}/invites/teacher")
# async def invite_teacher(
#     org_id: str,
#     payload: InviteTeacherRequest = Body(..., embed=False),
#     user_id: str = Depends(get_user_id),
# ):
#     supabase = get_supabase_admin()
#     is_org_admin = _is_org_admin_for(supabase, user_id, org_id)
#     if not is_org_admin:
#         raise HTTPException(status_code=403, detail="Only org admin can invite teachers")
#     invitee_email = str(payload.invitee_email).lower()
#     now_iso = datetime.now(timezone.utc).isoformat()
#     try:
#         invite_resp = supabase.table("invites").insert({
#             "inviter": user_id,
#             "invitee_email": invitee_email,
#             "role": "teacher",
#             "org_id": org_id,
#             "status": "pending",
#             "created_at": now_iso,
#         }).execute()
#         invite = (invite_resp.data or [None])[0]
#         if not invite:
#             raise HTTPException(status_code=500, detail="Failed to create invite")
#         email_sent = False
#         try:
#             org_resp = supabase.table("organizations").select("name").eq("id", org_id).single().execute()
#             org_name = (org_resp.data or {}).get("name") or "Your Organization"
#             email_sent = await send_invite_email(str(invitee_email), org_name, invite.get("id"))
#         except Exception:
#             email_sent = False
#         return {"ok": True, "invite": invite, "email_sent": email_sent}
#     except Exception:
#         raise HTTPException(status_code=500, detail="Error creating invite")


class AcceptInviteRequest(BaseModel):
    org_id: str


@router.post("/invites/accept")
async def accept_invite(request: AcceptInviteRequest, user_id: str = Depends(get_user_id)):
    supabase = get_supabase_admin()

    # Fetch current user's email from auth.users
    try:
        auth_user = supabase.schema("auth").table("users").select("email").eq("id", user_id).single().execute()
        user_email = (auth_user.data or {}).get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read user email")

    # Find pending invite for this user and org
    try:
        invite_resp = supabase.table("invites").select("id, role").eq("invitee_email", user_email).eq("org_id", request.org_id).eq("status", "pending").limit(1).execute()
        invite = (invite_resp.data or [None])[0]
        if not invite:
            raise HTTPException(status_code=404, detail="Pending invite not found")
        invite_id = invite.get("id")
        role = invite.get("role")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to lookup invite")

    # Create organization_membership and mark invite accepted
    try:
        supabase.table("organization_memberships").insert({
            "org_id": request.org_id,
            "user_id": user_id,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        supabase.table("invites").update({"status": "accepted"}).eq("id", invite_id).execute()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to accept invite")

    # Refresh session to include new org role
    session = await build_session_payload(user_id)
    await set_session(user_id, session)

    return {"ok": True, "org_id": request.org_id, "role": role}


class AcceptInviteByIdRequest(BaseModel):
    invite_id: str


@router.post("/invites/accept-by-id")
async def accept_invite_by_id(request: AcceptInviteByIdRequest, user_id: str = Depends(get_user_id), token_payload: dict = Depends(auth_middleware)):
    supabase = get_supabase_admin()

    # Prefer email from JWT payload to avoid auth schema lookup issues
    user_email = (token_payload or {}).get("email")

    # Fetch invite by id
    try:
        invite_resp = supabase.table("invites").select("id, invitee_email, role, org_id, status").eq("id", request.invite_id).single().execute()
        invite = invite_resp.data
        if not invite:
            raise HTTPException(status_code=404, detail="Invite not found")
        # Verify pending and email matches (case-insensitive)
        if invite.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Invite is not pending")
        if user_email:
            if str(invite.get("invitee_email", "")).lower() != str(user_email).lower():
                raise HTTPException(status_code=403, detail="Invite email does not match signed-in user")
        # Debug: log identifiers
        try:
            print("✅ ACCEPT_INVITE IDs:", {
                "request_invite_id": request.invite_id,
                "resolved_org_id": invite.get("org_id"),
                "user_id": user_id,
                "invite_role": invite.get("role"),
                "jwt_email": user_email,
                "invite_email": invite.get("invitee_email"),
            })
        except Exception:
            pass
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read invite")

    # Create membership and mark accepted
    try:
        mem_resp = supabase.table("organization_memberships").insert({
            "org_id": invite.get("org_id"),
            "user_id": user_id,
            "role": invite.get("role"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        membership = (mem_resp.data or [None])[0]
        if not membership:
            # If PostgREST didn't return row, verify with a read
            check = supabase.table("organization_memberships").select("id").eq("org_id", invite.get("org_id")).eq("user_id", user_id).eq("role", invite.get("role")).limit(1).execute()
            if not (check.data or []):
                raise Exception("Membership insert could not be verified")

        upd_resp = supabase.table("invites").update({"status": "accepted"}).eq("id", request.invite_id).execute()
        # Verify status changed
        verify = supabase.table("invites").select("id,status,org_id").eq("id", request.invite_id).single().execute()
        if (verify.data or {}).get("status") != "accepted":
            raise Exception("Invite status update failed")
        try:
            print("✅ ACCEPT_INVITE updated:", {
                "invite_id": request.invite_id,
                "status": (verify.data or {}).get("status"),
                "org_id": (verify.data or {}).get("org_id"),
            })
        except Exception:
            pass
    except Exception as e:
        print(f"❌ ACCEPT_INVITE error for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept invite")

    # Refresh session
    session = await build_session_payload(user_id)
    await set_session(user_id, session)

    return {"ok": True, "org_id": invite.get("org_id"), "role": invite.get("role")}


@router.get("/invites/{invite_id}")
async def get_invite(invite_id: str):
    supabase = get_supabase_admin()
    try:
        invite_resp = supabase.table("invites").select("id, invitee_email, role, org_id, status, created_at").eq("id", invite_id).single().execute()
        if not invite_resp.data:
            raise HTTPException(status_code=404, detail="Invite not found")
        return {"ok": True, "invite": invite_resp.data}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch invite")


