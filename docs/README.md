TeachMe Backend — Assistants & Chat
===================================

Overview
--------

This document summarizes the assistant-driven architecture added to the backend, what has been implemented so far (Phases 1–3), and what remains (Phases 4–5 and UI work).

Implemented (Phases 1–3)
------------------------

1) Assistant Registry (Phase 1)
- Table `public.assistants` with scopes: `global`, `organization`, `course`.
- Role-aware uniqueness and linkage:
  - Global: unique by `lower(name)`
  - Organization: unique by `(org_id, role)`
  - Course: unique by `(course_id)`
- `courses.assistant_id` column to pin a course to an assistant.
- Endpoints in `routes/assistants.py`:
  - `POST /assistants` — create assistant
  - `GET /assistants` — list assistants (filters: scope, role, org_id, course_id, active_only)
  - `PATCH /assistants/{assistant_id}` — update assistant
  - `GET /assistants/resolve` — resolve assistant by precedence course → org → global

2) Chat Persistence (Phase 2)
- Tables:
  - `public.chat_threads` — maps a user and assistant (optionally course/org) to an `openai_thread_id`.
  - `public.chat_messages` — stores message history and optional tool payloads.
- Endpoints in `routes/assistant_chats.py`:
  - `POST /assistant/chats` — create thread (optionally for a course)
  - `GET /assistant/chats` — list user threads (filter by `course_id`)
  - `POST /assistant/chats/send` — send a message, run OpenAI Assistant, persist responses
  - `GET /assistant/chats/{thread_id}/messages` — fetch history
- Course helper endpoints in `routes/courses.py`:
  - `POST /courses/{course_id}/assistant` — set/replace a course assistant (teacher/org admin only)
  - `GET /courses/my` — list enrolled courses for sidebar

3) Tool Calls + RBAC (Phase 3)
- `POST /assistant/chats/send` now processes `requires_action` tool-calls and submits tool outputs.
  - Minimal handlers included: `get_me`, `switch_role`, `create_course` (safe-scoped); other tools can be added.
- RBAC for course threads:
  - Teachers/org admins (in the course org) may create threads.
  - Students must be enrolled in the course to create course-scoped threads.
- Assistant resolution endpoint: `GET /assistants/resolve?role=...&org_id=...&course_id=...`.

Database Migrations
-------------------

Applied files (in `migrations/`):
- `005.sql`: creates `public.assistants`, adds `courses.assistant_id` and index.
- `006.sql`: creates `public.chat_threads` and `public.chat_messages` with indexes.

Dependencies
------------

Updated `requirements.txt`:
- `openai` added for Assistant API access.

Configuration
-------------

Required env for backend:
- `OPENAI_API_KEY` — for OpenAI Assistants.
- Supabase config in existing `core.config` (URL, keys).
- `config.jwt.SECRET`/`ALGORITHM` — for auth and any agent tokens (if used).

How To Run
----------

1) Install deps:
   - `pip install -r requirements.txt`
2) Run migrations (apply 005, 006 after `schema_latest.sql` seed, if used).
3) Start server:
   - `uvicorn trunk:app --reload`
4) Seed assistants:
   - Create 3 global assistants (roles: `super_admin`, `organization_admin`, `teacher`) via `POST /assistants`.
   - Optionally create per-organization and per-course assistants.

Key Endpoints (Quick Reference)
-------------------------------

- Assistants
  - POST `/assistants`
  - GET `/assistants`
  - PATCH `/assistants/{assistant_id}`
  - GET `/assistants/resolve?role=teacher&org_id=...&course_id=...`

- Courses
  - POST `/courses/{course_id}/assistant`
  - GET `/courses/my`

- Chat
  - POST `/assistant/chats`
  - GET `/assistant/chats?course_id=...`
  - POST `/assistant/chats/send`
  - POST `/assistant/chats/send/stream` (SSE)
  - GET `/assistant/chats/{thread_id}/messages`

What’s Next (Phases 4–5 + UI)
------------------------------

Phase 4 — UX polish, observability, QA (Detailed)
------------------------------------------------

1) UI flows
   - Teachers/Admins/Super Admins:
     - Add a “New chat” modal. On open, call `GET /assistants/resolve` with `role` (and `org_id` if available) to preselect default; offer `GET /assistants?scope=organization|global&role=...` to list alternatives.
     - On selection, `POST /assistant/chats` with `assistant_id`. Render returned thread and start messaging via `POST /assistant/chats/send`.
   - Students:
     - Left sidebar: show `GET /courses/my`. On select, call `GET /assistants/resolve?course_id=...` to get the course agent.
     - List course threads: `GET /assistant/chats?course_id=...`. Create new within course via `POST /assistant/chats` including `assistant_id` and `course_id`.
   - Message UX:
     - Optimistic user message append; replace with server confirmation.
     - Loading states, error toasts, and empty-state placeholders.
     - Thread list shows title, last message preview, and timestamp; allow rename.

2) Streaming responses
   - Implemented: `POST /assistant/chats/send/stream` (basic SSE of status and final message).
   - Client should consume `text/event-stream` to render a typing indicator; appends final text on completion.
   - Future: upgrade to token-level streaming with OpenAI Responses API.

3) Observability & QA
   - Structured logging (thread_id, run_id, latency, status) in chat routes.
   - Metrics (requests, errors, p95 latency, token counts) via your preferred stack.
   - Add unit tests for validation and RBAC paths; integration tests for end-to-end chat flows per role.

4) Tool payload persistence
   - When handling `requires_action`, store tool input/output JSON in `chat_messages.tool_call` for audit/debugging.

Phase 5 — Scale, caching, and guardrails (Detailed)
---------------------------------------------------

1) Performance and caching
   - Cache assistant resolution results `(scope, role, org_id, course_id)` in Redis for ~60 seconds.
   - Paginate chat threads (page/size) and messages (keyset pagination by `created_at` and `id`).
   - Background jobs for thread title generation and indexing (optional).

2) Guardrails and moderation
   - Add optional content moderation passes on user inputs and assistant outputs (configurable per env).
   - Redaction or masking for sensitive data before persistence/logging.

3) Rate limiting and quotas
   - Per-user: thread creation and send message rate limits (e.g., Redis token bucket).
   - Per-IP fallback limiter for unauthenticated paths (if any future ones).

4) Data retention & privacy
   - Add `archived_at` to `chat_threads` (migration) and implement soft-delete endpoints.
   - Retention policy jobs to purge old or archived content based on org policy.
   - Option to disable training/sharing inputs with OpenAI (set client params accordingly).

5) Resilience & error handling
   - Replace simple polling with exponential backoff on OpenAI operations.
   - Map OpenAI errors to structured HTTP errors with actionable messages.
   - Circuit-breaker or retry budget for transient failures.


Server startup troubleshooting (Windows)
---------------------------------------

If you see `ModuleNotFoundError: No module named 'websockets.asyncio'` during `uvicorn --reload`:
- Ensure the reloader child uses the same Python where you installed packages.
- Verify interpreter: `python -c "import websockets, sys; print(websockets.__version__, websockets.__file__, sys.executable)"`
- Force-reinstall into that interpreter: `python -m pip install --force-reinstall websockets==12.0 realtime==2.20.0 supabase==2.20.0`
- Try running without reload once: `python -m uvicorn trunk:app`
- Or keep `--reload` but ensure you run with the full path to the Python that has websockets 12 installed.

Notes
-----

- Tool-call handlers are intentionally minimal; extend them to call your internal endpoints when ready.
- All RBAC remains enforced by the backend using existing org memberships and enrollment checks.

Backlog for Later (Quick Fixes)
-------------------------------

- Persist tool-call inputs/outputs to `chat_messages.tool_call` for audit/debugging in Phase 4.
- Remove the unused `supabase.rpc("now")` probe inside the tool-call handler in `routes/assistant_chats.py`.
- Align logger signature in `routes/auth.py`:
  - Either add a `success: bool = True` parameter to `log_auth_operation`, or remove `success=` keyword usages in callers.

Gaps and Open Items from Phases 1–3
-----------------------------------

- Tool-call bridge currently persists assistant responses but does not save per-call input/output into `chat_messages.tool_call` yet (Phase 4 task).
- No external `service/assistant_runner.py` background runner; in-request bridge is implemented and sufficient for now.
- UI changes pending (see Phase 4 detailed plan above).


