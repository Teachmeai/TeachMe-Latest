from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime, timezone
import json
import asyncio

from core.supabase import get_supabase_admin
from middleware.auth_middleware import get_user_id
from service.session_service import get_session

def log_chat_operation(operation: str, user_id: str, additional_info: str = "", data: dict = None):
    """Log chat operations with detailed information"""
    print(f"💬 CHAT {operation.upper()}: user_id={user_id}")
    
    if additional_info:
        print(f"   ℹ️  {additional_info}")
    
    if data:
        print(f"   📋 Data: {data}")
    
    print(f"   ⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("   " + "="*50)

router = APIRouter(prefix="/chat", tags=["chat"])

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        log_chat_operation("CONNECT", user_id, f"User connected to chat WebSocket")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            log_chat_operation("DISCONNECT", user_id, "User disconnected from chat WebSocket")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message)
                log_chat_operation("SEND_MESSAGE", user_id, f"Message sent: {message[:50]}...")
            except Exception as e:
                log_chat_operation("SEND_MESSAGE", user_id, f"Failed to send message: {str(e)}", success=False)
                # Remove broken connection
                self.disconnect(user_id)

manager = ConnectionManager()

async def get_user_id_from_websocket(websocket: WebSocket) -> str | None:
    """Extract user ID from WebSocket connection"""
    try:
        # Get token from query params or headers
        token = websocket.query_params.get("token") or websocket.headers.get("authorization", "").replace("Bearer ", "")
        
        if not token:
            return None
            
        # Import here to avoid circular imports
        from core.deps import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Create a mock credentials object
        class MockCredentials:
            def __init__(self, token: str):
                self.credentials = token
        
        # Validate the token
        payload = get_current_user(MockCredentials(token))
        user_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
        return str(user_id) if user_id else None
        
    except Exception as e:
        log_chat_operation("AUTH", "unknown", f"Failed to authenticate WebSocket: {str(e)}", success=False)
        return None

async def prepare_ai_agent_context(user_id: str, jwt_token: str, user_message: str) -> dict:
    """Prepare complete context for AI agent including user session data"""
    try:
        # Get user session from Redis
        session_data = await get_session(user_id)
        
        context = {
            "user_id": user_id,
            "jwt_token": jwt_token,
            "user_message": user_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_data": session_data,
            "user_roles": session_data.get("roles", []) if session_data else [],
            "active_role": session_data.get("active_role") if session_data else None,
            "active_org_id": session_data.get("active_org_id") if session_data else None
        }
        
        log_chat_operation("AI_CONTEXT", user_id, f"Prepared AI context with {len(context['user_roles'])} roles")
        return context
        
    except Exception as e:
        log_chat_operation("AI_CONTEXT", user_id, f"Error preparing AI context: {str(e)}", success=False)
        # Return minimal context on error
        return {
            "user_id": user_id,
            "jwt_token": jwt_token,
            "user_message": user_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_data": None,
            "user_roles": [],
            "active_role": None,
            "active_org_id": None,
            "error": str(e)
        }

async def make_authenticated_api_call(user_id: str, jwt_token: str, endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Helper function for AI agent to make authenticated API calls"""
    try:
        # This function will be used by the AI agent to make API calls
        # The AI agent can call this with the user's JWT token to access protected endpoints
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Example: AI agent can call this to get user profile, switch roles, etc.
        log_chat_operation("AI_API_CALL", user_id, f"AI agent making {method} call to {endpoint}")
        
        # Return mock response for now
        return {
            "success": True,
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "message": f"AI agent API call to {endpoint} would be made with user {user_id}'s credentials"
        }
        
    except Exception as e:
        log_chat_operation("AI_API_CALL", user_id, f"Error in AI API call: {str(e)}", success=False)
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint,
            "user_id": user_id
        }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    user_id = None
    jwt_token = None
    
    try:
        # Authenticate the connection and get JWT token
        user_id = await get_user_id_from_websocket(websocket)
        if not user_id:
            await websocket.close(code=1008, reason="Authentication failed")
            return
            
        # Extract JWT token for AI agent
        jwt_token = websocket.query_params.get("token") or websocket.headers.get("authorization", "").replace("Bearer ", "")
        
        # Connect the user
        await manager.connect(websocket, user_id)
        log_chat_operation("WEBSOCKET_START", user_id, f"WebSocket connection established with JWT: {jwt_token[:20]}...")
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "message": "Connected to TeachMe AI Chat. Send me a message to start chatting!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_context": {
                "user_id": user_id,
                "authenticated": True
            }
        }
        await manager.send_personal_message(json.dumps(welcome_message), user_id)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                user_message = message_data.get("message", "")
                log_chat_operation("RECEIVE_MESSAGE", user_id, f"Received message: {user_message[:50]}...")
                
                # Prepare complete context for AI agent
                ai_agent_context = await prepare_ai_agent_context(user_id, jwt_token, user_message)
                
                # TODO: Send to AI agent with full context
                # ai_response = await call_ai_agent(ai_agent_context)
                
                # For now, simulate AI processing delay and send hardcoded response
                await asyncio.sleep(1)
                
                # Send hardcoded response (will be replaced with AI agent response)
                ai_response = {
                    "type": "ai",
                    "message": "Hello World! I'm TeachMe AI. How can I help you learn today?",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {
                        "user_id": user_id,
                        "processing_time_ms": 1000,
                        "ai_agent_ready": True
                    }
                }
                
                await manager.send_personal_message(json.dumps(ai_response), user_id)
                log_chat_operation("AI_RESPONSE", user_id, f"Sent AI response with context for user {user_id}")
                
            except WebSocketDisconnect:
                log_chat_operation("WEBSOCKET_DISCONNECT", user_id, "Client disconnected")
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid message format. Please send a JSON object with a 'message' field.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), user_id)
            except Exception as e:
                log_chat_operation("WEBSOCKET_ERROR", user_id, f"Error processing message: {str(e)}", success=False)
                error_message = {
                    "type": "error",
                    "message": "Sorry, I encountered an error. Please try again.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), user_id)
                
    except WebSocketDisconnect:
        log_chat_operation("WEBSOCKET_DISCONNECT", user_id or "unknown", "WebSocket disconnected")
    except Exception as e:
        log_chat_operation("WEBSOCKET_ERROR", user_id or "unknown", f"WebSocket error: {str(e)}", success=False)
    finally:
        if user_id:
            manager.disconnect(user_id)

@router.get("/status")
async def chat_status(user_id: str = Depends(get_user_id)):
    """Get chat connection status"""
    is_connected = user_id in manager.active_connections
    return {
        "connected": is_connected,
        "user_id": user_id,
        "active_connections": len(manager.active_connections)
    }
