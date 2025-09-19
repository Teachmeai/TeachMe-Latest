"""Super Admin Agent API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    PlatformStats,
    PlatformOperationRequest,
    PlatformOperationResponse,
    ErrorResponse
)
from ..utils.auth import require_super_admin, get_current_user
from ..services.super_admin_agent import super_admin_agent
from ..services.chat_service import chat_service
from ..utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/super-admin", tags=["Super Admin Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_super_admin(
    chat_request: ChatRequest,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> ChatResponse:
    """
    Chat with the Super Admin Agent.
    
    The Super Admin Agent can:
    - Create and manage course assistants
    - Answer questions about the platform
    - Perform platform operations via natural language
    - Provide platform statistics and insights
    """
    try:
        user_id = current_user["user_id"]
        
        response = await chat_service.chat_with_super_admin(
            user_id=user_id,
            chat_request=chat_request
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in super admin chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_super_admin_sessions(
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> List[SessionResponse]:
    """Get Super Admin chat sessions for the current user."""
    try:
        user_id = current_user["user_id"]
        
        sessions = await chat_service.get_user_chat_sessions(
            user_id=user_id,
            agent_type="super_admin",
            limit=limit
        )
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting super admin sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.post("/sessions", response_model=SessionResponse)
async def create_super_admin_session(
    session_data: SessionCreate,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> SessionResponse:
    """Create a new Super Admin chat session."""
    try:
        user_id = current_user["user_id"]
        
        # Force agent type to super_admin
        session_data.agent_type = "super_admin"
        
        session = await chat_service.create_chat_session(
            user_id=user_id,
            session_data=session_data
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating super admin session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_super_admin_session(
    session_id: str,
    update_data: SessionUpdate,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> SessionResponse:
    """Update a Super Admin chat session."""
    try:
        user_id = current_user["user_id"]
        
        session = await chat_service.update_chat_session(
            session_id=session_id,
            user_id=user_id,
            update_data=update_data
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error updating super admin session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_super_admin_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> JSONResponse:
    """Delete a Super Admin chat session."""
    try:
        user_id = current_user["user_id"]
        
        success = await chat_service.delete_chat_session(
            session_id=session_id,
            user_id=user_id
        )
        
        if success:
            return JSONResponse(
                content={"message": "Session deleted successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting super admin session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/sessions/{session_id}/export")
async def export_super_admin_session(
    session_id: str,
    format: str = Query("json", regex="^(json|csv|txt)$"),
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Export a Super Admin chat session."""
    try:
        user_id = current_user["user_id"]
        
        export_data = await chat_service.export_conversation(
            session_id=session_id,
            user_id=user_id,
            format=format
        )
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting super admin session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export session: {str(e)}"
        )


@router.get("/sessions/{session_id}/summary")
async def get_super_admin_session_summary(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Get summary of a Super Admin chat session."""
    try:
        user_id = current_user["user_id"]
        
        summary = await chat_service.get_session_summary(
            session_id=session_id,
            user_id=user_id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting super admin session summary {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session summary: {str(e)}"
        )


@router.get("/platform/stats", response_model=PlatformStats)
async def get_platform_statistics(
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> PlatformStats:
    """Get comprehensive platform statistics."""
    try:
        stats_data = await supabase_client.get_platform_stats()
        
        return PlatformStats(**stats_data)
        
    except Exception as e:
        logger.error(f"Error getting platform stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve platform statistics: {str(e)}"
        )


@router.get("/platform/analysis")
async def get_platform_analysis(
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Get detailed platform usage analysis."""
    try:
        analysis = await super_admin_agent.analyze_platform_usage()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting platform analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze platform usage: {str(e)}"
        )


@router.post("/platform/operations", response_model=PlatformOperationResponse)
async def execute_platform_operation(
    operation_request: PlatformOperationRequest,
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> PlatformOperationResponse:
    """
    Execute platform management operations.
    
    This endpoint allows Super Admins to perform various platform operations
    through structured API calls rather than just natural language.
    """
    try:
        user_id = current_user["user_id"]
        
        # This would contain the actual platform operation logic
        # For now, return a placeholder response
        
        from datetime import datetime
        return PlatformOperationResponse(
            operation=operation_request.operation,
            status="completed",
            result={"note": "Platform operation endpoints require specific implementation"},
            message=f"Operation '{operation_request.operation}' has been processed",
            executed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error executing platform operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute platform operation: {str(e)}"
        )


@router.get("/status")
async def get_super_admin_agent_status(
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Get Super Admin Agent status and capabilities."""
    try:
        # Initialize the agent if not already done
        assistant_id = await super_admin_agent.initialize()
        
        return {
            "status": "active",
            "assistant_id": assistant_id,
            "model": super_admin_agent.model,
            "capabilities": [
                "Course assistant creation",
                "Platform statistics",
                "User management",
                "Platform operations",
                "Natural language processing"
            ],
            "supported_operations": [
                "create_course_assistant",
                "get_platform_stats", 
                "manage_users",
                "platform_operations"
            ],
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting super admin agent status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/capabilities")
async def get_super_admin_capabilities(
    current_user: Dict[str, Any] = Depends(require_super_admin)
) -> Dict[str, Any]:
    """Get detailed capabilities and usage instructions for the Super Admin Agent."""
    try:
        return {
            "agent_type": "Super Admin Agent",
            "description": "Orchestration agent for educational platform management",
            "core_capabilities": {
                "course_management": {
                    "description": "Create and manage course assistants",
                    "examples": [
                        "Create a Calculus course for college students",
                        "Create an Advanced Physics course with lab constraints",
                        "Set up a beginner Python programming course"
                    ]
                },
                "platform_insights": {
                    "description": "Provide platform statistics and analysis",
                    "examples": [
                        "Show me platform usage statistics",
                        "How many active users do we have?",
                        "What are the most popular subjects?"
                    ]
                },
                "user_management": {
                    "description": "Assist with user administration",
                    "examples": [
                        "Show user details for user ID xyz",
                        "List all teachers in the system",
                        "Get organization membership information"
                    ]
                },
                "platform_operations": {
                    "description": "Perform platform management tasks",
                    "examples": [
                        "Schedule system maintenance",
                        "Generate analytics report",
                        "Configure backup settings"
                    ]
                }
            },
            "usage_instructions": {
                "course_creation": "Use natural language to describe the course you want to create. Include subject, target audience, and any special requirements.",
                "platform_queries": "Ask questions about users, statistics, or platform status in natural language.",
                "operations": "Describe the operation you want to perform and the agent will guide you through the process."
            },
            "limitations": [
                "Can only create course assistants, not modify existing platform users directly",
                "Platform operations may require additional confirmation",
                "Some advanced operations require manual intervention"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting super admin capabilities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )
