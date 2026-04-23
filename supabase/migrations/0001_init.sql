-- ============================================================
-- Hangd — initial schema
-- ============================================================
-- Tables, enums, and RLS for the personal chess analytics app.
-- Apply with: `supabase db push` (Supabase CLI) or paste into the
-- SQL editor of your project at https://supabase.com.
-- ============================================================

-- ----- Enums -------------------------------------------------

create type public.color_file_kind as enum ('white_file', 'black_file');

create type public.job_status as enum ('queued', 'running', 'done', 'failed');

create type public.error_label as enum ('ok', 'inaccuracy', 'mistake', 'blunder');

create type public.phase_kind as enum ('opening', 'middlegame', 'endgame');


-- ----- Profiles ----------------------------------------------

create table public.profiles (
    id uuid primary key references auth.users on delete cascade,
    display_name text,
    lichess_handle text,
    chesscom_handle text,
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles: owner read"
    on public.profiles for select
    using (auth.uid() = id);

create policy "profiles: owner write"
    on public.profiles for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

create policy "profiles: owner insert"
    on public.profiles for insert
    with check (auth.uid() = id);


-- Auto-create a profile row on signup.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, display_name)
    values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', new.email));
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();


-- ----- Uploads -----------------------------------------------

create table public.uploads (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users on delete cascade,
    color_file public.color_file_kind not null,
    storage_path text not null,
    original_filename text,
    sha256 text,
    bytes bigint,
    uploaded_at timestamptz not null default now()
);

create index uploads_user_idx on public.uploads (user_id);
create unique index uploads_user_sha_idx
    on public.uploads (user_id, color_file, sha256)
    where sha256 is not null;

alter table public.uploads enable row level security;

create policy "uploads: owner read"
    on public.uploads for select
    using (auth.uid() = user_id);

create policy "uploads: owner insert"
    on public.uploads for insert
    with check (auth.uid() = user_id);

create policy "uploads: owner delete"
    on public.uploads for delete
    using (auth.uid() = user_id);


-- ----- Analysis jobs -----------------------------------------

create table public.analysis_jobs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users on delete cascade,
    upload_white uuid references public.uploads on delete set null,
    upload_black uuid references public.uploads on delete set null,
    status public.job_status not null default 'queued',
    progress_games_done integer not null default 0,
    progress_games_total integer not null default 0,
    progress_moves_done integer not null default 0,
    progress_moves_total integer not null default 0,
    error_message text,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz not null default now()
);

create index analysis_jobs_user_idx on public.analysis_jobs (user_id);
create index analysis_jobs_status_idx on public.analysis_jobs (status);

alter table public.analysis_jobs enable row level security;

create policy "jobs: owner read"
    on public.analysis_jobs for select
    using (auth.uid() = user_id);

create policy "jobs: owner insert"
    on public.analysis_jobs for insert
    with check (auth.uid() = user_id);

-- The worker runs as service_role and bypasses RLS, so no policies
-- needed for its writes.


-- ----- Games -------------------------------------------------

create table public.games (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users on delete cascade,
    job_id uuid not null references public.analysis_jobs on delete cascade,
    color_file public.color_file_kind not null,
    pgn_game_id integer not null,           -- index of the game inside its PGN file
    white text,
    black text,
    result text,
    date text,
    white_elo integer,
    black_elo integer,
    eco text,
    opening_name text,
    ply_count integer not null default 0,
    created_at timestamptz not null default now(),
    unique (job_id, color_file, pgn_game_id)
);

create index games_user_idx on public.games (user_id);
create index games_job_idx on public.games (job_id);

alter table public.games enable row level security;

create policy "games: owner read"
    on public.games for select
    using (auth.uid() = user_id);


-- ----- Moves -------------------------------------------------

create table public.moves (
    id bigserial primary key,
    user_id uuid not null references auth.users on delete cascade,
    game_id uuid not null references public.games on delete cascade,
    ply integer not null,
    move_number integer not null,
    side text not null,
    san text not null,
    uci text not null,
    fen_before text,
    best_cp integer,
    played_cp integer,
    cp_drop integer,
    error_type public.error_label not null default 'ok',
    mate_swing boolean not null default false,
    phase public.phase_kind not null,
    unique (game_id, ply)
);

create index moves_user_idx on public.moves (user_id);
create index moves_game_idx on public.moves (game_id);
create index moves_error_idx on public.moves (user_id, error_type)
    where error_type <> 'ok';

alter table public.moves enable row level security;

create policy "moves: owner read"
    on public.moves for select
    using (auth.uid() = user_id);


-- ----- Insights summary --------------------------------------
-- Denormalized JSON blob the dashboard reads in one query. The worker
-- computes this last and overwrites for the latest job per user.

create table public.insights_summary (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users on delete cascade,
    job_id uuid not null references public.analysis_jobs on delete cascade,
    payload jsonb not null,
    generated_at timestamptz not null default now(),
    unique (job_id)
);

create index insights_user_idx on public.insights_summary (user_id);
create index insights_user_recent_idx
    on public.insights_summary (user_id, generated_at desc);

alter table public.insights_summary enable row level security;

create policy "insights: owner read"
    on public.insights_summary for select
    using (auth.uid() = user_id);


-- ----- Realtime publication ----------------------------------
-- Frontend subscribes to job progress; everything else is fine.

alter publication supabase_realtime add table public.analysis_jobs;


-- ----- Storage bucket ----------------------------------------
-- A private bucket for raw PGN uploads.

insert into storage.buckets (id, name, public)
values ('pgns', 'pgns', false)
on conflict (id) do nothing;

create policy "pgns: owner select"
    on storage.objects for select
    using (bucket_id = 'pgns' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "pgns: owner insert"
    on storage.objects for insert
    with check (bucket_id = 'pgns' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "pgns: owner delete"
    on storage.objects for delete
    using (bucket_id = 'pgns' and auth.uid()::text = (storage.foldername(name))[1]);


-- ----- Data API role grants ----------------------------------
-- Required when the project's "Automatically expose new tables" setting is OFF
-- (recommended for security). RLS policies above control row-level access;
-- these grants only let the API roles see the tables exist at all.

grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to authenticated, service_role;
grant usage, select on all sequences in schema public to authenticated, service_role;
grant execute on all functions in schema public to authenticated, service_role;

-- Make any future tables in this schema inherit the same grants.
alter default privileges in schema public
    grant select, insert, update, delete on tables to authenticated, service_role;
alter default privileges in schema public
    grant usage, select on sequences to authenticated, service_role;
alter default privileges in schema public
    grant execute on functions to authenticated, service_role;
