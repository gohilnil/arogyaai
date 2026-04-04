-- ArogyaAI Production Database Schema v3.0
-- Run this in your Supabase SQL editor
-- All tables use UUID primary keys and Row Level Security (RLS)

-- ── Extensions ──────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ── Users ────────────────────────────────────────────────────────
create table if not exists users (
  id               uuid default gen_random_uuid() primary key,
  email            text unique not null,
  name             text,
  hashed_password  text,
  is_premium       boolean default false,
  plan             text default 'free',        -- 'free' | 'pro' | 'elite'
  referral_code    text unique default upper(substr(md5(random()::text), 1, 8)),
  referred_by      uuid references users(id) on delete set null,
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

create index if not exists idx_users_email on users(email);
create index if not exists idx_users_plan on users(plan);

-- ── Subscriptions ────────────────────────────────────────────────
create table if not exists subscriptions (
  id                   uuid default gen_random_uuid() primary key,
  user_id              uuid references users(id) on delete cascade,
  plan                 text not null,           -- 'pro' | 'elite'
  status               text default 'active',   -- 'active' | 'cancelled' | 'expired'
  razorpay_order_id    text,
  razorpay_payment_id  text,
  amount_inr           integer,
  started_at           timestamptz default now(),
  expires_at           timestamptz,
  cancelled_at         timestamptz,
  created_at           timestamptz default now()
);

create index if not exists idx_subs_user on subscriptions(user_id, status);
create index if not exists idx_subs_payment on subscriptions(razorpay_payment_id);

-- ── Referrals ────────────────────────────────────────────────────
create table if not exists referrals (
  id               uuid default gen_random_uuid() primary key,
  referrer_id      uuid references users(id) on delete cascade,
  referred_user_id uuid references users(id) on delete cascade,
  bonus_credited   boolean default false,
  created_at       timestamptz default now()
);

create index if not exists idx_referrals_referrer on referrals(referrer_id);

-- ── Health Profiles ──────────────────────────────────────────────
create table if not exists health_profiles (
  id           uuid default gen_random_uuid() primary key,
  user_id      uuid references users(id) on delete cascade unique,
  age          integer,
  gender       text,
  blood_group  text,
  height_cm    integer,
  weight_kg    integer,
  conditions   text[] default '{}',
  allergies    text[] default '{}',
  medications  text[] default '{}',
  language     text default 'en',
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

create index if not exists idx_health_profiles_user on health_profiles(user_id);

-- ── Conversations ────────────────────────────────────────────────
create table if not exists conversations (
  id           uuid default gen_random_uuid() primary key,
  user_id      uuid references users(id) on delete cascade,
  message      text,
  reply        text,
  severity     text default 'mild',
  health_score integer,
  needs_doctor boolean default false,
  body_system  text,
  created_at   timestamptz default now()
);

create index if not exists idx_conversations_user on conversations(user_id, created_at desc);
create index if not exists idx_conversations_severity on conversations(severity);

-- ── Streaks ──────────────────────────────────────────────────────
create table if not exists streaks (
  id             uuid default gen_random_uuid() primary key,
  user_id        uuid references users(id) on delete cascade unique,
  current_streak integer default 1,
  longest_streak integer default 1,
  last_active    date default current_date,
  updated_at     timestamptz default now()
);

create index if not exists idx_streaks_user on streaks(user_id);

-- ── Query Usage (Freemium Limits) ────────────────────────────────
create table if not exists query_usage (
  id          uuid default gen_random_uuid() primary key,
  user_id     uuid references users(id) on delete cascade,
  query_date  date default current_date,
  count       integer default 1,
  created_at  timestamptz default now(),
  unique(user_id, query_date)
);

create index if not exists idx_query_usage_user_date on query_usage(user_id, query_date);

-- ── Family Members ───────────────────────────────────────────────
create table if not exists family_members (
  id         uuid default gen_random_uuid() primary key,
  owner_id   uuid references users(id) on delete cascade,
  name       text not null,
  relation   text,
  age        integer,
  gender     text,
  conditions text[] default '{}',
  created_at timestamptz default now()
);

create index if not exists idx_family_owner on family_members(owner_id);

-- ── Health Reports ───────────────────────────────────────────────
create table if not exists health_reports (
  id         uuid default gen_random_uuid() primary key,
  user_id    uuid references users(id) on delete cascade,
  period     text default 'weekly',
  content    text,
  created_at timestamptz default now()
);

create index if not exists idx_health_reports_user on health_reports(user_id, created_at desc);

-- ── Notifications ────────────────────────────────────────────────
create table if not exists notifications (
  id         uuid default gen_random_uuid() primary key,
  user_id    uuid references users(id) on delete cascade,
  type       text,   -- 'health_tip' | 'streak' | 'upgrade' | 'report_ready' | 'system'
  title      text,
  body       text,
  read       boolean default false,
  created_at timestamptz default now()
);

create index if not exists idx_notif_user on notifications(user_id, read, created_at desc);

-- ── Analytics Events (Privacy-First) ────────────────────────────
create table if not exists analytics_events (
  id         uuid default gen_random_uuid() primary key,
  user_id    uuid references users(id) on delete set null,
  event      text not null,
  properties jsonb default '{}',
  session_id text,
  created_at timestamptz default now()
);

create index if not exists idx_analytics_event on analytics_events(event, created_at desc);
create index if not exists idx_analytics_user on analytics_events(user_id, created_at desc);

-- ── Row Level Security ───────────────────────────────────────────
alter table users            enable row level security;
alter table subscriptions    enable row level security;
alter table referrals        enable row level security;
alter table health_profiles  enable row level security;
alter table conversations    enable row level security;
alter table streaks          enable row level security;
alter table query_usage      enable row level security;
alter table family_members   enable row level security;
alter table health_reports   enable row level security;
alter table notifications    enable row level security;
alter table analytics_events enable row level security;

-- RLS Policies — users can only access their own data
create policy "Users own their profile"
  on users for all using (auth.uid() = id);

create policy "Users own their subscriptions"
  on subscriptions for all using (auth.uid() = user_id);

create policy "Users own their health profile"
  on health_profiles for all using (auth.uid() = user_id);

create policy "Users own their conversations"
  on conversations for all using (auth.uid() = user_id);

create policy "Users own their streaks"
  on streaks for all using (auth.uid() = user_id);

create policy "Users own their query usage"
  on query_usage for all using (auth.uid() = user_id);

create policy "Users own their family"
  on family_members for all using (auth.uid() = owner_id);

create policy "Users own their health reports"
  on health_reports for all using (auth.uid() = user_id);

create policy "Users own their notifications"
  on notifications for all using (auth.uid() = user_id);

-- Service role bypasses RLS (backend uses service role key)
-- The above policies protect the Supabase JavaScript SDK (anon key)
-- Our backend uses the service_role key which bypasses all RLS

-- ── Useful Views ─────────────────────────────────────────────────
create or replace view user_dashboard_summary as
select
  u.id,
  u.email,
  u.name,
  u.is_premium,
  u.plan,
  hp.age,
  hp.gender,
  hp.conditions,
  hp.language,
  s.current_streak,
  s.longest_streak,
  (select count(*) from conversations c where c.user_id = u.id) as total_conversations,
  (select max(created_at) from conversations c where c.user_id = u.id) as last_active
from users u
left join health_profiles hp on hp.user_id = u.id
left join streaks s on s.user_id = u.id;
