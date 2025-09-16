-- Profiles (extends auth.users)
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  active_role text check (active_role in ('super_admin','school_admin','teacher','student')),
  created_at timestamp default now()
);

-- Schools
create table schools (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete cascade,
  created_at timestamp default now()
);

-- Memberships: user ↔ school roles (or solo if school_id is null)
create table memberships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  school_id uuid references schools(id) on delete cascade,
  role text check (role in ('super_admin','school_admin','teacher','student')),
  created_at timestamp default now()
);

-- Invitations
create table invites (
  id uuid primary key default gen_random_uuid(),
  inviter uuid references auth.users(id) on delete cascade,
  invitee_email text not null,
  role text not null check (role in ('school_admin','teacher','student')),
  school_id uuid references schools(id) on delete cascade,
  status text default 'pending', -- pending, accepted, rejected
  created_at timestamp default now()
);
-- Enable RLS
alter table profiles enable row level security;
alter table memberships enable row level security;
alter table schools enable row level security;
alter table invites enable row level security;

-- Profiles: only user can see/update their own profile
create policy "Users can view own profile"
on profiles for select
using (auth.uid() = id);

create policy "Users can update own profile"
on profiles for update
using (auth.uid() = id);

-- Memberships: users see their memberships
create policy "Users can view their memberships"
on memberships for select
using (auth.uid() = user_id);

-- Schools: users see schools they belong to
create policy "Users can view their schools"
on schools for select
using (
  exists (
    select 1 from memberships m
    where m.school_id = schools.id
    and m.user_id = auth.uid()
  )
);

-- Invites: invitee can view their invite
create policy "Invitee can view invite"
on invites for select
using (invitee_email = auth.jwt()->>'email');
-- Function to create a profile when a new auth.users record is created
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, full_name, active_role)
  values (
    new.id,
    -- Google/Email providers store metadata here
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    null -- no active role by default
  );
  return new;
end;
$$;
-- Trigger runs the function after a user is created
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();
