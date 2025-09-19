"""Chat API endpoints for managing conversations and sessions."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
import json

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    AgentRole,
    WebSocketMessage,
    WebSocketResponse
)
from ..utils.auth import get_current_user
from ..services.chat_service import chat_service
from ..services.super_admin_agent import super_admin_agent
from ..services.course_agent import course_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/chat", tags=["Chat & Sessions"])


@router.get("/sessions", response_model=List[SessionResponse])
async def get_chat_sessions(
    agent_type: Optional[AgentRole] = Query(None, description="Filter by agent type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[SessionResponse]:
    """Get user's chat sessions across all agents."""
    try:
        user_id = current_user["user_id"]
        
        sessions = await chat_service.get_user_chat_sessions(
            user_id=user_id,
            agent_type=agent_type,
            limit=limit
        )
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: SessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SessionResponse:
    """Create a new chat session."""
    try:
        user_id = current_user["user_id"]
        
        session = await chat_service.create_chat_session(
            user_id=user_id,
            session_data=session_data
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SessionResponse:
    """Get details of a specific chat session."""
    try:
        user_id = current_user["user_id"]
        
        # Get user sessions and find the requested one
        sessions = await chat_service.get_user_chat_sessions(user_id)
        session = None
        
        for s in sessions:
            if s.id == session_id:
                session = s
                break
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_chat_session(
    session_id: str,
    update_data: SessionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SessionResponse:
    """Update a chat session."""
    try:
        user_id = current_user["user_id"]
        
        session = await chat_service.update_chat_session(
            session_id=session_id,
            user_id=user_id,
            update_data=update_data
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error updating chat session {session_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Delete a chat session and all its messages."""
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
        logger.error(f"Error deleting chat session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[MessageResponse]:
    """Get messages for a specific session."""
    try:
        user_id = current_user["user_id"]
        
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return messages
        
    except Exception as e:
        logger.error(f"Error getting session messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: str,
    message_data: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MessageResponse:
    """Create a new message in a session."""
    try:
        user_id = current_user["user_id"]
        
        # Ensure session_id matches
        message_data.session_id = session_id
        
        message = await chat_service.create_message(
            user_id=user_id,
            message_data=message_data
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("json", regex="^(json|csv|txt)$", description="Export format"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export a chat session in various formats."""
    try:
        user_id = current_user["user_id"]
        
        export_data = await chat_service.export_conversation(
            session_id=session_id,
            user_id=user_id,
            format=format
        )
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export session: {str(e)}"
        )


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a summary of a chat session."""
    try:
        user_id = current_user["user_id"]
        
        summary = await chat_service.get_session_summary(
            session_id=session_id,
            user_id=user_id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting session summary {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session summary: {str(e)}"
        )


@router.post("/universal", response_model=ChatResponse)
async def universal_chat(
    chat_request: ChatRequest,
    agent_type: AgentRole = Query(..., description="Type of agent to chat with"),
    agent_id: Optional[str] = Query(None, description="Specific agent ID (required for course assistants)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    Universal chat endpoint that routes to the appropriate agent.
    
    This endpoint can handle chat requests for any type of agent:
    - Super Admin Agent (agent_type=super_admin)
    - Course Assistant (agent_type=course_instructor, requires agent_id)
    """
    try:
        user_id = current_user["user_id"]
        
        if agent_type == AgentRole.SUPER_ADMIN:
            # Check if user has super admin privileges
            from ..utils.supabase_client import supabase_client
            is_super_admin = await supabase_client.check_super_admin_role(user_id)
            
            if not is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Super admin role required"
                )
            
            response = await chat_service.chat_with_super_admin(
                user_id=user_id,
                chat_request=chat_request
            )
            
        elif agent_type == AgentRole.COURSE_INSTRUCTOR:
            if not agent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="agent_id is required for course assistant chat"
                )
            
            response = await chat_service.chat_with_course_assistant(
                user_id=user_id,
                assistant_id=agent_id,
                chat_request=chat_request
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported agent type: {agent_type}"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in universal chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/stream/{session_id}")
async def stream_chat_response(
    session_id: str,
    message: str = Query(..., description="Message to send"),
    agent_type: AgentRole = Query(..., description="Type of agent to chat with"),
    agent_id: Optional[str] = Query(None, description="Specific agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> StreamingResponse:
    """
    Stream chat responses in real-time.
    
    This endpoint provides Server-Sent Events (SSE) for streaming responses.
    """
    try:
        user_id = current_user["user_id"]
        
        async def generate_stream():
            try:
                # This is a placeholder for streaming implementation
                # In a full implementation, you would use OpenAI's streaming API
                
                yield f"data: {json.dumps({'type': 'start', 'message': 'Processing your request...'})}\n\n"
                
                # Create chat request
                chat_request = ChatRequest(
                    message=message,
                    session_id=session_id,
                    stream=True
                )
                
                # Route to appropriate agent
                if agent_type == AgentRole.SUPER_ADMIN:
                    response = await chat_service.chat_with_super_admin(user_id, chat_request)
                elif agent_type == AgentRole.COURSE_INSTRUCTOR and agent_id:
                    response = await chat_service.chat_with_course_assistant(
                        user_id, agent_id, chat_request
                    )
                else:
                    raise Exception("Invalid agent configuration")
                
                # Stream the response content
                content = response.message.content
                words = content.split()
                
                for i, word in enumerate(words):
                    chunk_data = {
                        'type': 'content',
                        'content': word + ' ',
                        'index': i,
                        'total': len(words)
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # Small delay to simulate streaming
                    import asyncio
                    await asyncio.sleep(0.05)
                
                yield f"data: {json.dumps({'type': 'end', 'message': 'Response complete'})}\n\n"
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'message': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}"
        )


# WebSocket endpoint for real-time chat
@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    agent_type: AgentRole = Query(...),
    agent_id: Optional[str] = Query(None),
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time chat communication.
    
    Provides bi-directional communication for chat applications.
    """
    await websocket.accept()
    
    try:
        # Authenticate user using token
        from ..utils.auth import verify_jwt_token
        from ..utils.supabase_client import supabase_client
        
        try:
            # Simple JWT verification for WebSocket
            import jwt
            from ..config.settings import settings
            
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
            
            if not user_id or not await supabase_client.verify_user_exists(user_id):
                await websocket.close(code=1008, reason="Authentication failed")
                return
                
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "user_id": user_id
        })
        
        # Handle WebSocket messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                if data.get("type") == "chat":
                    message_content = data.get("message", "")
                    
                    if not message_content:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Empty message"
                        })
                        continue
                    
                    # Process chat message
                    chat_request = ChatRequest(
                        message=message_content,
                        session_id=session_id,
                        metadata=data.get("metadata", {})
                    )
                    
                    # Send processing status
                    await websocket.send_json({
                        "type": "processing",
                        "message": "Processing your request..."
                    })
                    
                    # Route to appropriate agent
                    try:
                        if agent_type == AgentRole.SUPER_ADMIN:
                            response = await chat_service.chat_with_super_admin(user_id, chat_request)
                        elif agent_type == AgentRole.COURSE_INSTRUCTOR and agent_id:
                            response = await chat_service.chat_with_course_assistant(
                                user_id, agent_id, chat_request
                            )
                        else:
                            raise Exception("Invalid agent configuration")
                        
                        # Send response
                        await websocket.send_json({
                            "type": "response",
                            "message": response.message.content,
                            "session_id": response.session_id,
                            "message_id": response.message.id,
                            "usage": response.usage
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Chat processing failed: {str(e)}"
                        })
                
                elif data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {data.get('type')}"
                    })
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except Exception as e:
        logger.error(f"WebSocket setup error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")


@router.get("/health")
async def chat_health_check() -> Dict[str, Any]:
    """Health check endpoint for chat services."""
    try:
        return {
            "status": "healthy",
            "services": {
                "chat_service": "active",
                "super_admin_agent": "active",
                "course_agents": "active"
            },
            "features": {
                "text_chat": True,
                "streaming": True,
                "websockets": True,
                "session_management": True,
                "message_history": True
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )
