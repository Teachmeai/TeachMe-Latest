-- ==============================================
-- TEACHME PLATFORM DATABASE SCHEMA
-- ==============================================
-- Requires: Supabase (auth.users), pgcrypto

-- 1) PROFILES (extends auth.users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  active_role text check (active_role in ('super_admin','organization_admin','teacher','student')),
  phone text,
  address text,
  city text,
  state text,
  country text,
  postal_code text,
  date_of_birth date,
  bio text,
  avatar_url text,
  website text,
  linkedin_url text,
  twitter_url text,
  github_url text,
  profile_completion_percentage int default 0,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 2) ORGANIZATIONS
create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

-- 3) GLOBAL USER ROLES
create table if not exists public.user_roles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  role text check (role in ('super_admin','teacher','student')) not null,
  created_at timestamp default now(),
  unique(user_id, role)
);

-- 4) ORGANIZATION MEMBERSHIPS
create table if not exists public.organization_memberships (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text check (role in ('organization_admin','teacher','student')) not null,
  created_at timestamp default now(),
  unique(org_id, user_id, role)
);

-- 5) INVITES
create table if not exists public.invites (
  id uuid primary key default gen_random_uuid(),
  inviter uuid references auth.users(id) on delete cascade,
  invitee_email text not null,
  role text check (role in ('organization_admin','teacher','student')) not null,
  org_id uuid references public.organizations(id) on delete cascade,
  status text default 'pending' check (status in ('pending','accepted','rejected')),
  created_at timestamp default now()
);

-- 6) ORG POLICIES
create table if not exists public.org_policies (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  grading_policy jsonb,
  attendance_policy jsonb,
  invite_permissions jsonb,
  created_at timestamp default now()
);

-- 7) COURSES
create table if not exists public.courses (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  created_by uuid references auth.users(id) on delete cascade,
  title text not null,
  description text,
  status text default 'draft' check (status in ('draft','published','archived')),
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 8) MODULES & LESSONS
create table if not exists public.modules (
  id uuid primary key default gen_random_uuid(),
  course_id uuid references public.courses(id) on delete cascade,
  title text not null,
  position int,
  created_at timestamp default now()
);

create table if not exists public.lessons (
  id uuid primary key default gen_random_uuid(),
  module_id uuid references public.modules(id) on delete cascade,
  title text not null,
  content text,
  resources jsonb,
  position int,
  created_at timestamp default now()
);

-- 9) ENROLLMENTS
create table if not exists public.enrollments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete cascade,
  created_at timestamp default now(),
  unique(user_id, course_id)
);

-- 10) ASSIGNMENTS & QUIZZES
create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  course_id uuid references public.courses(id) on delete cascade,
  title text not null,
  description text,
  due_date timestamp,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

create table if not exists public.quizzes (
  id uuid primary key default gen_random_uuid(),
  course_id uuid references public.courses(id) on delete cascade,
  title text not null,
  config jsonb,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

-- 11) SUBMISSIONS & QUIZ ATTEMPTS
create table if not exists public.submissions (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid references public.assignments(id) on delete cascade,
  student_id uuid references auth.users(id) on delete cascade,
  content text,
  grade numeric,
  feedback text,
  created_at timestamp default now()
);

create table if not exists public.quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  quiz_id uuid references public.quizzes(id) on delete cascade,
  student_id uuid references auth.users(id) on delete cascade,
  answers jsonb,
  score numeric,
  created_at timestamp default now()
);

-- 12) ANNOUNCEMENTS
create table if not exists public.announcements (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  course_id uuid references public.courses(id) on delete set null,
  created_by uuid references auth.users(id) on delete cascade,
  title text not null,
  message text not null,
  created_at timestamp default now()
);

-- 13) NOTIFICATIONS
create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  type text,
  message text,
  read boolean default false,
  created_at timestamp default now()
);

-- 14) CHAT SESSIONS
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  org_id uuid references public.organizations(id) on delete set null,
  course_id uuid references public.courses(id) on delete set null,
  role_context text check (role_context in ('student','teacher','organization_admin','super_admin')),
  session_type text check (session_type in ('ai_assistant','direct_message')) default 'ai_assistant',
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 15) CHAT MESSAGES
create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.chat_sessions(id) on delete cascade,
  sender_id uuid references auth.users(id) on delete set null,
  sender_type text check (sender_type in ('user','ai','system')) not null,
  message text not null,
  metadata jsonb,
  parent_id uuid references public.chat_messages(id) on delete set null,
  created_at timestamp default now()
);

create index if not exists idx_chat_messages_session on public.chat_messages(session_id, created_at);

-- 16) ASSISTANT THREADS
create table if not exists public.assistant_threads (
  id uuid primary key default gen_random_uuid(),
  thread_id text unique not null,
  session_id uuid references public.chat_sessions(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  assistant_id text not null,
  org_id uuid references public.organizations(id) on delete set null,
  course_id uuid references public.courses(id) on delete set null,
  active boolean default true,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 17) ASSISTANT RUNS
create table if not exists public.assistant_runs (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid references public.assistant_threads(id) on delete cascade,
  run_id text unique not null,
  status text check (status in ('queued','in_progress','completed','failed','cancelled')) not null,
  prompt text,
  response text,
  tokens_in int,
  tokens_out int,
  cost numeric,
  error text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- 18) AI USAGE LOGS
create table if not exists public.ai_usage_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  assistant_id text not null,
  tokens_in int,
  tokens_out int,
  cost numeric,
  created_at timestamp default now()
);

-- 19) AUDIT LOGS
create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  action text not null,
  target text,
  details jsonb,
  created_at timestamp default now()
);

-- ==============================================
-- TRIGGERS
-- ==============================================

-- Auto-create profile
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

-- Default role = student
create or replace function public.handle_new_user_roles()
returns trigger language plpgsql security definer as $$
begin
  insert into public.user_roles(user_id, role)
  values (new.id, 'student')
  on conflict do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created_roles on auth.users;
create trigger on_auth_user_created_roles
after insert on auth.users
for each row execute function public.handle_new_user_roles();
