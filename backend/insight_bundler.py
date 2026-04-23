"""Compute the single JSON blob the dashboard renders from.

Centralising this in one function means the frontend does one query
(`select payload from insights_summary where job_id = ?`) and gets
everything it needs. New insights get added here; the frontend doesn't
need an API change.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from . import analytics_core, config
from .insights import (
    endgame_types,
    move_heatmap,
    openings_extended,
    repeat_offenders,
    time_trend,
)


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON-friendly conversion (NaN → None, numpy types → Python natives)."""
    if df is None or df.empty:
        return []
    df = df.copy()
    for col in df.columns:
        # Datetime / Period columns must be stringified — supabase-py/json can't serialize them.
        if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_period_dtype(df[col]):
            df[col] = df[col].astype(str).where(df[col].notna(), None)
    return df.where(pd.notna(df), None).to_dict(orient="records")


def build_payload(
    moves_df: pd.DataFrame,
    player_view_df: pd.DataFrame,
    pgn_paths: dict[str, str],
) -> dict[str, Any]:
    """Return the dashboard JSON.

    `moves_df`         — every analysed move (CSV/DB shape).
    `player_view_df`   — joined player-error rows with results + opening info.
    `pgn_paths`        — color_file → path on disk for opening repertoire stats.
    """
    payload: dict[str, Any] = {}

    # --- KPIs ------------------------------------------------------------
    error_only = player_view_df[player_view_df["error_type"].isin(config.ERROR_TYPES)]
    total_games = (
        moves_df.drop_duplicates(["color_file", "game_id"]).shape[0]
        if not moves_df.empty else 0
    )
    payload["kpis"] = {
        "total_games": int(total_games),
        "total_moves": int(len(moves_df)),
        "total_errors": int(len(error_only)),
        "blunders": int((error_only["error_type"] == "blunder").sum()),
        "mistakes": int((error_only["error_type"] == "mistake").sum()),
        "inaccuracies": int((error_only["error_type"] == "inaccuracy").sum()),
        "stability_score": float(move_heatmap.stability_score(moves_df)),
    }

    # --- Win rates per (phase, error_type) -------------------------------
    winrates = analytics_core.compute_phase_error_winrates(player_view_df)
    payload["phase_winrates"] = _df_to_records(winrates)

    # Aggregated per-phase summary (used for the phase ring)
    payload["phase_summary"] = _df_to_records(analytics_core.phase_summary(winrates))

    # --- Per-color split -------------------------------------------------
    payload["per_color"] = {}
    for label, sub in analytics_core.split_by_color(player_view_df).items():
        sub_winrates = analytics_core.compute_phase_error_winrates(sub)
        payload["per_color"][label.lower()] = {
            "phase_winrates": _df_to_records(sub_winrates),
            "phase_summary": _df_to_records(analytics_core.phase_summary(sub_winrates)),
            "totals": {
                k: int(v) for k, v in analytics_core.total_error_counts(sub).items()
            },
            "prescription": analytics_core.generate_prescription(sub_winrates, label=label),
        }

    payload["combined_prescription"] = analytics_core.generate_prescription(winrates)

    # --- Repeat offenders ------------------------------------------------
    payload["repeat_offenders"] = _df_to_records(
        repeat_offenders.by_move_number(player_view_df, min_count=3).head(50)
    )

    # --- Move heatmap ----------------------------------------------------
    payload["heatmap"] = _df_to_records(move_heatmap.heatmap(player_view_df))

    # --- Time trend ------------------------------------------------------
    payload["trend"] = _df_to_records(time_trend.errors_over_time(player_view_df))

    # --- Endgame types ---------------------------------------------------
    if "fen_before" in moves_df.columns and moves_df["fen_before"].notna().any():
        payload["endgame_types"] = _df_to_records(
            endgame_types.winrates_by_endgame_type(player_view_df, moves_df)
        )
    else:
        payload["endgame_types"] = []

    # --- Opening repertoire ---------------------------------------------
    repertoire = openings_extended.stats_with_errors(pgn_paths, player_view_df)
    payload["repertoire"] = _df_to_records(repertoire.head(40)) if not repertoire.empty else []

    return payload
