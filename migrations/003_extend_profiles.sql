-- Extend profiles table with additional fields

-- Safe guards in case columns already exist
do $$
begin
  -- phone
  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='phone'
  ) then
    alter table public.profiles add column phone text;
  end if;

  -- address fields
  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='address'
  ) then
    alter table public.profiles add column address text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='city'
  ) then
    alter table public.profiles add column city text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='state'
  ) then
    alter table public.profiles add column state text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='country'
  ) then
    alter table public.profiles add column country text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='postal_code'
  ) then
    alter table public.profiles add column postal_code text;
  end if;

  -- personal/bio
  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='date_of_birth'
  ) then
    alter table public.profiles add column date_of_birth date;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='bio'
  ) then
    alter table public.profiles add column bio text;
  end if;

  -- links/media
  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='avatar_url'
  ) then
    alter table public.profiles add column avatar_url text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='website'
  ) then
    alter table public.profiles add column website text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='linkedin_url'
  ) then
    alter table public.profiles add column linkedin_url text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='twitter_url'
  ) then
    alter table public.profiles add column twitter_url text;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='github_url'
  ) then
    alter table public.profiles add column github_url text;
  end if;

  -- completion and timestamps
  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='profile_completion_percentage'
  ) then
    alter table public.profiles add column profile_completion_percentage int default 0;
  end if;

  if not exists (
    select 1 from information_schema.columns 
    where table_schema='public' and table_name='profiles' and column_name='updated_at'
  ) then
    alter table public.profiles add column updated_at timestamp default now();
  end if;
end $$;


