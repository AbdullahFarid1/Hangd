"""Phase × error-type × outcome math, plus the prescription generator.

This module is the single source of truth for the win-rate analytics that
both `Analytics.py` and `Analyticswb.py` used to duplicate, and that the
web app reads to build the dashboard.

Modern pandas friendly: no more deprecated `groupby.apply` returning a
tuple (the original code triggered a FutureWarning).
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from . import config


# --------------------------------------------------
# Phase × error type × outcome → win rates
# --------------------------------------------------

def compute_phase_error_winrates(errors_player_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per (phase, error_type) with win/loss/draw/total/win_rate."""
    valid = errors_player_df[errors_player_df["outcome"].isin(["win", "loss", "draw"])]

    group = (
        valid.groupby(["phase", "error_type", "outcome"])
        .size()
        .unstack(fill_value=0)
    )

    for col in ("win", "loss", "draw"):
        if col not in group.columns:
            group[col] = 0

    group["total"] = group[["win", "loss", "draw"]].sum(axis=1)
    group["win_rate"] = group["win"] / group["total"].replace(0, pd.NA)

    return group.reset_index()


def phase_summary(phase_winrates_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse error-type axis: one row per phase with overall win rate."""
    summary = (
        phase_winrates_df
        .groupby("phase", as_index=False)[["win", "loss", "draw", "total"]]
        .sum()
    )
    summary["win_rate"] = summary["win"] / summary["total"].replace(0, pd.NA)
    summary["phase"] = pd.Categorical(
        summary["phase"], categories=list(config.PHASE_ORDER), ordered=True
    )
    return summary.sort_values("phase").reset_index(drop=True)


# --------------------------------------------------
# Prescription text
# --------------------------------------------------

PHASE_ADVICE: dict[str, list[str]] = {
    "opening": [
        "Narrow your repertoire to a few reliable systems and learn the core ideas rather than long forcing lines.",
        "Study your most frequent opening errors by move number and SAN, and prepare simple, safe alternative moves.",
        "Replay your first 10–15 moves from typical games with an engine and compare plans, not just single moves.",
        "Maintain a small personal opening file of the positions you actually reach, with one main plan each.",
    ],
    "middlegame": [
        "Focus on classic middlegame themes: piece activity, king safety, weak squares, and pawn breaks.",
        "Build a blunder notebook: for each repeated middlegame error, write why it failed and what the engine recommended.",
        "Train tactics using positions from your own games that match your mistake patterns (pins, forks, discovered attacks, etc.).",
        "Adopt a thinking checklist: before each move, scan for opponent threats and tactics to reduce one-move blunders.",
    ],
    "endgame": [
        "Identify which endgame types occur most for you (rook, minor-piece, pure pawn endings) and learn key reference positions.",
        "Convert your worst endgame blunders into training positions and play them out vs. engine or a partner.",
        "Favor simple improving moves (king activity, pawn structure) over speculative tactics in low-material positions.",
        "Study basic endgame principles (opposition, passed pawns, rook behind passer, active king) and relate them to your own errors.",
    ],
}


def generate_prescription(
    phase_winrates_df: pd.DataFrame,
    label: str | None = None,
) -> str:
    """Render a human-readable training prescription.

    `label` lets callers tag the output for a specific color
    ("White" / "Black"). Pass None for a combined prescription.
    """
    summary = phase_summary(phase_winrates_df)

    if summary.empty or summary["total"].sum() == 0:
        suffix = f" FOR {label.upper()}" if label else ""
        return f"=== PRESCRIPTION{suffix} ===\nNo data available."

    summary_sorted = summary.sort_values("win_rate", na_position="last")
    weakest = summary_sorted.iloc[0]
    strongest = summary_sorted.iloc[-1]

    title_suffix = f" AS {label.upper()}" if label else ""
    person_label = label or "you"
    convert_verb = "converts" if label else "convert"

    lines: list[str] = []
    lines.append(f"=== PRESCRIPTION BASED ON ERRORS AND WIN RATES{title_suffix} ===")
    lines.append("")
    lines.append(f"Overall phase performance ({person_label}, across inaccuracies / mistakes / blunders):")
    for _, row in summary_sorted.iterrows():
        wr = (row["win_rate"] * 100) if pd.notna(row["win_rate"]) else 0.0
        lines.append(
            f"- {row['phase'].capitalize():10s}: "
            f"Wins {int(row['win'])}/{int(row['total'])} → Win rate ≈ {wr:5.1f}%"
        )
    lines.append("")
    lines.append(
        f"The weakest phase by win rate is the **{weakest['phase']}** — focus training here."
    )
    lines.append(
        f"The strongest phase is the **{strongest['phase']}**, where {person_label} {convert_verb} more games despite errors."
    )
    lines.append("")
    lines.append(f"Recommended training focus for the **{weakest['phase']}**:")
    for tip in PHASE_ADVICE[str(weakest["phase"])]:
        lines.append(f"- {tip}")
    lines.append("")
    lines.append("General guidance by error type:")
    lines.append("- Inaccuracies: small evaluation drops; improve plan quality and move orders, not just calculation.")
    lines.append("- Mistakes: medium drops; review them as study positions and check which simple candidate moves were ignored.")
    lines.append("- Blunders: large drops; strengthen your blunder-check routine and always verify opponent forcing moves.")

    return "\n".join(lines)


# --------------------------------------------------
# Counting helpers used by the CLI Calculation step
# --------------------------------------------------

def per_phase_error_counts(errors_player_df: pd.DataFrame) -> pd.DataFrame:
    """Phase × error-type matrix of counts (no outcome axis)."""
    counts = (
        errors_player_df[errors_player_df["error_type"].isin(config.ERROR_TYPES)]
        .groupby(["phase", "error_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            index=list(config.PHASE_ORDER),
            columns=list(config.ERROR_TYPES),
            fill_value=0,
        )
    )
    return counts


def total_error_counts(errors_player_df: pd.DataFrame) -> pd.Series:
    """Single-row totals of inaccuracy / mistake / blunder."""
    return (
        errors_player_df[errors_player_df["error_type"].isin(config.ERROR_TYPES)][
            "error_type"
        ]
        .value_counts()
        .reindex(list(config.ERROR_TYPES), fill_value=0)
    )


# --------------------------------------------------
# Convenience: split player data by color
# --------------------------------------------------

def split_by_color(player_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return {'White': ..., 'Black': ...} subsets."""
    out: dict[str, pd.DataFrame] = {}
    for label, prefix in (("White", "white"), ("Black", "black")):
        sub = player_df[player_df["color_file"].str.startswith(prefix)].copy()
        if not sub.empty:
            out[label] = sub
    return out
