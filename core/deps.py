from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
import jwt

from core.config import config
from core.security import security  

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extract and validate JWT token from Authorization header
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            config.jwt.SECRET, 
            algorithms=[config.jwt.ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False,  # Disable iat validation due to time sync issues
                "verify_aud": False, 
                "verify_iss": False   
            },
            # Add 300 seconds (5 minutes) clock skew tolerance for iat validation
            leeway=300,
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user_id(payload: dict = Depends(get_current_user)) -> str:
    """
    Extract the current user's id from the validated JWT payload.
    Tries common claim names in order: 'sub', 'id', 'user_id'.
    """
    user_id = (
        payload.get("sub")
        or payload.get("id")
        or payload.get("user_id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    return str(user_id)