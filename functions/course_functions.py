import os
import logging
from datetime import datetime, timezone
import openai
from openai import OpenAI

from core.supabase import get_supabase_admin
from service.session_service import get_session, set_session
from service.user_service import build_session_payload
from service.opa_service import check_permission

logger = logging.getLogger("uvicorn.error")

async def create_course_assistant(user_id: str, course_name: str, custom_instructions: str = "") -> dict:
    """Create a dedicated AI assistant for a course"""
    try:
        logger.info(f"🎓 CREATE COURSE ASSISTANT: user_id={user_id}, course_name={course_name}")
        
        # Get user session and org context
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            return {"error": "Session not found"}
        
        # Try both org_id and active_org_id from session
        org_id = session.get("org_id") or session.get("active_org_id")
        if not org_id:
            logger.error(f"❌ CREATE COURSE ASSISTANT: No org_id in session. Session keys: {list(session.keys()) if session else 'None'}")
            return {"error": "No active organization found in session"}
        
        logger.info(f"🔧 CREATE COURSE ASSISTANT: Found org_id={org_id}")
        
        # Find course by name in user's org
        supabase = get_supabase_admin()
        course_resp = supabase.table("courses").select("*").eq("title", course_name).eq("org_id", org_id).limit(1).execute()
        if not course_resp.data:
            return {"error": f"Course '{course_name}' not found in your organization"}
        
        course = course_resp.data[0]
        course_id = course["id"]
        
        # Check if assistant already exists
        existing_assistant = supabase.table("assistants").select("*").eq("scope", "course").eq("course_id", course_id).limit(1).execute()
        if existing_assistant.data:
            existing = existing_assistant.data[0]
            logger.info(f"🔧 CREATE COURSE ASSISTANT: Assistant already exists: {existing['id']}")
            return {"error": f"Assistant for course '{course_name}' already exists (ID: {existing['id']})"}
        
        # Create OpenAI assistant
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Combine default system prompt with custom instructions
        default_prompt = f"""You are a dedicated AI assistant for the course "{course_name}".

Your role is to help students learn and understand the course material. You should:
- Answer questions about course content
- Provide explanations and examples
- Help with assignments and projects
- Guide students through learning objectives
- Be encouraging and supportive

Course Information:
- Course Name: {course_name}
- Course Description: {course.get('description', 'No description available')}

{custom_instructions if custom_instructions else ''}

Remember to stay focused on the course material and provide helpful, accurate information."""
        
        openai_assistant = client.beta.assistants.create(
            name=f"{course_name} Assistant",
            instructions=default_prompt,
            model="gpt-4o-mini",
            tools=[]  # Course assistants have no tools, just knowledge
        )
        
        # Create vector store for course knowledge base
        try:
            vector_store = client.beta.vector_stores.create(
                name=f"{course_name} Knowledge Base"
            )
            logger.info(f"🔧 CREATE COURSE ASSISTANT: Vector store created: {vector_store.id}")
        except AttributeError:
            # Fallback: create assistant without vector store for now
            logger.warning(f"⚠️ CREATE COURSE ASSISTANT: Vector stores not available, creating assistant without knowledge base")
            vector_store = None
        
        # Update assistant with vector store if available
        if vector_store:
            try:
                client.beta.assistants.update(
                    assistant_id=openai_assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
                )
                logger.info(f"🔧 CREATE COURSE ASSISTANT: Assistant updated with vector store")
            except Exception as e:
                logger.warning(f"⚠️ CREATE COURSE ASSISTANT: Failed to update assistant with vector store: {str(e)}")
                vector_store = None
        
        # Save assistant to database
        assistant_resp = supabase.table("assistants").insert({
            "scope": "course",
            "course_id": course_id,
            "name": f"{course_name} Assistant",
            "openai_assistant_id": openai_assistant.id,
            "custom_instructions": custom_instructions,
            "is_active": True,
            "created_by": user_id
        }).execute()
        
        assistant = (assistant_resp.data or [None])[0]
        if not assistant:
            return {"error": "Failed to create assistant in database"}
        
        # Link course to assistant (with or without vector store)
        update_data = {"assistant_id": assistant["id"]}
        if vector_store:
            update_data["vector_store_id"] = vector_store.id
        
        supabase.table("courses").update(update_data).eq("id", course_id).execute()
        
        result = {
            "ok": True,
            "assistant": assistant,
            "course": course
        }
        
        if vector_store:
            result["vector_store_id"] = vector_store.id
        
        return result
        
    except Exception as e:
        logger.error(f"❌ CREATE COURSE ASSISTANT ERROR: {str(e)}")
        return {"error": f"Failed to create course assistant: {str(e)}"}

async def upload_course_content(user_id: str, course_name: str, content_type: str, content: str, title: str) -> dict:
    """Upload content to course knowledge base"""
    try:
        logger.info(f"📚 UPLOAD COURSE CONTENT: user_id={user_id}, course_name={course_name}, type={content_type}")
        
        # Get user session and find course
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            return {"error": "Session not found"}
        
        org_id = session.get("org_id") or session.get("active_org_id")
        if not org_id:
            return {"error": "No active organization found in session"}
        
        supabase = get_supabase_admin()
        course_resp = supabase.table("courses").select("*").eq("title", course_name).eq("org_id", org_id).limit(1).execute()
        if not course_resp.data:
            return {"error": f"Course '{course_name}' not found in your organization"}
        
        course = course_resp.data[0]
        course_id = course["id"]
        
        # Check if course has an assistant
        if not course.get("assistant_id"):
            return {"error": f"Course '{course_name}' does not have an assistant. Create one first."}
        
        # Get assistant info
        assistant_resp = supabase.table("assistants").select("*").eq("id", course["assistant_id"]).single().execute()
        if not assistant_resp.data:
            return {"error": "Course assistant not found"}
        
        assistant = assistant_resp.data
        
        # Check if course has a vector store, create one if missing
        vector_store_id = course.get("vector_store_id")
        if not vector_store_id:
            logger.info(f"📚 UPLOAD COURSE CONTENT: No vector store found for course '{course_name}', creating one...")
            try:
                # Create vector store using curl (since OpenAI client has compatibility issues)
                import subprocess
                import json
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"error": "OpenAI API key not found"}
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "OpenAI-Beta": "assistants=v2"
                }
                
                # Create vector store
                vector_store_data = {
                    "name": f"{course_name} Knowledge Base",
                    "description": f"Knowledge base for {course_name} course"
                }
                
                cmd = [
                    "curl", "-s", "-X", "POST",
                    "-H", f"Authorization: Bearer {api_key}",
                    "-H", "Content-Type: application/json",
                    "-H", "OpenAI-Beta: assistants=v2",
                    "-d", json.dumps(vector_store_data),
                    "https://api.openai.com/v1/vector_stores"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                vector_store_response = json.loads(result.stdout)
                
                if "id" not in vector_store_response:
                    return {"error": f"Failed to create vector store: {vector_store_response}"}
                
                vector_store_id = vector_store_response["id"]
                logger.info(f"📚 UPLOAD COURSE CONTENT: Created vector store: {vector_store_id}")
                
                # Update course with vector store ID
                supabase.table("courses").update({"vector_store_id": vector_store_id}).eq("id", course_id).execute()
                logger.info(f"📚 UPLOAD COURSE CONTENT: Updated course with vector store ID")
                
                # Update assistant to use the vector store
                try:
                    # First, get current assistant configuration
                    get_assistant_cmd = [
                        "curl", "-s",
                        "-H", f"Authorization: Bearer {api_key}",
                        "-H", "OpenAI-Beta: assistants=v2",
                        f"https://api.openai.com/v1/assistants/{assistant['openai_assistant_id']}"
                    ]
                    
                    get_result = subprocess.run(get_assistant_cmd, capture_output=True, text=True, check=True)
                    assistant_config = json.loads(get_result.stdout)
                    
                    # Check if file_search tool is enabled
                    current_tools = assistant_config.get("tools", [])
                    has_file_search = any(t.get("type") == "file_search" for t in current_tools)
                    
                    # Prepare update data
                    update_data = {
                        "tool_resources": {
                            "file_search": {
                                "vector_store_ids": [vector_store_id]
                            }
                        }
                    }
                    
                    # Add file_search tool if not present
                    if not has_file_search:
                        update_data["tools"] = current_tools + [{"type": "file_search"}]
                        logger.info(f"📚 UPLOAD COURSE CONTENT: Adding file_search tool to assistant")
                    
                    # Update assistant with vector store
                    assistant_update_cmd = [
                        "curl", "-s", "-X", "POST",
                        "-H", f"Authorization: Bearer {api_key}",
                        "-H", "Content-Type: application/json",
                        "-H", "OpenAI-Beta: assistants=v2",
                        "-d", json.dumps(update_data),
                        f"https://api.openai.com/v1/assistants/{assistant['openai_assistant_id']}"
                    ]
                    
                    update_result = subprocess.run(assistant_update_cmd, capture_output=True, text=True, check=True)
                    update_response = json.loads(update_result.stdout)
                    
                    if "id" in update_response:
                        logger.info(f"📚 UPLOAD COURSE CONTENT: Updated assistant with vector store and file_search")
                    else:
                        logger.warning(f"⚠️ UPLOAD COURSE CONTENT: Failed to update assistant: {update_response}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ UPLOAD COURSE CONTENT: Failed to update assistant with vector store: {str(e)}")
                
            except Exception as e:
                logger.error(f"❌ UPLOAD COURSE CONTENT: Failed to create vector store: {str(e)}")
                return {"error": f"Failed to create vector store: {str(e)}"}
        
        # Create OpenAI file
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create a temporary file based on content type
        import tempfile
        import os as os_module
        
        if content_type == "text":
            # Text content - write as text
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_file_path = f.name
        elif content_type == "document":
            # Binary content (PDF, etc.) - write as binary
            # Content is stored as hex string, convert back to bytes
            try:
                binary_content = bytes.fromhex(content)
                # Determine file extension from title
                file_ext = ".pdf"  # Default to PDF
                if title.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
                    file_ext = os_module.path.splitext(title)[1]
                
                with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext, delete=False) as f:
                    f.write(binary_content)
                    temp_file_path = f.name
            except ValueError:
                # If hex conversion fails, treat as text
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(content)
                    temp_file_path = f.name
        else:
            return {"error": f"Content type '{content_type}' not supported"}
        
        try:
            # Upload file to OpenAI
            with open(temp_file_path, 'rb') as f:
                openai_file = client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            logger.info(f"📚 UPLOAD COURSE CONTENT: OpenAI file created: {openai_file.id}")
            
            # Try to add to vector store if available
            if vector_store_id:
                try:
                    # Use curl to add file to vector store
                    file_batch_cmd = [
                        "curl", "-s", "-X", "POST",
                        "-H", f"Authorization: Bearer {api_key}",
                        "-H", "Content-Type: application/json",
                        "-H", "OpenAI-Beta: assistants=v2",
                        "-d", json.dumps({"file_ids": [openai_file.id]}),
                        f"https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches"
                    ]
                    
                    result = subprocess.run(file_batch_cmd, capture_output=True, text=True, check=True)
                    batch_response = json.loads(result.stdout)
                    
                    if "id" in batch_response:
                        logger.info(f"📚 UPLOAD COURSE CONTENT: File batch created: {batch_response['id']}")
                        
                        # Wait for processing to complete
                        batch_id = batch_response["id"]
                        while True:
                            status_cmd = [
                                "curl", "-s",
                                "-H", f"Authorization: Bearer {api_key}",
                                "-H", "OpenAI-Beta: assistants=v2",
                                f"https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}"
                            ]
                            
                            status_result = subprocess.run(status_cmd, capture_output=True, text=True, check=True)
                            status_response = json.loads(status_result.stdout)
                            
                            status = status_response.get("status")
                            if status in ["completed", "failed", "cancelled"]:
                                if status == "completed":
                                    logger.info(f"📚 UPLOAD COURSE CONTENT: File successfully added to vector store")
                                else:
                                    logger.warning(f"⚠️ UPLOAD COURSE CONTENT: File batch {status}")
                                break
                            
                            import time
                            time.sleep(2)
                    else:
                        logger.warning(f"⚠️ UPLOAD COURSE CONTENT: Failed to create file batch: {batch_response}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ UPLOAD COURSE CONTENT: Failed to add to vector store: {str(e)}")
            
            # Save content record to course_content table
            # For binary files, don't store the full content in the database
            content_to_store = content if content_type == "text" else f"[Binary file: {title}]"
            
            content_resp = supabase.table("course_content").insert({
                "course_id": course_id,
                "title": title,
                "content_type": content_type,
                "content": content_to_store,
                "file_id": openai_file.id,
                "uploaded_by": user_id
            }).execute()
            
            content_record = (content_resp.data or [None])[0]
            if not content_record:
                return {"error": "Failed to save content record"}
            
            return {
                "ok": True,
                "content": content_record,
                "file_id": openai_file.id
            }
            
        finally:
            # Clean up temp file
            try:
                os_module.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ UPLOAD COURSE CONTENT ERROR: {str(e)}")
        return {"error": f"Failed to upload content: {str(e)}"}

async def update_course_assistant_instructions(user_id: str, course_name: str, instructions: str) -> dict:
    """Update course assistant instructions"""
    try:
        logger.info(f"🔧 UPDATE COURSE ASSISTANT INSTRUCTIONS: user_id={user_id}, course_name={course_name}")
        
        # Get user session and find course
        session = await get_session(user_id) or await build_session_payload(user_id)
        if not session:
            return {"error": "Session not found"}
        
        org_id = session.get("org_id") or session.get("active_org_id")
        if not org_id:
            return {"error": "No active organization found in session"}
        
        supabase = get_supabase_admin()
        course_resp = supabase.table("courses").select("*").eq("title", course_name).eq("org_id", org_id).limit(1).execute()
        if not course_resp.data:
            return {"error": f"Course '{course_name}' not found in your organization"}
        
        course = course_resp.data[0]
        
        # Check if course has an assistant
        if not course.get("assistant_id"):
            return {"error": f"Course '{course_name}' does not have an assistant. Create one first."}
        
        # Get assistant info
        assistant_resp = supabase.table("assistants").select("*").eq("id", course["assistant_id"]).single().execute()
        if not assistant_resp.data:
            return {"error": "Course assistant not found"}
        
        assistant = assistant_resp.data
        logger.info(f"🔧 UPDATE COURSE ASSISTANT: Found existing assistant {assistant['id']} for course {course_name}")
        
        # Update OpenAI assistant instructions
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        logger.info(f"🔧 UPDATE COURSE ASSISTANT: Updating assistant {assistant['openai_assistant_id']} with new instructions")
        
        # Combine default prompt with new instructions
        default_prompt = f"""You are a dedicated AI assistant for the course "{course_name}".

Your role is to help students learn and understand the course material. You should:
- Answer questions about course content
- Provide explanations and examples
- Help with assignments and projects
- Guide students through learning objectives
- Be encouraging and supportive

Course Information:
- Course Name: {course_name}
- Course Description: {course.get('description', 'No description available')}

{instructions}

Remember to stay focused on the course material and provide helpful, accurate information."""
        
        # Update the existing assistant (not create a new one)
        updated_assistant = client.beta.assistants.update(
            assistant_id=assistant["openai_assistant_id"],
            instructions=default_prompt
        )
        
        logger.info(f"🔧 UPDATE COURSE ASSISTANT: Assistant updated successfully, ID: {updated_assistant.id}")
        
        # Update database
        supabase.table("assistants").update({
            "custom_instructions": instructions
        }).eq("id", assistant["id"]).execute()
        
        return {
            "ok": True,
            "assistant": assistant,
            "updated_instructions": instructions
        }
        
    except Exception as e:
        logger.error(f"❌ UPDATE COURSE ASSISTANT INSTRUCTIONS ERROR: {str(e)}")
        return {"error": f"Failed to update assistant instructions: {str(e)}"}
