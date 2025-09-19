"""Course Assistant API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..models.schemas import (
    CourseAssistantCreate,
    CourseAssistantUpdate,
    CourseAssistantResponse,
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    ErrorResponse
)
from ..utils.auth import require_super_admin, get_current_user
from ..services.course_agent import course_agent_service
from ..services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/course-assistants", tags=["Course Assistants"])


@router.post("", response_model=CourseAssistantResponse, status_code=status.HTTP_201_CREATED)
async def create_course_assistant(
    assistant_data: CourseAssistantCreate,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> CourseAssistantResponse:
    """
    Create a new course assistant.
    
    Only Super Admins can create course assistants. The assistant will be
    specialized for the specified subject with custom role instructions.
    """
    try:
        user_id = current_user["user_id"]
        
        assistant = await course_agent_service.create_course_assistant(
            assistant_data=assistant_data,
            user_id=user_id
        )
        
        return assistant
        
    except Exception as e:
        logger.error(f"Error creating course assistant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course assistant: {str(e)}"
        )


@router.get("", response_model=List[CourseAssistantResponse])
async def list_course_assistants(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of assistants to return"),
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> List[CourseAssistantResponse]:
    """Get list of course assistants created by the current user."""
    try:
        user_id = current_user["user_id"]
        
        assistants = await course_agent_service.list_user_course_assistants(
            user_id=user_id,
            is_active=is_active,
            limit=limit
        )
        
        return assistants
        
    except Exception as e:
        logger.error(f"Error listing course assistants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve course assistants: {str(e)}"
        )


@router.get("/{assistant_id}", response_model=CourseAssistantResponse)
async def get_course_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> CourseAssistantResponse:
    """Get details of a specific course assistant."""
    try:
        user_id = current_user["user_id"]
        
        assistant = await course_agent_service.get_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id
        )
        
        return assistant
        
    except Exception as e:
        logger.error(f"Error getting course assistant {assistant_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve course assistant: {str(e)}"
        )


@router.put("/{assistant_id}", response_model=CourseAssistantResponse)
async def update_course_assistant(
    assistant_id: str,
    update_data: CourseAssistantUpdate,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> CourseAssistantResponse:
    """Update an existing course assistant."""
    try:
        user_id = current_user["user_id"]
        
        assistant = await course_agent_service.update_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id,
            update_data=update_data
        )
        
        return assistant
        
    except Exception as e:
        logger.error(f"Error updating course assistant {assistant_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course assistant: {str(e)}"
        )


@router.delete("/{assistant_id}")
async def delete_course_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> JSONResponse:
    """Delete a course assistant."""
    try:
        user_id = current_user["user_id"]
        
        success = await course_agent_service.delete_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id
        )
        
        if success:
            return JSONResponse(
                content={"message": "Course assistant deleted successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course assistant {assistant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course assistant: {str(e)}"
        )


@router.post("/{assistant_id}/chat", response_model=ChatResponse)
async def chat_with_course_assistant(
    assistant_id: str,
    chat_request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    Chat with a specific course assistant.
    
    This endpoint allows users to interact with course assistants.
    The assistant will use uploaded course materials as knowledge base.
    """
    try:
        user_id = current_user["user_id"]
        
        response = await chat_service.chat_with_course_assistant(
            user_id=user_id,
            assistant_id=assistant_id,
            chat_request=chat_request
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error chatting with course assistant {assistant_id}: {str(e)}")
        if "not found" in str(e).lower() or "not active" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found or not active"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/{assistant_id}/sessions", response_model=List[SessionResponse])
async def get_course_assistant_sessions(
    assistant_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[SessionResponse]:
    """Get chat sessions for a specific course assistant."""
    try:
        user_id = current_user["user_id"]
        
        sessions = await chat_service.get_user_chat_sessions(
            user_id=user_id,
            agent_type="course_instructor",
            limit=limit
        )
        
        # Filter sessions for this specific assistant
        assistant_sessions = [
            session for session in sessions 
            if session.agent_id == assistant_id
        ]
        
        return assistant_sessions
        
    except Exception as e:
        logger.error(f"Error getting course assistant sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.post("/{assistant_id}/sessions", response_model=SessionResponse)
async def create_course_assistant_session(
    assistant_id: str,
    session_data: SessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SessionResponse:
    """Create a new chat session with a course assistant."""
    try:
        user_id = current_user["user_id"]
        
        # Verify assistant exists and is accessible
        await course_agent_service.get_course_assistant(assistant_id)
        
        # Force correct agent type and ID
        session_data.agent_type = "course_instructor"
        session_data.agent_id = assistant_id
        
        session = await chat_service.create_chat_session(
            user_id=user_id,
            session_data=session_data
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating course assistant session: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{assistant_id}/statistics")
async def get_course_assistant_statistics(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Get usage statistics for a course assistant."""
    try:
        user_id = current_user["user_id"]
        
        stats = await course_agent_service.get_assistant_statistics(
            assistant_id=assistant_id,
            user_id=user_id
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting course assistant statistics: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/{assistant_id}/activate")
async def activate_course_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> JSONResponse:
    """Activate a course assistant."""
    try:
        user_id = current_user["user_id"]
        
        update_data = CourseAssistantUpdate(is_active=True)
        await course_agent_service.update_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id,
            update_data=update_data
        )
        
        return JSONResponse(
            content={"message": "Course assistant activated successfully"},
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error activating course assistant {assistant_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate course assistant: {str(e)}"
        )


@router.post("/{assistant_id}/deactivate")
async def deactivate_course_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> JSONResponse:
    """Deactivate a course assistant."""
    try:
        user_id = current_user["user_id"]
        
        update_data = CourseAssistantUpdate(is_active=False)
        await course_agent_service.update_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id,
            update_data=update_data
        )
        
        return JSONResponse(
            content={"message": "Course assistant deactivated successfully"},
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error deactivating course assistant {assistant_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate course assistant: {str(e)}"
        )


@router.get("/{assistant_id}/capabilities")
async def get_course_assistant_capabilities(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get capabilities and information about a specific course assistant."""
    try:
        user_id = current_user["user_id"]
        
        assistant = await course_agent_service.get_course_assistant(
            assistant_id=assistant_id,
            user_id=user_id
        )
        
        return {
            "assistant_id": assistant.id,
            "name": assistant.name,
            "subject": assistant.subject,
            "description": assistant.description,
            "capabilities": {
                "subject_expertise": f"Specialized knowledge in {assistant.subject}",
                "document_analysis": "Can analyze and reference uploaded course materials",
                "interactive_teaching": "Provides explanations, examples, and practice problems",
                "personalized_learning": "Adapts to student's level and learning pace",
                "assessment_support": "Can create quizzes and evaluate student responses"
            },
            "role_instructions": assistant.role_instructions,
            "constraints": assistant.constraints,
            "is_active": assistant.is_active,
            "file_count": assistant.file_count,
            "usage_instructions": {
                "chat": "Ask questions about the subject matter or upload materials for analysis",
                "file_upload": "Upload PDFs, documents, presentations, or images for the assistant to reference",
                "examples": [
                    f"Explain the key concepts in {assistant.subject}",
                    "Help me understand this problem",
                    "Create a practice quiz on this topic",
                    "Summarize the uploaded document"
                ]
            },
            "limitations": [
                "Knowledge is limited to uploaded materials and training data",
                "Cannot browse the internet for real-time information",
                "Cannot directly grade assignments or access external systems"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting course assistant capabilities: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course assistant not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )
