"""Stockfish wrapper that turns a PGN file into per-move evaluation rows.

Key fixes vs the original Clean.py:
  * Engine is context-managed so a crash never leaks a Stockfish process.
  * Mate evaluations are clamped before the cp_drop diff so mate-in-N moves
    don't get bucketed as 99,000 cp blunders.
  * Resume support: rows for already-analyzed (game_id, color_file) tuples
    are skipped if an existing CSV is passed in.
  * Exposes a generator-style API (`analyse_pgn_iter`) the worker can hook
    into for live progress updates, plus the original CSV-writing helper for
    the legacy CLI flow.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

import chess
import chess.engine

from . import config
from .pgn_ingest import GameRecord, count_games_and_moves, iter_games


# --------------------------------------------------
# Data shape — one row per analysed ply
# --------------------------------------------------

MOVE_FIELDS = (
    "game_id",
    "color_file",
    "move_number",
    "ply",
    "side",
    "san",
    "uci",
    "fen_before",
    "best_cp",
    "played_cp",
    "cp_drop",
    "error_type",
    "mate_swing",
    "phase",
)


@dataclass
class MoveRow:
    game_id: int
    color_file: str
    move_number: int
    ply: int
    side: str
    san: str
    uci: str
    fen_before: str
    best_cp: int
    played_cp: int
    cp_drop: int
    error_type: str
    mate_swing: bool
    phase: str


@dataclass
class ProgressEvent:
    games_done: int
    games_total: int
    moves_done: int
    moves_total: int


# --------------------------------------------------
# Score handling
# --------------------------------------------------

def _clamped_score(info: dict, mover: chess.Color) -> tuple[int, bool]:
    """Return (clamped_cp, is_mate_score).

    `mover` is whose POV we want — always the side that made (or is about to
    make) the move under analysis.
    """
    raw = info["score"].pov(mover).score(mate_score=config.MATE_SCORE)
    is_mate = abs(raw) >= config.MATE_SCORE - 1000  # safe band around mate
    clamped = max(-config.EVAL_CLAMP, min(config.EVAL_CLAMP, raw))
    return clamped, is_mate


# --------------------------------------------------
# Engine lifecycle
# --------------------------------------------------

def _open_engine() -> chess.engine.SimpleEngine:
    creationflags = 0
    try:
        # CREATE_NO_WINDOW on Windows so Stockfish doesn't flash a console.
        import subprocess
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    except Exception:
        pass

    engine = chess.engine.SimpleEngine.popen_uci(
        str(config.STOCKFISH_PATH),
        timeout=20,
        **({"creationflags": creationflags} if creationflags else {}),
    )
    engine.configure({
        "Threads": config.ENGINE_THREADS,
        "Hash": config.ENGINE_HASH_MB,
    })
    return engine


# --------------------------------------------------
# Resume support
# --------------------------------------------------

def _already_analysed_games(csv_path: Path, color_label: str) -> set[int]:
    """Read game_ids already present in csv_path for the given color file."""
    if not csv_path.exists():
        return set()
    seen: set[int] = set()
    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("color_file") == color_label:
                try:
                    seen.add(int(row["game_id"]))
                except (KeyError, ValueError):
                    continue
    return seen


def _ensure_schema(csv_path: Path) -> None:
    """Migrate an older games_with_errors.csv to the current schema in place.

    Old runs of Clean.py wrote CSVs without fen_before / mate_swing / phase.
    Appending new rows with the new columns would silently corrupt the file.
    Instead, on resume we backfill missing columns once (fen_before='',
    mate_swing=False, phase computed from move_number) and rewrite the file.
    """
    if not csv_path.exists():
        return

    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        existing_fields = list(reader.fieldnames or [])
        if existing_fields == list(MOVE_FIELDS):
            return  # already current
        rows = list(reader)

    missing = [f for f in MOVE_FIELDS if f not in existing_fields]
    if not missing:
        # Same columns, different order — just rewrite with the canonical order.
        pass
    else:
        print(f"Migrating {csv_path.name}: adding columns {missing}")

    backup = csv_path.with_suffix(csv_path.suffix + ".legacy.bak")
    if not backup.exists():
        csv_path.replace(backup)
        print(f"Backed up legacy CSV to {backup.name}")
    else:
        # Backup already exists from a prior partial migration — don't clobber.
        csv_path.unlink()

    with backup.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        with csv_path.open("w", newline="", encoding="utf-8") as out_fh:
            writer = csv.DictWriter(out_fh, fieldnames=MOVE_FIELDS)
            writer.writeheader()
            for row in reader:
                if "fen_before" not in row:
                    row["fen_before"] = ""
                if "mate_swing" not in row:
                    row["mate_swing"] = False
                if "phase" not in row or not row.get("phase"):
                    try:
                        row["phase"] = config.assign_phase(int(row.get("move_number", 0)))
                    except (TypeError, ValueError):
                        row["phase"] = ""
                # Drop any extra columns we don't recognise.
                writer.writerow({k: row.get(k, "") for k in MOVE_FIELDS})

    print(f"Migrated {csv_path.name} to current schema.")


# --------------------------------------------------
# Core analysis loop
# --------------------------------------------------

def _analyse_one_game(
    engine: chess.engine.SimpleEngine,
    record: GameRecord,
    color_label: str,
) -> Iterator[MoveRow]:
    board = record.game.board()

    for ply, move in enumerate(record.game.mainline_moves(), start=1):
        mover = board.turn

        info_best = engine.analyse(board, chess.engine.Limit(depth=config.DEPTH_BEST))
        best_cp, best_was_mate = _clamped_score(info_best, mover)

        san = board.san(move)
        uci = move.uci()
        fen_before = board.fen()

        board.push(move)

        info_played = engine.analyse(board, chess.engine.Limit(depth=config.DEPTH_PLAYED))
        played_cp, played_was_mate = _clamped_score(info_played, mover)

        cp_drop = best_cp - played_cp
        # Negative drops happen when the played move is *better* than the
        # depth-N "best" — keep the sign so debugging is honest, but classify
        # only positive drops as errors.
        label = config.classify_delta(cp_drop) if cp_drop > 0 else "ok"
        mate_swing = best_was_mate or played_was_mate

        side = "White" if mover == chess.WHITE else "Black"
        move_number = (ply + 1) // 2
        phase = config.assign_phase(move_number)

        yield MoveRow(
            game_id=record.meta.game_id,
            color_file=color_label,
            move_number=move_number,
            ply=ply,
            side=side,
            san=san,
            uci=uci,
            fen_before=fen_before,
            best_cp=best_cp,
            played_cp=played_cp,
            cp_drop=cp_drop,
            error_type=label,
            mate_swing=mate_swing,
            phase=phase,
        )


def analyse_pgn_iter(
    pgn_path: str | Path,
    color_label: str,
    *,
    skip_game_ids: Iterable[int] = (),
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> Iterator[MoveRow]:
    """Analyse a PGN, yielding one MoveRow per move.

    The web worker uses this directly so it can stream progress back to the
    client and persist rows incrementally. The CLI wraps this in a CSV writer.
    """
    skip = set(skip_game_ids)
    total_games, total_moves = count_games_and_moves(pgn_path)

    games_done = 0
    moves_done = 0

    with _open_engine() as engine:
        for record in iter_games(pgn_path):
            games_done += 1
            if record.meta.game_id in skip:
                # Still count its moves toward the progress denominator so
                # the bar doesn't jump backwards on resume.
                moves_done += record.meta.ply_count
                if on_progress:
                    on_progress(ProgressEvent(games_done, total_games, moves_done, total_moves))
                continue

            for row in _analyse_one_game(engine, record, color_label):
                moves_done += 1
                yield row
                if on_progress and moves_done % 10 == 0:
                    on_progress(ProgressEvent(games_done, total_games, moves_done, total_moves))

    if on_progress:
        on_progress(ProgressEvent(games_done, total_games, moves_done, total_moves))


# --------------------------------------------------
# CSV writer for the legacy CLI flow
# --------------------------------------------------

def analyse_pgn_to_csv(
    pgn_path: str | Path,
    color_label: str,
    output_csv: str | Path,
    *,
    resume: bool = False,
    print_progress: bool = True,
) -> int:
    """Append (or create) the move-level CSV for one PGN.

    Returns the number of rows written.
    """
    output_csv = Path(output_csv)
    if resume:
        _ensure_schema(output_csv)
    skip = _already_analysed_games(output_csv, color_label) if resume else set()

    file_exists = output_csv.exists()
    write_header = not file_exists or not resume

    if write_header and file_exists:
        # Fresh run — overwrite. Use 'w'.
        mode = "w"
    elif file_exists:
        mode = "a"
    else:
        mode = "w"

    rows_written = 0

    def _print(event: ProgressEvent) -> None:
        if not print_progress:
            return
        pct = (event.moves_done / event.moves_total * 100) if event.moves_total else 100.0
        print(
            f"\r[{color_label}] Games: {event.games_done}/{event.games_total} | "
            f"Moves: {event.moves_done}/{event.moves_total} ({pct:5.1f}%)",
            end="",
            flush=True,
        )

    with output_csv.open(mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MOVE_FIELDS)
        if mode == "w":
            writer.writeheader()

        for row in analyse_pgn_iter(
            pgn_path,
            color_label,
            skip_game_ids=skip,
            on_progress=_print if print_progress else None,
        ):
            writer.writerow(asdict(row))
            rows_written += 1

    if print_progress:
        print()
        if skip:
            print(f"[{color_label}] Resumed — skipped {len(skip)} already-analysed game(s).")
        print(f"[{color_label}] Wrote {rows_written} new move row(s) to {output_csv}")

    return rows_written
