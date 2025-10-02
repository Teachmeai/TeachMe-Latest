-- Assistants registry and course linkage

-- assistants table
CREATE TABLE IF NOT EXISTS public.assistants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope text NOT NULL CHECK (scope IN ('global','organization','course')),
    role text CHECK (role IN ('super_admin','organization_admin','teacher')),
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    course_id uuid REFERENCES public.courses(id) ON DELETE CASCADE,
    name text NOT NULL,
    openai_assistant_id text NOT NULL,
    is_active boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at timestamp DEFAULT now()
);

-- uniqueness per scope
CREATE UNIQUE INDEX IF NOT EXISTS assistants_global_unique
  ON public.assistants ((lower(name)))
  WHERE scope = 'global';

CREATE UNIQUE INDEX IF NOT EXISTS assistants_org_role_unique
  ON public.assistants (org_id, role)
  WHERE scope = 'organization';

CREATE UNIQUE INDEX IF NOT EXISTS assistants_course_unique
  ON public.assistants (course_id)
  WHERE scope = 'course';

-- link a course to its assistant
ALTER TABLE public.courses
ADD COLUMN IF NOT EXISTS assistant_id uuid REFERENCES public.assistants(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS courses_assistant_id_idx ON public.courses(assistant_id);

-- ==============================================
-- CLEANUP: Drop all excess tables
-- ==============================================
drop table if exists public.ai_usage_logs cascade;
drop table if exists public.audit_logs cascade;
drop table if exists public.announcements cascade;
drop table if exists public.notifications cascade;
drop table if exists public.submissions cascade;
drop table if exists public.quiz_attempts cascade;
drop table if exists public.quizzes cascade;
drop table if exists public.assignments cascade;
drop table if exists public.lessons cascade;
drop table if exists public.modules cascade;
drop table if exists public.org_policies cascade;
drop table if exists public.chat_messages cascade;
drop table if exists public.chat_sessions cascade;
drop table if exists public.assistant_runs cascade;
drop table if exists public.assistant_threads cascade;

-- ==============================================
-- CORE TABLES (minimal needed for APIs)
-- ==============================================

-- 1) PROFILES
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  active_role text check (active_role in ('super_admin','organization_admin','teacher','student')),
  created_at timestamp default now()
);

-- 2) ORGANIZATIONS
create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

-- 3) ORGANIZATION MEMBERSHIPS
create table if not exists public.organization_memberships (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text check (role in ('organization_admin','teacher','student')) not null,
  created_at timestamp default now(),
  unique(org_id, user_id, role)
);

-- 4) INVITES
create table if not exists public.invites (
  id uuid primary key default gen_random_uuid(),
  inviter uuid references auth.users(id) on delete cascade,
  invitee_email text not null,
  role text check (role in ('organization_admin','teacher','student')) not null,
  org_id uuid references public.organizations(id) on delete cascade,
  status text default 'pending' check (status in ('pending','accepted','rejected')),
  created_at timestamp default now()
);

-- 5) COURSES
create table if not exists public.courses (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  created_by uuid references auth.users(id) on delete cascade,
  title text not null,
  description text,
  assistant_id text, -- asst_xxx on OpenAI
  status text default 'draft' check (status in ('draft','published','archived')),
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 6) ENROLLMENTS
create table if not exists public.enrollments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete cascade,
  created_at timestamp default now(),
  unique(user_id, course_id)
);

-- ==============================================
-- TRIGGERS
-- ==============================================

-- Auto-create profile when user is created
create or replace function public.handle_new_user_profile()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', new.email))
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created_profile on auth.users;
create trigger on_auth_user_created_profile
after insert on auth.users
for each row execute function public.handle_new_user_profile();

-- Default membership = student (optional)
-- ⚠️ If you want all new users to auto-join as students in a "global org",
-- you’d need a placeholder org_id (or set to null).
