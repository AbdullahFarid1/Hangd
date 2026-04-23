"""Detect mistakes the player makes over and over.

Two complementary views:
  * `by_move_number`: identical (side, error_type, move_number, san) across
    multiple games — matches the format of the existing
    `error_move_repeats_by_move_number_ranked.csv`.
  * `by_opening`: same SAN keeps blundering inside the same opening (ECO).
"""

from __future__ import annotations

import pandas as pd

from .. import config


def by_move_number(player_df: pd.DataFrame, min_count: int = 2) -> pd.DataFrame:
    """Repeated errors grouped by (side, error_type, move_number, san)."""
    df = player_df[player_df["error_type"].isin(config.ERROR_TYPES)]

    grouped = (
        df.groupby(["side", "error_type", "move_number", "san"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    grouped = grouped[grouped["count"] >= min_count]
    grouped["move_san"] = grouped.apply(
        lambda r: f"{int(r['move_number'])}. {r['san']}", axis=1
    )

    error_rank = {"blunder": 0, "mistake": 1, "inaccuracy": 2}
    grouped["__rank"] = grouped["error_type"].map(error_rank).fillna(99)

    return (
        grouped.sort_values(["__rank", "count"], ascending=[True, False])
        .drop(columns="__rank")
        [["side", "error_type", "move_number", "san", "move_san", "count"]]
        .reset_index(drop=True)
    )


def by_opening(player_df: pd.DataFrame, min_count: int = 2) -> pd.DataFrame:
    """Repeated errors grouped by (eco, opening_name, san, error_type)."""
    if "eco" not in player_df.columns:
        return pd.DataFrame(columns=["eco", "opening_name", "san", "error_type", "count"])

    df = player_df[player_df["error_type"].isin(config.ERROR_TYPES)]
    grouped = (
        df.groupby(["eco", "opening_name", "san", "error_type"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    grouped = grouped[grouped["count"] >= min_count]
    return grouped.sort_values(["count"], ascending=False).reset_index(drop=True)
