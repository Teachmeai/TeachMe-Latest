## Repository directory structure

Overview of the main folders and notable files in this project.

```
.
├─ ascend-educate-nextjs/           # Next.js frontend
│  ├─ src/
│  │  ├─ app/                       # App Router pages/layouts
│  │  ├─ components/                # UI, forms, layout components
│  │  ├─ config/                    # UI tokens, roles config
│  │  ├─ hooks/                     # React hooks (auth, chat, courses)
│  │  ├─ lib/                       # API helpers, Supabase client
│  │  ├─ types/                     # Shared TypeScript types
│  │  └─ utils/                     # Validation and helpers
│  ├─ public/                       # Static assets
│  ├─ package.json                  # Frontend deps and scripts
│  └─ README.md                     # Frontend setup and env variables
│
├─ core/                            # Backend core modules
│  ├─ config.py                     # Reads env vars, central config
│  ├─ deps.py                       # FastAPI dependencies (JWT decode, user id)
│  ├─ email_service.py              # SMTP-based email sending
│  ├─ opa_client.py                 # Async HTTP client for OPA checks
│  ├─ redis_client.py               # Redis init and accessors
│  ├─ security.py                   # HTTPBearer security scheme
│  └─ supabase.py                   # Supabase admin/anon clients init
│
├─ functions/                       # Domain logic helpers
│  ├─ course_functions.py
│  ├─ organization_functions.py
│  └─ teacher_functions.py
│
├─ middleware/                      # Cross-cutting middleware
│  ├─ auth_middleware.py            # Auth helpers (extract user id)
│  ├─ authz.py                      # OPA authorization dependency
│  └─ cors.py                       # CORS setup
│
├─ routes/                          # FastAPI routers
│  ├─ auth.py                       # /auth/me, /auth/switch-role, /auth/logout
│  ├─ profiles.py                   # Profile endpoints
│  ├─ organizations.py              # Org and invites endpoints
│  ├─ courses.py                    # Course CRUD and queries
│  ├─ assistants.py                 # Assistant management
│  ├─ assistant_chats.py            # Chat endpoints
│  └─ file_upload.py                # Course content uploads to OpenAI
│
├─ service/                         # Service layer (business logic)
│  ├─ opa_service.py
│  ├─ session_service.py
│  └─ user_service.py
│
├─ opa/
│  └─ policy.rego                   # Rego policy for OPA (`authz.allow`)
│
├─ migrations/
│  └─ schema.sql                    # SQL to create core tables and triggers
│
├─ scripts/
│  ├─ run_windows.ps1               # One-time and dev scripts
│  ├─ run_mac.sh
│  ├─ setup_windows.ps1
│  └─ setup_mac.sh
│
├─ trunk.py                         # FastAPI entrypoint, lifespan, router wiring
├─ README.md                        # Backend overview and setup
├─ requirements.txt                 # Python dependencies
└─ docs/
   ├─ ARCHITECTURE.md               # Detailed architecture rationale
   ├─ AUTH_SETUP.md                 # Email OTP + Google setup and templates
   ├─ ENV_REFERENCE.md              # Env variables list and notes
   ├─ SUPABASE_SETUP.md             # Get envs from Supabase and run SQL
   └─ DIRECTORY_STRUCTURE.md        # This document
```

### Notes
- Frontend uses `NEXT_PUBLIC_BACKEND_URL` to reach the backend.
- Backend reads environment variables via `core/config.py` (loaded from `.env`).
- OPA must be running with `opa/policy.rego` loaded for protected routes.
- Redis must be available before backend startup to initialize the session client.


