## Unused APIs and integrations (current status)

This document lists backend endpoints, frontend utilities, and OpenAI capabilities that are present in the codebase but not yet wired into the current UI flows. Treat this as a living document and update as features are adopted.

Last reviewed: 2025-10-07

### Backend (FastAPI) endpoints likely unused by the frontend

- Debug and helper routes
  - `GET /debug/session/{user_id}` (in `trunk.py`): developer-only inspection.

- File upload helpers (teacher/org-admin only)
  - `POST /upload/temp-file` and `GET /upload/temp-file/{file_id}` (in `routes/file_upload.py`): temporary storage and retrieval; primarily diagnostic.

- Assistant/chat advanced operations
  - Some endpoints under `routes/assistants.py` and `routes/assistant_chats.py` may not be invoked by the current UI screens (the chat dashboard shell exists, but full thread/message flows might be partial). Verify actual calls from the frontend before enabling in menus.

Notes:
- Core auth (`/auth/me`, `/auth/switch-role`, `/auth/logout`), profiles, org invites, and course enrollment are in use or partially integrated.

### Frontend utilities not fully used

- Dual base-URL helpers
  - `src/lib/api.ts` supports `NEXT_PUBLIC_API_BASE_URL` and default `http://127.0.0.1:8000`.
  - `src/lib/backend.ts` prefers `NEXT_PUBLIC_BACKEND_URL` (recommended). If the app standardizes on `NEXT_PUBLIC_BACKEND_URL`, the `NEXT_PUBLIC_API_BASE_URL` path may be redundant.

- Chat and assistant hooks/components
  - Some hooks (`useThreads`, parts of `useChat`) and UI shells are present; specific thread/message features may be unhooked without final UI actions.

### OpenAI features present but not yet surfaced in UI

- Vector store management beyond upload
  - The backend attaches files to an existing `vector_store_id` if present.
  - UI flows for creating/listing/removing vector store files are not exposed yet.

- Assistants advanced features
  - Tools/functions, streaming events, and run/status management are not wired into the current UI.

### Recommendations

1) Inventory actual network calls from the frontend (e.g., inspect `backend.ts` usages) to confirm which endpoints are live.
2) For unused backend endpoints, either:
   - Hide them from public docs until adopted, or
   - Guard behind feature flags and mark as experimental.
3) Consolidate frontend base URL handling to `NEXT_PUBLIC_BACKEND_URL` for consistency.
4) Plan UI for vector store management (list/remove) if needed by teachers.


