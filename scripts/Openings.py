"""Legacy entry point — opening repertoire stats per color."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config
from backend.insights.openings_extended import repertoire_stats


def main() -> None:
    pgn_paths = {
        "white_file": config.pgn_path("MAF13-white.pgn"),
        "black_file": config.pgn_path("MAF13-black.pgn"),
    }
    df = repertoire_stats(pgn_paths)

    out = config.data_path(config.CSV_OPENING_STATS)
    df.to_csv(out, index=False)
    print(f"Saved opening stats per color to: {out}\n")

    print("=== SAMPLE OPENING STATS ===")
    print(df.head(20))


if __name__ == "__main__":
    main()
