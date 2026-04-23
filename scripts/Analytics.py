"""Legacy entry point — combined-color prescription.

Reads the player-view CSV produced by `Calculation.py` (or
`backend.cli build-analytics`) and prints a single combined prescription.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from backend import analytics_core, config


def main() -> None:
    path = config.data_path(config.CSV_PLAYER_ONLY)
    if not path.exists():
        raise SystemExit(f"Missing {path} — run Calculation.py first.")

    df = pd.read_csv(path)
    df = df[df["error_type"].isin(config.ERROR_TYPES)].copy()

    winrates = analytics_core.compute_phase_error_winrates(df)
    print("=== RAW PHASE × ERROR TYPE STATS (PLAYER ONLY) ===")
    print(winrates)
    print()
    print(analytics_core.generate_prescription(winrates))


if __name__ == "__main__":
    main()
