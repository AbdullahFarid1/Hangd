"""Move-number × error-type heatmap data.

Returns a long-form DataFrame the frontend can render directly:
    move_number | error_type | count

Bin granularity is per-move-number; collapse to bins client-side if needed.
"""

from __future__ import annotations

import pandas as pd

from .. import config


def heatmap(player_df: pd.DataFrame) -> pd.DataFrame:
    df = player_df[player_df["error_type"].isin(config.ERROR_TYPES)]
    grouped = (
        df.groupby(["move_number", "error_type"])
        .size()
        .reset_index(name="count")
    )
    return grouped.sort_values(["move_number", "error_type"]).reset_index(drop=True)


def stability_score(moves_df: pd.DataFrame) -> float:
    """Average absolute cp_drop over all analysed moves (lower = more stable)."""
    if "cp_drop" not in moves_df.columns or moves_df.empty:
        return 0.0
    return float(moves_df["cp_drop"].abs().mean())
