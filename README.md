# Hangd

> Find out exactly **where** you blunder.

A chess analytics pipeline that evaluates PGN games with Stockfish, classifies move quality, and surfaces the patterns you keep repeating. Two ways to use it:

- **CLI** (Phase A, fully working today) — point it at two PGN files and get CSV outputs + a textual prescription.
- **Web app** (Phases B + C, code complete; needs a Supabase project) — upload PGNs through a styled Next.js dashboard, watch live progress, browse an animated post-mortem.

## Table of contents

1. [What Hangd shows you](#what-hangd-shows-you)
2. [Project layout](#project-layout)
3. [Quickstart — CLI only](#quickstart--cli-only)
4. [Quickstart — full web stack](#quickstart--full-web-stack)
5. [Configuration knobs](#configuration-knobs)
6. [Documentation](#documentation)

---

## What Hangd shows you

For two PGN files (your White games and your Black games) the pipeline produces:

- Move-level error labels — `ok` / `inaccuracy` / `mistake` / `blunder`, with mate-swings flagged separately so they don't pollute blunder counts.
- Phase-wise error breakdowns — opening / middlegame / endgame.
- Win-rate stats per phase × error type.
- **Repeat-offender mistakes** — `(side, error_type, move_number, san)` patterns that recur across multiple games ("you blunder 4. Bg5 37 times").
- **Move-number heatmap** — when in the game you typically err.
- **Stability score** — average absolute centipawn swing per move.
- **Time-trend** — rolling per-period error rate when PGN `Date` headers are present.
- **Position fingerprint** — which structural features (queens on, opposite-side castling, central tension, …) correlate with your errors.
- **Endgame type breakdown** — material-signature (`KRP_v_KR`, `KBN_v_K`, …) win rates.
- **Opening repertoire** — per-opening win rate, avg cp drop, most common error.
- A textual training prescription based on your weakest phase.

---

## Project layout

```
DBA Chess Project/
├── README.md                ← you are here
├── docs/
│   ├── PLAN.md              Approved phased implementation plan
│   └── INFO.md              Living project journal ("operating manual")
├── requirements.txt         Python deps
├── .gitignore
├── backend/                 Python package — analytics engine + worker
│   ├── config.py            Every path / depth / threshold; env-overridable
│   ├── pgn_ingest.py        PGN parsing helpers (always via python-chess)
│   ├── engine_analysis.py   Stockfish wrapper. Resume + auto-migration.
│   ├── build_player_view.py Joins move errors with PGN game results.
│   ├── analytics_core.py    Phase × error × outcome math + prescription.
│   ├── insight_bundler.py   Bundles all insights into one JSON for the dashboard.
│   ├── supabase_client.py   Service-role Supabase client (worker only).
│   ├── worker.py            Long-running poller for analysis_jobs table.
│   ├── cli.py               Unified CLI (pipeline / build-analytics / insight).
│   ├── .env.example         Template for backend/.env (Supabase keys).
│   └── insights/            repeat_offenders, position_features, endgame_types,
│                            openings_extended, move_heatmap, time_trend.
├── scripts/                 Legacy CLI entry points (Run-button friendly)
│   ├── Clean.py             Engine analysis
│   ├── Calculation.py       Builds player view + per-color phase counts
│   ├── Analytics.py         Combined-color prescription
│   ├── Analyticswb.py       Separate White / Black prescriptions
│   └── Openings.py          Opening repertoire stats
├── data/
│   ├── pgn/                 Input PGN files
│   └── outputs/             Generated CSVs (gitignored; re-buildable)
├── supabase/
│   ├── config.toml          Local Supabase CLI config
│   └── migrations/
│       └── 0001_init.sql    Schema + RLS + storage bucket
└── web/                     Next.js 14 dashboard (App Router + Tailwind + Framer Motion)
    ├── app/                 Pages (landing, login, app/**)
    ├── components/          UI primitives + chess-themed components
    ├── lib/                 Supabase clients, typed queries, helpers
    ├── middleware.ts        Auth guard for /app/**
    ├── package.json
    ├── tailwind.config.ts
    └── …
```

---

## Quickstart — CLI only

```bash
# 1. Set up a venv and install Python deps
python -m venv .venv
source .venv/Scripts/activate      # Windows bash. On cmd: .venv\Scripts\activate.bat
pip install -r requirements.txt

# 2. Point STOCKFISH_PATH at your Stockfish binary (or edit backend/config.py)
export STOCKFISH_PATH="C:/path/to/stockfish.exe"

# 3. Drop your PGN files in data/pgn/
#    Defaults expect MAF13-white.pgn and MAF13-black.pgn

# 4. Full pipeline — engine analysis, all CSVs, prescription
python -m backend.cli pipeline --white MAF13-white.pgn --black MAF13-black.pgn --resume

# Or just one insight at a time from the existing analysis
python -m backend.cli insight repeats
python -m backend.cli insight heatmap
python -m backend.cli insight trend
python -m backend.cli insight fingerprint   # needs fen_before on newly-analysed games
```

Legacy run-button scripts under `scripts/` still work: `python scripts/Clean.py`, `python scripts/Analyticswb.py`, etc.

---

## Quickstart — full web stack

The web app needs a live Supabase project. You do this once.

### Step 1 — Create a Supabase project

1. Sign in at https://supabase.com and create a new project.
2. From **Settings → API** copy: your project URL, the `anon` key, and the `service_role` key.

### Step 2 — Run the migration

Two options:

- **Easy**: open `supabase/migrations/0001_init.sql` in your Supabase dashboard's SQL editor and click Run.
- **Proper**: install the Supabase CLI (`npm i -g supabase`), run `supabase link --project-ref <your-project-ref>`, then `supabase db push`.

This creates: `profiles`, `uploads`, `analysis_jobs`, `games`, `moves`, `insights_summary`, RLS policies, a `handle_new_user` trigger, and a private `pgns` storage bucket.

### Step 3 — Configure the worker

```bash
cp backend/.env.example backend/.env
# edit backend/.env — fill in SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
```

### Step 4 — Configure the frontend

```bash
cp web/.env.example web/.env.local
# edit web/.env.local — fill in NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY
cd web && npm install
```

### Step 5 — Run both processes

```bash
# Terminal 1 — the worker
source .venv/Scripts/activate
python -m backend.worker

# Terminal 2 — the frontend
cd web
npm run dev
```

Open http://localhost:3000. Sign up, upload two PGNs, watch the progress bar move in real time, then browse your dashboard.

### What the worker does

It polls the `analysis_jobs` table every 5 seconds, claims queued jobs atomically (guarding against two workers racing), downloads each PGN from Supabase Storage, runs Stockfish through `backend/engine_analysis.py` (the same code the CLI uses), writes rows to `games` and `moves` in batches of 200, updates `progress_*` fields as it goes so the frontend can animate live, and finally writes the dashboard JSON blob to `insights_summary`. On any exception the job is marked `failed` with the error text.

---

## Configuration knobs

All backend settings live in `backend/config.py` and are overridable via env var:

| Env var | Default | Meaning |
|---|---|---|
| `STOCKFISH_PATH` | hardcoded Windows path | Stockfish executable |
| `HANGD_DATA_DIR` | `data/outputs/` | Where generated CSVs go |
| `HANGD_PGN_DIR` | `data/pgn/` | Where input PGNs are read from |
| `HANGD_DEPTH_BEST` | `10` | Engine depth for pre-move eval |
| `HANGD_DEPTH_PLAYED` | `8` | Engine depth for post-move eval |
| `HANGD_ENGINE_THREADS` | `4` | Stockfish thread count |
| `HANGD_ENGINE_HASH_MB` | `512` | Stockfish hash table size (MB) |
| `HANGD_OPENING_LAST_MOVE` | `15` | Last move number considered "opening" |
| `HANGD_MIDDLEGAME_LAST_MOVE` | `40` | Last move number considered "middlegame" |
| `HANGD_EVAL_CLAMP` | `2000` | cp clamp window (mate scores clipped to this) |
| `HANGD_WORKER_POLL_SECS` | `5` | Worker poll interval |
| `HANGD_WORKER_BATCH_SIZE` | `200` | Moves per DB insert batch |
| `SUPABASE_URL` | — | Required for the worker |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Required for the worker (bypasses RLS) |

---

## Documentation

- **[docs/PLAN.md](docs/PLAN.md)** — the phased implementation plan (what / why / how).
- **[docs/INFO.md](docs/INFO.md)** — the living project journal. Every folder, every module, every decision.

## Repository

GitHub: `AbdullahFarid1/Hangd`.
