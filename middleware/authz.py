from fastapi import Depends, HTTPException

from middleware.auth_middleware import get_user_id
from service.session_service import get_session
from service.opa_service import check_permission


async def authorize(action: str, resource: str, user_id: str = Depends(get_user_id)) -> str:
    session = await get_session(user_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")
    role = session.get("active_role")
    if not role:
        raise HTTPException(status_code=403, detail="No active role")
    allowed = await check_permission(user_id, role, action, resource)
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id


