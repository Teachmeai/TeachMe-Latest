## Agent functions (what functions are added to which agent)

This document summarizes the functions implemented for different assistant/agent roles and where they live in the codebase. These functions can be bound as “tools” for agents to call.

### Course agent

File: `functions/course_functions.py`
- `create_course_assistant(user_id, course_name, custom_instructions="")`:
  - Creates an OpenAI assistant dedicated to a course and (attempts to) create a vector store.
  - Persists the assistant in `public.assistants` and links it to the course (`assistant_id` and optional `vector_store_id`).
- `upload_course_content(user_id, course_name, content_type, content, title)`:
  - Accepts text or binary content and uploads it to OpenAI, then attaches to the course’s vector store.
  - Stores a record in `public.course_content` with the file reference.
- `update_course_assistant_instructions(user_id, course_name, instructions)`:
  - Updates the OpenAI assistant instructions and persists the new custom instructions in the DB.

Typical actions exposed to a “Course Assistant” agent:
- Create course assistant
- Upload course content to knowledge base
- Update assistant instructions

### Organization agent

File: `functions/organization_functions.py`
- `create_organization(user_id, name)`:
  - Creates a new organization (requires `super_admin` via OPA/role checks).
- `invite_organization_admin(user_id, org_id, invitee_email, role="organization_admin")`:
  - Invites an admin or teacher to an organization, creates a DB invite, and sends an email.

Typical actions for an “Organization Admin” agent:
- Create organization (super_admin only)
- Invite organization admin / teacher

### Teacher agent

File: `functions/teacher_functions.py`
- `create_course(user_id, org_id, name, description=None)`:
  - Creates a course inside an organization.
- `invite_student(user_id, course_id, email)`:
  - Creates a course invite row (email dispatch can be layered on top).
- `send_course_invite_email_function(user_id, course_id, email, expires_in_minutes=60)`:
  - Generates a signed enroll token and sends an invite email for the course.
- `enroll_student(user_id, course_id, student_id=None, email=None)`:
  - Enrolls a student by ID, or resolves by email.

Typical actions for a “Teacher” agent:
- Create course
- Invite student (and email)
- Enroll student

### Notes
- Authorization: Most functions rely on existing role in the session and OPA checks where appropriate.
- Persistence: Functions use Supabase Admin client for server-side DB operations.
- OpenAI: Course-related functions use the OpenAI Assistants + Vector Stores APIs.


