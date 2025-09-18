from typing import Any, Dict, Optional
import json
import time
from datetime import datetime, timezone

from core.redis_client import get_redis


SESSION_TTL_SECONDS = 3600

def log_session_operation(operation: str, user_id: str, session_data: dict = None, additional_info: str = ""):
    """Log session operations with detailed information"""
    print(f"🔐 SESSION {operation.upper()}: user_id={user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    if session_data:
        active_role = session_data.get('active_role', 'None')
        active_scope = session_data.get('active_scope', 'None')
        active_org_id = session_data.get('active_org_id', 'None')
        roles_count = len(session_data.get('roles', []))
        exp = session_data.get('exp', 'None')
        
        print(f"   📊 Session Data: role={active_role}, scope={active_scope}, org_id={active_org_id}, roles_count={roles_count}, exp={exp}")
        
        if session_data.get('roles'):
            print(f"   🎭 Available Roles:")
            for role in session_data['roles']:
                scope = role.get('scope', 'unknown')
                role_name = role.get('role', 'unknown')
                org_name = role.get('org_name', '')
                org_info = f" at {org_name}" if org_name else ""
                print(f"      - {scope}: {role_name}{org_info}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


def _session_key(user_id: str) -> str:
    return f"session:{user_id}"


async def get_session(user_id: str) -> Optional[Dict[str, Any]]:
    redis = get_redis()
    data = await redis.get(_session_key(user_id))
    if data is None:
        log_session_operation("GET", user_id, additional_info="Session not found in Redis")
        return None
    
    session = json.loads(data)
    log_session_operation("GET", user_id, session, "Session found, refreshing TTL")
    
    # refresh exp on read
    session["exp"] = int(time.time()) + SESSION_TTL_SECONDS
    await redis.expire(_session_key(user_id), SESSION_TTL_SECONDS)
    await redis.set(_session_key(user_id), json.dumps(session), ex=SESSION_TTL_SECONDS)
    return session


async def set_session(user_id: str, session_data: Dict[str, Any]) -> None:
    redis = get_redis()
    # ensure exp is stamped on create/update
    session_data = dict(session_data)
    session_data["exp"] = int(time.time()) + SESSION_TTL_SECONDS
    log_session_operation("SET", user_id, session_data, "Creating/updating session in Redis")
    await redis.set(_session_key(user_id), json.dumps(session_data), ex=SESSION_TTL_SECONDS)


async def delete_session(user_id: str) -> None:
    redis = get_redis()
    log_session_operation("DELETE", user_id, additional_info="Removing session from Redis")
    await redis.delete(_session_key(user_id))


