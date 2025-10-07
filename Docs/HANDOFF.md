## Project handoff guide

This document is a single-source handoff for the next developer. It covers onboarding, deployment, operations, troubleshooting, data model, API coverage, testing, security, OpenAI usage, and a short roadmap.

### 1) Onboarding
- Prereqs: Python 3.12+, Node 18+, Redis, OPA, Supabase project, OpenAI API key.
- Backend
  - Create `.env` at repo root (names only in README; see `docs/ENV_REFERENCE.md`).
  - Install deps: `pip install -r requirements.txt`.
  - Start OPA: see `README.md` (policy at `opa/policy.rego`).
  - Run: `python -m uvicorn trunk:app --reload` → docs at http://127.0.0.1:8000/docs
- Frontend
  - `cd ascend-educate-nextjs && npm install && npm run dev` → http://localhost:3000
  - Create `.env.local` using names in `docs/ENV_REFERENCE.md` and ensure `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`.
- Supabase setup
  - See `docs/SUPABASE_SETUP.md` to fetch envs and run `migrations/schema.sql`.
- First test
  - Sign in via Supabase (Email OTP template in `docs/AUTH_SETUP.md`).
  - Call `/auth/me` from the UI or curl to confirm session creation and profile attach.

### 2) Deployment
- Environments and secrets
  - Store backend `.env` and frontend `.env.local` equivalents in your platform’s secret manager.
  - Set `ALLOWED_ORIGINS` to your deployed frontend URL.
- Backend
  - Build and run a process that starts after OPA is available.
  - Provision Redis (managed service recommended). Point `REDIS_URL` accordingly.
  - Health checks: GET `/docs` for router load; add a simple `/health` if needed.
- Frontend
  - Configure `NEXT_PUBLIC_*` envs, especially `NEXT_PUBLIC_BACKEND_URL`.
- OPA
  - Deploy OPA alongside backend or as a separate service; load `opa/policy.rego` on boot and expose `:8181`.

### 3) Operations runbook
- Start/stop
  - Backend: uvicorn `trunk:app`. Ensure Redis and OPA are reachable at startup.
  - OPA: run with `opa run --server opa/policy.rego`.
- Sessions
  - Clear a user session: delete key `session:<user_id>` in Redis.
- Policy updates
  - Update `opa/policy.rego` and reload OPA (or push via OPA API).
- Logs
  - API routes log structured lines for auth/profile, file upload, assistants.

### 4) Troubleshooting
- JWT invalid: verify Supabase `JWT_SECRET` and that tokens aren’t expired.
- 403 from protected routes: check OPA policy verdict and `active_role` in Redis session.
- CORS errors: ensure `ALLOWED_ORIGINS` includes the frontend URL.
- Redis connection: validate `REDIS_URL`; backend requires it during startup.
- OpenAI vector store issues: confirm `OPENAI_API_KEY`, review file batch processing logs.

### 5) Data model (key tables)
- `profiles (id, full_name, active_role, ..., created_at, updated_at)`
- `organizations (id, name, created_by, created_at)`
- `organization_memberships (id, org_id, user_id, role, created_at)`
- `invites (id, inviter, invitee_email, role, org_id, status, created_at)`
- `courses (id, org_id, created_by, title, description, assistant_id, vector_store_id, status, created_at, updated_at)`
- `enrollments (id, user_id, course_id, created_at)`
- Assistants/chat: `assistants`, `chat_threads`, `chat_messages`
- Course content: `course_content`
See `migrations/schema.sql` for exact DDL and indices.

### 6) API coverage (selected routes)
- Auth (`routes/auth.py`)
  - `GET /auth/me`: validates JWT, creates/refreshes Redis session, attaches profile.
  - `POST /auth/switch-role?role=...&org_id?=`: switches `active_role` (and org).
  - `POST /auth/logout`: deletes session; returns `{ ok: true }`.
  - `POST /auth/assign-global-role`: add `student` or `teacher` to global roles.
  - `POST /auth/logout/force`: clears session without JWT (used on client expiry).
- Profiles (`routes/profiles.py`)
  - `GET /profiles/me`: returns/upserts profile.
  - `PUT /profiles/me`: partial update; recomputes completion percentage.
- Organizations (`routes/organizations.py`)
  - `GET /organizations`: list organizations (super_admin only).
  - `POST /organizations/invites/accept`: accept invite by org_id.
  - `POST /organizations/invites/accept-by-id`: accept invite by invite_id (email checked against JWT).
  - `GET /organizations/invites/{invite_id}`: fetch invite details.
- File uploads (`routes/file_upload.py`)
  - `POST /upload/course-content`: upload file and attach to vector store.
  - `POST /upload/course-content/text`: upload text as file for vector store.

Additional routers exist for assistants/chat; see source for current surface.

### 7) Frontend ↔ Backend
- Base URL: `NEXT_PUBLIC_BACKEND_URL`.
- Auth: Supabase issues JWT; frontend sends `Authorization: Bearer <jwt>`.
- Helpers: `src/lib/api.ts` (`apiGet`, `apiPost`) and `src/lib/backend.ts` typed client.
See `docs/COMMUNICATION_FLOW.md` for details.

### 8) Security
- Secrets: never commit values; store in secret managers.
- JWT: use Supabase `JWT_SECRET`/`HS256`; backend decodes with leeway.
- OPA: keep policy minimal exposure; enforce least privilege.
- Supabase keys: use service role only server-side.
- CORS: tighten `ALLOWED_ORIGINS` per environment.

### 9) OpenAI usage
- Assistants (per course) created with `gpt-4o-mini` and optional vector stores.
- File uploads: backend creates OpenAI files, then attaches to `vector_store_id`.
- Config: `OPENAI_API_KEY` (and optional `OPENAI_ORG_ID`).

### 10) Testing
- Manual
  - Login, then call `/auth/me` and switch roles.
  - Update profile and verify completion percentage.
  - Create org invite, accept invite, verify membership.
  - Upload course content and verify vector store attachment.
- Collections
  - Add Postman/Thunder collection under `docs/postman/` for repeatable calls.

### 11) Roadmap (short)
- Frontend chat: complete thread/message flows; add vector store file list/remove.
- Admin UX: org creation (super_admin), invites, membership views.
- Observability: structured logs/metrics; add `/health`.
- Tests: add lightweight API tests and seed scripts.

### 12) Quick links
- Architecture: `docs/ARCHITECTURE.md`
- Communication: `docs/COMMUNICATION_FLOW.md`
- Agent functions: `docs/AGENT_FUNCTIONS.md`
- Schema: `migrations/schema.sql`
- Env reference: `docs/ENV_REFERENCE.md`


