## Teachme Backend TODO

### Stage 2 – Organizations & Invites
- [ ] Add POST `/orgs` (super_admin only) to create organizations
- [ ] Add GET `/orgs` (self memberships) and GET `/orgs/:id` (member)
- [ ] Add POST `/invites` (organization_admin only) to invite users
- [ ] Add POST `/invites/accept` and `/invites/reject`
- [ ] On accept: insert into `organization_memberships` or `user_roles`

### OPA Policy & Enforcement
- [ ] Expand Rego policy for actions/resources:
  - [ ] `org:create` (super_admin)
  - [ ] `org:invite_admin|teacher|student` (organization_admin)
  - [ ] `org:view`, `org:list` (members)
  - [ ] General read/write rules per role
- [ ] Add example protected routes using `authorize(action, resource)`

### Roles & Sessions
- [ ] Consider storing structured active role in session: `{scope, role, org_id?}`
- [ ] Optionally persist `active_org_id` in `profiles` (new column) for org-scoped last role
- [ ] Add endpoint `/auth/session` to inspect current session

### Database & Migrations
- [ ] Seed initial `super_admin` (manual or SQL seed script)
- [ ] Add indexes: `organization_memberships(user_id)`, `organization_memberships(org_id)`
- [ ] Backfill from legacy `schools/memberships` if migrating existing data

### Developer Experience
- [ ] `.env.example` with all required variables
- [ ] Postman/Thunder tests for `/auth/*`, `/orgs`, `/invites`
- [ ] Health endpoint `/healthz` for readiness/liveness

### Operational
- [ ] Logging and error handling standardization
- [ ] Rate limiting (per IP/user) on auth-sensitive endpoints
- [ ] Add simple CI (lint) and formatting checks


