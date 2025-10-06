"""
Update existing role assistants (organization_admin, teacher) in-place.

Usage (PowerShell examples):
  $env:OPENAI_API_KEY="your-key"
  $env:ORG_ADMIN_ASSISTANT_ID="asst_4B33eCYhtL4rU8JyIBmGUSwk"
  $env:TEACHER_ASSISTANT_ID="asst_WNdxrkBvg5IEzDlLvljAdf2H"
  python scripts/update_role_assistants.py

This script does NOT create new assistants; it only updates if IDs are provided.
It also loads .env and env.backend automatically if present.
"""

import os

try:
    from openai import OpenAI
except Exception:
    from openai import OpenAI  # type: ignore


def load_env():
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
        if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "env.backend")):
            load_dotenv(os.path.join(os.path.dirname(__file__), "..", "env.backend"), override=False)
        elif os.path.exists("env.backend"):
            load_dotenv("env.backend", override=False)
    except Exception:
        pass


def build_org_admin_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "invite_teacher",
                "description": "Invite a teacher by email. If org_id is omitted, infer from session.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "org_id": {"type": "string", "description": "Organization UUID (optional)"},
                        "invitee_email": {"type": "string", "description": "Teacher email"}
                    },
                    "required": ["invitee_email"]
                }
            }
        }
    ]


def build_teacher_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "create_course",
                "description": "Create a course within an organization.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "org_id": {"type": "string", "description": "Organization UUID"},
                        "name": {"type": "string", "description": "Course name"},
                        "description": {"type": "string", "description": "Optional course description"}
                    },
                    "required": ["org_id", "name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_course_invite_email",
                "description": "Send course invitation email to a student",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "string", "description": "Course UUID"},
                        "invitee_email": {"type": "string", "description": "Student email"},
                        "expires_in_minutes": {"type": "integer", "description": "Invitation expiry in minutes", "default": 60}
                    },
                    "required": ["course_id", "invitee_email"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_course_assistant",
                "description": "Create a dedicated AI assistant for a course by course name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_name": {"type": "string", "description": "Name of the course to create assistant for"},
                        "custom_instructions": {"type": "string", "description": "Custom instructions for the course assistant"}
                    },
                    "required": ["course_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "upload_course_content",
                "description": "Upload documents/resources to a course's knowledge base by course name. Can accept file IDs for pre-uploaded files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_name": {"type": "string", "description": "Name of the course"},
                        "content_type": {"type": "string", "enum": ["document", "video", "link", "text"], "description": "Type of content (optional if file_ids provided)"},
                        "content": {"type": "string", "description": "Content to upload (optional if file_ids provided)"},
                        "title": {"type": "string", "description": "Title of the content"},
                        "file_ids": {"type": "array", "items": {"type": "string"}, "description": "List of temporary file IDs to upload"}
                    },
                    "required": ["course_name"]  # content or file_ids should be provided
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_course_assistant_instructions",
                "description": "Update the system instructions for a course assistant by course name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_name": {"type": "string", "description": "Name of the course"},
                        "instructions": {"type": "string", "description": "New system instructions"}
                    },
                    "required": ["course_name", "instructions"]
                }
            }
        }
    ]


def main():
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY env var is required")

    org = os.getenv("OPENAI_ORG")
    client = OpenAI(api_key=api_key, organization=org) if org else OpenAI(api_key=api_key)

    org_admin_id = os.getenv("ORG_ADMIN_ASSISTANT_ID") or "asst_4B33eCYhtL4rU8JyIBmGUSwk"
    teacher_id = os.getenv("TEACHER_ASSISTANT_ID") or "asst_WNdxrkBvg5IEzDlLvljAdf2H"

    org_admin_instructions = (
        "You are the Organization Admin Assistant. You help organization admins manage staff. "
        "Use tools to invite teachers. Infer org_id from the user's session when omitted."
    )
    teacher_instructions = (
        "You are the Teacher Assistant. You help teachers manage courses and students. "
        "Use tools to create courses, send course invites, create course assistants, upload content, and update assistant instructions. "
        "When working with courses, use course names instead of IDs for better user experience. "
        "IMPORTANT: When users attach files and mention uploading to a course, ALWAYS use the upload_course_content tool with the provided file_ids. "
        "The tool can accept file_ids parameter for pre-uploaded files - use this when files are attached to messages."
    )

    if org_admin_id:
        updated = client.beta.assistants.update(
            assistant_id=org_admin_id,
            instructions=org_admin_instructions,
            tools=build_org_admin_tools(),
            model="gpt-4o",
        )
        print(f"Organization Admin assistant updated: {updated.id}")

    if teacher_id:
        updated = client.beta.assistants.update(
            assistant_id=teacher_id,
            instructions=teacher_instructions,
            tools=build_teacher_tools(),
            model="gpt-4o",
        )
        print(f"Teacher assistant updated: {updated.id}")


if __name__ == "__main__":
    main()


