from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.auth_middleware import get_user_id
from core.supabase import get_supabase_admin


def log_profile_operation(operation: str, user_id: str, additional_info: str = "", data: dict | None = None):
    print(f"👤 PROFILE {operation.upper()}: user_id={user_id}")
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    if data is not None:
        print(f"   📋 Data: {data}")
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO date string
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    profile_completion_percentage: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_user_id)):
    """Get current user's profile"""
    log_profile_operation("GET_PROFILE", user_id, "Fetching user profile")

    supabase = get_supabase_admin()

    try:
        # Get profile from profiles table
        response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()

        if not response.data:
            log_profile_operation("GET_PROFILE", user_id, "Profile not found, creating new profile")
            now_iso = datetime.now(timezone.utc).isoformat()
            new_profile = {
                "id": user_id,
                "profile_completion_percentage": 0,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            create_response = supabase.table("profiles").insert(new_profile).execute()
            profile_data = create_response.data[0] if create_response.data else new_profile
        else:
            profile_data = response.data
            log_profile_operation("GET_PROFILE", user_id, "Profile found successfully")

        # Skip attaching email to avoid cross-schema errors in some environments

        return ProfileResponse(**profile_data)

    except Exception as e:
        log_profile_operation("GET_PROFILE", user_id, f"Error fetching profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdateRequest,
    user_id: str = Depends(get_user_id)
):
    log_profile_operation("UPDATE_PROFILE", user_id, "Updating user profile", profile_update.dict())

    supabase = get_supabase_admin()

    try:
        # Prepare update data, excluding None values
        update_data = {k: v for k, v in profile_update.dict().items() if v is not None}

        if not update_data:
            log_profile_operation("UPDATE_PROFILE", user_id, "No fields to update")
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Get current profile to calculate completion
        current_profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()

        if current_profile.data:
            merged_data = {**current_profile.data, **update_data}
        else:
            merged_data = {
                "id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **update_data
            }

        # Calculate completion percentage
        # Business rule: if phone is provided, consider profile 100% complete
        if merged_data.get('phone'):
            update_data["profile_completion_percentage"] = 100
        else:
            completion_fields = [
                'phone', 'address', 'city', 'state', 'country', 'postal_code',
                'date_of_birth', 'bio', 'avatar_url', 'website', 'linkedin_url',
                'twitter_url', 'github_url'
            ]
            completed_fields = sum(1 for field in completion_fields if merged_data.get(field))
            completion_percentage = int((completed_fields / len(completion_fields)) * 100)
            update_data["profile_completion_percentage"] = completion_percentage

        # Upsert profile
        upsert_data = {"id": user_id, **update_data}
        supabase.table("profiles").upsert(upsert_data, on_conflict="id").execute()

        # Return updated profile
        refreshed = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        profile_data = refreshed.data or upsert_data

        # Skip attaching email to avoid cross-schema errors in some environments

        log_profile_operation("UPDATE_PROFILE", user_id, "Profile updated successfully")
        return ProfileResponse(**profile_data)

    except HTTPException:
        raise
    except Exception as e:
        log_profile_operation("UPDATE_PROFILE", user_id, f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Removed duplicate legacy definitions that queried auth.users directly
