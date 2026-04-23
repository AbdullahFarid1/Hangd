"""Command-line interface that drives the whole local pipeline.

Usage examples:

    # Analyse two PGN files (white + black) end-to-end
    python -m backend.cli pipeline \
        --white MAF13-white.pgn \
        --black MAF13-black.pgn \
        --resume

    # Just (re-)build the analytics CSVs from an existing engine output
    python -m backend.cli build-analytics \
        --white MAF13-white.pgn \
        --black MAF13-black.pgn

    # Run a single insight on the prepared player-view CSV
    python -m backend.cli insight repeats
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import analytics_core, config
from .build_player_view import build_player_view
from .engine_analysis import analyse_pgn_to_csv
from .insights import (
    move_heatmap,
    openings_extended,
    position_features,
    repeat_offenders,
    time_trend,
)


# --------------------------------------------------
# Sub-command implementations
# --------------------------------------------------

def _cmd_analyse(args: argparse.Namespace) -> None:
    """Run Stockfish over one PGN."""
    out = config.data_path(args.output or config.CSV_GAMES_WITH_ERRORS)
    analyse_pgn_to_csv(config.pgn_path(args.pgn), args.color_label, out, resume=args.resume)


def _run_engine_for_pair(white_pgn: Path, black_pgn: Path, resume: bool) -> Path:
    out_csv = config.data_path(config.CSV_GAMES_WITH_ERRORS)
    if not resume and out_csv.exists():
        out_csv.unlink()
    analyse_pgn_to_csv(white_pgn, "white_file", out_csv, resume=resume)
    analyse_pgn_to_csv(black_pgn, "black_file", out_csv, resume=True)
    return out_csv


def _build_analytics(white_pgn: Path, black_pgn: Path) -> dict[str, pd.DataFrame]:
    moves_csv = config.data_path(config.CSV_GAMES_WITH_ERRORS)
    if not moves_csv.exists():
        raise SystemExit(
            f"Missing {moves_csv}. Run `python -m backend.cli analyse` first or use `pipeline`."
        )

    moves_df = pd.read_csv(moves_csv)

    # 1) IMB-only CSV (legacy compatibility)
    errors_only = moves_df[moves_df["error_type"].isin(config.ERROR_TYPES)]
    errors_only_path = config.data_path(config.CSV_ERRORS_ONLY_IMB)
    errors_only.to_csv(errors_only_path, index=False)

    # 2) Player view (the missing glue file)
    pgn_paths = {"white_file": white_pgn, "black_file": black_pgn}
    player_view_path = config.data_path(config.CSV_PLAYER_ONLY)
    player_df = build_player_view(moves_csv, pgn_paths, player_view_path)

    # 3) Phase × error counts per color (legacy CSVs)
    by_color = analytics_core.split_by_color(player_df)
    if "White" in by_color:
        analytics_core.per_phase_error_counts(by_color["White"]).to_csv(
            config.data_path(config.CSV_WHITE_PHASE_COUNTS)
        )
    if "Black" in by_color:
        analytics_core.per_phase_error_counts(by_color["Black"]).to_csv(
            config.data_path(config.CSV_BLACK_PHASE_COUNTS)
        )

    # 4) Phase winrates (combined + player-only)
    combined_winrates = analytics_core.compute_phase_error_winrates(player_df)
    combined_winrates.to_csv(
        config.data_path(config.CSV_PHASE_WINRATES_PLAYER), index=False
    )

    # 5) Repeat offenders
    repeats = repeat_offenders.by_move_number(player_df)
    repeats.to_csv(config.data_path(config.CSV_REPEAT_OFFENDERS), index=False)

    # 6) Opening repertoire stats
    opening_view = player_df.merge(
        moves_df[["color_file", "game_id", "ply", "cp_drop"]],
        on=["color_file", "game_id", "ply"],
        how="left",
    )
    repertoire = openings_extended.stats_with_errors(pgn_paths, opening_view)
    repertoire.to_csv(config.data_path(config.CSV_OPENING_STATS), index=False)

    return {
        "moves": moves_df,
        "player_view": player_df,
        "winrates": combined_winrates,
        "repeats": repeats,
        "repertoire": repertoire,
    }


def _cmd_build_analytics(args: argparse.Namespace) -> None:
    bundle = _build_analytics(config.pgn_path(args.white), config.pgn_path(args.black))

    print()
    print("Total errors per color (player only):")
    for color, sub in analytics_core.split_by_color(bundle["player_view"]).items():
        totals = analytics_core.total_error_counts(sub)
        bits = " | ".join(f"{k}: {int(v)}" for k, v in totals.items())
        print(f"  {color}: {bits}")
    print()

    print(analytics_core.generate_prescription(bundle["winrates"]))


def _cmd_pipeline(args: argparse.Namespace) -> None:
    white = config.pgn_path(args.white)
    black = config.pgn_path(args.black)
    _run_engine_for_pair(white, black, resume=args.resume)
    args_for_build = argparse.Namespace(white=str(white), black=str(black))
    _cmd_build_analytics(args_for_build)


def _cmd_insight(args: argparse.Namespace) -> None:
    player_view_path = config.data_path(config.CSV_PLAYER_ONLY)
    moves_path = config.data_path(config.CSV_GAMES_WITH_ERRORS)
    if not player_view_path.exists():
        raise SystemExit(f"{player_view_path} not found — run `build-analytics` first.")

    player_df = pd.read_csv(player_view_path)
    moves_df = pd.read_csv(moves_path) if moves_path.exists() else pd.DataFrame()

    if args.name == "repeats":
        out = repeat_offenders.by_move_number(player_df)
    elif args.name == "heatmap":
        out = move_heatmap.heatmap(player_df)
    elif args.name == "trend":
        out = time_trend.errors_over_time(player_df)
    elif args.name == "fingerprint":
        if "fen_before" not in moves_df.columns:
            raise SystemExit("moves CSV missing fen_before — re-run engine analysis.")
        annotated = position_features.annotate(moves_df)
        # Re-merge with player view so we only see player rows.
        player_keys = set(zip(player_df["color_file"], player_df["game_id"], player_df["ply"]))
        keys = list(zip(annotated["color_file"], annotated["game_id"], annotated["ply"]))
        annotated = annotated[[k in player_keys for k in keys]]
        out = position_features.fingerprint(annotated)
    else:
        raise SystemExit(f"Unknown insight: {args.name}")

    pd.set_option("display.max_rows", 50)
    pd.set_option("display.width", 140)
    print(out)


# --------------------------------------------------
# Argparse wiring
# --------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hangd",
        description="Hangd chess analytics — local CLI.",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    p_analyse = subs.add_parser("analyse", help="Run Stockfish over one PGN file.")
    p_analyse.add_argument("pgn", help="Path to PGN file.")
    p_analyse.add_argument(
        "color_label",
        help="Label for this file: 'white_file' if you played White, 'black_file' otherwise.",
    )
    p_analyse.add_argument("--output", help="CSV output path (defaults to games_with_errors.csv).")
    p_analyse.add_argument("--resume", action="store_true", help="Skip already-analysed games in the output CSV.")
    p_analyse.set_defaults(func=_cmd_analyse)

    p_build = subs.add_parser("build-analytics", help="Build all analytics CSVs from games_with_errors.csv.")
    p_build.add_argument("--white", required=True, help="White PGN file.")
    p_build.add_argument("--black", required=True, help="Black PGN file.")
    p_build.set_defaults(func=_cmd_build_analytics)

    p_pipe = subs.add_parser("pipeline", help="Run the engine then build all analytics in one go.")
    p_pipe.add_argument("--white", required=True, help="White PGN file.")
    p_pipe.add_argument("--black", required=True, help="Black PGN file.")
    p_pipe.add_argument("--resume", action="store_true", help="Resume engine analysis if interrupted.")
    p_pipe.set_defaults(func=_cmd_pipeline)

    p_ins = subs.add_parser("insight", help="Print one insight to stdout.")
    p_ins.add_argument(
        "name",
        choices=["repeats", "heatmap", "trend", "fingerprint"],
        help="Which insight to compute.",
    )
    p_ins.set_defaults(func=_cmd_insight)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
