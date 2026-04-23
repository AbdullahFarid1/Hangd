"""Centralised configuration.

Every value is overridable via environment variable so the same code runs
locally for the CLI and inside the deployed worker.
"""

from __future__ import annotations

import os
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STOCKFISH_PATH = Path(
    os.environ.get(
        "STOCKFISH_PATH",
        "C:/Users/Abdullah Farid/Downloads/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe",
    )
)

# Generated CSVs live under data/outputs by default; raw PGNs under data/pgn.
DATA_DIR = Path(os.environ.get("HANGD_DATA_DIR", str(PROJECT_ROOT / "data" / "outputs")))
PGN_DIR = Path(os.environ.get("HANGD_PGN_DIR", str(PROJECT_ROOT / "data" / "pgn")))


# --------------------------------------------------
# Engine settings
# --------------------------------------------------

DEPTH_BEST = int(os.environ.get("HANGD_DEPTH_BEST", "10"))
DEPTH_PLAYED = int(os.environ.get("HANGD_DEPTH_PLAYED", "8"))
ENGINE_THREADS = int(os.environ.get("HANGD_ENGINE_THREADS", "4"))
ENGINE_HASH_MB = int(os.environ.get("HANGD_ENGINE_HASH_MB", "512"))

# Mate scores are reported as ±MATE_SCORE by the engine so that a forced mate
# beats every regular evaluation. The raw delta is meaningless as a centipawn
# loss (a mate-in-1 vs mate-in-3 should not register as a 99,000 cp blunder),
# so we clamp every score into a finite window before computing cp_drop.
MATE_SCORE = 100_000
EVAL_CLAMP = int(os.environ.get("HANGD_EVAL_CLAMP", "2000"))


# --------------------------------------------------
# Move quality thresholds (centipawn drop, after clamping)
# --------------------------------------------------

THRESHOLD_INACCURACY = 50
THRESHOLD_MISTAKE = 100
THRESHOLD_BLUNDER = 300


# --------------------------------------------------
# Phase boundaries (move number, inclusive upper bound)
# --------------------------------------------------

OPENING_LAST_MOVE = int(os.environ.get("HANGD_OPENING_LAST_MOVE", "15"))
MIDDLEGAME_LAST_MOVE = int(os.environ.get("HANGD_MIDDLEGAME_LAST_MOVE", "40"))


# --------------------------------------------------
# CSV filenames (relative to DATA_DIR unless absolute)
# --------------------------------------------------

CSV_GAMES_RAW = "games_raw.csv"
CSV_GAMES_WITH_ERRORS = "games_with_errors.csv"
CSV_ERRORS_ONLY_IMB = "games_with_errors_only_imb.csv"
CSV_PLAYER_ONLY = "errors_imb_with_result_and_phase_player_only.csv"
CSV_WHITE_PHASE_COUNTS = "white_phase_error_counts.csv"
CSV_BLACK_PHASE_COUNTS = "black_phase_error_counts.csv"
CSV_OPENING_STATS = "opening_stats_by_color.csv"
CSV_REPEAT_OFFENDERS = "error_move_repeats_by_move_number_ranked.csv"
CSV_PHASE_WINRATES = "phase_error_winrates.csv"
CSV_PHASE_WINRATES_PLAYER = "phase_error_winrates_player_only.csv"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def data_path(name: str) -> Path:
    """Resolve a CSV name (or any path) against DATA_DIR."""
    p = Path(name)
    return p if p.is_absolute() else DATA_DIR / p


def pgn_path(name: str) -> Path:
    """Resolve a PGN filename against PGN_DIR (or pass-through if absolute)."""
    p = Path(name)
    return p if p.is_absolute() else PGN_DIR / p


ERROR_TYPES = ("inaccuracy", "mistake", "blunder")
PHASE_ORDER = ("opening", "middlegame", "endgame")


def assign_phase(move_number: int) -> str:
    if move_number <= OPENING_LAST_MOVE:
        return "opening"
    if move_number <= MIDDLEGAME_LAST_MOVE:
        return "middlegame"
    return "endgame"


def classify_delta(cp_drop: int) -> str:
    """Bucket a clamped centipawn drop into a move-quality label."""
    if cp_drop < THRESHOLD_INACCURACY:
        return "ok"
    if cp_drop < THRESHOLD_MISTAKE:
        return "inaccuracy"
    if cp_drop < THRESHOLD_BLUNDER:
        return "mistake"
    return "blunder"
