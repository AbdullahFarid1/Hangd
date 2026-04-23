"""Classify endgame positions by material signature and report win rates.

Material signature examples:
    "KP_v_K"           — king + pawn vs king
    "KRP_v_KR"         — rook + pawn vs rook
    "KQ_v_KR"          — queen vs rook
    "KBN_v_K"          — bishop + knight mate

A position is considered "endgame" if it falls in the endgame phase as
defined by config, OR has no queens and ≤ 14 pieces total (a more flexible
material-based heuristic).
"""

from __future__ import annotations

from collections import Counter

import chess
import pandas as pd

from .. import config


PIECE_LETTER = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
}


def _signature_for_color(board: chess.Board, color: chess.Color) -> str:
    counts = Counter()
    for piece, letter in PIECE_LETTER.items():
        n = len(board.pieces(piece, color))
        if n:
            counts[letter] = n

    # Order: K then Q, R, B, N, P (descending value); pawns last.
    order = ("Q", "R", "B", "N", "P")
    parts = ["K"] + [letter * counts[letter] for letter in order if counts[letter]]
    return "".join(parts)


def material_signature(fen: str) -> str:
    board = chess.Board(fen)
    white = _signature_for_color(board, chess.WHITE)
    black = _signature_for_color(board, chess.BLACK)
    # Always print the player-to-move's side first so signatures are
    # comparable across colors.
    if board.turn == chess.WHITE:
        return f"{white}_v_{black}"
    return f"{black}_v_{white}"


def _is_material_endgame(fen: str) -> bool:
    board = chess.Board(fen)
    no_queens = not (board.pieces(chess.QUEEN, chess.WHITE) | board.pieces(chess.QUEEN, chess.BLACK))
    few_pieces = chess.popcount(board.occupied) <= 14
    return no_queens or few_pieces


def winrates_by_endgame_type(
    player_view_df: pd.DataFrame,
    moves_df: pd.DataFrame,
    *,
    min_games: int = 2,
) -> pd.DataFrame:
    """Return one row per endgame signature with win rate.

    Strategy: pick the latest endgame-phase ply per game (color_file, game_id)
    so each game contributes one signature. Join with the player-view's
    outcome.
    """
    if "fen_before" not in moves_df.columns:
        return pd.DataFrame(columns=["signature", "wins", "losses", "draws", "total", "win_rate"])

    # Deepest endgame ply per game = the position closest to the result.
    eg_moves = moves_df[moves_df["phase"] == "endgame"].copy()
    if eg_moves.empty:
        # Fall back to any position with material-style endgame
        eg_moves = moves_df[moves_df["fen_before"].apply(_is_material_endgame)].copy()
        if eg_moves.empty:
            return pd.DataFrame(columns=["signature", "wins", "losses", "draws", "total", "win_rate"])

    last_per_game = (
        eg_moves.sort_values("ply")
        .groupby(["color_file", "game_id"], as_index=False)
        .tail(1)
        [["color_file", "game_id", "fen_before"]]
    )
    last_per_game["signature"] = last_per_game["fen_before"].apply(material_signature)

    # Join with player-view to get outcome (one outcome per game).
    outcomes = (
        player_view_df.dropna(subset=["outcome"])
        [["color_file", "game_id", "outcome"]]
        .drop_duplicates(["color_file", "game_id"])
    )
    joined = last_per_game.merge(outcomes, on=["color_file", "game_id"], how="inner")

    grouped = (
        joined.groupby("signature")["outcome"]
        .value_counts()
        .unstack(fill_value=0)
        .rename(columns={"win": "wins", "loss": "losses", "draw": "draws"})
    )
    for col in ("wins", "losses", "draws"):
        if col not in grouped.columns:
            grouped[col] = 0

    grouped["total"] = grouped[["wins", "losses", "draws"]].sum(axis=1)
    grouped["win_rate"] = grouped["wins"] / grouped["total"].replace(0, pd.NA)
    grouped = grouped[grouped["total"] >= min_games]

    return (
        grouped.reset_index()
        .sort_values("total", ascending=False)
        [["signature", "wins", "losses", "draws", "total", "win_rate"]]
    )
