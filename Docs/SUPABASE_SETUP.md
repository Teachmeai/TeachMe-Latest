## Supabase setup: environment variables and database migrations

Follow these steps to collect the required values from Supabase and run the database schema.

### 1) Create a Supabase project
- Go to your Supabase account and create a new project.

### 2) Collect API keys and URLs (for .env files)
- In Supabase Dashboard → Settings → API:
  - Copy Project URL → use as `SUPABASE_URL`
  - Copy `anon` public key → use as `SUPABASE_ANON_KEY`
  - Copy `service_role` secret key → use as `SUPABASE_SERVICE_ROLE_KEY`
- In Supabase Dashboard → Settings → API (JWT):
  - Copy the JWT secret → use as `JWT_SECRET`
  - Algorithm is typically `HS256` → use as `JWT_ALGORITHM`

Backend `.env` names (fill in your values):
```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
JWT_SECRET=
JWT_ALGORITHM=
```

Frontend `ascend-educate-nextjs/.env.local` names:
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

### 3) Run database migrations
You can run the provided schema directly in the Supabase SQL editor.

- Open Supabase Dashboard → SQL → New query
- Paste the contents of `migrations/schema.sql` from this repo
- Run the query and ensure it completes without errors

This creates minimal tables like `profiles`, `organizations`, `organization_memberships`, `invites`, `courses`, `enrollments`, assistants and chat tables, plus helpful triggers.

### 4) Post-setup checks
- In Table editor, verify that the new tables appear (e.g., `profiles`, `organizations`, `invites`, `courses`).
- In Authentication → Users, add a test user and confirm that a `profiles` row is created automatically (trigger).


