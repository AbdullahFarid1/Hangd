import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

INPUT_CSV = "games_with_errors.csv"
OUTPUT_ERRORS_ONLY_CSV = "games_with_errors_only_imb.csv"

# Error types of interest
ERROR_TYPES = ["inaccuracy", "mistake", "blunder"]


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_CSV)

# --------------------------------------------------
# 1) FILTER BY COLOR FILE + SIDE
# --------------------------------------------------
# From white_file → only White moves
white_df = df[(df["color_file"] == "white_file") & (df["side"] == "White")]

# From black_file → only Black moves
black_df = df[(df["color_file"] == "black_file") & (df["side"] == "Black")]

# --------------------------------------------------
# 2) TOTAL INACCURACIES, MISTAKES, BLUNDERS (WHITE & BLACK)
# --------------------------------------------------

white_counts = (
    white_df[white_df["error_type"].isin(ERROR_TYPES)]["error_type"]
    .value_counts()
    .reindex(ERROR_TYPES, fill_value=0)
)

black_counts = (
    black_df[black_df["error_type"].isin(ERROR_TYPES)]["error_type"]
    .value_counts()
    .reindex(ERROR_TYPES, fill_value=0)
)

print("=== TOTAL ERRORS – WHITE (from white_file, White moves only) ===")
for et in ERROR_TYPES:
    print(f"{et.capitalize()}: {white_counts[et]}")
print()

print("=== TOTAL ERRORS – BLACK (from black_file, Black moves only) ===")
for et in ERROR_TYPES:
    print(f"{et.capitalize()}: {black_counts[et]}")
print()

# --------------------------------------------------
# 3) CREATE CSV WITH ONLY I/M/B
# --------------------------------------------------

errors_only_df = df[df["error_type"].isin(ERROR_TYPES)]
errors_only_df.to_csv(OUTPUT_ERRORS_ONLY_CSV, index=False)
print(f"Saved filtered errors CSV to: {OUTPUT_ERRORS_ONLY_CSV}")
print()

# --------------------------------------------------
# 4) DEFINE GAME PHASE BY MOVE NUMBER
# --------------------------------------------------
# Simple phase rule:
#   Opening:    move 1–15
#   Middlegame: move 16–40
#   Endgame:    move 41+

def assign_phase(move_number: int) -> str:
    if move_number <= 15:
        return "opening"
    elif move_number <= 40:
        return "middlegame"
    else:
        return "endgame"

white_df = white_df.copy()
black_df = black_df.copy()

white_df["phase"] = white_df["move_number"].apply(assign_phase)
black_df["phase"] = black_df["move_number"].apply(assign_phase)

# --------------------------------------------------
# 5) COUNT ERRORS PER PHASE (WHITE & BLACK)
# --------------------------------------------------

def phase_error_counts(colored_df: pd.DataFrame, label: str):
    phase_counts = (
        colored_df[colored_df["error_type"].isin(ERROR_TYPES)]
        .groupby(["phase", "error_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=["opening", "middlegame", "endgame"],
                 columns=ERROR_TYPES,
                 fill_value=0)
    )

    print(f"=== ERRORS BY PHASE – {label} ===")
    for phase in ["opening", "middlegame", "endgame"]:
        row = phase_counts.loc[phase]
        print(
            f"{phase.capitalize():10s} | "
            f"Inaccuracies: {row['inaccuracy']:6d} | "
            f"Mistakes: {row['mistake']:6d} | "
            f"Blunders: {row['blunder']:6d}"
        )
    print()
    return phase_counts

white_phase_counts = phase_error_counts(white_df, "WHITE (white_file, White moves only)")
black_phase_counts = phase_error_counts(black_df, "BLACK (black_file, Black moves only)")

# --------------------------------------------------
# (OPTIONAL) SAVE PHASE-WISE COUNTS TO CSV
# --------------------------------------------------
white_phase_counts.to_csv("white_phase_error_counts.csv")
black_phase_counts.to_csv("black_phase_error_counts.csv")
print("Saved phase-wise counts to:")
print("  white_phase_error_counts.csv")
print("  black_phase_error_counts.csv")
