-- TEACHME BASELINE SCHEMA (FROM SCRATCH)
-- Requires: Supabase (auth.users), pgcrypto (for gen_random_uuid)

-- 1) PROFILES (extends auth.users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  active_role text check (active_role in ('super_admin','organization_admin','teacher','student')),
  created_at timestamp default now()
);

-- 2) ORGANIZATIONS (replaces "schools")
create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

-- 3) GLOBAL USER ROLES (e.g., super_admin, solo teacher/student)
create table if not exists public.user_roles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  role text check (role in ('super_admin','teacher','student')) not null,
  created_at timestamp default now()
);

-- prevent duplicate global roles per user
create unique index if not exists idx_user_roles_user_role_unique on public.user_roles(user_id, role);

-- 4) ORGANIZATION MEMBERSHIPS (org-scoped roles)
create table if not exists public.organization_memberships (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text check (role in ('organization_admin','teacher','student')) not null,
  created_at timestamp default now()
);

-- 5) INVITES (org-scoped invites)
create table if not exists public.invites (
  id uuid primary key default gen_random_uuid(),
  inviter uuid references auth.users(id) on delete cascade,
  invitee_email text not null,
  role text not null check (role in ('organization_admin','teacher','student')),
  org_id uuid references public.organizations(id) on delete cascade,
  status text default 'pending', -- pending, accepted, rejected
  created_at timestamp default now()
);

-- 6) ENABLE ROW LEVEL SECURITY
alter table public.profiles enable row level security;
alter table public.organizations enable row level security;
alter table public.user_roles enable row level security;
alter table public.organization_memberships enable row level security;
alter table public.invites enable row level security;

-- 7) RLS POLICIES

-- profiles: users can view/update their own profile
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
on public.profiles for select
using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles for update
using (auth.uid() = id);

-- user_roles: users can view their global roles
drop policy if exists "Users can view their global roles" on public.user_roles;
create policy "Users can view their global roles"
on public.user_roles for select
using (auth.uid() = user_id);

-- organizations: users can view orgs they belong to
drop policy if exists "Users can view their organizations" on public.organizations;
create policy "Users can view their organizations"
on public.organizations for select
using (
  exists (
    select 1
    from public.organization_memberships m
    where m.org_id = organizations.id
      and m.user_id = auth.uid()
  )
);

-- organization_memberships: users can view their org memberships
drop policy if exists "Users can view their org memberships" on public.organization_memberships;
create policy "Users can view their org memberships"
on public.organization_memberships for select
using (auth.uid() = user_id);

-- invites: invitee can view their invite
drop policy if exists "Invitee can view invite" on public.invites;
create policy "Invitee can view invite"
on public.invites for select
using (invitee_email = auth.jwt()->>'email');

-- 8) TRIGGERS

-- 8a) Create a profile row when a new auth.users row appears
create or replace function public.handle_new_user_profile()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, full_name, active_role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    null  -- no active role by default; backend will set last active or default
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_profile on auth.users;
create trigger on_auth_user_created_profile
after insert on auth.users
for each row execute function public.handle_new_user_profile();

-- 8b) Assign default global role (student) at signup
create or replace function public.handle_new_user_roles()
returns trigger
language plpgsql
security definer
as $$
begin
  if not exists (
    select 1 from public.user_roles ur
    where ur.user_id = new.id and ur.role = 'student'
  ) then
    insert into public.user_roles(user_id, role) values (new.id, 'student');
  end if;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_roles on auth.users;
create trigger on_auth_user_created_roles
after insert on auth.users
for each row execute function public.handle_new_user_roles();