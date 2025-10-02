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
    print(f"🔧 OPA DEBUG: payload={payload}, result={result}")
    
    # Handle different OPA response formats
    if isinstance(result, bool):
        return result
    elif isinstance(result, dict):
        # Try nested result format first
        if "result" in result and isinstance(result["result"], dict):
            return bool(result["result"].get("allow", False))
        # Try direct allow format
        elif "allow" in result:
            return bool(result["allow"])
        # Try direct boolean result
        else:
            return bool(result)
    else:
        return False


