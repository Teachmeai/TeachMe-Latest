from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from openai import OpenAI

from core.config import config

# Initialize OpenAI client
def get_openai_client():
    """Get OpenAI client instance"""
    api_key = config.openai.API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in environment")
    
    client_kwargs = {"api_key": api_key}
    if config.openai.ORG_ID:
        client_kwargs["organization"] = config.openai.ORG_ID
    
    return OpenAI(**client_kwargs)


def log_openai_operation(operation: str, additional_info: str = "", data: dict = None):
    """Log OpenAI service operations"""
    print(f"🤖 OPENAI {operation.upper()}: {additional_info}")
    if data:
        print(f"   📋 Data: {data}")
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)


async def get_all_assistants() -> List[Dict[str, Any]]:
    """
    Fetch all assistants from OpenAI platform.
    Returns a list of assistant objects.
    """
    try:
        client = get_openai_client()
        log_openai_operation("GET_ASSISTANTS", "Fetching all assistants from OpenAI")
        
        assistants_response = client.beta.assistants.list()
        assistants = []
        
        for assistant in assistants_response.data:
            assistant_dict = {
                "id": assistant.id,
                "name": assistant.name,
                "description": assistant.description,
                "model": assistant.model,
                "instructions": assistant.instructions,
                "tools": [tool.type for tool in assistant.tools] if assistant.tools else [],
                "metadata": assistant.metadata or {}
            }
            assistants.append(assistant_dict)
        
        log_openai_operation("GET_ASSISTANTS", f"Found {len(assistants)} assistants", 
                            {"count": len(assistants)})
        return assistants
    
    except Exception as e:
        log_openai_operation("GET_ASSISTANTS", f"Error: {str(e)}", {"error": str(e)})
        raise


async def filter_assistants_by_role(
    assistants: List[Dict[str, Any]], 
    user_role: str, 
    user_org_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter assistants based on user role and organization.
    
    Filtering logic (flexible, works without metadata):
    1. If assistant has metadata.role_access, check if it matches user_role
    2. If assistant has metadata.org_id, check if it matches user_org_id
    3. If no metadata, show to all users (generic assistants)
    """
    filtered = []
    
    for assistant in assistants:
        metadata = assistant.get("metadata", {})
        
        # If no metadata, it's a generic assistant - show to everyone
        if not metadata:
            filtered.append(assistant)
            continue
        
        # Check role access
        role_access = metadata.get("role_access")
        if role_access:
            # If role_access is specified, user must have that role
            if user_role != role_access:
                continue
        
        # Check org access
        org_id = metadata.get("org_id")
        if org_id:
            # If org_id is specified, user must be in that org
            if user_org_id != org_id:
                continue
        
        # Passed all filters
        filtered.append(assistant)
    
    log_openai_operation("FILTER_ASSISTANTS", 
                        f"Filtered {len(filtered)} assistants for role={user_role}, org={user_org_id}",
                        {"user_role": user_role, "user_org_id": user_org_id, "filtered_count": len(filtered)})
    
    return filtered


async def create_thread() -> str:
    """
    Create a new conversation thread.
    Returns thread_id.
    """
    try:
        client = get_openai_client()
        log_openai_operation("CREATE_THREAD", "Creating new conversation thread")
        
        thread = client.beta.threads.create()
        
        log_openai_operation("CREATE_THREAD", f"Thread created successfully", 
                            {"thread_id": thread.id})
        return thread.id
    
    except Exception as e:
        log_openai_operation("CREATE_THREAD", f"Error: {str(e)}", {"error": str(e)})
        raise


async def send_message_to_thread(thread_id: str, message_content: str) -> Dict[str, Any]:
    """
    Send a user message to a thread.
    Returns the message object.
    """
    try:
        client = get_openai_client()
        log_openai_operation("SEND_MESSAGE", 
                            f"Sending message to thread {thread_id}",
                            {"thread_id": thread_id, "message_length": len(message_content)})
        
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_content
        )
        
        message_dict = {
            "id": message.id,
            "role": message.role,
            "content": message.content[0].text.value if message.content else "",
            "created_at": message.created_at
        }
        
        log_openai_operation("SEND_MESSAGE", "Message sent successfully", 
                            {"message_id": message.id})
        return message_dict
    
    except Exception as e:
        log_openai_operation("SEND_MESSAGE", f"Error: {str(e)}", {"error": str(e)})
        raise


async def run_assistant(thread_id: str, assistant_id: str) -> Dict[str, Any]:
    """
    Run an assistant on a thread and wait for completion.
    Returns the assistant's response message.
    """
    try:
        client = get_openai_client()
        log_openai_operation("RUN_ASSISTANT", 
                            f"Running assistant {assistant_id} on thread {thread_id}",
                            {"thread_id": thread_id, "assistant_id": assistant_id})
        
        # Create run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Poll for completion
        import time
        max_attempts = 60  # 60 seconds max
        attempt = 0
        
        while attempt < max_attempts:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                log_openai_operation("RUN_ASSISTANT", "Run completed successfully", 
                                    {"run_id": run.id, "status": "completed"})
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                error_msg = f"Run {run_status.status}: {run_status.last_error}"
                log_openai_operation("RUN_ASSISTANT", f"Run failed: {error_msg}", 
                                    {"run_id": run.id, "status": run_status.status})
                raise Exception(error_msg)
            
            time.sleep(1)
            attempt += 1
        
        if attempt >= max_attempts:
            raise Exception("Run timed out after 60 seconds")
        
        # Get the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
        
        if messages.data:
            latest_message = messages.data[0]
            response = {
                "id": latest_message.id,
                "role": latest_message.role,
                "content": latest_message.content[0].text.value if latest_message.content else "",
                "created_at": latest_message.created_at
            }
            
            log_openai_operation("RUN_ASSISTANT", "Got assistant response", 
                                {"message_id": response["id"]})
            return response
        else:
            raise Exception("No response from assistant")
    
    except Exception as e:
        log_openai_operation("RUN_ASSISTANT", f"Error: {str(e)}", {"error": str(e)})
        raise


async def get_thread_messages(thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all messages from a thread.
    Returns list of message objects in chronological order (oldest first).
    """
    try:
        client = get_openai_client()
        log_openai_operation("GET_MESSAGES", 
                            f"Fetching messages from thread {thread_id}",
                            {"thread_id": thread_id, "limit": limit})
        
        messages_response = client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=limit
        )
        
        messages = []
        for msg in reversed(messages_response.data):  # Reverse to get chronological order
            message_dict = {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content[0].text.value if msg.content else "",
                "created_at": msg.created_at
            }
            messages.append(message_dict)
        
        log_openai_operation("GET_MESSAGES", f"Retrieved {len(messages)} messages", 
                            {"count": len(messages)})
        return messages
    
    except Exception as e:
        log_openai_operation("GET_MESSAGES", f"Error: {str(e)}", {"error": str(e)})
        raise
