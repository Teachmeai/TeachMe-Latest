
-- ORGANIZATIONS
CREATE TABLE public.organizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    created_by uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at timestamp DEFAULT now()
);

-- PROFILES
CREATE TABLE public.profiles (
    id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name text,
    active_role text CHECK (active_role IN ('super_admin','organization_admin','teacher','student')),
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
    profile_completion_percentage int DEFAULT 0,
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- GLOBAL USER ROLES
CREATE TABLE public.user_roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('super_admin','organization_admin','teacher','student')),
    created_at timestamp DEFAULT now(),
    UNIQUE(user_id, role)
);

-- ORGANIZATION MEMBERSHIPS
CREATE TABLE public.organization_memberships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('organization_admin','teacher','student')),
    created_at timestamp DEFAULT now()
);

-- INVITES
CREATE TABLE public.invites (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inviter uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    invitee_email text NOT NULL,
    role text NOT NULL CHECK (role IN ('organization_admin','teacher','student')),
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    status text DEFAULT 'pending' CHECK (status IN ('pending','accepted','rejected')),
    created_at timestamp DEFAULT now()
);

-- COURSES
CREATE TABLE public.courses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    created_by uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    title text NOT NULL,
    description text,
    status text DEFAULT 'draft' CHECK (status IN ('draft','published','archived')),
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- ENROLLMENTS
CREATE TABLE public.enrollments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    course_id uuid REFERENCES public.courses(id) ON DELETE CASCADE,
    created_at timestamp DEFAULT now()
);

-- TRIGGERS
-- Create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user_profile()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, active_role)
    VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email), NULL)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_profile();

-- Assign default role or invited role
CREATE OR REPLACE FUNCTION public.handle_new_user_roles()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    invite_role text;
BEGIN
    SELECT role INTO invite_role
    FROM public.invites
    WHERE invitee_email = NEW.email AND status = 'pending'
    LIMIT 1;

    IF invite_role IS NOT NULL THEN
        INSERT INTO public.user_roles(user_id, role) VALUES (NEW.id, invite_role)
        ON CONFLICT (user_id, role) DO NOTHING;
    ELSE
        INSERT INTO public.user_roles(user_id, role) VALUES (NEW.id, 'student')
        ON CONFLICT (user_id, role) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_roles ON auth.users;
CREATE TRIGGER on_auth_user_created_roles
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_roles();
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
-- Chat persistence: threads and messages

-- chat threads
CREATE TABLE IF NOT EXISTS public.chat_threads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assistant_id uuid NOT NULL REFERENCES public.assistants(id) ON DELETE CASCADE,
    course_id uuid REFERENCES public.courses(id) ON DELETE CASCADE,
    org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    role text CHECK (role IN ('super_admin','organization_admin','teacher','student')),
    openai_thread_id text NOT NULL,
    title text,
    last_message_at timestamp DEFAULT now(),
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_threads_user_idx ON public.chat_threads(user_id);
CREATE INDEX IF NOT EXISTS chat_threads_course_idx ON public.chat_threads(course_id);
CREATE INDEX IF NOT EXISTS chat_threads_assistant_idx ON public.chat_threads(assistant_id);

-- chat messages
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id uuid NOT NULL REFERENCES public.chat_threads(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content text,
    openai_message_id text,
    tool_call jsonb DEFAULT '{}'::jsonb,
    created_at timestamp DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_messages_thread_idx ON public.chat_messages(thread_id);


-- Phase 5: archival support on chat_threads

ALTER TABLE public.chat_threads
ADD COLUMN IF NOT EXISTS archived_at timestamp NULL;

CREATE INDEX IF NOT EXISTS chat_threads_archived_idx ON public.chat_threads(archived_at);


-- Add custom instructions and vector store to assistants table
ALTER TABLE public.assistants 
ADD COLUMN custom_instructions text;

-- Add vector store ID to courses table  
ALTER TABLE public.courses 
ADD COLUMN vector_store_id text;

-- Create course content table for storing uploaded materials
CREATE TABLE public.course_content (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id uuid NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    title text NOT NULL,
    content_type text NOT NULL CHECK (content_type IN ('document', 'video', 'link', 'text')),
    content text NOT NULL,
    file_id text, -- OpenAI file ID
    uploaded_by uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at timestamp without time zone DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX course_content_course_idx ON public.course_content(course_id);
CREATE INDEX course_content_uploaded_by_idx ON public.course_content(uploaded_by);

-- Add index for role-based thread filtering
CREATE INDEX chat_threads_role_idx ON public.chat_threads(role);
CREATE INDEX chat_threads_user_role_idx ON public.chat_threads(user_id, role);
-- Course invites table for inviting students to courses
CREATE TABLE public.course_invites (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id uuid NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    invitee_email text NOT NULL,
    inviter uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX course_invites_course_idx ON public.course_invites(course_id);
CREATE INDEX course_invites_email_idx ON public.course_invites(invitee_email);
CREATE INDEX course_invites_status_idx ON public.course_invites(status);
CREATE INDEX course_invites_expires_idx ON public.course_invites(expires_at);

-- Unique constraint to prevent duplicate invites
CREATE UNIQUE INDEX course_invites_unique ON public.course_invites(course_id, invitee_email) 
WHERE status = 'pending';
-- Migration 007: Add vector_store_id column to courses table
-- This allows each course to have its own vector store for knowledge base

-- Add vector_store_id column to courses table
ALTER TABLE public.courses 
ADD COLUMN IF NOT EXISTS vector_store_id text;

-- Add comment for documentation
COMMENT ON COLUMN public.courses.vector_store_id IS 'OpenAI vector store ID for course knowledge base (e.g., vs_xxx)';

-- Update existing courses to have NULL vector_store_id (will be created on first upload)
UPDATE public.courses 
SET vector_store_id = NULL 
WHERE vector_store_id IS NULL;
