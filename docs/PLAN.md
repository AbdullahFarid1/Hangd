# Hangd — implementation plan

> Working copy of the approved plan, kept inside the repo so it travels with the code. The original lives at `~/.claude/plans/ok-now-ill-tell-glittery-token.md`.

## Why this exists

A personal CLI pipeline that takes two PGN files (your White games and your Black games), runs Stockfish, and writes CSVs is being rebuilt into a public web app. Players upload their PGNs, get back a polished dashboard showing where in the game they err (opening / middlegame / endgame), what mistakes repeat, and what to study. Personal-tool first, but architected from day one for multi-user public deployment.

Three phases: **A** fix and extend the analytics, **B** add the web app shell with Supabase + a long-running analysis worker, **C** build the styled dashboard frontend.

---

## Phase A — Analytics engine (DONE ✅)

**Correctness fixes**
- `Clean.py` mate-score handling — clamp to ±2000 cp before computing `cp_drop`; tag mate-related drops as `mate_swing` instead of inflating blunder counts.
- Engine wrapped in a context manager so a crash doesn't leak Stockfish processes.
- Resume support: `--resume` skips already-analysed `(game_id, color_file)` pairs.
- Auto-migration: legacy CSVs without the new columns are upgraded in place (with a `.legacy.bak` backup) on first resume.
- The missing glue script (`build_player_view.py`) that joins error rows with PGN game results — the file the prescription scripts expected but no script in the original repo produced.
- Deduplicated `Analytics.py` and `Analyticswb.py` into `analytics_core.py` shared by both (and the future web worker).
- Centralised config (paths, depths, thresholds, phase boundaries) in `backend/config.py`, all env-overridable.
- UTF-8 stdout reconfigure so prescription text doesn't crash Windows cp1252.
- Deleted `Prescription.py` (empty) and `tempCodeRunnerFile.python` (editor scratch).

**New insight modules** (`backend/insights/`)
- `repeat_offenders.py` — identical (side, error_type, move_number, san) patterns recurring across games.
- `position_features.py` — feature flags per error position (queens-on, opposite-side castling, central tension, material imbalance) → "60 % of your blunders happen with queens on" type fingerprint.
- `endgame_types.py` — material-signature classification (`KRP_v_KR`, `KBN_v_K`, …) with per-signature win rate.
- `openings_extended.py` — repertoire stats with avg `cp_drop` per opening + most common error.
- `move_heatmap.py` — per-`move_number` × error-type counts; plus a stability score (avg absolute cp swing).
- `time_trend.py` — rolling per-period error rate when PGN `Date` headers are present.

**Folder restructure**
```
backend/      Python package (analytics engine)
scripts/      legacy run-button wrappers (Clean.py, Calculation.py, ...)
data/pgn/     input PGN files
data/outputs/ generated CSVs (incl. the 760k-row games_with_errors.csv)
docs/         this file + future architecture notes
web/          (Phase C) Next.js dashboard
supabase/     (Phase B) SQL migrations + local config
```

---

## Phase B — Web app shell

### Stack

- **Backend API**: Next.js Route Handlers for read paths, Supabase RLS for security boundaries.
- **Analysis worker**: standalone Python process (`backend/worker.py`) that polls Supabase's `analysis_jobs` table, runs Stockfish through the same `engine_analysis.py` the CLI uses, and writes results back. Lives outside Vercel because Stockfish needs minutes-to-hours per upload.
- **Database / Auth / Storage**: Supabase (Postgres + Auth + Storage buckets for PGNs).
- **Realtime progress**: Supabase Realtime subscription on `analysis_jobs` rows → frontend animates live without polling.

### Supabase schema

```
profiles            (id uuid pk = auth.uid, display_name, lichess_handle, chesscom_handle, ...)
uploads             (id, user_id, color_file enum('white','black'), storage_path, sha256, ...)
analysis_jobs       (id, upload_id, status, progress_games_done, progress_games_total,
                     progress_moves_done, progress_moves_total, error_message, ...)
games               (id, user_id, upload_id, color_file, white, black, result, date, white_elo, black_elo,
                     eco, opening_name, ply_count)
moves               (id, game_id, ply, move_number, side, san, uci, fen_before,
                     best_cp, played_cp, cp_drop, error_type, mate_swing, phase)
insights_summary    (user_id, generated_at, payload jsonb)   -- denormalized for dashboard reads
```

Row-level security on every user-owned table (`auth.uid() = user_id`). Storage bucket `pgns` is private; signed URLs only.

### Upload → analysis flow

1. User drags PGN(s) onto the upload page → file uploaded to Supabase Storage; `uploads` row inserted.
2. Server action creates an `analysis_jobs` row with status `queued`.
3. Python worker polls `analysis_jobs`, claims one with a transactional update, downloads the PGN, runs `engine_analysis.analyse_pgn_iter`, persists rows in batches, updates `progress_*` fields after each move.
4. Frontend dashboard subscribes via Supabase Realtime → progress bar animates live → on `done`, redirects to results page.

### What you (the user) still have to do for Phase B

The code can't create a Supabase project for you. After I finish the files, you do this once:

1. Sign up / log in at https://supabase.com and create a new project.
2. From its dashboard → Settings → API, copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL` and `SUPABASE_URL`
   - `anon` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key (worker only, never ship to browser) → `SUPABASE_SERVICE_ROLE_KEY`
3. Paste them into `web/.env.local` and `backend/.env` (templates supplied).
4. Apply the migration: `supabase db push` from the project root (after installing the Supabase CLI), or copy `supabase/migrations/0001_init.sql` into the Supabase SQL editor.
5. Create the Storage bucket: SQL editor or dashboard → "pgns" bucket, **private**.

---

## Phase C — Frontend

### Stack
Next.js 14 (App Router) · TypeScript · Tailwind · Framer Motion · 21st.dev components (manually copied; no MCP wiring required) · react-chessboard · Recharts · lucide-react · Supabase JS SDK · next-themes.

### Pages
| Route | Purpose |
|---|---|
| `/` | Landing — hero + sample dashboard preview + upload CTA |
| `/login` | Supabase Auth UI |
| `/app` | Dashboard hub — list of past analyses, "new analysis" button |
| `/app/upload` | Drag-and-drop White PGN + Black PGN, eval depth picker |
| `/app/jobs/[id]` | Live progress page (animated bar, current game/move) |
| `/app/analyses/[id]` | Main results dashboard |
| `/app/analyses/[id]/openings` | Opening repertoire deep dive |
| `/app/analyses/[id]/repeats` | Repeat-offender mistakes with embedded boards |
| `/app/analyses/[id]/positions/[ply]` | Single-position reviewer (board + eval bar + best move) |
| `/app/settings` | Profile, linked accounts |

### Key components
- `<EvalBar />` — vertical animated centipawn bar, pulses on swings.
- `<MiniBoard fen={...} />` — react-chessboard with Framer Motion piece transitions.
- `<PhaseRing />` — three concentric arcs (opening / middle / end), animated draw on mount.
- `<ErrorHeatmap />` — move-number × error-type grid, cells animate in sequentially.
- `<RepeatOffenderCard />` — one repeated mistake: board + your move + best move + count.
- `<OpeningWinRateBar />` — horizontal bar with win/draw/loss split.
- `<ProgressLive />` — Realtime-driven progress component with animated counter.
- `<UploadDropzone />` — drag-drop PGN, validates `.pgn` extension client-side.

### Visual direction
- Dark mode default (chess analysis is night-owl territory); light toggle persisted via `next-themes`.
- Wood-board accent palette (cream + walnut warm tones, not full skeuomorphism).
- Framer Motion on: page transitions, dashboard card stagger-in, eval bar, board piece moves on best-move replay, KPI counters that tick up.

### What you still have to do for Phase C
1. `cd web && npm install` (downloads Next.js, React, Tailwind, Framer Motion, etc.)
2. Fill in `web/.env.local` with the same Supabase keys you set for the worker.
3. `npm run dev` and visit http://localhost:3000.
4. Run the Python worker in a second terminal: `python -m backend.worker` (after `pip install -r requirements.txt` in the venv).

---

## Phase D — Deployment (later)

- **Frontend**: Vercel (free tier).
- **Worker**: Render or Railway background worker (~$7/mo), or a $5 Hetzner VPS for full control. Bundle Stockfish in the Docker image.
- **DB / Auth / Storage**: Supabase free tier covers personal use; Pro ($25/mo) when public.

---

## What success looks like

- **End of A** — `python -m backend.cli pipeline --white ... --black ... --resume` runs to completion with no mate-score false-positive blunders, restarts cleanly if killed, and `python -m backend.cli insight repeats` matches the existing `error_move_repeats_by_move_number_ranked.csv` exactly. (Done.)
- **End of B** — local stack (`supabase start` + `npm run dev` + `python -m backend.worker`) runs together; uploading a PGN through the UI creates `uploads` + `analysis_jobs` rows, the worker picks the job up within ~5 s, the job's `progress_moves_done` increments live in Postgres, and the frontend's Realtime subscription shows it counting up.
- **End of C** — full flow from landing → login → upload → live progress → results dashboard works in a fresh browser; dashboard renders eval bar, phase ring, heatmap, repeat-offender cards, and opening table with animations; dark-mode toggle persists; tab-navigable; Chrome / Firefox / Safari at desktop and mobile widths.
