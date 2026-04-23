"""Legacy entry point — separate White / Black prescriptions."""

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

    by_color = analytics_core.split_by_color(df)

    for label in ("White", "Black"):
        if label not in by_color:
            print(f"No data for player as {label}.\n")
            continue
        winrates = analytics_core.compute_phase_error_winrates(by_color[label])
        print(f"=== RAW PHASE × ERROR TYPE STATS (PLAYER AS {label.upper()}) ===")
        print(winrates)
        print()
        print(analytics_core.generate_prescription(winrates, label=label))
        print()


if __name__ == "__main__":
    main()
