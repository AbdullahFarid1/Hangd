# Hangd

A Python-based chess analysis pipeline that evaluates PGN games with Stockfish, classifies move quality, and generates practical performance insights by phase and opening.

## What This Project Does

This project analyzes your games from two PGN files (one where you played White, one where you played Black) and produces:

- Move-level error labels: `ok`, `inaccuracy`, `mistake`, `blunder`
- Phase-wise error breakdowns (opening, middlegame, endgame)
- Win-rate statistics by phase and error type
- Opening performance summaries by color
- Training prescriptions based on your weakest phase

## Project Files

Core scripts:

- `Calculation.py`: Runs Stockfish on PGN moves and writes `games_with_errors.csv`
- `Analytics.py`: Aggregates error counts and phase-level metrics, writes filtered outputs
- `Analyticswb.py`: Builds separate white/black phase prescriptions from player-only error data
- `Openings.py`: Extracts opening names and per-color opening results from PGN headers
- `Prescription.py`: Reserved for custom prescriptions (currently empty)

Main generated datasets:

- `games_with_errors.csv`
- `games_with_errors_only_imb.csv`
- `errors_imb_with_result_and_phase_player_only.csv`
- `white_phase_error_counts.csv`
- `black_phase_error_counts.csv`
- `phase_error_winrates.csv`
- `phase_error_winrates_player_only.csv`
- `opening_stats_by_color.csv`

Input PGN files:

- `MAF13-white.pgn`
- `MAF13-black.pgn`

## Requirements

- Python 3.10+
- Stockfish binary
- Python packages:
  - `pandas`
  - `python-chess`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Setup

1. Update `STOCKFISH_PATH` in `Calculation.py` to point to your local Stockfish executable.
2. Place your PGN files in the project root (or update file names in scripts).

## Typical Workflow

Run these scripts in order:

```bash
python Calculation.py
python Analytics.py
python Openings.py
python Analyticswb.py
```

This will regenerate the analysis CSV outputs from your PGN data.

## Notes

- Scripts currently assume the two-file setup (`white_file` and `black_file`) and rely on fixed file names.
- For reproducibility, keep PGN file naming consistent with script configs.

## Repository

GitHub repository: `AbdullahFarid1/Hangd`.
