"""Course Agent service for managing specialized course assistants."""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..utils.openai_client import openai_client
from ..utils.supabase_client import supabase_client
from ..config.settings import settings
from ..models.schemas import (
    CourseAssistantCreate,
    CourseAssistantUpdate,
    CourseAssistantResponse
)

logger = logging.getLogger(__name__)


class CourseAgentService:
    """Service for managing course-specific AI assistants."""
    
    def __init__(self):
        """Initialize Course Agent Service."""
        self.default_model = settings.text_model
        self.default_prompt = settings.default_course_assistant_prompt
    
    async def create_course_assistant(
        self,
        assistant_data: CourseAssistantCreate,
        user_id: str
    ) -> CourseAssistantResponse:
        """Create a new course assistant."""
        try:
            # Build comprehensive system prompt
            system_prompt = self._build_system_prompt(assistant_data)
            
            # Create vector store for this course
            vector_store = await openai_client.create_vector_store(
                name=f"{assistant_data.name} - Knowledge Base",
                metadata={
                    "course_name": assistant_data.name,
                    "subject": assistant_data.subject,
                    "created_by": user_id
                }
            )
            
            # Create OpenAI assistant
            openai_assistant = await openai_client.create_assistant(
                name=assistant_data.name,
                instructions=system_prompt,
                model=self.default_model,
                tools=[
                    {"type": "file_search"},
                    {"type": "code_interpreter"}
                ],
                vector_store_ids=[vector_store.id],
                metadata={
                    "type": "course_assistant",
                    "subject": assistant_data.subject,
                    "created_by": user_id,
                    "course_name": assistant_data.name
                }
            )
            
            # Store in database
            db_assistant = await supabase_client.create_course_assistant(
                user_id=user_id,
                name=assistant_data.name,
                subject=assistant_data.subject,
                description=assistant_data.description or "",
                role_instructions=assistant_data.role_instructions,
                constraints=assistant_data.constraints or "",
                system_prompt=system_prompt,
                temperature=assistant_data.temperature,
                max_tokens=assistant_data.max_tokens,
                openai_assistant_id=openai_assistant.id,
                vector_store_id=vector_store.id,
                metadata=assistant_data.metadata or {}
            )
            
            logger.info(f"Created course assistant: {db_assistant['id']}")
            
            return CourseAssistantResponse(
                id=db_assistant["id"],
                name=db_assistant["name"],
                subject=db_assistant["subject"],
                description=db_assistant["description"],
                role_instructions=db_assistant["role_instructions"],
                constraints=db_assistant["constraints"],
                system_prompt=db_assistant["system_prompt"],
                temperature=db_assistant["temperature"],
                max_tokens=db_assistant["max_tokens"],
                is_active=db_assistant.get("is_active", True),
                openai_assistant_id=db_assistant["openai_assistant_id"],
                vector_store_id=db_assistant["vector_store_id"],
                file_count=0,
                session_count=0,
                created_by=db_assistant["created_by"],
                created_at=datetime.fromisoformat(db_assistant["created_at"]),
                metadata=db_assistant.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error creating course assistant: {str(e)}")
            raise
    
    async def update_course_assistant(
        self,
        assistant_id: str,
        user_id: str,
        update_data: CourseAssistantUpdate
    ) -> CourseAssistantResponse:
        """Update an existing course assistant."""
        try:
            # Get existing assistant
            existing = await supabase_client.get_course_assistant(assistant_id, user_id)
            
            # Prepare updates
            updates = {}
            
            if update_data.name is not None:
                updates["name"] = update_data.name
            if update_data.subject is not None:
                updates["subject"] = update_data.subject
            if update_data.description is not None:
                updates["description"] = update_data.description
            if update_data.role_instructions is not None:
                updates["role_instructions"] = update_data.role_instructions
            if update_data.constraints is not None:
                updates["constraints"] = update_data.constraints
            if update_data.temperature is not None:
                updates["temperature"] = update_data.temperature
            if update_data.max_tokens is not None:
                updates["max_tokens"] = update_data.max_tokens
            if update_data.is_active is not None:
                updates["is_active"] = update_data.is_active
            if update_data.metadata is not None:
                updates["metadata"] = update_data.metadata
            
            # Update system prompt if instructions changed
            if any(key in updates for key in ["role_instructions", "constraints", "subject"]):
                # Build new system prompt
                assistant_data = CourseAssistantCreate(
                    name=updates.get("name", existing["name"]),
                    subject=updates.get("subject", existing["subject"]),
                    description=updates.get("description", existing["description"]),
                    role_instructions=updates.get("role_instructions", existing["role_instructions"]),
                    constraints=updates.get("constraints", existing["constraints"])
                )
                updates["system_prompt"] = self._build_system_prompt(assistant_data)
            
            # Update OpenAI assistant if relevant fields changed
            openai_updates = {}
            if "name" in updates:
                openai_updates["name"] = updates["name"]
            if "system_prompt" in updates:
                openai_updates["instructions"] = updates["system_prompt"]
            
            if openai_updates:
                await openai_client.update_assistant(
                    existing["openai_assistant_id"],
                    **openai_updates
                )
            
            # Update database record
            updated_assistant = await supabase_client.update_course_assistant(
                assistant_id, user_id, updates
            )
            
            logger.info(f"Updated course assistant: {assistant_id}")
            
            return CourseAssistantResponse(
                id=updated_assistant["id"],
                name=updated_assistant["name"],
                subject=updated_assistant["subject"],
                description=updated_assistant["description"],
                role_instructions=updated_assistant["role_instructions"],
                constraints=updated_assistant["constraints"],
                system_prompt=updated_assistant["system_prompt"],
                temperature=updated_assistant["temperature"],
                max_tokens=updated_assistant["max_tokens"],
                is_active=updated_assistant.get("is_active", True),
                openai_assistant_id=updated_assistant["openai_assistant_id"],
                vector_store_id=updated_assistant["vector_store_id"],
                file_count=updated_assistant.get("file_count", 0),
                session_count=updated_assistant.get("session_count", 0),
                created_by=updated_assistant["created_by"],
                created_at=datetime.fromisoformat(updated_assistant["created_at"]),
                updated_at=datetime.fromisoformat(updated_assistant["updated_at"]) if updated_assistant.get("updated_at") else None,
                metadata=updated_assistant.get("metadata", {})
            )
            
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
            # Get assistant details
            assistant = await supabase_client.get_course_assistant(assistant_id, user_id)
            
            # Delete from OpenAI
            if assistant.get("openai_assistant_id"):
                try:
                    await openai_client.delete_assistant(assistant["openai_assistant_id"])
                except Exception as e:
                    logger.warning(f"Failed to delete OpenAI assistant: {str(e)}")
            
            # Delete vector store if exists
            if assistant.get("vector_store_id"):
                try:
                    # Note: OpenAI doesn't provide direct vector store deletion in current API
                    # This would be handled through file management
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete vector store: {str(e)}")
            
            # Delete from database
            await supabase_client.delete_course_assistant(assistant_id, user_id)
            
            logger.info(f"Deleted course assistant: {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting course assistant {assistant_id}: {str(e)}")
            raise
    
    async def get_course_assistant(
        self,
        assistant_id: str,
        user_id: str = None
    ) -> CourseAssistantResponse:
        """Get a course assistant by ID."""
        try:
            assistant = await supabase_client.get_course_assistant(assistant_id, user_id)
            
            # Get file count if vector store exists
            file_count = 0
            session_count = 0
            
            # These would require additional queries to count related records
            # For now, using placeholder values
            
            return CourseAssistantResponse(
                id=assistant["id"],
                name=assistant["name"],
                subject=assistant["subject"],
                description=assistant["description"],
                role_instructions=assistant["role_instructions"],
                constraints=assistant["constraints"],
                system_prompt=assistant["system_prompt"],
                temperature=assistant["temperature"],
                max_tokens=assistant["max_tokens"],
                is_active=assistant.get("is_active", True),
                openai_assistant_id=assistant["openai_assistant_id"],
                vector_store_id=assistant["vector_store_id"],
                file_count=file_count,
                session_count=session_count,
                created_by=assistant["created_by"],
                created_at=datetime.fromisoformat(assistant["created_at"]),
                updated_at=datetime.fromisoformat(assistant["updated_at"]) if assistant.get("updated_at") else None,
                metadata=assistant.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error getting course assistant {assistant_id}: {str(e)}")
            raise
    
    async def list_user_course_assistants(
        self,
        user_id: str,
        is_active: bool = None,
        limit: int = 50
    ) -> List[CourseAssistantResponse]:
        """List user's course assistants."""
        try:
            assistants = await supabase_client.get_user_course_assistants(
                user_id, is_active, limit
            )
            
            result = []
            for assistant in assistants:
                result.append(CourseAssistantResponse(
                    id=assistant["id"],
                    name=assistant["name"],
                    subject=assistant["subject"],
                    description=assistant["description"],
                    role_instructions=assistant["role_instructions"],
                    constraints=assistant["constraints"],
                    system_prompt=assistant["system_prompt"],
                    temperature=assistant["temperature"],
                    max_tokens=assistant["max_tokens"],
                    is_active=assistant.get("is_active", True),
                    openai_assistant_id=assistant["openai_assistant_id"],
                    vector_store_id=assistant["vector_store_id"],
                    file_count=assistant.get("file_count", 0),
                    session_count=assistant.get("session_count", 0),
                    created_by=assistant["created_by"],
                    created_at=datetime.fromisoformat(assistant["created_at"]),
                    updated_at=datetime.fromisoformat(assistant["updated_at"]) if assistant.get("updated_at") else None,
                    metadata=assistant.get("metadata", {})
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing course assistants for user {user_id}: {str(e)}")
            raise
    
    async def chat_with_course_assistant(
        self,
        assistant_id: str,
        message: str,
        user_id: str,
        thread_id: str = None,
        temperature: float = None,
        max_tokens: int = None,
        file_ids: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Chat with a course assistant."""
        try:
            # Get assistant details
            assistant = await supabase_client.get_course_assistant(assistant_id)
            
            if not assistant.get("is_active", True):
                raise Exception("Course assistant is not active")
            
            openai_assistant_id = assistant["openai_assistant_id"]
            
            # Create or use existing thread
            if not thread_id:
                thread = await openai_client.create_thread(
                    metadata={
                        "user_id": user_id,
                        "assistant_id": assistant_id,
                        "agent_type": "course_assistant"
                    }
                )
                thread_id = thread.id
            
            # Add user message to thread
            await openai_client.add_message_to_thread(
                thread_id=thread_id,
                content=message,
                role="user",
                file_ids=file_ids or [],
                metadata=metadata or {}
            )
            
            # Run the assistant
            run = await openai_client.run_assistant(
                thread_id=thread_id,
                assistant_id=openai_assistant_id,
                temperature=temperature or assistant["temperature"],
                max_completion_tokens=max_tokens or assistant["max_tokens"],
                metadata={"user_id": user_id, "assistant_id": assistant_id}
            )
            
            # Wait for completion
            completed_run = await openai_client.wait_for_run_completion(
                thread_id, run.id, timeout=120
            )
            
            if completed_run.status != "completed":
                raise Exception(f"Run failed with status: {completed_run.status}")
            
            # Get the assistant's response
            messages = await openai_client.get_thread_messages(thread_id, limit=1)
            assistant_message = messages[0] if messages else None
            
            if assistant_message and assistant_message.role == "assistant":
                response_content = ""
                for content_block in assistant_message.content:
                    if content_block.type == "text":
                        response_content += content_block.text.value
                
                return response_content, {
                    "thread_id": thread_id,
                    "run_id": completed_run.id,
                    "usage": getattr(completed_run, "usage", None),
                    "assistant_id": assistant_id,
                    "model": assistant.get("model", self.default_model)
                }
            else:
                raise Exception("No assistant response received")
                
        except Exception as e:
            logger.error(f"Error chatting with course assistant {assistant_id}: {str(e)}")
            raise
    
    async def add_files_to_course_assistant(
        self,
        assistant_id: str,
        file_ids: List[str],
        user_id: str
    ) -> bool:
        """Add files to a course assistant's vector store."""
        try:
            # Get assistant details
            assistant = await supabase_client.get_course_assistant(assistant_id, user_id)
            vector_store_id = assistant.get("vector_store_id")
            
            if not vector_store_id:
                raise Exception("Course assistant has no vector store")
            
            # Add files to vector store
            await openai_client.add_files_to_vector_store(vector_store_id, file_ids)
            
            # Update file records to associate with this assistant
            for file_id in file_ids:
                await supabase_client.update_file_record(
                    file_id,
                    {
                        "assistant_id": assistant_id,
                        "vector_store_id": vector_store_id,
                        "processing_status": "processed"
                    }
                )
            
            logger.info(f"Added {len(file_ids)} files to course assistant {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding files to course assistant {assistant_id}: {str(e)}")
            raise
    
    def _build_system_prompt(self, assistant_data: CourseAssistantCreate) -> str:
        """Build comprehensive system prompt for course assistant."""
        prompt_parts = [
            f"You are a specialized AI instructor for {assistant_data.subject}.",
            f"\nCOURSE: {assistant_data.name}",
            f"\nDESCRIPTION: {assistant_data.description or 'No description provided'}",
            f"\nROLE INSTRUCTIONS:\n{assistant_data.role_instructions}"
        ]
        
        if assistant_data.constraints:
            prompt_parts.append(f"\nCONSTRAINTS:\n{assistant_data.constraints}")
        
        # Add metadata-based instructions
        metadata = assistant_data.metadata or {}
        if metadata.get("target_audience"):
            prompt_parts.append(f"\nTARGET AUDIENCE: {metadata['target_audience']}")
        
        if metadata.get("difficulty_level"):
            prompt_parts.append(f"\nDIFFICULTY LEVEL: {metadata['difficulty_level']}")
        
        # Add core teaching guidelines
        prompt_parts.extend([
            "\n" + "="*50,
            "CORE TEACHING GUIDELINES:",
            "• Use uploaded course materials as your primary knowledge base",
            "• Adapt explanations to student's level of understanding",
            "• Encourage active learning through questions and examples",
            "• Break down complex concepts into digestible steps",
            "• Provide practice problems and exercises when appropriate",
            "• Give constructive feedback on student responses",
            "• Be patient, encouraging, and supportive",
            "• Use real-world examples to illustrate concepts",
            "• Check for understanding before moving to new topics",
            "• Suggest additional resources when helpful",
            "",
            "RESPONSE FORMAT:",
            "• Structure responses clearly with headings when needed",
            "• Use bullet points for lists and key concepts",
            "• Include examples and practice opportunities",
            "• End with questions to check understanding",
            "",
            "If no course materials are uploaded, rely on your extensive knowledge while strictly following the role instructions and constraints provided above."
        ])
        
        return "\n".join(prompt_parts)
    
    async def get_assistant_statistics(self, assistant_id: str, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a course assistant."""
        try:
            assistant = await supabase_client.get_course_assistant(assistant_id, user_id)
            
            # Get session count
            sessions = await supabase_client.get_user_chat_sessions(
                user_id, agent_type="course_assistant"
            )
            session_count = len([s for s in sessions if s.get("agent_id") == assistant_id])
            
            # Get file count
            files = await supabase_client.get_user_files(user_id, assistant_id)
            file_count = len(files)
            
            # Calculate total file size
            total_file_size = sum(f.get("file_size", 0) for f in files)
            
            return {
                "assistant_id": assistant_id,
                "name": assistant["name"],
                "subject": assistant["subject"],
                "session_count": session_count,
                "file_count": file_count,
                "total_file_size_mb": round(total_file_size / (1024 * 1024), 2),
                "is_active": assistant.get("is_active", True),
                "created_at": assistant["created_at"],
                "last_updated": assistant.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting assistant statistics {assistant_id}: {str(e)}")
            raise


# Global instance
course_agent_service = CourseAgentService()
