"""Build the joined per-error view that the analytics modules consume.

Takes the move-level errors CSV and joins each row with its game's PGN
result (so we can compute win rates per error type / phase / opening).

Output columns:
    game_id, color_file, side, move_number, ply, san, uci,
    error_type, mate_swing, result, outcome, phase, eco, opening_name

This file replaces the missing glue step that produced
`errors_imb_with_result_and_phase_player_only.csv` in the original repo.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config
from .pgn_ingest import iter_games, result_from_perspective


# --------------------------------------------------
# Game-meta lookup table (built by reading PGNs once)
# --------------------------------------------------

def _build_game_meta_table(pgn_paths: dict[str, Path]) -> pd.DataFrame:
    """Return a DataFrame with one row per (color_file, game_id) → headers."""
    records = []
    for color_label, pgn_path in pgn_paths.items():
        for record in iter_games(pgn_path):
            records.append({
                "color_file": color_label,
                "game_id": record.meta.game_id,
                "result": record.meta.result,
                "white_elo": record.meta.white_elo,
                "black_elo": record.meta.black_elo,
                "eco": record.meta.eco,
                "opening_name": record.meta.opening_name,
                "date": record.meta.date,
            })
    return pd.DataFrame.from_records(records)


def _player_color_for_file(color_file: str) -> str:
    """white_file ⇒ user is White, black_file ⇒ user is Black."""
    if color_file.startswith("white"):
        return "White"
    if color_file.startswith("black"):
        return "Black"
    raise ValueError(f"Unknown color_file label: {color_file!r}")


# --------------------------------------------------
# Public API
# --------------------------------------------------

def build_player_view(
    games_with_errors_csv: str | Path,
    pgn_paths: dict[str, str | Path],
    output_csv: str | Path,
) -> pd.DataFrame:
    """Produce the player-only I/M/B-with-result-and-phase CSV.

    Parameters
    ----------
    games_with_errors_csv :
        Output of ``engine_analysis.analyse_pgn_to_csv`` for both colors.
    pgn_paths :
        Mapping of color_file label → path to that color's PGN. Used to look
        up each game's PGN headers (Result, ECO, ratings, ...).
    output_csv :
        Where to write the joined CSV.
    """
    df = pd.read_csv(games_with_errors_csv)

    # 1) Keep only player moves (player as White from white_file, etc.) and
    #    drop everything that isn't a real error.
    player_color = df["color_file"].map(_player_color_for_file)
    df = df[df["side"] == player_color].copy()
    df = df[df["error_type"].isin(config.ERROR_TYPES)]

    # 2) Drop mate-swing rows from the win-rate analysis — they're flagged
    #    separately and would otherwise dominate the "blunder" bucket in
    #    games where a forced mate exists.
    if "mate_swing" in df.columns:
        df["mate_swing"] = df["mate_swing"].astype(bool)
        df = df[~df["mate_swing"]]

    # 3) Re-stamp phase from move_number using the current config — keeps
    #    re-runs consistent with whatever phase boundaries are configured now.
    df["phase"] = df["move_number"].apply(config.assign_phase)

    # 4) Join in each game's PGN headers.
    pgn_paths_resolved = {label: Path(p) for label, p in pgn_paths.items()}
    meta = _build_game_meta_table(pgn_paths_resolved)
    df = df.merge(meta, on=["color_file", "game_id"], how="left")

    # 5) Compute outcome from the player's perspective.
    df["outcome"] = df.apply(
        lambda r: result_from_perspective(
            r["result"], _player_color_for_file(r["color_file"])
        ),
        axis=1,
    )

    keep_cols = [
        "game_id",
        "color_file",
        "side",
        "move_number",
        "ply",
        "san",
        "uci",
        "error_type",
        "result",
        "outcome",
        "phase",
        "eco",
        "opening_name",
        "white_elo",
        "black_elo",
        "date",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols]

    output_csv = Path(output_csv)
    df.to_csv(output_csv, index=False)
    print(f"Wrote player-view CSV ({len(df)} rows) → {output_csv}")
    return df
