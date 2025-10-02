Assistant Function Catalog (Aligned to Backend APIs)
===================================================

Role Model (Final)
------------------

- super_admin: creates organizations; invites organization_admin.
- organization_admin: invites teachers for their org.
- teacher: creates courses; invites students (enrolling them).
- student: chats only; no management tools.

Auth Model
----------

- Assistants do not switch roles. The frontend/session manages roles.
- Frontend sends an access token with chat/API calls; backend authorizes.
- Only include functions below that a given agent must be able to call.

Functions by Agent
------------------

Super Admin Assistant
---------------------

1) create_organization
```json
{
  "name": "create_organization",
  "description": "Create a new organization",
  "parameters": {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    },
    "required": ["name"]
  }
}
```
Backend: POST `/organizations`

2) invite_org_admin
```json
{
  "name": "invite_org_admin",
  "description": "Invite an organization admin to an organization",
  "parameters": {
    "type": "object",
    "properties": {
      "org_id": { "type": "string" },
      "invitee_email": { "type": "string" }
    },
    "required": ["org_id","invitee_email"]
  }
}
```
Backend: POST `/organizations/{org_id}/invites` (role must be `organization_admin`)


Organization Admin Assistant
----------------------------

3) invite_teacher
```json
{
  "name": "invite_teacher",
  "description": "Invite a teacher to the organization",
  "parameters": {
    "type": "object",
    "properties": {
      "org_id": { "type": "string" },
      "invitee_email": { "type": "string" }
    },
    "required": ["org_id","invitee_email"]
  }
}
```
Backend: POST `/organizations/{org_id}/invites/teacher`


Teacher Assistant
-----------------

4) create_course
```json
{
  "name": "create_course",
  "description": "Create a new course in an organization",
  "parameters": {
    "type": "object",
    "properties": {
      "org_id": { "type": "string" },
      "title": { "type": "string" },
      "description": { "type": "string" }
    },
    "required": ["org_id","title"]
  }
}
```
Backend: POST `/courses`

5) generate_invite_link
```json
{
  "name": "generate_invite_link",
  "description": "Generate a short-lived invite token for a course",
  "parameters": {
    "type": "object",
    "properties": {
      "course_id": { "type": "string" },
      "expires_in_minutes": { "type": "integer", "minimum": 5, "maximum": 1440, "default": 60 }
    },
    "required": ["course_id"]
  }
}
```
Backend: POST `/courses/invite-link`

6) send_course_invite_email
```json
{
  "name": "send_course_invite_email",
  "description": "Send a course invite email to a student",
  "parameters": {
    "type": "object",
    "properties": {
      "course_id": { "type": "string" },
      "invitee_email": { "type": "string" },
      "expires_in_minutes": { "type": "integer", "minimum": 5, "maximum": 1440, "default": 60 }
    },
    "required": ["course_id","invitee_email"]
  }
}
```
Backend: POST `/courses/{course_id}/invite-email`


Student Assistant (Course Agent)
--------------------------------

- No management tools. Pure chat from knowledge base.

7) create_chat_thread
```json
{
  "name": "create_chat_thread",
  "description": "Create a chat thread (optionally course-scoped)",
  "parameters": {
    "type": "object",
    "properties": {
      "assistant_id": { "type": "string" },
      "course_id": { "type": "string" },
      "title": { "type": "string" }
    },
    "required": ["assistant_id"]
  }
}
```
Backend: POST `/assistant/chats`

8) list_chat_threads
```json
{
  "name": "list_chat_threads",
  "description": "List user's chat threads, optionally filtered by course",
  "parameters": { "type": "object", "properties": { "course_id": { "type": "string" } } }
}
```
Backend: GET `/assistant/chats?course_id=...`

9) send_chat_message
```json
{
  "name": "send_chat_message",
  "description": "Send a message in a chat thread and receive assistant replies",
  "parameters": {
    "type": "object",
    "properties": {
      "thread_id": { "type": "string" },
      "message": { "type": "string" }
    },
    "required": ["thread_id","message"]
  }
}
```
Backend: POST `/assistant/chats/send`

10) get_chat_history
```json
{
  "name": "get_chat_history",
  "description": "Get full message history for a chat thread",
  "parameters": {
    "type": "object",
    "properties": { "thread_id": { "type": "string" } },
    "required": ["thread_id"]
  }
}
```
Backend: GET `/assistant/chats/{thread_id}/messages`


