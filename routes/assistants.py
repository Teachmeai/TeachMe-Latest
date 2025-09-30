from typing import List, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.auth_middleware import get_user_id
from service.session_service import get_session, store_thread_mapping, get_thread_for_assistant
from service.openai_service import (
    get_all_assistants,
    filter_assistants_by_role,
    create_thread,
    send_message_to_thread,
    run_assistant,
    get_thread_messages
)


def log_assistant_operation(operation: str, user_id: str, additional_info: str = "", data: dict = None):
    """Log assistant route operations"""
    print(f"🎯 ASSISTANT {operation.upper()}: user_id={user_id}")
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    if data:
        print(f"   📋 Data: {data}")
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


class MessageRequest(BaseModel):
    message: str


router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("")
async def get_assistants(user_id: str = Depends(get_user_id)):
    """
    Get all assistants accessible by the current user.
    Filters based on user's active role and organization.
    """
    try:
        log_assistant_operation("GET_ASSISTANTS", user_id, "Fetching assistants for user")
        
        # Get user session to determine role and org
        session = await get_session(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        active_role = session.get("active_role")
        active_org_id = session.get("active_org_id")
        
        log_assistant_operation("GET_ASSISTANTS", user_id, 
                               f"User role: {active_role}, org: {active_org_id}")
        
        # Fetch all assistants from OpenAI
        all_assistants = await get_all_assistants()
        
        # Filter based on user's role and org
        filtered_assistants = await filter_assistants_by_role(
            all_assistants, 
            active_role, 
            active_org_id
        )
        
        log_assistant_operation("GET_ASSISTANTS", user_id, 
                               f"Returning {len(filtered_assistants)} assistants",
                               {"count": len(filtered_assistants)})
        
        return {
            "ok": True,
            "assistants": filtered_assistants,
            "user_role": active_role,
            "user_org_id": active_org_id
        }
    
    except Exception as e:
        log_assistant_operation("GET_ASSISTANTS", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assistant_id}")
async def get_assistant(assistant_id: str, user_id: str = Depends(get_user_id)):
    """
    Get details of a specific assistant.
    Verifies user has access to this assistant.
    """
    try:
        log_assistant_operation("GET_ASSISTANT", user_id, 
                               f"Fetching assistant {assistant_id}")
        
        # Get user session
        session = await get_session(user_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        active_role = session.get("active_role")
        active_org_id = session.get("active_org_id")
        
        # Fetch all assistants and filter
        all_assistants = await get_all_assistants()
        filtered_assistants = await filter_assistants_by_role(
            all_assistants, 
            active_role, 
            active_org_id
        )
        
        # Find the requested assistant
        assistant = next(
            (a for a in filtered_assistants if a["id"] == assistant_id), 
            None
        )
        
        if not assistant:
            raise HTTPException(
                status_code=403, 
                detail="Assistant not found or access denied"
            )
        
        log_assistant_operation("GET_ASSISTANT", user_id, 
                               f"Returning assistant {assistant_id}")
        
        return {"ok": True, "assistant": assistant}
    
    except HTTPException:
        raise
    except Exception as e:
        log_assistant_operation("GET_ASSISTANT", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assistant_id}/threads")
async def create_or_get_thread(assistant_id: str, user_id: str = Depends(get_user_id)):
    """
    Create a new thread for conversation with an assistant.
    If thread already exists for this user-assistant pair, returns existing thread.
    """
    try:
        log_assistant_operation("CREATE_THREAD", user_id, 
                               f"Creating/getting thread for assistant {assistant_id}")
        
        # Check if thread already exists
        existing_thread_id = await get_thread_for_assistant(user_id, assistant_id)
        
        if existing_thread_id:
            log_assistant_operation("CREATE_THREAD", user_id, 
                                   f"Returning existing thread {existing_thread_id}")
            return {
                "ok": True,
                "thread_id": existing_thread_id,
                "created": False
            }
        
        # Create new thread
        thread_id = await create_thread()
        
        # Store mapping
        await store_thread_mapping(user_id, assistant_id, thread_id)
        
        log_assistant_operation("CREATE_THREAD", user_id, 
                               f"Created new thread {thread_id}")
        
        return {
            "ok": True,
            "thread_id": thread_id,
            "created": True
        }
    
    except Exception as e:
        log_assistant_operation("CREATE_THREAD", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: str, 
    request: MessageRequest,
    user_id: str = Depends(get_user_id)
):
    """
    Send a message to a thread and get assistant's response.
    """
    try:
        log_assistant_operation("SEND_MESSAGE", user_id, 
                               f"Sending message to thread {thread_id}",
                               {"message_length": len(request.message)})
        
        # Find which assistant this thread belongs to
        # (We need to search Redis for the thread mapping)
        # For now, we'll extract assistant_id from request or require it
        # Let's modify this to require assistant_id in query params
        
        # Send user message
        user_message = await send_message_to_thread(thread_id, request.message)
        
        log_assistant_operation("SEND_MESSAGE", user_id, 
                               "Message sent, waiting for assistant response")
        
        return {
            "ok": True,
            "message": user_message,
            "status": "message_sent"
        }
    
    except Exception as e:
        log_assistant_operation("SEND_MESSAGE", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/{thread_id}/run")
async def run_assistant_on_thread(
    thread_id: str,
    assistant_id: str,  # Pass as query parameter
    user_id: str = Depends(get_user_id)
):
    """
    Run assistant on a thread to generate response.
    """
    try:
        log_assistant_operation("RUN_ASSISTANT", user_id, 
                               f"Running assistant {assistant_id} on thread {thread_id}")
        
        # Run assistant and get response
        response = await run_assistant(thread_id, assistant_id)
        
        log_assistant_operation("RUN_ASSISTANT", user_id, 
                               "Assistant completed successfully")
        
        return {
            "ok": True,
            "response": response
        }
    
    except Exception as e:
        log_assistant_operation("RUN_ASSISTANT", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    limit: int = 50,
    user_id: str = Depends(get_user_id)
):
    """
    Get all messages from a thread.
    """
    try:
        log_assistant_operation("GET_MESSAGES", user_id, 
                               f"Fetching messages from thread {thread_id}")
        
        messages = await get_thread_messages(thread_id, limit)
        
        log_assistant_operation("GET_MESSAGES", user_id, 
                               f"Retrieved {len(messages)} messages")
        
        return {
            "ok": True,
            "messages": messages,
            "count": len(messages)
        }
    
    except Exception as e:
        log_assistant_operation("GET_MESSAGES", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/{thread_id}/messages/complete")
async def send_and_run(
    thread_id: str,
    assistant_id: str,  # Query parameter
    request: MessageRequest,
    user_id: str = Depends(get_user_id)
):
    """
    Combined endpoint: Send message and run assistant in one call.
    This is more convenient for the frontend.
    """
    try:
        log_assistant_operation("SEND_AND_RUN", user_id, 
                               f"Sending message and running assistant {assistant_id} on thread {thread_id}")
        
        # Send user message
        await send_message_to_thread(thread_id, request.message)
        
        # Run assistant and get response
        response = await run_assistant(thread_id, assistant_id)
        
        log_assistant_operation("SEND_AND_RUN", user_id, 
                               "Message sent and assistant responded successfully")
        
        return {
            "ok": True,
            "user_message": {
                "role": "user",
                "content": request.message
            },
            "assistant_response": response
        }
    
    except Exception as e:
        log_assistant_operation("SEND_AND_RUN", user_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
