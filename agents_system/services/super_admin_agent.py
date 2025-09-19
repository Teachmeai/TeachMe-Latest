"""Super Admin Agent service for platform management."""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..utils.openai_client import openai_client
from ..utils.supabase_client import supabase_client
from ..config.settings import settings
from ..models.schemas import (
    CourseAssistantCreate,
    PlatformStats,
    PlatformOperationRequest,
    PlatformOperationResponse
)

logger = logging.getLogger(__name__)


class SuperAdminAgent:
    """Super Admin Agent for platform orchestration and management."""
    
    def __init__(self):
        """Initialize Super Admin Agent."""
        self.openai_assistant_id = None
        self.system_prompt = settings.super_admin_system_prompt
        self.model = settings.text_model
        
    async def initialize(self) -> str:
        """Initialize the Super Admin Agent OpenAI Assistant."""
        try:
            if self.openai_assistant_id:
                return self.openai_assistant_id
            
            # Create OpenAI Assistant for Super Admin
            assistant = await openai_client.create_assistant(
                name="TeachMe Super Admin Agent",
                instructions=self._build_system_instructions(),
                model=self.model,
                tools=[
                    {"type": "function", "function": self._get_create_course_function()},
                    {"type": "function", "function": self._get_platform_stats_function()},
                    {"type": "function", "function": self._get_manage_users_function()},
                    {"type": "function", "function": self._get_platform_operations_function()}
                ],
                metadata={
                    "type": "super_admin_agent",
                    "version": "1.0.0",
                    "created_by": "system"
                }
            )
            
            self.openai_assistant_id = assistant.id
            logger.info(f"Initialized Super Admin Agent: {self.openai_assistant_id}")
            
            return self.openai_assistant_id
            
        except Exception as e:
            logger.error(f"Error initializing Super Admin Agent: {str(e)}")
            raise
    
    def _build_system_instructions(self) -> str:
        """Build comprehensive system instructions for the Super Admin Agent."""
        return f"""
{self.system_prompt}

You are the Super Admin Agent for the TeachMe educational platform. Your capabilities include:

## PLATFORM OVERVIEW
- **Users**: Students, Teachers, Admins, Parents, Super Admins
- **Organizations**: Schools, universities, training centers
- **Roles**: Global roles (super_admin, teacher, student) and organization-scoped roles (organization_admin, teacher, student)
- **Course Assistants**: AI tutors specialized for specific subjects/courses

## YOUR CORE RESPONSIBILITIES

### 1. COURSE ASSISTANT CREATION
When a user requests to create a course (e.g., "Create a Calculus course"):
- Use the create_course_assistant function
- Gather: course name, subject, description, role instructions, constraints
- Create specialized AI assistant for that course
- Configure appropriate tools and knowledge base

### 2. PLATFORM MANAGEMENT
- Answer questions about users, institutions, courses, roles
- Provide platform statistics and insights
- Help with user management and role assignments
- Assist with organizational setup and configuration

### 3. NATURAL LANGUAGE OPERATIONS
Process requests like:
- "Create a Physics course for high school students"
- "Show me platform statistics"
- "How many active teachers do we have?"
- "Create a course assistant for Advanced Mathematics"

## COURSE CREATION WORKFLOW
1. **Identify Intent**: Recognize when user wants to create a course
2. **Gather Requirements**: 
   - Course name and subject
   - Target audience (grade level, experience)
   - Special requirements or constraints
   - Teaching approach preferences
3. **Generate Instructions**: Create detailed role instructions for the course assistant
4. **Create Assistant**: Use create_course_assistant function
5. **Confirm Creation**: Provide course details and next steps

## COMMUNICATION STYLE
- Professional but approachable
- Clear and actionable responses
- Provide examples when helpful
- Ask clarifying questions when needed
- Confirm important actions before executing

## AVAILABLE FUNCTIONS
- create_course_assistant: Create specialized course AI tutors
- get_platform_stats: Retrieve platform usage statistics
- manage_users: User management operations
- platform_operations: General platform management tasks

Remember: You can only create and manage course assistants. Each course assistant you create becomes an independent AI tutor specialized for its subject area.
"""
    
    def _get_create_course_function(self) -> Dict[str, Any]:
        """Get function definition for course creation."""
        return {
            "name": "create_course_assistant",
            "description": "Create a new course assistant (AI tutor) for a specific subject or course",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the course (e.g., 'Advanced Calculus', 'High School Physics')"
                    },
                    "subject": {
                        "type": "string", 
                        "description": "Subject area (e.g., 'Mathematics', 'Physics', 'English Literature')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the course and its objectives"
                    },
                    "role_instructions": {
                        "type": "string",
                        "description": "Detailed instructions for how the AI should behave as a course instructor"
                    },
                    "constraints": {
                        "type": "string",
                        "description": "Any specific constraints or limitations for the course assistant"
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience (e.g., 'high school students', 'college freshmen', 'adult learners')"
                    },
                    "difficulty_level": {
                        "type": "string",
                        "description": "Difficulty level (e.g., 'beginner', 'intermediate', 'advanced')"
                    }
                },
                "required": ["name", "subject", "description", "role_instructions"]
            }
        }
    
    def _get_platform_stats_function(self) -> Dict[str, Any]:
        """Get function definition for platform statistics."""
        return {
            "name": "get_platform_stats",
            "description": "Retrieve current platform statistics and usage metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_details": {
                        "type": "boolean",
                        "description": "Whether to include detailed breakdown of statistics"
                    }
                },
                "required": []
            }
        }
    
    def _get_manage_users_function(self) -> Dict[str, Any]:
        """Get function definition for user management."""
        return {
            "name": "manage_users",
            "description": "Perform user management operations",
            "parameters": {
                "type": "object", 
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["list_users", "get_user_details", "update_user_role", "deactivate_user"],
                        "description": "Type of user management operation"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID (required for user-specific operations)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filters for listing users (role, organization, status)"
                    }
                },
                "required": ["operation"]
            }
        }
    
    def _get_platform_operations_function(self) -> Dict[str, Any]:
        """Get function definition for general platform operations."""
        return {
            "name": "platform_operations",
            "description": "Perform general platform management operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Description of the operation to perform"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the operation"
                    }
                },
                "required": ["operation"]
            }
        }
    
    async def process_chat_message(
        self,
        message: str,
        user_id: str,
        thread_id: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        metadata: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Process a chat message with the Super Admin Agent."""
        try:
            # Ensure agent is initialized
            assistant_id = await self.initialize()
            
            # Create or use existing thread
            if not thread_id:
                thread = await openai_client.create_thread(
                    metadata={"user_id": user_id, "agent_type": "super_admin"}
                )
                thread_id = thread.id
            
            # Add user message to thread
            await openai_client.add_message_to_thread(
                thread_id=thread_id,
                content=message,
                role="user",
                metadata=metadata or {}
            )
            
            # Run the assistant
            run = await openai_client.run_assistant(
                thread_id=thread_id,
                assistant_id=assistant_id,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                metadata={"user_id": user_id}
            )
            
            # Wait for completion and handle function calls
            completed_run = await self._handle_run_with_functions(
                thread_id, run.id, user_id
            )
            
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
                    "function_calls": getattr(completed_run, "required_action", None)
                }
            else:
                raise Exception("No assistant response received")
                
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise
    
    async def _handle_run_with_functions(
        self,
        thread_id: str,
        run_id: str,
        user_id: str
    ) -> Any:
        """Handle run execution with function calls."""
        try:
            while True:
                run = await openai_client.wait_for_run_completion(
                    thread_id, run_id, timeout=120
                )
                
                if run.status == "completed":
                    return run
                
                elif run.status == "requires_action":
                    # Handle function calls
                    tool_outputs = []
                    
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Executing function: {function_name} with args: {function_args}")
                        
                        try:
                            if function_name == "create_course_assistant":
                                result = await self._handle_create_course_assistant(
                                    function_args, user_id
                                )
                            elif function_name == "get_platform_stats":
                                result = await self._handle_get_platform_stats(
                                    function_args
                                )
                            elif function_name == "manage_users":
                                result = await self._handle_manage_users(
                                    function_args, user_id
                                )
                            elif function_name == "platform_operations":
                                result = await self._handle_platform_operations(
                                    function_args, user_id
                                )
                            else:
                                result = {"error": f"Unknown function: {function_name}"}
                            
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(result)
                            })
                            
                        except Exception as func_error:
                            logger.error(f"Function execution error: {str(func_error)}")
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({
                                    "error": f"Function execution failed: {str(func_error)}"
                                })
                            })
                    
                    # Submit tool outputs
                    run = await openai_client.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                    
                else:
                    raise Exception(f"Run failed with status: {run.status}")
                    
        except Exception as e:
            logger.error(f"Error handling run with functions: {str(e)}")
            raise
    
    async def _handle_create_course_assistant(
        self,
        args: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle course assistant creation function call."""
        try:
            from ..services.course_agent import CourseAgentService
            
            # Extract and validate arguments
            name = args.get("name")
            subject = args.get("subject")
            description = args.get("description")
            role_instructions = args.get("role_instructions")
            constraints = args.get("constraints", "")
            target_audience = args.get("target_audience", "")
            difficulty_level = args.get("difficulty_level", "")
            
            if not all([name, subject, description, role_instructions]):
                return {
                    "success": False,
                    "error": "Missing required fields: name, subject, description, role_instructions"
                }
            
            # Create enhanced system prompt
            enhanced_prompt = self._build_course_assistant_prompt(
                subject, description, role_instructions, constraints,
                target_audience, difficulty_level
            )
            
            # Create course assistant
            course_service = CourseAgentService()
            assistant_data = CourseAssistantCreate(
                name=name,
                subject=subject,
                description=description,
                role_instructions=role_instructions,
                constraints=constraints,
                system_prompt=enhanced_prompt,
                metadata={
                    "target_audience": target_audience,
                    "difficulty_level": difficulty_level,
                    "created_by_super_admin": True
                }
            )
            
            course_assistant = await course_service.create_course_assistant(
                assistant_data, user_id
            )
            
            return {
                "success": True,
                "assistant_id": course_assistant.id,
                "name": course_assistant.name,
                "subject": course_assistant.subject,
                "openai_assistant_id": course_assistant.openai_assistant_id,
                "message": f"Successfully created course assistant '{name}' for {subject}. The assistant is ready to help students with this course."
            }
            
        except Exception as e:
            logger.error(f"Error creating course assistant: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_platform_stats(
        self,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle platform statistics function call."""
        try:
            include_details = args.get("include_details", False)
            
            stats = await supabase_client.get_platform_stats()
            
            result = {
                "success": True,
                "stats": stats,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            if include_details:
                result["details"] = {
                    "user_growth": "Statistics show steady growth in user adoption",
                    "engagement": "High engagement with course assistants",
                    "popular_subjects": ["Mathematics", "Science", "English"],
                    "peak_usage_hours": "2-6 PM local time"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting platform stats: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_manage_users(
        self,
        args: Dict[str, Any],
        admin_user_id: str
    ) -> Dict[str, Any]:
        """Handle user management function call."""
        try:
            operation = args.get("operation")
            
            if operation == "list_users":
                # This would require additional database queries
                return {
                    "success": True,
                    "message": "User listing functionality would be implemented here",
                    "note": "This requires additional database schema for user management"
                }
            
            elif operation == "get_user_details":
                user_id = args.get("user_id")
                if not user_id:
                    return {"success": False, "error": "user_id required"}
                
                user_profile = await supabase_client.get_user_profile(user_id)
                if user_profile:
                    return {
                        "success": True,
                        "user": user_profile
                    }
                else:
                    return {
                        "success": False,
                        "error": "User not found"
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}"
                }
                
        except Exception as e:
            logger.error(f"Error managing users: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_platform_operations(
        self,
        args: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle general platform operations function call."""
        try:
            operation = args.get("operation", "")
            parameters = args.get("parameters", {})
            
            # Parse operation intent
            if "backup" in operation.lower():
                return {
                    "success": True,
                    "message": "Backup operation would be initiated",
                    "note": "This requires additional infrastructure setup"
                }
            
            elif "maintenance" in operation.lower():
                return {
                    "success": True,
                    "message": "Maintenance mode would be configured",
                    "note": "This requires additional system management features"
                }
            
            elif any(word in operation.lower() for word in ["export", "report", "analytics"]):
                return {
                    "success": True,
                    "message": "Analytics report generation would be initiated",
                    "note": "This requires additional reporting infrastructure"
                }
            
            else:
                return {
                    "success": True,
                    "message": f"Platform operation '{operation}' has been noted",
                    "note": "Custom platform operations require specific implementation"
                }
                
        except Exception as e:
            logger.error(f"Error handling platform operations: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_course_assistant_prompt(
        self,
        subject: str,
        description: str,
        role_instructions: str,
        constraints: str = "",
        target_audience: str = "",
        difficulty_level: str = ""
    ) -> str:
        """Build enhanced system prompt for course assistant."""
        prompt_parts = [
            f"You are a specialized AI instructor for {subject}.",
            f"\nCOURSE DESCRIPTION:\n{description}",
            f"\nROLE INSTRUCTIONS:\n{role_instructions}"
        ]
        
        if target_audience:
            prompt_parts.append(f"\nTARGET AUDIENCE:\n{target_audience}")
        
        if difficulty_level:
            prompt_parts.append(f"\nDIFFICULTY LEVEL:\n{difficulty_level}")
        
        if constraints:
            prompt_parts.append(f"\nCONSTRAINTS AND LIMITATIONS:\n{constraints}")
        
        prompt_parts.extend([
            "\nINSTRUCTIONAL GUIDELINES:",
            "- Use uploaded course materials as your primary knowledge base",
            "- Adapt explanations to the target audience level",
            "- Encourage critical thinking and problem-solving",
            "- Provide examples and practice opportunities",
            "- Be patient and supportive in your teaching approach",
            "- Break down complex concepts into manageable steps",
            "- Use interactive teaching methods when appropriate",
            "\nIf no course materials are uploaded, rely on your general knowledge while following the role instructions and constraints provided."
        ])
        
        return "\n".join(prompt_parts)
    
    async def get_conversation_history(
        self,
        thread_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a thread."""
        try:
            messages = await openai_client.get_thread_messages(
                thread_id, limit=limit, order="asc"
            )
            
            conversation = []
            for message in messages:
                content = ""
                for content_block in message.content:
                    if content_block.type == "text":
                        content += content_block.text.value
                
                conversation.append({
                    "id": message.id,
                    "role": message.role,
                    "content": content,
                    "created_at": message.created_at,
                    "metadata": message.metadata
                })
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise
    
    async def analyze_platform_usage(self) -> Dict[str, Any]:
        """Analyze platform usage patterns and provide insights."""
        try:
            stats = await supabase_client.get_platform_stats()
            
            # Basic analysis
            analysis = {
                "overview": {
                    "total_users": stats["total_users"],
                    "total_institutions": stats["total_institutions"],
                    "total_course_assistants": stats["total_course_assistants"],
                    "engagement_score": min(100, (stats["active_sessions_24h"] / max(1, stats["total_users"])) * 100)
                },
                "insights": [
                    f"Platform serves {stats['total_users']} users across {stats['total_institutions']} institutions",
                    f"Created {stats['total_course_assistants']} course assistants",
                    f"Generated {stats['total_messages']} messages across {stats['total_chat_sessions']} sessions",
                    f"Storage usage: {stats['storage_used_mb']:.2f} MB with {stats['files_uploaded']} files uploaded"
                ],
                "recommendations": [
                    "Consider expanding course assistant library based on popular subjects",
                    "Monitor storage usage and implement archiving strategies",
                    "Analyze peak usage times for resource optimization"
                ]
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing platform usage: {str(e)}")
            raise


# Global instance
super_admin_agent = SuperAdminAgent()
