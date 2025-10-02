## API Reference

Base URL: `http://localhost:8000`

Authentication: Most endpoints require `Authorization: Bearer <JWT>` (Supabase access_token).

Headers: `Content-Type: application/json`

### Auth / Session

- GET `/auth/me`
  - Purpose: Get or bootstrap current session (roles, active role, token2)
  - Optional header: `X-Device-Id: <string>`
  - Response: `{ user_id, roles, active_role, active_org_id?, token2?, exp }`

- POST `/auth/switch-role?role=<role>[&org_id=<org_id>]`
  - Purpose: Switch active role (and org)
  - Response: `{ ok, active_role, active_org_id? }`

- POST `/auth/logout`
  - Purpose: Clear backend session
  - Response: `{ ok: true }`

- POST `/auth/assign-global-role`
  - Body: `{ "role": "student" | "teacher" }`
  - Purpose: Assign a global role to current user
  - Response: `{ ok, message, role }`

### Organizations

- GET `/organizations`
  - Role: super_admin only
  - Purpose: List organizations
  - Response: `{ ok, organizations: [{ id, name, created_by, created_at }] }`

- POST `/organizations`
  - Role: super_admin only
  - Body: `{ "name": "<org name>" }`
  - Response: `{ ok, organization }`

- POST `/organizations/{org_id}/invites`
  - Role: super_admin → can invite `organization_admin`
  - Role: organization_admin (of that org) → can invite `organization_admin` or `teacher`
  - Body: `{ "invitee_email": "user@example.com", "role": "organization_admin" | "teacher" }`
  - Response: `{ ok, invite, email_sent }`

- POST `/organizations/{org_id}/invites/teacher`
  - Role: organization_admin (of that org) only
  - Body: `{ "invitee_email": "teacher@example.com" }`
  - Response: `{ ok, invite, email_sent }`

- GET `/organizations/invites/{invite_id}`
  - Purpose: Fetch invite by id
  - Response: `{ ok, invite: { id, invitee_email, role, org_id, status, created_at } }`

- POST `/organizations/invites/accept`
  - Body: `{ "org_id": "<ORG_ID>" }`
  - Purpose: Accept pending invite for the signed-in user's email; creates `organization_memberships`, marks invite accepted, refreshes session
  - Response: `{ ok, org_id, role }`

- POST `/organizations/invites/accept-by-id`
  - Body: `{ "invite_id": "<INVITE_ID>" }`
  - Purpose: Accept invite using invite id; verifies pending and (if available) email match; creates membership and marks accepted
  - Response: `{ ok, org_id, role }`

### Courses (teacher / org_admin)

- POST `/courses`
  - Role: `teacher` or `organization_admin` in the target org
  - Body: `{ "org_id": "<ORG_ID>", "title": "<title>", "description": "<optional>" }`
  - Response: `{ ok, course }`

- POST `/courses/invite-link`
  - Role: `teacher` or `organization_admin` for the course's org
  - Body: `{ "course_id": "<COURSE_ID>", "expires_in_minutes": 60 }`
  - Purpose: Generate a signed token for course enrollment
  - Response: `{ ok, token, expires_at }`

- POST `/courses/{course_id}/invite-email`
  - Role: `teacher` or `organization_admin` for the course's org
  - Body: `{ "invitee_email": "student@example.com", "expires_in_minutes": 60 }`
  - Purpose: Send an email with a link to `http://localhost:3000/courses/enroll?token=...`
  - Response: `{ ok, email_sent }`

- POST `/courses/enroll-by-token`
  - Body: `{ "token": "<token from invite-link/email>" }`
  - Purpose: Enroll the signed-in user into the course; ensures org membership (`student`) and creates `enrollments` row
  - Response: `{ ok, enrolled, already? }`

### Debug

- GET `/debug/session/{user_id}`
  - Purpose: Inspect cached session for a user (redis)
  - Response: `{ user_id, session_exists, session_data }`

### Data Model Links

- Organization membership: `organization_memberships (user_id, org_id, role)`
- Course enrollment: `enrollments (user_id, course_id)`
- Course belongs to organization: `courses (org_id, ...)`

### Email Setup

Set environment variables for SMTP before running backend:

- `MAIL_USERNAME`, `MAIL_PASSWORD` (App Password for Gmail), `MAIL_FROM`

Email endpoints used:

- Organization invites: `POST /organizations/{org_id}/invites` and `POST /organizations/{org_id}/invites/teacher`
- Course invites: `POST /courses/{course_id}/invite-email`



