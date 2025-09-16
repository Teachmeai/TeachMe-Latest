from typing import Any, Dict

from core.opa_client import opa_check


async def check_permission(user_id: str, role: str, action: str, resource: str) -> bool:
    payload = {
        "user": user_id,
        "role": role,
        "action": action,
        "resource": resource,
    }
    result = await opa_check(payload)
    return bool(result.get("result", {}).get("allow", False))


