"""Legacy entry point — thin wrapper.

The original Calculation.py filtered the engine output down to player-only
I/M/B rows, tagged phases, counted errors per phase, and saved CSVs.
That logic now lives in `backend/build_player_view.py` and
`backend/analytics_core.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from backend import analytics_core, config
from backend.build_player_view import build_player_view


def main() -> None:
    moves_csv = config.data_path(config.CSV_GAMES_WITH_ERRORS)
    if not moves_csv.exists():
        raise SystemExit(f"Missing {moves_csv} — run Clean.py first.")

    # 1) IMB-only CSV (legacy compatibility)
    moves_df = pd.read_csv(moves_csv)
    errors_only = moves_df[moves_df["error_type"].isin(config.ERROR_TYPES)]
    errors_only_path = config.data_path(config.CSV_ERRORS_ONLY_IMB)
    errors_only.to_csv(errors_only_path, index=False)
    print(f"Saved filtered errors CSV to: {errors_only_path}")

    # 2) Build the joined player view (the previously missing step)
    pgn_paths = {
        "white_file": config.pgn_path("MAF13-white.pgn"),
        "black_file": config.pgn_path("MAF13-black.pgn"),
    }
    player_df = build_player_view(
        moves_csv, pgn_paths, config.data_path(config.CSV_PLAYER_ONLY)
    )

    # 3) Per-color phase × error counts (legacy CSVs)
    by_color = analytics_core.split_by_color(player_df)

    print()
    for label, sub in by_color.items():
        totals = analytics_core.total_error_counts(sub)
        bits = " | ".join(f"{k.capitalize()}: {int(v)}" for k, v in totals.items())
        print(f"=== TOTAL ERRORS – {label.upper()} ===")
        print(bits)
        print()

    if "White" in by_color:
        analytics_core.per_phase_error_counts(by_color["White"]).to_csv(
            config.data_path(config.CSV_WHITE_PHASE_COUNTS)
        )
    if "Black" in by_color:
        analytics_core.per_phase_error_counts(by_color["Black"]).to_csv(
            config.data_path(config.CSV_BLACK_PHASE_COUNTS)
        )
    print("Saved phase-wise counts to:")
    print(f"  {config.CSV_WHITE_PHASE_COUNTS}")
    print(f"  {config.CSV_BLACK_PHASE_COUNTS}")


if __name__ == "__main__":
    main()
