"""Legacy entry point — thin wrapper around backend.engine_analysis.

Runs Stockfish over the two MAF13 PGNs and writes data/outputs/games_with_errors.csv.
Run from anywhere with `python scripts/Clean.py` (sys.path is fixed up below).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config
from backend.engine_analysis import analyse_pgn_to_csv


def main() -> None:
    out = config.data_path(config.CSV_GAMES_WITH_ERRORS)
    if out.exists():
        out.unlink()  # legacy script always wrote a fresh file
    analyse_pgn_to_csv(config.pgn_path("MAF13-white.pgn"), "white_file", out, resume=False)
    analyse_pgn_to_csv(config.pgn_path("MAF13-black.pgn"), "black_file", out, resume=True)
    print(f"\nAll done. CSV written to {out}")


if __name__ == "__main__":
    main()
