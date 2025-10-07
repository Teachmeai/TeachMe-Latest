## Implemented features overview

A concise list of what is working end-to-end in this repository.

### Backend (FastAPI)
- Authentication/session APIs
  - `GET /auth/me`: validate JWT, create/refresh Redis session, return session payload
  - `POST /auth/switch-role`: switch active role if permitted
  - `POST /auth/logout`: invalidate session
- Profiles
  - `GET /profiles/me`, `PUT /profiles/me`
- Organizations
  - Invites (create, accept) and membership updates
- Courses
  - CRUD scaffolding and enrollment paths
- Assistants and chat
  - Assistant registry and chat endpoints (threads/messages schema present)
- File uploads to OpenAI
  - `POST /upload/course-content` (file) and `POST /upload/course-content/text` (text)
  - Upload to OpenAI Files API and attach to course vector store
- Redis sessions
  - TTL-based session storage with refresh-on-use
- OPA authorization
  - Policy checks via Rego `authz.allow`
- Email service
  - SMTP-based invite emails (org and course invites)

### Frontend (Next.js)
- Supabase auth integration (Email OTP / Google ready)
- Session handling and API calls using `NEXT_PUBLIC_BACKEND_URL`
- UI scaffolding
  - Auth/login, role switching
  - Profile management forms
  - Notifications and chat dashboard shell
- Hooks for data and interactions
  - `useAuth`, `useAssistants`, `useChat`, `useCourses`, `useThreads`

### Database (Supabase)
- Core schema and triggers via `migrations/schema.sql`
  - `profiles`, `organizations`, `organization_memberships`, `invites`, `courses`, `enrollments`
  - Assistants and chat tables; vector store support
  - Trigger: auto-create `profiles` on user creation

### Infrastructure/Config
- `.env` and `.env.local` variable names documented (no values)
- Redis and OPA integration configured via envs

### Documentation
- `docs/ARCHITECTURE.md`: rationale and flows (Redis, OPA, vector stores)
- `docs/COMMUNICATION_FLOW.md`: frontend↔backend and backend↔OpenAI
- `docs/SUPABASE_SETUP.md`: get envs, run migrations
- `docs/AUTH_SETUP.md`: Email OTP + Google with exact magic code template
- `docs/ENV_REFERENCE.md`: env names (backend and frontend)
- `docs/DIRECTORY_STRUCTURE.md`: folders and key files


