## TeachMe Backend

FastAPI backend with Supabase auth, Redis-backed sessions, and OPA (Open Policy Agent) RBAC enforcement.

### Architecture
- FastAPI app in `trunk.py` with lifespan init
  - Initializes Supabase clients (`core/supabase.py`)
  - Initializes Redis client (`core/redis_client.py`)
  - CORS middleware (`middleware/cors.py`)
- Auth
  - Bearer JWT required globally via `HTTPBearer` (`core/security.py`)
  - JWT validated and user id extracted (`middleware/auth_middleware.py` / `core/deps.py`)
- Session
  - Redis session with TTL, refresh-on-use (`service/session_service.py`)
  - Stores: `user_id`, `roles`, `active_role`, optional `device_id`, `exp`
- Roles
  - Pulled from Supabase `memberships` table (`service/user_service.py`)
- OPA authorization
  - HTTP client to OPA (`core/opa_client.py`)
  - Wrapper service (`service/opa_service.py`)
  - Route dependency to enforce decisions (`middleware/authz.py`)
- Routes
  - `routes/auth.py`: `/auth/me`, `/auth/switch-role`, `/auth/logout`

### Prerequisites
- Python 3.12+
- Redis running locally (recommended via WSL/Ubuntu)
- OPA running locally (native Windows binary)
- Supabase project (with `auth.users`, `memberships`, etc.)

### Environment Variables (.env)
Create a `.env` in the project root:

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
FRONTEND_URL=
GOOGLE_REDIRECT_URI=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
JWT_SECRET=
JWT_ALGORITHM=
REDIS_URL=
OPA_URL=
ALLOWED_ORIGINS=
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=
MAIL_SERVER=
OPENAI_API_KEY=
OPENAI_ORG_ID=
```

Notes:
- `JWT_SECRET` must match the JWT secret your Supabase instance uses to sign access tokens.
- `ALLOWED_ORIGINS` is comma-separated when multiple values are needed.

### Install Dependencies
```
pip install -r requirements.txt
```

### Run Redis on Windows (without Docker)
Option A (Recommended): WSL Ubuntu
```
wsl -d Ubuntu
sudo apt update
sudo apt install -y redis-server
sudo sed -i 's/^#* *supervised .*/supervised systemd/' /etc/redis/redis.conf
sudo systemctl enable --now redis-server
redis-cli ping   # expect PONG
```

Option B: Memurai (Redis-compatible for Windows) — install and ensure it listens on 6379.

### Run OPA on Windows (without Docker)
1) Download OPA once:
```
Invoke-WebRequest "https://openpolicyagent.org/downloads/latest/opa_windows_amd64.exe" -OutFile "$env:USERPROFILE\opa.exe"
```
2) Project policy file location: `opa/policy.rego`
```
package authz

default allow := false

allow if {
  input.role == "teacher"
}
```
3) Start OPA using the project policy:
```
# From project root: C:\Users\Kamra\Desktop\TeachMe-Latest
& "$env:USERPROFILE\opa.exe" run --server ".\opa\policy.rego"
```
OPA listens on `http://localhost:8181`.

Test policy:
```
Invoke-RestMethod -Method Post -Uri http://localhost:8181/v1/data/authz/allow \
  -Body (@{input=@{user="u"; role="teacher"; action="x"; resource="y"}} | ConvertTo-Json) \
  -ContentType "application/json"
```

### Database Schema
Apply `migrations/first.sql` to your Supabase/Postgres. Ensure `memberships` exists with `user_id` and `role` columns.

### Run the Backend
```
# Apply websocket compatibility shim first-time import (already handled in trunk.py)
python -m uvicorn trunk:app --reload
```
Open docs at `http://127.0.0.1:8000/docs`.

### Auth Flow (Frontend → Backend)
1) Frontend authenticates via Supabase (Google / email+password / magic link) and obtains a JWT.
2) Frontend calls backend APIs with headers:
   - `Authorization: Bearer <jwt>`
   - `X-Device-Id: <your-device-id>` (recommended)

### Endpoints
- `GET /auth/me`
  - Creates/refreshes a Redis session if missing.
  - Response: `{ user_id, roles, active_role, device_id?, exp }`

- `POST /auth/switch-role?role=<role>`
  - Switches `active_role` if the user has that role.

- `POST /auth/logout`
  - Deletes the session from Redis.

### Sessions
- Stored in Redis under key `session:<user_id>`.
- TTL is 1 hour (config in `service/session_service.py`).
- `exp` is refreshed on each read.

### OPA Enforcement in Routes
Use the dependency from `middleware/authz.py` to guard protected endpoints:
```
from fastapi import APIRouter, Depends
from middleware.authz import authorize

router = APIRouter()

@router.post("/invite")
async def invite_student(user_id: str = Depends(lambda: authorize("invite_student", "school:123"))):
    return {"ok": True}
```

Backend sends this input to OPA:
```
{
  "input": {
    "user": "<user_id>",
    "role": "<active_role>",
    "action": "invite_student",
    "resource": "school:123"
  }
}
```

### CORS
Ensure `ALLOWED_ORIGINS` contains your frontend URL (e.g., `http://localhost:3000`).

### Troubleshooting
- `uvicorn not found`: run `python -m uvicorn trunk:app --reload` or activate a venv.
- Redis URL error: set `REDIS_URL=redis://localhost:6379/0` in `.env`.
- JWT invalid: confirm `JWT_SECRET` matches Supabase JWT secret; tokens must be fresh and valid.
- OPA denies: adjust `policy.rego` or your route’s `action`/`resource` to match policy.

### Project Structure
- Backend (FastAPI): project root, app entry `trunk.py`
- Frontend (Next.js): `ascend-educate-nextjs/` — see its README for setup

### Environment Summary
- `.env` in project root for backend
- `ascend-educate-nextjs/.env.local` for frontend

### Notes
- Extend policies by editing `opa/policy.rego` in the project and restarting OPA (or `PUT /v1/policies/authz`).
- Replace the example OPA rule with your real RBAC logic.


### Further reading
- See `docs/ARCHITECTURE.md` for architecture and rationale (Redis, OPA, flows)
- See `docs/COMMUNICATION_FLOW.md` for frontend↔backend and backend↔OpenAI communication
- See `docs/SUPABASE_SETUP.md` for Supabase envs and migrations
- See `docs/AUTH_SETUP.md` for Email OTP + Google setup and templates
- See `docs/ENV_REFERENCE.md` for all env variable names
- See `docs/DIRECTORY_STRUCTURE.md` for an overview of folders and key files
- See `docs/IMPLEMENTED_FEATURES.md` for a concise list of what's implemented
- See `docs/UNUSED_APIS.md` for endpoints and utilities not yet used by the UI
- See `docs/AGENT_FUNCTIONS.md` for functions available to each agent
- See `docs/HANDOFF.md` for a comprehensive handoff (onboarding, ops, APIs, etc.)
- See `docs/NEXT_IMPLEMENTATION.md` for the upcoming super_admin + grading plan


