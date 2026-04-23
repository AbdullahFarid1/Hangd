"""Improvement-over-time trend lines.

If PGN games have parseable Date headers, compute rolling error rates per
month / quarter / N-game window. Otherwise return an empty frame so callers
can gracefully skip the chart.
"""

from __future__ import annotations

import pandas as pd

from .. import config


def _parse_date(value: str | None) -> pd.Timestamp | None:
    if not value or value in ("?", "????.??.??"):
        return None
    try:
        return pd.to_datetime(value.replace(".??", ".01").replace("??.", "01."), errors="coerce")
    except Exception:
        return None


def errors_over_time(
    player_view_df: pd.DataFrame,
    *,
    freq: str = "M",
) -> pd.DataFrame:
    """Per-period error counts and per-game error rate.

    `freq` is any pandas offset alias ('M' for month, 'Q' for quarter,
    'W' for week).
    """
    if "date" not in player_view_df.columns or player_view_df.empty:
        return pd.DataFrame()

    df = player_view_df.copy()
    df["timestamp"] = df["date"].apply(_parse_date)
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return pd.DataFrame()

    df["period"] = df["timestamp"].dt.to_period(freq).dt.to_timestamp()

    games_per_period = (
        df.drop_duplicates(["color_file", "game_id"])
        .groupby("period")
        .size()
        .rename("games")
    )
    errors_per_period = (
        df[df["error_type"].isin(config.ERROR_TYPES)]
        .groupby(["period", "error_type"])
        .size()
        .unstack(fill_value=0)
    )
    for col in config.ERROR_TYPES:
        if col not in errors_per_period.columns:
            errors_per_period[col] = 0
    errors_per_period["total_errors"] = errors_per_period[list(config.ERROR_TYPES)].sum(axis=1)

    out = errors_per_period.join(games_per_period, how="outer").fillna(0)
    out["errors_per_game"] = out["total_errors"] / out["games"].replace(0, pd.NA)
    return out.reset_index().sort_values("period")
