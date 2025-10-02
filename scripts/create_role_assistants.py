"""
Create two role assistants (organization_admin and teacher) with function tools
and print SQL INSERTs for the public.assistants table.

Usage:
  - Set environment variable OPENAI_API_KEY
  - Optional: set OPENAI_ORG
  - Run: python scripts/create_role_assistants.py

This script does NOT store any secrets in the codebase.
"""

import os
import json
from datetime import datetime, timezone

try:
    from openai import OpenAI
except Exception:
    # Fallback import path for some environments
    from openai import OpenAI  # type: ignore


def build_org_admin_tools():
    """Function tool schemas for organization_admin assistant."""
    return [
        {
            "type": "function",
            "function": {
                "name": "invite_teacher",
                "description": "Invite a teacher to an organization by email. If org_id is omitted, use caller's active org.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "org_id": {"type": "string", "description": "Organization UUID (optional; inferred from session if omitted)"},
                        "invitee_email": {"type": "string", "description": "Teacher email"}
                    },
                    "required": ["invitee_email"]
                }
            }
        }
    ]


def build_teacher_tools():
    """Function tool schemas for teacher assistant."""
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
                "name": "invite_student",
                "description": "Invite a student to a course by email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "string", "description": "Course UUID"},
                        "email": {"type": "string", "description": "Student email"}
                    },
                    "required": ["course_id", "email"]
                }
            }
        }
    ]


def create_assistant(client: OpenAI, name: str, instructions: str, tools: list) -> str:
    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model="gpt-4o",
        tools=tools,
    )
    return assistant.id


def print_sql_inserts(org_admin_asst_id: str, teacher_asst_id: str, created_by: str | None = None):
    now_iso = datetime.now(timezone.utc).isoformat()
    created_by_sql = f"'{created_by}'" if created_by else "NULL"

    # global organization_admin assistant
    org_admin_sql = (
        "INSERT INTO public.assistants (scope, role, name, openai_assistant_id, is_active, metadata, created_by, created_at) "
        f"VALUES ('global', 'organization_admin', 'Organization_admin_agent', '{org_admin_asst_id}', true, '{{}}'::jsonb, {created_by_sql}, '{now_iso}');"
    )

    # global teacher assistant
    teacher_sql = (
        "INSERT INTO public.assistants (scope, role, name, openai_assistant_id, is_active, metadata, created_by, created_at) "
        f"VALUES ('global', 'teacher', 'Teacher_agent', '{teacher_asst_id}', true, '{{}}'::jsonb, {created_by_sql}, '{now_iso}');"
    )

    print("\n-- Run these SQL statements in your database:")
    print(org_admin_sql)
    print(teacher_sql)


def main():
    # Load env files if present
    try:
        from dotenv import load_dotenv  # type: ignore
        # Load default .env
        load_dotenv()
        # Load optional env.backend without overriding already-set vars
        if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "env.backend")):
            load_dotenv(os.path.join(os.path.dirname(__file__), "..", "env.backend"), override=False)
        elif os.path.exists("env.backend"):
            load_dotenv("env.backend", override=False)
    except Exception:
        pass

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY env var is required")

    org = os.getenv("OPENAI_ORG")
    client = OpenAI(api_key=api_key, organization=org) if org else OpenAI(api_key=api_key)

    org_admin_instructions = (
        "You are the Organization Admin Assistant. You help organization admins manage staff. "
        "Use tools to invite teachers. Ask for missing context like org_id when needed."
    )
    teacher_instructions = (
        "You are the Teacher Assistant. You help teachers manage courses and students. "
        "Use tools to create courses, invite students, and enroll them. Ask for missing context."
    )

    org_admin_tools = build_org_admin_tools()
    teacher_tools = build_teacher_tools()

    print("Creating Organization Admin assistant...")
    org_admin_id = create_assistant(
        client,
        name="Organization Admin Assistant",
        instructions=org_admin_instructions,
        tools=org_admin_tools,
    )
    print(f"Organization Admin assistant id: {org_admin_id}")

    print("Creating Teacher assistant...")
    teacher_id = create_assistant(
        client,
        name="Teacher Assistant",
        instructions=teacher_instructions,
        tools=teacher_tools,
    )
    print(f"Teacher assistant id: {teacher_id}")

    # Optional: set created_by from env USER_ID to embed provenance
    created_by = os.getenv("ASSISTANT_CREATED_BY_USER_ID")
    print_sql_inserts(org_admin_id, teacher_id, created_by)


if __name__ == "__main__":
    main()


