#!/usr/bin/env python3
"""
Fix vector store binding to the teacher assistant
"""

import os
import json
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_curl_command(url, method="GET", data=None, headers=None):
    cmd = ["curl", "-s", "-X", method]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Curl error: {e}")
        print(f"Error output: {e.stderr}")
        print(f"Command: {' '.join(cmd)}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response: {result.stdout}")
        return None

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    teacher_id = "asst_WNdxrkBvg5IEzDlLvljAdf2H"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2"
    }
    
    print(f"🔍 Checking Teacher Assistant: {teacher_id}")
    
    # Get current assistant info
    assistant_response = run_curl_command(
        f"https://api.openai.com/v1/assistants/{teacher_id}",
        headers=headers
    )
    
    if not assistant_response:
        print("❌ Failed to get assistant info")
        return
    
    print(f"✅ Assistant found: {assistant_response.get('name')}")
    current_tools = assistant_response.get("tools", [])
    print(f"🔧 Current tools: {[t.get('type') for t in current_tools]}")
    
    # Check if file_search tool is present
    file_search_tool_exists = any(t.get("type") == "file_search" for t in current_tools)
    print(f"🔍 File search tool exists: {file_search_tool_exists}")
    
    # Get current tool_resources
    current_tool_resources = assistant_response.get("tool_resources", {})
    current_vector_stores = current_tool_resources.get("file_search", {}).get("vector_store_ids", [])
    print(f"📚 Current vector stores: {current_vector_stores}")
    
    # List all vector stores
    print("\n🔍 Listing all vector stores...")
    vector_stores_response = run_curl_command(
        "https://api.openai.com/v1/vector_stores",
        headers=headers
    )
    
    if vector_stores_response and vector_stores_response.get("data"):
        vector_stores = vector_stores_response["data"]
        print(f"📚 Found {len(vector_stores)} vector stores:")
        for vs in vector_stores:
            print(f"   - ID: {vs['id']}, Name: {vs['name']}, Status: {vs.get('status', 'unknown')}")
        
        # Find the most recent SPM vector store
        spm_stores = [vs for vs in vector_stores if vs.get('name') and 'spm' in vs['name'].lower()]
        if spm_stores:
            latest_spm_store = max(spm_stores, key=lambda x: x['created_at'])
            vector_store_id = latest_spm_store['id']
            print(f"\n🎯 Using SPM vector store: {vector_store_id} ({latest_spm_store['name']})")
            
            # Update assistant to use this vector store
            print(f"\n🔗 Binding vector store to assistant...")
            
            # Ensure file_search tool is present
            updated_tools = current_tools
            if not file_search_tool_exists:
                print("🔧 Adding file_search tool...")
                updated_tools = current_tools + [{"type": "file_search"}]
            else:
                print("🔧 File search tool already present")
            
            update_data = {
                "tools": updated_tools,
                "tool_resources": {
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            }
            
            update_response = run_curl_command(
                f"https://api.openai.com/v1/assistants/{teacher_id}",
                method="POST",
                data=update_data,
                headers=headers
            )
            
            if update_response and "id" in update_response:
                print(f"✅ Assistant updated successfully!")
                print(f"🔧 Updated tools: {[t.get('type') for t in update_response.get('tools', [])]}")
                new_vector_stores = update_response.get("tool_resources", {}).get("file_search", {}).get("vector_store_ids", [])
                print(f"📚 Bound vector stores: {new_vector_stores}")
            else:
                print(f"❌ Failed to update assistant: {update_response}")
        else:
            print("❌ No SPM vector stores found")
    else:
        print("❌ No vector stores found")

if __name__ == "__main__":
    main()

