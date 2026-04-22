import chess
import chess.pgn
import chess.engine
import csv
from pathlib import Path

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

STOCKFISH_PATH = Path(
    "C:/Users/Abdullah Farid/Downloads/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"
)

DEPTH_BEST = 10
DEPTH_PLAYED = 8
PROGRESS_EVERY = 10  # update terminal every N moves

# --------------------------------------------------
# ENGINE START (Windows + VS Code safe)
# --------------------------------------------------

engine = chess.engine.SimpleEngine.popen_uci(
    str(STOCKFISH_PATH),
    timeout=20,
    creationflags=0x08000000  # CREATE_NO_WINDOW
)

engine.configure({
    "Threads": 4,   # adjust if needed
    "Hash": 512
})

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def classify_delta(cp_drop):
    if cp_drop < 50:
        return "ok"
    if cp_drop < 100:
        return "inaccuracy"
    if cp_drop < 300:
        return "mistake"
    return "blunder"


def count_games_and_moves(pgn_path):
    games = 0
    moves = 0
    with open(pgn_path, encoding="utf-8") as f:
        while (game := chess.pgn.read_game(f)) is not None:
            games += 1
            moves += sum(1 for _ in game.mainline_moves())
    return games, moves


# --------------------------------------------------
# MAIN ANALYSIS FUNCTION
# --------------------------------------------------

def analyse_pgn(pgn_path, color_label):
    rows = []

    total_games, total_moves = count_games_and_moves(pgn_path)
    print(f"\nProcessing {pgn_path}")
    print(f"Total games: {total_games}, total moves: {total_moves}\n")

    processed_games = 0
    processed_moves = 0

    with open(pgn_path, encoding="utf-8") as f:
        game_id = 0

        while (game := chess.pgn.read_game(f)) is not None:
            game_id += 1
            processed_games += 1
            board = game.board()

            for ply, move in enumerate(game.mainline_moves(), start=1):
                processed_moves += 1

                player = board.turn  # side making the move

                # ---- engine best evaluation BEFORE move ----
                info_best = engine.analyse(
                    board,
                    chess.engine.Limit(depth=DEPTH_BEST)
                )
                best_score = info_best["score"].pov(player).score(mate_score=100000)

                san = board.san(move)
                uci = move.uci()

                board.push(move)

                # ---- evaluation AFTER played move ----
                info_played = engine.analyse(
                    board,
                    chess.engine.Limit(depth=DEPTH_PLAYED)
                )
                played_score = info_played["score"].pov(player).score(mate_score=100000)

                cp_drop = best_score - played_score
                label = classify_delta(cp_drop)

                side = "White" if player == chess.WHITE else "Black"
                move_number = (ply + 1) // 2

                rows.append({
                    "game_id": game_id,
                    "color_file": color_label,
                    "move_number": move_number,
                    "ply": ply,
                    "side": side,
                    "san": san,
                    "uci": uci,
                    "best_cp": best_score,
                    "played_cp": played_score,
                    "cp_drop": cp_drop,
                    "error_type": label,
                })

                # ---- progress display ----
                if processed_moves % PROGRESS_EVERY == 0 or processed_moves == total_moves:
                    percent = (processed_moves / total_moves) * 100
                    print(
                        f"\rGames: {processed_games}/{total_games} | "
                        f"Moves: {processed_moves}/{total_moves} "
                        f"({percent:5.1f}%)",
                        end=""
                    )

    print(f"\nFinished {pgn_path}")
    return rows


# --------------------------------------------------
# RUN ANALYSIS
# --------------------------------------------------

white_rows = analyse_pgn("MAF13-white.pgn", "white_file")
black_rows = analyse_pgn("MAF13-black.pgn", "black_file")

# --------------------------------------------------
# WRITE CSV
# --------------------------------------------------

with open("games_with_errors.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=white_rows[0].keys())
    writer.writeheader()
    writer.writerows(white_rows + black_rows)

# --------------------------------------------------
# CLEAN SHUTDOWN
# --------------------------------------------------

engine.quit()
print("\nAll done. CSV written to games_with_errors.csv")
