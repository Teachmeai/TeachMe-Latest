## Next implementation plan

This document outlines the next set of changes to implement.

### 1) Move course creation and assistant ownership to super_admin

Goal
- Only `super_admin` can create global courses and their assistants.
- Organizations can adopt published courses into their grades.

Proposed changes
- Authorization
  - Enforce `super_admin` on course creation/assistant creation paths (routes and `functions/course_functions.py`).
  - Update OPA policy to reflect global vs org-scoped permissions.
- Data model
  - Add `scope` to `courses` with values: `global`, `org` (default `global` for super_admin-created courses).
  - Keep `assistant_id` and `vector_store_id` on `courses` as is.
- Endpoints
  - `POST /admin/courses` (super_admin): create course (global scope).
  - `POST /admin/courses/{id}/assistant` (super_admin): create/update assistant and vector store.

Frontend
- Add super_admin-only UI to create/manage global courses.

### 2) Grading model: users enrolled by grade can access all courses in that grade

Goal
- Create a grade concept; org admins can attach global courses to grades in their org.
- Users enrolled in a specific grade get access to all courses assigned to that grade.

Schema additions (Supabase SQL)
```
-- Grades per organization
create table if not exists public.grades (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  created_at timestamp default now(),
  unique(org_id, lower(name))
);

-- Course adoption into grades (from global catalog)
create table if not exists public.grade_courses (
  id uuid primary key default gen_random_uuid(),
  grade_id uuid not null references public.grades(id) on delete cascade,
  course_id uuid not null references public.courses(id) on delete cascade,
  created_at timestamp default now(),
  unique(grade_id, course_id)
);

-- Grade enrollments
create table if not exists public.grade_enrollments (
  id uuid primary key default gen_random_uuid(),
  grade_id uuid not null references public.grades(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamp default now(),
  unique(grade_id, user_id)
);
```

Access rules
- A user can access a course if:
  - The course is global AND included in a grade of the user’s organization via `grade_courses`, AND the user is enrolled in that `grade` via `grade_enrollments`.
  - Or the course is org-scoped to that org (future work).

API additions
- Admin (org)
  - `POST /orgs/{org_id}/grades` create grade
  - `POST /orgs/{org_id}/grades/{grade_id}/courses` add adopted course (from catalog) to grade
  - `POST /orgs/{org_id}/grades/{grade_id}/enrollments` enroll user into grade
- Catalog (super_admin)
  - `GET /admin/courses` list global courses
  - `POST /admin/courses` create global course

OPA updates
- Add rules to allow org admins to manage grades within their org.
- Allow users to access courses when a `grade_enrollments` link exists to any grade that includes the course.

### 3) Org admin workflow to adopt courses into org/grade

Flow
1. Super_admin creates course (global) and assistant/vector store.
2. Org admin browses catalog; selects courses.
3. Org admin assigns selected courses to grades (creates `grade_courses` rows).
4. Org admin enrolls users into grades (creates `grade_enrollments`).
5. Users see all grade courses in their dashboard.

Frontend
- Add catalog browsing view for org admins.
- Add grade management UI (create grade, attach courses, enroll users).

Backend tasks summary
- New tables and indices (above SQL).
- New org admin endpoints for grades/courses/enrollments.
- New admin (super_admin) endpoints for course creation and assistant creation.
- Update session building to include grade memberships when needed.

Notes
- Keep `NEXT_PUBLIC_BACKEND_URL` for frontend API base; do not hardcode.
- Ensure migrations are idempotent (IF NOT EXISTS, unique constraints).


