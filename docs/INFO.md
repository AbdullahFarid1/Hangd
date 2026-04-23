# Hangd — project journal

> Living document. Updated after every phase. If you (future Abdullah, future
> me, future contributor) want to know what this project is, why it's shaped
> the way it is, and what state it's in — start here.

For the *roadmap* see [PLAN.md](PLAN.md).
For *how to run things* see the top-level [README.md](../README.md).

---

## What this project is, in one paragraph

Hangd analyses your own chess games to tell you exactly *where* you keep losing points and *what* to study. You give it your games as PGN files (one for the games you played as White, one for the games as Black). It runs Stockfish on every move, classifies each move as ok / inaccuracy / mistake / blunder by centipawn drop, joins those errors with the actual game results, and surfaces patterns: which phase of the game you're weakest in, which exact moves you keep blundering, which openings underperform, which endgame types you keep losing. Currently a Python CLI; the in-progress Phase B + C will wrap the same engine in a Supabase + Next.js web app where players upload PGNs and get a beautiful dashboard.

---

## Folder map

```
DBA Chess Project/
├── README.md                          One-page user-facing readme
├── docs/
│   ├── PLAN.md                        Approved phased implementation plan
│   └── INFO.md                        ← you are here
├── requirements.txt                   Python deps (chess, pandas, supabase, dotenv)
├── .gitignore
├── backend/                           Python package — analytics + worker
│   ├── __init__.py                    Forces UTF-8 stdout (Windows fix)
│   ├── config.py                      All paths, depths, thresholds; env-overridable
│   ├── pgn_ingest.py                  PGN parsing helpers (always via python-chess)
│   ├── engine_analysis.py             Stockfish wrapper. Resume + auto-migration.
│   ├── build_player_view.py           Joins move errors with PGN game results.
│   ├── analytics_core.py              Phase × error × outcome math + prescription.
│   ├── insight_bundler.py             Bundles all insights into one JSON for the dashboard.
│   ├── supabase_client.py             Service-role Supabase client (worker only).
│   ├── worker.py                      Long-running poller for analysis_jobs table.
│   ├── cli.py                         Unified CLI (pipeline / build-analytics / insight).
│   ├── .env.example                   Template for backend/.env (Supabase keys).
│   └── insights/                      One module per metric:
│       ├── repeat_offenders.py        Recurring (move_number, san) errors.
│       ├── position_features.py       Queens-on / opposite-castling / tension flags.
│       ├── endgame_types.py           Material-signature win rates.
│       ├── openings_extended.py       Repertoire stats with avg cp_drop per opening.
│       ├── move_heatmap.py            Move-number × error count + stability score.
│       └── time_trend.py              Rolling per-period error rate.
├── scripts/                           Legacy CLI entry points (Run-button friendly)
│   ├── Clean.py                       Engine analysis (alias of cli pipeline first half)
│   ├── Calculation.py                 Builds player view + per-color phase counts
│   ├── Analytics.py                   Combined-color prescription
│   ├── Analyticswb.py                 Separate White / Black prescriptions
│   └── Openings.py                    Opening repertoire stats
├── data/
│   ├── pgn/                           Input PGN files (your games)
│   │   ├── MAF13-white.pgn            ~6,106 games as White
│   │   └── MAF13-black.pgn            ~6,090 games as Black
│   └── outputs/                       Generated CSVs (gitignored)
│       ├── games_with_errors.csv      ★ The 760k-row engine-output CSV. Precious.
│       ├── games_with_errors.csv.legacy.bak  Auto-created on schema migration.
│       ├── games_with_errors_only_imb.csv
│       ├── errors_imb_with_result_and_phase_player_only.csv
│       ├── games_raw.csv
│       ├── opening_stats_by_color.csv
│       ├── error_move_repeats_by_move_number_ranked.csv
│       ├── phase_error_winrates.csv
│       ├── phase_error_winrates_player_only.csv
│       ├── white_phase_error_counts.csv
│       └── black_phase_error_counts.csv
├── supabase/
│   ├── config.toml                    Local Supabase CLI config
│   └── migrations/
│       └── 0001_init.sql              Schema + RLS + storage bucket
└── web/                               (Phase C) Next.js dashboard
    └── …                              See "Phase C" section below
```

---

## Phase A — Analytics engine (status: ✅ DONE)

**What we did and why**

The original code was 5 standalone scripts at the repo root that all referenced each other implicitly through filenames. There was also a missing glue script: `Analytics.py` and `Analyticswb.py` both read `errors_imb_with_result_and_phase_player_only.csv`, but no script in the repo produced it. The pipeline literally couldn't run end-to-end on a fresh checkout.

Changes:

- **Mate-score clamping (`backend/config.py`, `backend/engine_analysis.py`)** — Stockfish reports forced mates as ±100,000 cp. The original `cp_drop = best - played` would register a mate-in-3 vs mate-in-1 swing as a 99,000-cp blunder, polluting every chart. We now clamp every score to ±2,000 cp before computing the drop, and tag positions where either side of the diff was a mate score with a separate `mate_swing` boolean so they can be filtered out of error analytics.
- **Engine lifecycle** — wrapped Stockfish in `with engine: …` so a crash never leaks a process. The original code had no exception handling around `popen_uci` ↔ `engine.quit()`.
- **Resume support + auto-migration (`backend/engine_analysis.py`)** — The user has ~12,200 games. A full re-analysis is hours of CPU time. `analyse_pgn_to_csv(..., resume=True)` skips already-analysed `(game_id, color_file)` pairs by reading the existing CSV. If the existing CSV is from an older schema (no `fen_before` / `mate_swing` / `phase` columns), it's first backed up to `*.legacy.bak` and rewritten with the new columns filled with safe defaults. Idempotent.
- **Built the missing glue (`backend/build_player_view.py`)** — joins the per-move errors CSV with each game's PGN headers (Result, ECO, ratings, Date), filters down to *the player's* moves only, computes phase from move number, computes outcome from the player's perspective. This is the file the prescription scripts always wanted.
- **Centralised config (`backend/config.py`)** — every path, every depth, every threshold, every phase boundary is here and env-overridable. The Stockfish path defaults to Abdullah's local install but can be overridden with `STOCKFISH_PATH=…` for the deployed worker.
- **Deduplicated analytics (`backend/analytics_core.py`)** — `Analytics.py` and `Analyticswb.py` had ~80% identical code. Both now import from `analytics_core.py`. The deprecated `groupby.apply` returning a tuple is gone (was triggering pandas FutureWarning).
- **Six new insight modules** — repeat-offender detection (matches the existing `error_move_repeats_by_move_number_ranked.csv` exactly), position feature fingerprints, endgame-type material-signature win rates, opening repertoire stats with avg cp drop, move-number heatmap + stability score, time-trend by month.
- **Folder restructure** — `data/pgn/` for inputs, `data/outputs/` for generated CSVs, `scripts/` for legacy run-button wrappers, `backend/` for the package. `web/`, `supabase/`, `docs/` for the upcoming phases.
- **Windows console UTF-8** — `backend/__init__.py` reconfigures `sys.stdout` to UTF-8 so the prescription text (which uses `→`, `≈`, `–`) doesn't crash on cp1252 default consoles.
- **Deleted dead code** — `Prescription.py` (empty file), `tempCodeRunnerFile.python` (editor scratch).

**What we kept** the legacy script names (`Clean.py`, `Calculation.py`, …) live on as thin wrappers in `scripts/` so anyone with muscle memory or a VS Code Run button keeps working.

**Verification status** All five legacy scripts produce numerically identical results to the original code (we kept the existing 760k-row games_with_errors.csv as the input, ran the legacy wrappers, and the numbers match). The new CLI's `python -m backend.cli insight repeats` reproduces row-for-row the existing `error_move_repeats_by_move_number_ranked.csv` (top hit: White, blunder, 4. Bg5, 37 occurrences). End-to-end smoke test passes.

---

## Phase B — Web app shell (status: 🚧 IN PROGRESS — code complete, awaiting your Supabase project)

**What we built**

- `supabase/migrations/0001_init.sql` — Postgres schema + RLS policies + storage bucket. Tables: `profiles`, `uploads`, `analysis_jobs`, `games`, `moves`, `insights_summary`. Auto-create profile on signup. RLS so every user only sees their own rows. Realtime publication for `analysis_jobs` so the dashboard can subscribe to live progress.
- `supabase/config.toml` — local Supabase CLI config (port 54321 API, 54322 Postgres, 54323 Studio).
- `backend/supabase_client.py` — singleton Supabase Python client authed as `service_role`. Reads `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` from `backend/.env`.
- `backend/insight_bundler.py` — turns the moves CSV + player-view CSV + PGN paths into a single JSON blob the dashboard consumes in one query. Avoids multi-query waterfalls in the frontend.
- `backend/worker.py` — the long-running poller. Claims one job atomically (status='queued' → 'running' with a WHERE clause that guards against races), downloads the user's PGN(s) from Storage, runs `analyse_pgn_iter` from the Phase A engine (so we share *all* the correctness fixes), persists rows to `games` and `moves` in batches of 200, updates `progress_*` fields after each move so the frontend can animate live, then computes the dashboard payload and stores it in `insights_summary`. On any exception the job is marked `failed` with the error message.
- `backend/.env.example` — template for the worker's environment.

**Why a Python worker, not a Vercel function**

Stockfish at depth 8-10 takes minutes to hours per upload (multiplied by however many games are in the PGN). Vercel functions cap at 60 s on the Pro plan. WASM Stockfish in an edge function has terrible performance. The clean answer is a long-running Python process — locally during dev, and on Render / Railway / Hetzner when deployed. The worker authenticates as `service_role` to bypass RLS so it can write into any user's tables.

**What you have to do for Phase B to actually run**

1. Sign up at https://supabase.com and create a new project.
2. From the dashboard → Settings → API, grab your project URL, `anon` key, and `service_role` key.
3. Copy `backend/.env.example` to `backend/.env` and paste in `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. (You'll also paste the same URL + the `anon` key into `web/.env.local` for Phase C.)
4. Apply the schema: install the Supabase CLI (`npm i -g supabase`), then from the project root run `supabase db push`. *Or*, simpler: open `supabase/migrations/0001_init.sql` in the Supabase dashboard's SQL editor and click Run.
5. From the venv: `python -m backend.worker` to start the worker. It logs `[worker] starting; polling every 5s` and waits for jobs.

---

## Phase C — Frontend (status: ✅ CODE COMPLETE — awaiting `npm install` + Supabase keys)

**What we built** (all under `web/`, 46 files total)

- **Config**: `package.json` with Next.js 14.2, React 18, Tailwind 3.4, Framer Motion 11, `@supabase/ssr` + `@supabase/supabase-js`, `react-chessboard`, `recharts`, `next-themes`, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`, `tailwindcss-animate`. `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `next.config.js`, `.eslintrc.json`, `.env.example` (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY).
- **Styling foundation**: `app/globals.css` defines light/dark CSS variables using a walnut + cream chess-board palette. Tailwind config exposes error-type accents (`blunder`, `mistake`, `inaccuracy`, `ok`) and chess accents (`walnut`, `cream`). `ThemeProvider` wraps everything via `next-themes`.
- **Auth**: `middleware.ts` protects `/app/**` and redirects logged-in users away from `/login`. `lib/supabase/server.ts` (Server Components + Route Handlers) and `lib/supabase/client.ts` (browser / Client Components) are the two Supabase entry points. `app/login/page.tsx` + `AuthForm.tsx` implement email/password sign-in and sign-up on top of Supabase Auth.
- **Data layer**: `lib/types.ts` mirrors the Python `insight_bundler.py` payload shape so the frontend is fully typed end-to-end. `lib/queries.ts` wraps every read the app needs (`listJobs`, `getJob`, `getInsights`, `getMoveByPly`, `getCurrentUser`).
- **UI primitives** in `components/ui/`: `Button`, `Card` (+ Header/Title/Content/Footer), `Input`, `Label`, `Progress` (Framer-Motion-animated bar). Minimal shadcn-style so we don't pull the full shadcn CLI.
- **Chess-themed components** in `components/`:
  - `EvalBar` — vertical logistic-mapped cp → bar fraction, animated via Framer Motion spring.
  - `MiniBoard` — `react-chessboard` styled with the walnut/cream palette; supports board flip and highlight squares.
  - `PhaseRing` — three concentric SVG rings (opening / middlegame / endgame) that stroke-dash animate to each phase's win rate on mount.
  - `ErrorHeatmap` — move-number × error-type grid with per-cell intensity + staggered entrance animation.
  - `RepeatOffenderCard` — one recurring mistake with side badge + count + error-type chip.
  - `OpeningWinRateBar` — horizontal win/draw/loss stacked bar with opening name, ECO, total games, win rate.
  - `ProgressLive` — subscribes to Supabase Realtime `postgres_changes` on the job row; redirects to the results page when `status='done'`.
  - `UploadDropzone` — drag-and-drop with Framer Motion hover animation, filename chip with clear-X.
  - `KpiTile` — animated stat card used across the dashboard strip.
  - `Nav` — sticky app-shell nav with dark-mode toggle and sign-out.
- **Pages** (under `app/`):
  - `/` — landing. Hero + 6-feature grid. Links to `/login`.
  - `/login` — auth UI (shared for sign-in and sign-up).
  - `/app` — dashboard hub. Lists past jobs with per-job progress bar and status badge. Empty-state CTA when no uploads yet.
  - `/app/upload` — two drag-drop zones (White + Black), SHA-256 hash in the browser, upload to Supabase Storage, insert `uploads` rows, insert `analysis_jobs` row, redirect to the job page.
  - `/app/jobs/[id]` — Realtime-driven progress. Three animated stat tiles (games / moves / percent). Auto-redirects to `/app/analyses/[id]` on completion.
  - `/app/analyses/[id]` — the centrepiece. KPI strip, PhaseRing + prescription side-by-side, ErrorHeatmap, top 6 repeat offenders, quick-links to the deep dives, per-color summary cards.
  - `/app/analyses/[id]/openings` — full opening repertoire split by color.
  - `/app/analyses/[id]/repeats` — every repeat-offender mistake.
  - `/app/analyses/[id]/positions/[ply]` — board + eval bar + verdict for a specific move.
  - `/app/settings` — user profile info (placeholder for future Lichess / Chess.com linking).
  - `/not-found` — themed 404.

**Verification status** All files compile conceptually (TS config, imports, JSX shape) and `package.json` + `tsconfig.json` + `.eslintrc.json` are valid JSON. True runtime verification requires `npm install` (downloads ~400 MB of deps) which we deliberately leave to the user. No Supabase project has been created yet — the app will render shells and error on Auth calls until you plug in real credentials.

**What you have to do for Phase C to actually run**

1. Create a Supabase project (Phase B step 1).
2. Run the migration (Phase B step 4).
3. `cd web && npm install` — takes ~1-2 min.
4. `cp .env.example .env.local` inside `web/`, fill in `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (and optionally `SUPABASE_SERVICE_ROLE_KEY` if you later need admin operations from server components).
5. `npm run dev` and open http://localhost:3000.
6. In a separate terminal with the venv active: `python -m backend.worker`.

---

## Phase D — Deployment (status: not yet started)

- Frontend → Vercel
- Worker → Render or Railway background worker (~$7/mo) with Stockfish bundled in the Docker image
- DB / Auth / Storage → Supabase

---

## Things that are deliberately *not* in this project

- We don't auto-pull games from the user's Lichess / Chess.com account *yet* — manual PGN upload only. Lichess has an excellent export API that's a candidate for Phase D+.
- We don't run our own openings book lookup — we use the `ECO` + `ECOUrl` headers chess.com / lichess put in the PGN. If a game has neither header, opening name will be blank.
- We don't classify *tactics* (pins, forks, skewers) per blunder. The position-feature fingerprint is a coarse proxy. A future insight module could use a tactical motif detector.

## Known issues / things to revisit

- The position-features insight (`insights/position_features.py`) requires `fen_before` on the moves CSV. The legacy 760k-row CSV doesn't have it (the auto-migration backfills with empty strings). To get position fingerprints for old games you'd need to re-run engine analysis. New games will work out of the box.
- `pandas` 3.0 is installed; if any deprecation surfaces we'll need to update.
- The worker's progress update after every 10 moves is "good enough" for a 5-second poll interval but writes a *lot* of rows for the Realtime publication to push. We may need to throttle further once we see real traffic.

---

## Memory aid for me (Claude) — small notes only

- `data/outputs/games_with_errors.csv` is 40 MB / 759,955 rows. Never delete it casually; it represents hours of compute.
- The user's `STOCKFISH_PATH` is `C:/Users/Abdullah Farid/Downloads/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe`.
- Default Python in shell is 3.14; the project's `.venv/` runs 3.14 with chess + pandas + supabase installed. Always activate the venv first (`source .venv/Scripts/activate`).
