## Communication flow: Frontend ⇄ Backend and Backend ⇄ OpenAI

This guide explains how the Next.js frontend talks to the FastAPI backend, and how the backend integrates with OpenAI for assistants and vector stores. It also points to important functions and files.

### Frontend → Backend

Environment
- Frontend reads the backend base URL from `NEXT_PUBLIC_BACKEND_URL` (see `ascend-educate-nextjs/.env.local`).

Key modules
- `ascend-educate-nextjs/src/lib/supabase.ts`: creates the Supabase client using public envs.
- `ascend-educate-nextjs/src/lib/api.ts`: generic `apiGet`/`apiPost` with auth header injection.
- `ascend-educate-nextjs/src/lib/backend.ts`: typed client for backend endpoints (sessions, profiles, orgs, invites, enroll, etc.).

Auth headers
- The frontend obtains a Supabase JWT after login.
- `getAuthHeaders()` in `src/lib/api.ts` retrieves the access token and sets `Authorization: Bearer <jwt>`.
- Some calls add `X-Device-Id` for device-aware sessions.

Typical calls
- Session: `backend.getMe()` → `GET /auth/me`
- Switch role: `backend.switchRole(role, orgId?)` → `POST /auth/switch-role?role=...`
- Logout: `backend.logout()` → `POST /auth/logout`
- Profile: `backend.getProfile()` / `backend.updateProfile()`
- Invites: `backend.acceptInvite(...)`, `backend.getInvite(...)`, `backend.acceptInviteById(...)`
- Courses: `backend.enrollByToken(token)`

Request path composition
- `src/lib/api.ts` uses `NEXT_PUBLIC_API_BASE_URL` if present, else defaults to `http://127.0.0.1:8000`.
- `src/lib/backend.ts` uses `NEXT_PUBLIC_BACKEND_URL` (preferred) to avoid hardcoding the URL.

### Backend (FastAPI) responsibilities

JWT validation
- `core/deps.py` decodes and verifies JWT using `JWT_SECRET`/`JWT_ALGORITHM` from `.env`.

Sessions (Redis)
- `service/session_service.py` reads/creates Redis sessions keyed by user, storing `roles`, `active_role`, and expiry.
- `routes/auth.py` exposes `/auth/me`, `/auth/switch-role`, `/auth/logout` using those services.

Authorization (OPA)
- `middleware/authz.py` composes an input document `(user, role, action, resource)`.
- `core/opa_client.py` posts to OPA `v1/data/authz/allow` and enforces decisions.

Database (Supabase)
- `core/supabase.py` uses the Supabase Admin client (service role) for server-side operations.
- Tables and triggers are created via `migrations/schema.sql`.

### Backend → OpenAI

Use cases
- Course file uploads: teachers/org admins upload documents to enrich a course’s knowledge base.

Key endpoints and flow
- `routes/file_upload.py`
  - `POST /upload/course-content` accepts `multipart/form-data` with `file` and metadata.
  - `POST /upload/course-content/text` accepts raw text, writes a temp file, and uploads.
  - Creates an OpenAI file via `OpenAI(...).files.create(...)`.
  - If the course has `vector_store_id`, attaches the file: `client.beta.vector_stores.files.create(...)`.

Configuration
- Requires `OPENAI_API_KEY` (and optionally `OPENAI_ORG_ID`) in backend `.env`.

### Reference: important files and functions

Frontend
- `src/lib/supabase.ts`: `createClient(supabaseUrl, supabaseAnonKey)`
- `src/lib/api.ts`: `getAuthHeaders`, `apiGet`, `apiPost`
- `src/lib/backend.ts`: `BackendClient` methods (`getMe`, `switchRole`, `logout`, `getProfile`, `updateProfile`, `acceptInvite`, `getInvite`, `acceptInviteById`, `enrollByToken`)

Backend
- `trunk.py`: app entry, routers, lifespan, CORS
- `core/config.py`: loads `.env` into a typed config object
- `core/deps.py`: `get_current_user`, `get_current_user_id` (JWT validation)
- `core/redis_client.py`: `init_redis`, `get_redis`
- `core/opa_client.py`: `opa_check`
- `routes/auth.py`: session routes
- `routes/file_upload.py`: OpenAI file uploads and vector store linkage
- `service/session_service.py`: session storage/refresh in Redis

### Sequence overview

1) User logs in via Supabase → browser stores access token.
2) Frontend calls backend (e.g., `/auth/me`) with Bearer token.
3) Backend verifies JWT, loads session from Redis (or builds it), returns session payload.
4) For protected actions, backend calls OPA; if allowed, proceeds.
5) For course uploads, backend uploads file to OpenAI and links to the course’s vector store.


