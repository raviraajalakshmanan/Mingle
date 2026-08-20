-- Koodal — initial schema (docs/03-lld.md §2)
-- Privacy model: `responses` / `response_slots` have NO client SELECT policy, so
-- the anon/authed client key can never read anyone's budget or availability.
-- All writes and all aggregation go through the FastAPI backend (service role),
-- which bypasses RLS but enforces its own authorization in code.

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table if not exists profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  email        text,
  created_at   timestamptz not null default now()
);

create table if not exists catchups (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references profiles(id) on delete cascade,
  title        text not null,
  message      text,
  location     text,
  type         text not null check (type in ('casual','food','activity','outing','trip')),
  link_token   text not null unique,
  result_token text not null unique,
  deadline     timestamptz,
  status       text not null default 'open' check (status in ('open','closed')),
  created_at   timestamptz not null default now()
);
create index if not exists catchups_owner_idx on catchups (owner_id);

create table if not exists slots (
  id          uuid primary key default gen_random_uuid(),
  catchup_id  uuid not null references catchups(id) on delete cascade,
  starts_at   timestamptz not null,
  ends_at     timestamptz not null,
  label       text,
  sort_order  int not null default 0,
  check (ends_at > starts_at)
);
create index if not exists slots_catchup_idx on slots (catchup_id);

create table if not exists responses (
  id           uuid primary key default gen_random_uuid(),
  catchup_id   uuid not null references catchups(id) on delete cascade,
  name         text not null,
  companions   int  not null default 0 check (companions >= 0),
  budget_min   int  not null check (budget_min >= 0),
  budget_max   int  not null check (budget_max >= budget_min),
  contribution int  not null default 0 check (contribution >= 0),
  interests    text[] not null default '{}',
  created_at   timestamptz not null default now()
);
create index if not exists responses_catchup_idx on responses (catchup_id);

create table if not exists response_slots (
  response_id uuid not null references responses(id) on delete cascade,
  slot_id     uuid not null references slots(id) on delete cascade,
  primary key (response_id, slot_id)
);

-- ---------------------------------------------------------------------------
-- Row-Level Security (defense in depth)
-- ---------------------------------------------------------------------------

alter table profiles       enable row level security;
alter table catchups       enable row level security;
alter table slots          enable row level security;
alter table responses      enable row level security;
alter table response_slots enable row level security;

-- profiles: a user may read/update only their own row.
create policy profiles_self_select on profiles
  for select using (auth.uid() = id);
create policy profiles_self_update on profiles
  for update using (auth.uid() = id);

-- catchups: owner may read their own catch-ups.
create policy catchups_owner_select on catchups
  for select using (auth.uid() = owner_id);

-- slots: readable only if the parent catch-up belongs to the caller.
create policy slots_owner_select on slots
  for select using (
    exists (select 1 from catchups c where c.id = slots.catchup_id and c.owner_id = auth.uid())
  );

-- responses / response_slots: NO policies on purpose.
-- With RLS enabled and no SELECT/INSERT policy, the anon/authed client key gets
-- zero rows and cannot write. Only the service role (FastAPI) can touch them.
-- (Do NOT add client policies here — that would break invariant I1.)
