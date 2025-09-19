"""Chat service for managing conversations and sessions."""

import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..utils.openai_client import openai_client
from ..utils.supabase_client import supabase_client
from ..config.settings import settings
from ..models.schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse,
    AgentRole
)

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and messages."""
    
    def __init__(self):
        """Initialize Chat Service."""
        self.max_sessions_per_user = settings.max_sessions_per_user
        self.session_timeout = settings.session_timeout
    
    async def create_chat_session(
        self,
        user_id: str,
        session_data: SessionCreate
    ) -> SessionResponse:
        """Create a new chat session."""
        try:
            # Generate title if not provided
            title = session_data.title or self._generate_session_title(session_data.agent_type)
            
            # Check user session limit
            existing_sessions = await supabase_client.get_user_chat_sessions(
                user_id, session_data.agent_type.value
            )
            
            if len(existing_sessions) >= self.max_sessions_per_user:
                # Delete oldest session
                oldest_session = min(existing_sessions, key=lambda x: x["created_at"])
                await self.delete_chat_session(oldest_session["id"], user_id)
            
            # Create session in database
            db_session = await supabase_client.create_chat_session(
                user_id=user_id,
                title=title,
                agent_type=session_data.agent_type.value,
                agent_id=session_data.agent_id,
                metadata=session_data.metadata or {}
            )
            
            logger.info(f"Created chat session: {db_session['id']}")
            
            return SessionResponse(
                id=db_session["id"],
                title=db_session["title"],
                agent_type=AgentRole(db_session["agent_type"]),
                agent_id=db_session.get("agent_id"),
                user_id=db_session["user_id"],
                message_count=0,
                last_message_at=None,
                created_at=datetime.fromisoformat(db_session["created_at"]),
                metadata=db_session.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise
    
    async def update_chat_session(
        self,
        session_id: str,
        user_id: str,
        update_data: SessionUpdate
    ) -> SessionResponse:
        """Update a chat session."""
        try:
            updates = {}
            
            if update_data.title is not None:
                updates["title"] = update_data.title
            if update_data.metadata is not None:
                updates["metadata"] = update_data.metadata
            
            updated_session = await supabase_client.update_chat_session(
                session_id, user_id, updates
            )
            
            logger.info(f"Updated chat session: {session_id}")
            
            # Get message count
            messages = await supabase_client.get_session_messages(session_id, user_id, limit=1)
            message_count = len(messages)
            last_message_at = None
            
            if messages:
                last_message_at = datetime.fromisoformat(messages[0]["created_at"])
            
            return SessionResponse(
                id=updated_session["id"],
                title=updated_session["title"],
                agent_type=AgentRole(updated_session["agent_type"]),
                agent_id=updated_session.get("agent_id"),
                user_id=updated_session["user_id"],
                message_count=message_count,
                last_message_at=last_message_at,
                created_at=datetime.fromisoformat(updated_session["created_at"]),
                updated_at=datetime.fromisoformat(updated_session["updated_at"]) if updated_session.get("updated_at") else None,
                metadata=updated_session.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error updating chat session {session_id}: {str(e)}")
            raise
    
    async def delete_chat_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """Delete a chat session and all associated messages."""
        try:
            # Delete from database (messages will be deleted via cascade)
            await supabase_client.delete_chat_session(session_id, user_id)
            
            logger.info(f"Deleted chat session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {str(e)}")
            raise
    
    async def get_user_chat_sessions(
        self,
        user_id: str,
        agent_type: AgentRole = None,
        limit: int = 50
    ) -> List[SessionResponse]:
        """Get user's chat sessions."""
        try:
            sessions = await supabase_client.get_user_chat_sessions(
                user_id, agent_type.value if agent_type else None, limit
            )
            
            result = []
            for session in sessions:
                # Get message count for each session
                messages = await supabase_client.get_session_messages(
                    session["id"], user_id, limit=1
                )
                message_count = len(messages)
                last_message_at = None
                
                if messages:
                    last_message_at = datetime.fromisoformat(messages[0]["created_at"])
                
                result.append(SessionResponse(
                    id=session["id"],
                    title=session["title"],
                    agent_type=AgentRole(session["agent_type"]),
                    agent_id=session.get("agent_id"),
                    user_id=session["user_id"],
                    message_count=message_count,
                    last_message_at=last_message_at,
                    created_at=datetime.fromisoformat(session["created_at"]),
                    updated_at=datetime.fromisoformat(session["updated_at"]) if session.get("updated_at") else None,
                    metadata=session.get("metadata", {})
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user chat sessions: {str(e)}")
            raise
    
    async def create_message(
        self,
        user_id: str,
        message_data: MessageCreate
    ) -> MessageResponse:
        """Create a new message in a session."""
        try:
            # Create message in database
            db_message = await supabase_client.create_message(
                session_id=message_data.session_id,
                user_id=user_id,
                content=message_data.content,
                role=message_data.role.value,
                metadata=message_data.metadata or {}
            )
            
            logger.info(f"Created message: {db_message['id']}")
            
            return MessageResponse(
                id=db_message["id"],
                content=db_message["content"],
                role=message_data.role,
                session_id=db_message["session_id"],
                user_id=db_message["user_id"],
                created_at=datetime.fromisoformat(db_message["created_at"]),
                metadata=db_message.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageResponse]:
        """Get messages for a session."""
        try:
            messages = await supabase_client.get_session_messages(
                session_id, user_id, limit, offset
            )
            
            result = []
            for message in messages:
                result.append(MessageResponse(
                    id=message["id"],
                    content=message["content"],
                    role=message["role"],
                    session_id=message["session_id"],
                    user_id=message["user_id"],
                    created_at=datetime.fromisoformat(message["created_at"]),
                    metadata=message.get("metadata", {})
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            raise
    
    async def chat_with_super_admin(
        self,
        user_id: str,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """Handle chat with Super Admin Agent."""
        try:
            from ..services.super_admin_agent import super_admin_agent
            
            # Get or create session
            session_id = chat_request.session_id
            if not session_id:
                session_data = SessionCreate(
                    title="Super Admin Chat",
                    agent_type=AgentRole.SUPER_ADMIN,
                    metadata=chat_request.metadata or {}
                )
                session = await self.create_chat_session(user_id, session_data)
                session_id = session.id
            
            # Store user message
            user_message_data = MessageCreate(
                content=chat_request.message,
                role="user",
                session_id=session_id,
                metadata=chat_request.metadata
            )
            user_message = await self.create_message(user_id, user_message_data)
            
            # Get OpenAI thread ID from session metadata
            thread_id = None
            if session_id:
                sessions = await supabase_client.get_user_chat_sessions(user_id)
                for s in sessions:
                    if s["id"] == session_id:
                        thread_id = s.get("metadata", {}).get("thread_id")
                        break
            
            # Process with Super Admin Agent
            response_content, response_metadata = await super_admin_agent.process_chat_message(
                message=chat_request.message,
                user_id=user_id,
                thread_id=thread_id,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                metadata=chat_request.metadata
            )
            
            # Store thread ID in session metadata if new
            if not thread_id and response_metadata.get("thread_id"):
                await supabase_client.update_chat_session(
                    session_id,
                    user_id,
                    {
                        "metadata": {
                            **(chat_request.metadata or {}),
                            "thread_id": response_metadata["thread_id"]
                        }
                    }
                )
            
            # Store assistant message
            assistant_message_data = MessageCreate(
                content=response_content,
                role="assistant",
                session_id=session_id,
                metadata={
                    "usage": response_metadata.get("usage"),
                    "run_id": response_metadata.get("run_id"),
                    "function_calls": response_metadata.get("function_calls")
                }
            )
            assistant_message = await self.create_message(user_id, assistant_message_data)
            
            return ChatResponse(
                message=assistant_message,
                session_id=session_id,
                usage=response_metadata.get("usage")
            )
            
        except Exception as e:
            logger.error(f"Error in super admin chat: {str(e)}")
            raise
    
    async def chat_with_course_assistant(
        self,
        user_id: str,
        assistant_id: str,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """Handle chat with Course Assistant."""
        try:
            from ..services.course_agent import course_agent_service
            
            # Get or create session
            session_id = chat_request.session_id
            if not session_id:
                session_data = SessionCreate(
                    title="Course Assistant Chat",
                    agent_type=AgentRole.COURSE_INSTRUCTOR,
                    agent_id=assistant_id,
                    metadata=chat_request.metadata or {}
                )
                session = await self.create_chat_session(user_id, session_data)
                session_id = session.id
            
            # Store user message
            user_message_data = MessageCreate(
                content=chat_request.message,
                role="user",
                session_id=session_id,
                metadata=chat_request.metadata
            )
            user_message = await self.create_message(user_id, user_message_data)
            
            # Get OpenAI thread ID from session metadata
            thread_id = None
            if session_id:
                sessions = await supabase_client.get_user_chat_sessions(user_id)
                for s in sessions:
                    if s["id"] == session_id:
                        thread_id = s.get("metadata", {}).get("thread_id")
                        break
            
            # Process with Course Assistant
            response_content, response_metadata = await course_agent_service.chat_with_course_assistant(
                assistant_id=assistant_id,
                message=chat_request.message,
                user_id=user_id,
                thread_id=thread_id,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                metadata=chat_request.metadata
            )
            
            # Store thread ID in session metadata if new
            if not thread_id and response_metadata.get("thread_id"):
                await supabase_client.update_chat_session(
                    session_id,
                    user_id,
                    {
                        "metadata": {
                            **(chat_request.metadata or {}),
                            "thread_id": response_metadata["thread_id"]
                        }
                    }
                )
            
            # Store assistant message
            assistant_message_data = MessageCreate(
                content=response_content,
                role="assistant",
                session_id=session_id,
                metadata={
                    "usage": response_metadata.get("usage"),
                    "run_id": response_metadata.get("run_id"),
                    "assistant_id": assistant_id
                }
            )
            assistant_message = await self.create_message(user_id, assistant_message_data)
            
            return ChatResponse(
                message=assistant_message,
                session_id=session_id,
                usage=response_metadata.get("usage")
            )
            
        except Exception as e:
            logger.error(f"Error in course assistant chat: {str(e)}")
            raise
    
    async def export_conversation(
        self,
        session_id: str,
        user_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export conversation history."""
        try:
            # Get session details
            sessions = await supabase_client.get_user_chat_sessions(user_id)
            session = None
            for s in sessions:
                if s["id"] == session_id:
                    session = s
                    break
            
            if not session:
                raise Exception("Session not found")
            
            # Get all messages
            messages = await supabase_client.get_session_messages(
                session_id, user_id, limit=1000
            )
            
            export_data = {
                "session": {
                    "id": session["id"],
                    "title": session["title"],
                    "agent_type": session["agent_type"],
                    "agent_id": session.get("agent_id"),
                    "created_at": session["created_at"],
                    "metadata": session.get("metadata", {})
                },
                "messages": [
                    {
                        "id": msg["id"],
                        "role": msg["role"],
                        "content": msg["content"],
                        "created_at": msg["created_at"],
                        "metadata": msg.get("metadata", {})
                    }
                    for msg in messages
                ],
                "exported_at": datetime.utcnow().isoformat(),
                "format": format
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting conversation {session_id}: {str(e)}")
            raise
    
    def _generate_session_title(self, agent_type: AgentRole) -> str:
        """Generate a default session title."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
        if agent_type == AgentRole.SUPER_ADMIN:
            return f"Super Admin Session - {timestamp}"
        elif agent_type == AgentRole.COURSE_INSTRUCTOR:
            return f"Course Chat - {timestamp}"
        else:
            return f"Chat Session - {timestamp}"
    
    async def get_session_summary(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get a summary of a chat session."""
        try:
            # Get session and messages
            sessions = await supabase_client.get_user_chat_sessions(user_id)
            session = None
            for s in sessions:
                if s["id"] == session_id:
                    session = s
                    break
            
            if not session:
                raise Exception("Session not found")
            
            messages = await supabase_client.get_session_messages(
                session_id, user_id, limit=100
            )
            
            # Calculate statistics
            user_message_count = len([m for m in messages if m["role"] == "user"])
            assistant_message_count = len([m for m in messages if m["role"] == "assistant"])
            total_characters = sum(len(m["content"]) for m in messages)
            
            # Get first and last message timestamps
            first_message = messages[0] if messages else None
            last_message = messages[-1] if messages else None
            
            duration = None
            if first_message and last_message:
                start_time = datetime.fromisoformat(first_message["created_at"])
                end_time = datetime.fromisoformat(last_message["created_at"])
                duration = (end_time - start_time).total_seconds()
            
            return {
                "session_id": session_id,
                "title": session["title"],
                "agent_type": session["agent_type"],
                "total_messages": len(messages),
                "user_messages": user_message_count,
                "assistant_messages": assistant_message_count,
                "total_characters": total_characters,
                "duration_seconds": duration,
                "created_at": session["created_at"],
                "first_message_at": first_message["created_at"] if first_message else None,
                "last_message_at": last_message["created_at"] if last_message else None
            }
            
        except Exception as e:
            logger.error(f"Error getting session summary {session_id}: {str(e)}")
            raise


# Global instance
chat_service = ChatService()
