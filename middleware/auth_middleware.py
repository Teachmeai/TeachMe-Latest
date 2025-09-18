from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timezone

from core.config import config
from core.security import security

def log_auth_middleware(operation: str, user_id: str = None, additional_info: str = "", success: bool = True):
    """Log authentication middleware operations"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"🔒 AUTH_MIDDLEWARE {operation.upper()}: {status}")
    
    if user_id:
        print(f"   👤 User ID: {user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


def auth_middleware(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    log_auth_middleware("JWT_VALIDATION", additional_info=f"Token length: {len(token)}")
    
    try:
        payload = jwt.decode(
            token,
            config.jwt.SECRET or config.supabase.ANON_KEY,  # prefer explicit JWT secret
            algorithms=[config.jwt.ALGORITHM or "HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False,  # Disable iat validation due to time sync issues
                "verify_aud": False,
                "verify_iss": False,
            },
            # Add 300 seconds (5 minutes) clock skew tolerance for iat validation
            leeway=300,
        )
        
        user_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
        exp = payload.get('exp')
        
        # Check if token is close to expiry (within 5 minutes)
        if exp:
            import time
            current_time = time.time()
            time_until_expiry = exp - current_time
            if time_until_expiry <= 300:  # 5 minutes
                log_auth_middleware("JWT_VALIDATION", user_id, f"JWT expires soon in {time_until_expiry:.0f} seconds")
            else:
                log_auth_middleware("JWT_VALIDATION", user_id, f"JWT decoded successfully, exp: {exp}")
        else:
            log_auth_middleware("JWT_VALIDATION", user_id, "JWT decoded successfully, no expiry")
            
        return payload
    except jwt.ExpiredSignatureError as e:
        log_auth_middleware("JWT_VALIDATION", additional_info=f"JWT expired: {str(e)}", success=False)
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        # Add more detailed error information for debugging
        import time
        current_time = time.time()
        log_auth_middleware("JWT_VALIDATION", additional_info=f"JWT validation failed: {str(e)}", success=False)
        log_auth_middleware("JWT_VALIDATION", additional_info=f"Current server time: {current_time} ({datetime.fromtimestamp(current_time, tz=timezone.utc)})", success=False)
        
        # Try to decode without verification to get token info for debugging
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            iat = unverified_payload.get('iat')
            exp = unverified_payload.get('exp')
            if iat:
                log_auth_middleware("JWT_VALIDATION", additional_info=f"Token iat: {iat} ({datetime.fromtimestamp(iat, tz=timezone.utc)})", success=False)
            if exp:
                log_auth_middleware("JWT_VALIDATION", additional_info=f"Token exp: {exp} ({datetime.fromtimestamp(exp, tz=timezone.utc)})", success=False)
        except:
            pass  # Ignore errors in debugging
        
        raise HTTPException(status_code=401, detail="Invalid token")


def get_user_id(payload: dict = Depends(auth_middleware)) -> str:
    user_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
    if not user_id:
        log_auth_middleware("EXTRACT_USER_ID", additional_info="User ID not found in token payload", success=False)
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    log_auth_middleware("EXTRACT_USER_ID", str(user_id), f"User ID extracted from token: {user_id}")
    return str(user_id)


