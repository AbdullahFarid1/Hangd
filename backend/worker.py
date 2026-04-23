"""Long-running analysis worker.

Polls the Supabase `analysis_jobs` table for queued jobs, claims one
atomically, downloads the user's PGN(s) from Storage, runs the same
`engine_analysis.analyse_pgn_iter` the CLI uses, persists rows in
batches as it goes, computes the dashboard JSON, and marks the job done.

Run with:
    python -m backend.worker

Environment (backend/.env):
    SUPABASE_URL              https://<project>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY <secret service role key — server only>
    HANGD_WORKER_POLL_SECS    poll interval (default 5)
    HANGD_WORKER_BATCH_SIZE   moves per DB insert (default 200)
    STOCKFISH_PATH            override engine binary path
"""

from __future__ import annotations

import os
import signal
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from . import config
from .build_player_view import build_player_view
from .engine_analysis import MOVE_FIELDS, MoveRow, analyse_pgn_iter
from .insight_bundler import build_payload
from .pgn_ingest import iter_games
from .supabase_client import get_client, storage_download

POLL_SECS = float(os.environ.get("HANGD_WORKER_POLL_SECS", "5"))
BATCH_SIZE = int(os.environ.get("HANGD_WORKER_BATCH_SIZE", "200"))

_stop = False


def _jsonify(value: Any) -> Any:
    """Coerce anything (pandas Timestamp, numpy scalars, NaN, …) into JSON-safe form.

    Why: supabase-py calls `json.dumps` on the payload, so any exotic type
    (pandas Timestamp, numpy.int64, NaN floats) breaks the insert. We walk
    the structure once and normalise every leaf to a primitive.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if (value == value and value not in (float("inf"), float("-inf"))) else None
    # Pandas / numpy scalars, Timestamps, Periods, etc. fall through to str().
    try:
        import numpy as np

        if isinstance(value, np.generic):
            scalar = value.item()
            return _jsonify(scalar)
    except ImportError:
        pass
    if pd.isna(value):
        return None
    return str(value)


def _install_signal_handlers() -> None:
    def _handle(signum, _frame):
        global _stop
        print(f"[worker] received signal {signum}, draining…", flush=True)
        _stop = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle)
        except (ValueError, OSError):
            # SIGTERM not available on Windows in some configs; ignore.
            pass


# --------------------------------------------------
# Job claim — atomic so two workers can't race
# --------------------------------------------------

def _claim_one_job() -> dict | None:
    sb = get_client()
    # Pick the oldest queued job (FIFO).
    resp = (
        sb.table("analysis_jobs")
        .select("*")
        .eq("status", "queued")
        .order("created_at")
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return None
    job = rows[0]
    # Try to flip status atomically. Postgres returns the updated row only
    # if the WHERE clause still matched, so we can detect lost races.
    update = (
        sb.table("analysis_jobs")
        .update({"status": "running", "started_at": "now()"})
        .eq("id", job["id"])
        .eq("status", "queued")
        .execute()
    )
    if not update.data:
        return None  # someone else got it
    return update.data[0]


# --------------------------------------------------
# Persisting games + moves in batches
# --------------------------------------------------

def _ensure_game_row(
    sb,
    user_id: str,
    job_id: str,
    color_file: str,
    pgn_meta,
) -> str:
    """Insert (or fetch) the game row, return its uuid."""
    existing = (
        sb.table("games")
        .select("id")
        .eq("job_id", job_id)
        .eq("color_file", color_file)
        .eq("pgn_game_id", pgn_meta.game_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    payload = {
        "user_id": user_id,
        "job_id": job_id,
        "color_file": color_file,
        "pgn_game_id": pgn_meta.game_id,
        "white": pgn_meta.white or None,
        "black": pgn_meta.black or None,
        "result": pgn_meta.result or None,
        "date": pgn_meta.date or None,
        "white_elo": pgn_meta.white_elo,
        "black_elo": pgn_meta.black_elo,
        "eco": pgn_meta.eco or None,
        "opening_name": pgn_meta.opening_name or None,
        "ply_count": pgn_meta.ply_count,
    }
    inserted = sb.table("games").insert(payload).execute()
    return inserted.data[0]["id"]


def _flush_moves(sb, batch: list[dict]) -> None:
    if not batch:
        return
    # supabase-py returns 4xx if an insert is too large; we keep batches small.
    sb.table("moves").insert(batch).execute()
    batch.clear()


# --------------------------------------------------
# Main per-job runner
# --------------------------------------------------

def _process_color(
    sb,
    job: dict,
    upload_id: str | None,
    color_file: str,
    workdir: Path,
    moves_csv_path: Path,
) -> int:
    """Download one PGN, analyse it, persist rows, return total moves done."""
    if not upload_id:
        return 0

    upload = (
        sb.table("uploads").select("*").eq("id", upload_id).single().execute().data
    )
    pgn_path = workdir / f"{color_file}.pgn"
    storage_download("pgns", upload["storage_path"], pgn_path)

    # game_id-in-PGN → uuid in `games` table.
    game_uuid_by_pgn_id: dict[int, str] = {}
    game_meta_by_id = {}
    for record in iter_games(pgn_path):
        game_meta_by_id[record.meta.game_id] = record.meta

    moves_batch: list[dict] = []
    csv_writer_rows: list[dict] = []
    moves_in_color = 0

    def _on_progress(event):
        # Cheap update; no need to do this every move.
        sb.table("analysis_jobs").update({
            "progress_games_done": event.games_done,
            "progress_games_total": event.games_total,
            "progress_moves_done": int(job.get("progress_moves_done", 0)) + event.moves_done,
            "progress_moves_total": int(job.get("progress_moves_total", 0)) + event.moves_total,
        }).eq("id", job["id"]).execute()

    for row in analyse_pgn_iter(pgn_path, color_file, on_progress=_on_progress):
        # Lazily ensure the game row exists.
        if row.game_id not in game_uuid_by_pgn_id:
            game_uuid_by_pgn_id[row.game_id] = _ensure_game_row(
                sb, job["user_id"], job["id"], color_file, game_meta_by_id[row.game_id]
            )

        moves_batch.append({
            "user_id": job["user_id"],
            "game_id": game_uuid_by_pgn_id[row.game_id],
            "ply": row.ply,
            "move_number": row.move_number,
            "side": row.side,
            "san": row.san,
            "uci": row.uci,
            "fen_before": row.fen_before,
            "best_cp": row.best_cp,
            "played_cp": row.played_cp,
            "cp_drop": row.cp_drop,
            "error_type": row.error_type,
            "mate_swing": row.mate_swing,
            "phase": row.phase,
        })
        # Append to a sidecar CSV too — feeds the insight bundler at the end.
        csv_writer_rows.append({k: getattr(row, k) for k in MOVE_FIELDS} | {"color_file": color_file})
        moves_in_color += 1

        if len(moves_batch) >= BATCH_SIZE:
            _flush_moves(sb, moves_batch)

    _flush_moves(sb, moves_batch)

    # Append (or create) the local sidecar CSV used for insight computation.
    pd.DataFrame(csv_writer_rows).to_csv(
        moves_csv_path,
        mode="a" if moves_csv_path.exists() else "w",
        header=not moves_csv_path.exists(),
        index=False,
    )

    return moves_in_color


def _run_job(job: dict) -> None:
    sb = get_client()
    print(f"[worker] running job {job['id']} for user {job['user_id']}", flush=True)

    with tempfile.TemporaryDirectory(prefix="hangd-job-") as td:
        workdir = Path(td)
        moves_csv_path = workdir / "moves.csv"

        try:
            _process_color(sb, job, job.get("upload_white"), "white_file", workdir, moves_csv_path)
            _process_color(sb, job, job.get("upload_black"), "black_file", workdir, moves_csv_path)

            # Build the dashboard payload and persist it.
            moves_df = pd.read_csv(moves_csv_path) if moves_csv_path.exists() else pd.DataFrame()
            pgn_paths = {
                color_file: str(workdir / f"{color_file}.pgn")
                for color_file in ("white_file", "black_file")
                if (workdir / f"{color_file}.pgn").exists()
            }

            if not moves_df.empty:
                player_view_path = workdir / "player_view.csv"
                player_view_df = build_player_view(moves_csv_path, pgn_paths, player_view_path)
                payload = build_payload(moves_df, player_view_df, pgn_paths)
            else:
                payload = {"empty": True}

            sb.table("insights_summary").upsert({
                "user_id": job["user_id"],
                "job_id": job["id"],
                "payload": _jsonify(payload),
            }, on_conflict="job_id").execute()

            sb.table("analysis_jobs").update({
                "status": "done",
                "finished_at": "now()",
            }).eq("id", job["id"]).execute()
            print(f"[worker] job {job['id']} done", flush=True)

        except Exception as exc:  # pragma: no cover — surfaces real failures
            traceback.print_exc()
            sb.table("analysis_jobs").update({
                "status": "failed",
                "error_message": f"{type(exc).__name__}: {exc}"[:1000],
                "finished_at": "now()",
            }).eq("id", job["id"]).execute()


# --------------------------------------------------
# Main loop
# --------------------------------------------------

class _Tee:
    """Mirror writes to multiple streams — so stdout goes to both the terminal and a log file."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
        return len(data)

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass


def _install_file_logging() -> None:
    """Tee stdout + stderr to data/logs/worker.log so nothing is lost when a window closes."""
    log_dir = Path(__file__).resolve().parents[1] / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "worker.log"
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = _Tee(sys.__stdout__, log_file)
    sys.stderr = _Tee(sys.__stderr__, log_file)
    print(f"[worker] logging to {log_path}", flush=True)


def main() -> None:
    _install_file_logging()
    _install_signal_handlers()
    print(f"[worker] starting; polling every {POLL_SECS}s", flush=True)

    while not _stop:
        try:
            job = _claim_one_job()
        except Exception:
            traceback.print_exc()
            time.sleep(POLL_SECS)
            continue

        if job is None:
            time.sleep(POLL_SECS)
            continue

        _run_job(job)

    print("[worker] stopped cleanly.", flush=True)


if __name__ == "__main__":
    main()
