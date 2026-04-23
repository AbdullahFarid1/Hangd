"""Opening repertoire stats — extends the basic Openings.py output with
average cp drop and the most common error per opening.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .. import config
from ..pgn_ingest import iter_games, result_from_perspective


def _player_color_for_file(color_file: str) -> str:
    if color_file.startswith("white"):
        return "White"
    if color_file.startswith("black"):
        return "Black"
    raise ValueError(color_file)


def repertoire_stats(pgn_paths: dict[str, str | Path]) -> pd.DataFrame:
    """One row per (your_color, opening_name, eco) with win/loss/draw/total/win_rate.

    Mirrors the original Openings.py behavior but routes through python-chess
    rather than regex.
    """
    records = []
    for color_label, pgn_path in pgn_paths.items():
        you_are = _player_color_for_file(color_label)
        for record in iter_games(pgn_path):
            outcome = result_from_perspective(record.meta.result, you_are)
            records.append({
                "your_color": you_are,
                "opening_name": record.meta.opening_name,
                "eco": record.meta.eco,
                "outcome": outcome,
            })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame.from_records(records)
    df = df[df["outcome"].isin(["win", "loss", "draw"])]

    grouped = (
        df.groupby(["your_color", "opening_name", "eco", "outcome"])
        .size()
        .unstack(fill_value=0)
    )
    for col in ("win", "loss", "draw"):
        if col not in grouped.columns:
            grouped[col] = 0

    grouped["total"] = grouped[["win", "loss", "draw"]].sum(axis=1)
    grouped["win_rate"] = grouped["win"] / grouped["total"].replace(0, pd.NA)
    return grouped.reset_index().sort_values(
        ["your_color", "total"], ascending=[True, False]
    )


def stats_with_errors(
    pgn_paths: dict[str, str | Path],
    player_view_df: pd.DataFrame,
) -> pd.DataFrame:
    """Adds avg_cp_drop and most_common_error columns to repertoire_stats.

    Requires player_view_df to carry `cp_drop` (so this is best called with a
    join of `games_with_errors.csv` extended with opening info — which the
    CLI assembles for us).
    """
    base = repertoire_stats(pgn_paths)
    if base.empty or "cp_drop" not in player_view_df.columns:
        return base

    enriched = (
        player_view_df.groupby(["color_file", "opening_name", "eco"])
        .agg(
            avg_cp_drop=("cp_drop", "mean"),
            error_count=("error_type", "size"),
            most_common_error=(
                "error_type",
                lambda s: s.mode().iat[0] if not s.mode().empty else "",
            ),
        )
        .reset_index()
    )
    enriched["your_color"] = enriched["color_file"].map(_player_color_for_file)
    enriched = enriched.drop(columns="color_file")

    return base.merge(
        enriched,
        on=["your_color", "opening_name", "eco"],
        how="left",
    )
