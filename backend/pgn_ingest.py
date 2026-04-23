"""PGN parsing helpers shared by every other module.

Always parses through python-chess (never regex on PGN text), so games with
quirky comments, NAGs, or variations don't break the pipeline.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import chess
import chess.pgn


@dataclass
class GameMeta:
    game_id: int
    white: str
    black: str
    result: str           # "1-0" / "0-1" / "1/2-1/2" / "*"
    date: str             # PGN Date header, may be "????.??.??"
    white_elo: int | None
    black_elo: int | None
    eco: str
    opening_name: str
    eco_url: str
    ply_count: int = 0


@dataclass
class GameRecord:
    meta: GameMeta
    game: chess.pgn.Game = field(repr=False)


def _safe_int(value: str | None) -> int | None:
    if value is None or value == "" or value == "?":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _opening_name_from_eco_url(eco_url: str) -> str:
    """Convert chess.com style ECOUrl to a human opening name.

    Example:
      https://www.chess.com/openings/Nimzowitsch-Larsen-Attack-Indian-Variation...4.f4
      -> "Nimzowitsch Larsen Attack Indian Variation"
    """
    if not eco_url:
        return ""
    last = eco_url.rsplit("/", 1)[-1]
    main = last.split("...")[0]
    return main.replace("-", " ").replace("%20", " ").strip()


def iter_games(pgn_path: str | Path) -> Iterator[GameRecord]:
    """Yield (meta, game) for every game in the PGN file."""
    pgn_path = Path(pgn_path)
    with pgn_path.open(encoding="utf-8") as fh:
        game_id = 0
        while True:
            game = chess.pgn.read_game(fh)
            if game is None:
                break
            game_id += 1

            headers = game.headers
            ply_count = sum(1 for _ in game.mainline_moves())

            meta = GameMeta(
                game_id=game_id,
                white=headers.get("White", ""),
                black=headers.get("Black", ""),
                result=headers.get("Result", ""),
                date=headers.get("Date", ""),
                white_elo=_safe_int(headers.get("WhiteElo")),
                black_elo=_safe_int(headers.get("BlackElo")),
                eco=headers.get("ECO", ""),
                eco_url=headers.get("ECOUrl", ""),
                opening_name=_opening_name_from_eco_url(headers.get("ECOUrl", "")),
                ply_count=ply_count,
            )

            yield GameRecord(meta=meta, game=game)


def count_games_and_moves(pgn_path: str | Path) -> tuple[int, int]:
    """Cheap pre-pass for progress bars."""
    games = 0
    moves = 0
    for record in iter_games(pgn_path):
        games += 1
        moves += record.meta.ply_count
    return games, moves


def result_from_perspective(result_tag: str, you_are: str) -> str:
    """Map a PGN Result + which side the player is to win/loss/draw/other."""
    if result_tag == "1-0":
        return "win" if you_are == "White" else "loss"
    if result_tag == "0-1":
        return "win" if you_are == "Black" else "loss"
    if result_tag == "1/2-1/2":
        return "draw"
    return "other"


def hash_pgn_file(pgn_path: str | Path) -> str:
    """SHA-256 of the PGN file. Used by the worker to deduplicate uploads."""
    h = hashlib.sha256()
    with Path(pgn_path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
