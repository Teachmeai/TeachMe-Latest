"""Supabase client wrapper for database operations."""

import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from datetime import datetime

from ..config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseClientWrapper:
    """Wrapper for Supabase client with agent-specific functionality."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    # Chat Sessions Management
    async def create_chat_session(
        self,
        user_id: str,
        title: str,
        agent_type: str,
        agent_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new chat session."""
        try:
            session_data = {
                "user_id": user_id,
                "title": title,
                "agent_type": agent_type,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            if agent_id:
                session_data["agent_id"] = agent_id
            
            result = self.client.table("agent_chat_sessions").insert(session_data).execute()
            
            if result.data:
                logger.info(f"Created chat session: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create chat session")
                
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise
    
    async def get_user_chat_sessions(
        self,
        user_id: str,
        agent_type: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's chat sessions."""
        try:
            query = self.client.table("agent_chat_sessions").select("*").eq("user_id", user_id)
            
            if agent_type:
                query = query.eq("agent_type", agent_type)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user chat sessions: {str(e)}")
            raise
    
    async def update_chat_session(
        self,
        session_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a chat session."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("agent_chat_sessions").update(updates).eq("id", session_id).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Updated chat session: {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update chat session")
                
        except Exception as e:
            logger.error(f"Error updating chat session {session_id}: {str(e)}")
            raise
    
    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        try:
            result = self.client.table("agent_chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
            
            logger.info(f"Deleted chat session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {str(e)}")
            raise
    
    # Messages Management
    async def create_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        role: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new message."""
        try:
            message_data = {
                "session_id": session_id,
                "user_id": user_id,
                "content": content,
                "role": role,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("agent_messages").insert(message_data).execute()
            
            if result.data:
                logger.info(f"Created message: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create message")
                
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a session."""
        try:
            result = self.client.table("agent_messages").select("*").eq("session_id", session_id).eq("user_id", user_id).order("created_at", desc=False).range(offset, offset + limit - 1).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            raise
    
    # Course Assistants Management
    async def create_course_assistant(
        self,
        user_id: str,
        name: str,
        subject: str,
        description: str,
        role_instructions: str,
        constraints: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        openai_assistant_id: str,
        vector_store_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new course assistant."""
        try:
            assistant_data = {
                "created_by": user_id,
                "name": name,
                "subject": subject,
                "description": description,
                "role_instructions": role_instructions,
                "constraints": constraints,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "openai_assistant_id": openai_assistant_id,
                "vector_store_id": vector_store_id,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("course_assistants").insert(assistant_data).execute()
            
            if result.data:
                logger.info(f"Created course assistant: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create course assistant")
                
        except Exception as e:
            logger.error(f"Error creating course assistant: {str(e)}")
            raise
    
    async def get_user_course_assistants(
        self,
        user_id: str,
        is_active: bool = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's course assistants."""
        try:
            query = self.client.table("course_assistants").select("*").eq("created_by", user_id)
            
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user course assistants: {str(e)}")
            raise
    
    async def get_course_assistant(
        self,
        assistant_id: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Get a course assistant by ID."""
        try:
            query = self.client.table("course_assistants").select("*").eq("id", assistant_id)
            
            if user_id:
                query = query.eq("created_by", user_id)
            
            result = query.execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Course assistant not found")
                
        except Exception as e:
            logger.error(f"Error getting course assistant {assistant_id}: {str(e)}")
            raise
    
    async def update_course_assistant(
        self,
        assistant_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a course assistant."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("course_assistants").update(updates).eq("id", assistant_id).eq("created_by", user_id).execute()
            
            if result.data:
                logger.info(f"Updated course assistant: {assistant_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update course assistant")
                
        except Exception as e:
            logger.error(f"Error updating course assistant {assistant_id}: {str(e)}")
            raise
    
    async def delete_course_assistant(
        self,
        assistant_id: str,
        user_id: str
    ) -> bool:
        """Delete a course assistant."""
        try:
            result = self.client.table("course_assistants").delete().eq("id", assistant_id).eq("created_by", user_id).execute()
            
            logger.info(f"Deleted course assistant: {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting course assistant {assistant_id}: {str(e)}")
            raise
    
    # Files Management
    async def create_file_record(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        upload_path: str,
        openai_file_id: str = None,
        assistant_id: str = None,
        vector_store_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a file record."""
        try:
            file_data = {
                "uploaded_by": user_id,
                "filename": filename,
                "original_filename": original_filename,
                "file_type": file_type,
                "file_size": file_size,
                "upload_path": upload_path,
                "openai_file_id": openai_file_id,
                "assistant_id": assistant_id,
                "vector_store_id": vector_store_id,
                "processing_status": "pending",
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("agent_files").insert(file_data).execute()
            
            if result.data:
                logger.info(f"Created file record: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create file record")
                
        except Exception as e:
            logger.error(f"Error creating file record: {str(e)}")
            raise
    
    async def update_file_record(
        self,
        file_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a file record."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("agent_files").update(updates).eq("id", file_id).execute()
            
            if result.data:
                logger.info(f"Updated file record: {file_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update file record")
                
        except Exception as e:
            logger.error(f"Error updating file record {file_id}: {str(e)}")
            raise
    
    async def get_user_files(
        self,
        user_id: str,
        assistant_id: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's files."""
        try:
            query = self.client.table("agent_files").select("*").eq("uploaded_by", user_id)
            
            if assistant_id:
                query = query.eq("assistant_id", assistant_id)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user files: {str(e)}")
            raise
    
    async def delete_file_record(self, file_id: str, user_id: str) -> bool:
        """Delete a file record."""
        try:
            result = self.client.table("agent_files").delete().eq("id", file_id).eq("uploaded_by", user_id).execute()
            
            logger.info(f"Deleted file record: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file record {file_id}: {str(e)}")
            raise
    
    # Platform Stats
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        try:
            # Get user count from profiles table
            users_result = self.client.table("profiles").select("id", count="exact").execute()
            total_users = users_result.count or 0
            
            # Get organizations count
            orgs_result = self.client.table("organizations").select("id", count="exact").execute()
            total_institutions = orgs_result.count or 0
            
            # Get course assistants count
            assistants_result = self.client.table("course_assistants").select("id", count="exact").execute()
            total_course_assistants = assistants_result.count or 0
            
            # Get chat sessions count
            sessions_result = self.client.table("agent_chat_sessions").select("id", count="exact").execute()
            total_chat_sessions = sessions_result.count or 0
            
            # Get messages count
            messages_result = self.client.table("agent_messages").select("id", count="exact").execute()
            total_messages = messages_result.count or 0
            
            # Get files count and storage
            files_result = self.client.table("agent_files").select("id,file_size", count="exact").execute()
            files_uploaded = files_result.count or 0
            storage_used_mb = sum(f.get("file_size", 0) for f in (files_result.data or [])) / (1024 * 1024)
            
            # Get active sessions in last 24 hours
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            active_sessions_result = self.client.table("agent_chat_sessions").select("id", count="exact").gte("created_at", yesterday.isoformat()).execute()
            active_sessions_24h = active_sessions_result.count or 0
            
            return {
                "total_users": total_users,
                "total_institutions": total_institutions,
                "total_courses": 0,  # Placeholder - could be derived from assistants
                "total_course_assistants": total_course_assistants,
                "total_chat_sessions": total_chat_sessions,
                "total_messages": total_messages,
                "active_sessions_24h": active_sessions_24h,
                "files_uploaded": files_uploaded,
                "storage_used_mb": round(storage_used_mb, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting platform stats: {str(e)}")
            raise
    
    # User Authentication
    async def verify_user_exists(self, user_id: str) -> bool:
        """Verify if user exists in the system."""
        try:
            result = self.client.table("profiles").select("id").eq("id", user_id).execute()
            return len(result.data or []) > 0
            
        except Exception as e:
            logger.error(f"Error verifying user {user_id}: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        try:
            result = self.client.table("profiles").select("*").eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {str(e)}")
            return None
    
    async def check_super_admin_role(self, user_id: str) -> bool:
        """Check if user has super admin role."""
        try:
            # Check global roles
            global_result = self.client.table("user_roles").select("role").eq("user_id", user_id).eq("role", "super_admin").execute()
            
            if global_result.data:
                return True
            
            # Check organization roles
            org_result = self.client.table("organization_memberships").select("role").eq("user_id", user_id).eq("role", "organization_admin").execute()
            
            return len(org_result.data or []) > 0
            
        except Exception as e:
            logger.error(f"Error checking super admin role for user {user_id}: {str(e)}")
            return False


# Global client instance
supabase_client = SupabaseClientWrapper()
