-- DROP ALL TABLES (safe drop with cascade)
DROP TABLE IF EXISTS public.enrollments CASCADE;
DROP TABLE IF EXISTS public.courses CASCADE;
DROP TABLE IF EXISTS public.invites CASCADE;
DROP TABLE IF EXISTS public.organization_memberships CASCADE;
DROP TABLE IF EXISTS public.organizations CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TABLE IF EXISTS public.user_roles CASCADE;

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
