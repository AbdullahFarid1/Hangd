import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

IMB_PLAYER_CSV = "errors_imb_with_result_and_phase_player_only.csv"
ERROR_TYPES = ["inaccuracy", "mistake", "blunder"]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def compute_phase_error_winrates(errors_imb_player):
    """Return phase × error_type × (wins, losses, draws, total, win_rate)."""
    valid = errors_imb_player[errors_imb_player["outcome"].isin(["win", "loss", "draw"])].copy()

    group = (
        valid
        .groupby(["phase", "error_type", "outcome"])
        .size()
        .unstack(fill_value=0)
    )

    for col in ["win", "loss", "draw"]:
        if col not in group.columns:
            group[col] = 0

    group["total"] = group[["win", "loss", "draw"]].sum(axis=1)
    group["win_rate"] = group["win"] / group["total"].replace(0, pd.NA)

    return group.reset_index()


def generate_prescription(phase_winrates_df):
    """Generalised training prescription based on which phase has the lowest win rate."""
    # Aggregate over error types to get phase-level win rates
    phase_summary = (
        phase_winrates_df
        .groupby("phase")
        .apply(lambda g: (g["win"].sum(), g["total"].sum()))
    )

    phase_stats = {}
    for phase, (wins, total) in phase_summary.items():
        win_rate = wins / total if total > 0 else 0.0
        phase_stats[phase] = {"wins": wins, "total": total, "win_rate": win_rate}

    phases_sorted = sorted(
        phase_stats.items(),
        key=lambda kv: kv[1]["win_rate"]
    )

    lines = []
    lines.append("=== PRESCRIPTION BASED ON PLAYER'S ERRORS AND WIN RATES ===")
    lines.append("")

    # High-level summary
    lines.append("Overall phase performance (across inaccuracies, mistakes, and blunders):")
    for phase, stats in phases_sorted:
        wr = stats["win_rate"] * 100 if stats["total"] > 0 else 0.0
        lines.append(
            f"- {phase.capitalize():10s}: Wins {stats['wins']}/{stats['total']} "
            f"→ Win rate ≈ {wr:5.1f}%"
        )
    lines.append("")

    weakest_phase, weakest_stats = phases_sorted[0]
    strongest_phase, strongest_stats = phases_sorted[-1]

    lines.append(f"The weakest phase by win rate is the **{weakest_phase}**.")
    lines.append(
        f"This is where your inaccuracies, mistakes, and blunders have the largest negative impact on results, "
        f"so training should primarily focus here."
    )
    lines.append(
        f"The strongest phase is the **{strongest_phase}**, where you convert more games despite errors."
    )
    lines.append("")

    def phase_advice(phase_name):
        if phase_name == "opening":
            return [
                "Narrow your repertoire to a few reliable systems and learn the core ideas rather than long forcing lines.",
                "Study your most frequent opening errors by move number and SAN, and prepare simple, safe alternative moves.",
                "Replay your first 10–15 moves from typical games with an engine and compare plans, not just single moves.",
                "Maintain a small personal opening file of the positions you actually reach, with one main plan each."
            ]
        elif phase_name == "middlegame":
            return [
                "Focus on classic middlegame themes: piece activity, king safety, weak squares, and pawn breaks.",
                "Build a blunder notebook: for each repeated middlegame error, write why it failed and what the engine recommended.",
                "Train tactics using positions from your own games that match your mistake patterns (pins, forks, discovered attacks, etc.).",
                "Adopt a thinking checklist: before each move, scan for opponent threats and tactics to reduce one-move blunders."
            ]
        else:  # endgame
            return [
                "Identify which endgame types occur most for you (rook, minor-piece, pure pawn endings) and learn key reference positions.",
                "Convert your worst endgame blunders into training positions and play them out vs. engine or a friend.",
                "Favor simple improving moves (king activity, pawn structure) over speculative tactics in low-material positions.",
                "Study basic endgame principles (opposition, passed pawns, rook behind passer, active king) and relate them to your own errors."
            ]

    lines.append(f"Recommended training focus for the **{weakest_phase}**:")
    for tip in phase_advice(weakest_phase):
        lines.append(f"- {tip}")
    lines.append("")

    lines.append("General guidance by error type:")
    lines.append("- Inaccuracies: Small evaluation drops; improve plan quality and move orders, not just calculation.")
    lines.append("- Mistakes: Medium drops; review them as study positions and check which simple candidate moves you ignored.")
    lines.append("- Blunders: Large drops; strengthen your blunder-check routine and always verify opponent forcing moves.")
    lines.append("")
    lines.append(
        "For future datasets, re-run this script on the new I/M/B file. "
        "Whichever phase shows the lowest win rate after errors becomes your main training target, "
        "and you reuse the matching phase checklist above."
    )

    return "\n".join(lines)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    # Load the already-prepared player-only I/M/B file
    df = pd.read_csv(IMB_PLAYER_CSV)

    # Sanity filter: only known error types
    df = df[df["error_type"].isin(ERROR_TYPES)].copy()

    # Compute phase×error winrates
    phase_winrates_df = compute_phase_error_winrates(df)

    print("=== RAW PHASE × ERROR TYPE STATS (PLAYER ONLY, FROM PREPARED FILE) ===")
    print(phase_winrates_df)
    print()

    # Generate and print prescription
    prescription = generate_prescription(phase_winrates_df)
    print(prescription)


if __name__ == "__main__":
    main()
