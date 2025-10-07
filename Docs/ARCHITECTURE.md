## TeachMe Architecture Overview

This document explains the overall architecture, the role of each major component, and why Redis and OPA are part of the design. It also describes request flows and operational considerations.

### High-level components
- Frontend: Next.js app in `ascend-educate-nextjs/`.
- Backend: FastAPI app (`trunk.py`) with modular routes in `routes/`.
- Supabase: Authentication (user management, JWT issuing) and Postgres database.
- Redis: Session cache and low-latency state for authenticated requests.
- OPA (Open Policy Agent): Policy-as-code authorization engine.
- OpenAI: Assistants, vector stores, and file ingestion for course knowledge.

### Why Redis?
The backend is stateless but needs a fast way to cache session context derived from Supabase and user roles. Redis is used because it provides:
- Low-latency access to session data in memory.
- TTL-based expiry with refresh-on-use semantics.
- Horizontal scalability: multiple backend instances can share the same session store.
- Operational simplicity: straightforward to run locally or in managed services.

Stored session fields typically include:
- `user_id`: the authenticated user's ID.
- `roles`: aggregated roles (global and organization-scoped).
- `active_role`: the role currently enforced for authorization.
- Optional `device_id` and `exp`.

Sessions are refreshed during `GET /auth/me` reads; TTL extends with each use to reduce re-auth churn while preserving expiration guarantees.

### Why OPA?
Authorization grows complex as roles and scopes expand (global roles, org roles, course-level permissions). OPA allows you to:
- Externalize authorization logic from application code.
- Express policies declaratively in Rego, version them, and test them.
- Evolve policy without redeploying the backend (push new policies or reload).
- Achieve consistent decisions across multiple services if needed.

The backend sends a minimal input document to OPA, e.g.:
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
OPA responds with an `allow` decision, which the middleware uses to permit or deny the request.

### Data model summary
Core tables (see `migrations/schema.sql`):
- `profiles`: basic user profile and `active_role`.
- `organizations`: tenant-like entities.
- `organization_memberships`: membership and role per org.
- `invites`: email invites to organizations.
- `courses`: courses under organizations, optional assistant and vector store.
- `enrollments`: user-to-course relationship.
- Assistants and chat-related tables: associate OpenAI assistants/threads/messages to users/orgs/courses.

### Backend layout
- `trunk.py`: application entry, lifespan hooks, route registration, custom OpenAPI config.
- `core/`: foundational clients and configuration
  - `config.py`: environment-driven config (Supabase, Redis, JWT, OPA, frontend URL).
  - `supabase.py`: initializes admin/anon clients.
  - `redis_client.py`: initializes a single Redis client.
  - `opa_client.py`: async HTTP client for OPA queries.
  - `security.py`: shared HTTPBearer security scheme.
  - `email_service.py`: transactional emails (invites, course invites) via SMTP.
- `middleware/`: cross-cutting concerns
  - `cors.py`: CORS policy setup using `ALLOWED_ORIGINS`.
  - `auth_middleware.py` / `deps.py`: JWT parsing, user ID extraction, error mapping.
  - `authz.py`: OPA authorization dependency for protected routes.
- `routes/`: feature APIs
  - `auth.py`: `/auth/me`, `/auth/switch-role`, `/auth/logout`.
  - `profiles.py`: profile read/update.
  - `organizations.py`: org invites and membership actions.
  - `courses.py`: course lifecycle.
  - `assistants.py`, `assistant_chats.py`: assistant and chat operations.
  - `file_upload.py`: uploading course materials and pushing to OpenAI vector stores.
- `service/`: business logic
  - `session_service.py`: session create/refresh/read against Redis.
  - `user_service.py`: role aggregation based on memberships and global roles.
  - `opa_service.py`: higher-level wrappers around OPA checks.

### Request flow: authentication and sessions
1. Frontend authenticates with Supabase (email OTP or Google). Supabase issues a JWT access token.
2. Frontend calls backend with `Authorization: Bearer <jwt>` and optionally `X-Device-Id`.
3. Backend validates JWT signature and expiration using `JWT_SECRET` and `JWT_ALGORITHM` (from Supabase project settings).
4. Backend looks up or creates a Redis session, enriching with roles from Supabase if needed.
5. Response includes `user_id`, `roles`, `active_role`, and expiry info.

### Request flow: authorization with OPA
1. A protected endpoint wraps a handler with `authorize(action, resource)` dependency.
2. The dependency composes an input document (user, role, action, resource).
3. `opa_client.py` posts the input to OPA at `/v1/data/authz/allow`.
4. If OPA returns `allow: true`, the request proceeds; otherwise, the backend returns 403.

### Vector stores and file uploads
Teachers and organization admins can upload files to course knowledge bases:
- The backend accepts `UploadFile` via `multipart/form-data` and optionally text content.
- Files are temporarily staged on disk, then uploaded to OpenAI as files.
- If the course has a `vector_store_id`, the file is attached to that vector store.
- This enables retrieval-augmented conversations with the course assistant.

### CORS and app composition
`ALLOWED_ORIGINS` governs which frontend origins can call the backend. For local development, set it to `http://localhost:3000`. The Next.js app reads `NEXT_PUBLIC_BACKEND_URL` to find the backend base URL.

### Operational concerns
- Secrets management: store environment variables securely (do not commit values).
- Redis availability: the backend requires Redis during startup. Configure health checks and timeouts.
- OPA lifecycle: load `opa/policy.rego`; update policies without backend redeploys when possible.
- Logging: route handlers log key actions to aid in debugging; avoid leaking sensitive information.
- Scalability: Redis and OPA are network services; size them and secure them appropriately in production.

### Extensibility
- Add new actions/resources by updating Rego policies and calling `authorize("action", "resource")` from routes.
- Extend roles by adjusting membership tables and role enumeration checks.
- Introduce additional providers (e.g., S3 for file storage) behind service abstractions.


