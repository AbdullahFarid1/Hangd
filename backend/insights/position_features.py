"""Tag each error position with simple structural features and aggregate.

The features intentionally stay shallow: queens-on, opposite-side castling,
material imbalance, central tension. The goal is a fingerprint like
"60% of your blunders happen with queens on and central tension" — not
deep positional understanding.

Requires `fen_before` on the moves CSV (added by engine_analysis.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import chess
import pandas as pd

from .. import config


@dataclass
class PositionFeatures:
    queens_on: bool
    opposite_castling: bool
    material_imbalance: bool
    central_tension: bool
    piece_count: int


def _board_features(fen: str) -> PositionFeatures:
    board = chess.Board(fen)

    queens = board.pieces(chess.QUEEN, chess.WHITE) | board.pieces(chess.QUEEN, chess.BLACK)
    queens_on = bool(queens)

    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)
    opposite_castling = False
    if white_king_sq is not None and black_king_sq is not None:
        wk_side = "k" if chess.square_file(white_king_sq) >= 4 else "q"
        bk_side = "k" if chess.square_file(black_king_sq) >= 4 else "q"
        opposite_castling = wk_side != bk_side and white_king_sq != chess.E1 and black_king_sq != chess.E8

    def _material(color: chess.Color) -> int:
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        return sum(
            len(board.pieces(piece, color)) * value
            for piece, value in values.items()
        )

    material_imbalance = abs(_material(chess.WHITE) - _material(chess.BLACK)) >= 2

    central_tension = False
    central_squares = (chess.D4, chess.D5, chess.E4, chess.E5)
    for sq in central_squares:
        attackers_white = board.attackers(chess.WHITE, sq)
        attackers_black = board.attackers(chess.BLACK, sq)
        if attackers_white and attackers_black:
            central_tension = True
            break

    piece_count = chess.popcount(board.occupied)

    return PositionFeatures(
        queens_on=queens_on,
        opposite_castling=opposite_castling,
        material_imbalance=material_imbalance,
        central_tension=central_tension,
        piece_count=piece_count,
    )


def annotate(moves_df: pd.DataFrame) -> pd.DataFrame:
    """Add feature columns to a per-move DataFrame containing `fen_before`."""
    if "fen_before" not in moves_df.columns:
        raise ValueError("moves_df must contain a 'fen_before' column")

    features = moves_df["fen_before"].apply(_board_features)
    out = moves_df.copy()
    out["queens_on"] = features.apply(lambda f: f.queens_on)
    out["opposite_castling"] = features.apply(lambda f: f.opposite_castling)
    out["material_imbalance"] = features.apply(lambda f: f.material_imbalance)
    out["central_tension"] = features.apply(lambda f: f.central_tension)
    out["piece_count"] = features.apply(lambda f: f.piece_count)
    return out


def fingerprint(annotated_player_df: pd.DataFrame) -> pd.DataFrame:
    """Per error_type: % share of errors that have each feature flag on."""
    df = annotated_player_df[annotated_player_df["error_type"].isin(config.ERROR_TYPES)]
    feature_cols = ["queens_on", "opposite_castling", "material_imbalance", "central_tension"]

    rows = []
    for et, sub in df.groupby("error_type", dropna=False):
        total = len(sub)
        if total == 0:
            continue
        row = {"error_type": et, "total": total}
        for col in feature_cols:
            row[f"pct_{col}"] = sub[col].sum() / total
        rows.append(row)

    return pd.DataFrame(rows)
