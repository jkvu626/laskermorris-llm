import random
import time
import sys
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import game

def sys_instruct(board, bluePlayer, blue_hand, orange_hand, mills):
    instructions = f"""
    "You are an expert Lasker Morris (Ten Men's Morris) game AI. Given the current board state and the game rules, determine a valid move for the current player.

    Here are the game rules:
    Condensed Lasker Morris Rules:

    Players: Blue and Orange.
    Stones: Each player starts with 10 stones in their hand (h1 for blue, h2 for orange).
    Board Points: Valid points are intersections on the board (e.g., a4, d1). Invalid points exist (e.g. b5).
    Mills: Three stones of the same color in a horizontal or vertical line.
    Moves:
    Format: (A B C)
    A: Source (h1/h2 or board point).
    B: Destination (empty board point).
    C: Removed opponent stone (board point) or "r0" (no removal).
    Initial phase: Stones from hand to empty board points, or stones on board to adjacent empty board points.
    Flying Phase: When a player has 3 stones left, stones can move to any open space.
    Mills: If a move creates a mill, remove one opponent stone (not in a mill unless all opponent stones are in mills).
    Invalid moves result in a loss.
    Game End:
    One player has 2 stones.
    One player is immobilized.
    Illegal move.
    Stalemate (no mills or removals in predefined number of moves)
    Key Considerations for Move Generation:

    Adjacency: Stones can only move to adjacent empty points (unless flying).
    Mills: Prioritize forming mills and removing opponent stones.
    Valid Moves: Ensure moves adhere to all rules.
    Flying: When a player has 3 stones they can move to any open space.
    Stalemate tracking will be needed, but is not needed for individual move generation.

    The current player is: {"blue" if bluePlayer else "orange"}
    Your pieces are denoted by {"h1" if bluePlayer else "h2"}

    Here is the current board state in the form of a python dictionary: {board}

    Here is the number of stones in each players hand: Blue: {blue_hand}, Orange: {orange_hand}

    Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return "no valid move". Do not include any additional text or explanation."

    You want to prioritize forming mills, these mills are represented by this python array: {mills}
    """
    return instructions

client = genai.Client(api_key="AIzaSyCDK_eV3y7ATB0Mr5ERpwCNFfxgbdcTnE8")
game_instance = game.LaskerMorris()
board = game_instance.positions
min_delay = 4

# this should generate a valid fallback move for the player
def gen_fallback_move(player):
    possible_moves = []
    if player == 'X' and game_instance.bluepieces > 0:
        for dest in game_instance.positions:
            if game_instance.positions[dest] is None:
                possible_moves.append(f"h1 {dest} r0")
    elif player == 'O' and game_instance.orangepieces > 0:
        for dest in game_instance.positions:
            if game_instance.positions[dest] is None:
                possible_moves.append(f"h2 {dest} r0")
    else:
        for source, piece in game_instance.positions.items():
            if piece == player:
                for dest in game_instance.adjacent.get(source, []):
                    if game_instance.positions[dest] is None:
                        possible_moves.append(f"{source} {dest} r0")

    for move in possible_moves:
        if game_instance.validate_move(move, player):
            return move
    return None

# this should get a valid move from Gemini or falls back to a generated move
def get_valid_ai_move(ai_player):
    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        try:
            start_time = time.time()
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct(board, bluePlayer, game_instance.bluepieces, game_instance.orangepieces, game_instance.mills)),
                contents=["Provide a single valid move in the format A B C"]
            )
            move = response.text.strip()
            if game_instance.validate_move(move, ai_player):
                elapsed_time = time.time() - start_time
                delay = max(0, min_delay - elapsed_time)
                time.sleep(delay)
                return move
        except ClientError as e:
            error_message = e.args[0]
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                print("Gemini hit quota limit", flush=True)
                time.sleep(5)
                continue
            else:
                print(f"Gemini ClientError: {e}", flush=True)
                break
        attempts += 1
    return get_valid_fallback_move(ai_player)

# this should keep generating fallback moves until a valid one is found
def get_valid_fallback_move(ai_player):
    while True:
        fallback_move = gen_fallback_move(ai_player)
        if fallback_move and game_instance.validate_move(fallback_move, ai_player):
            print(f"Fallback move: {fallback_move}", flush=True)
            return fallback_move
        print("Invalid fallback move...just WRONG!", flush=True)
        if fallback_move is None:
            print("No valid fallback moves are there so the game is ending", flush=True)
            return None

def main():
    global bluePlayer
    player_color = None
    while True:
        try:
            game_input = sys.stdin.readline().strip()
            if game_input in ['blue', 'orange']:
                player_color = game_input
                bluePlayer = (player_color == 'blue')
                ai_player = "X" if bluePlayer else "O"
                if bluePlayer:
                    move = get_valid_ai_move(ai_player)
                    if move:
                        game_instance.apply_move(move, ai_player)
                        print(move, flush=True)
                    else:
                        print("No valid move available so the game is ending", flush=True)
                        break
                continue
            else:
                opponent_player = "O" if bluePlayer else "X"
                if not game_instance.apply_move(game_input.strip(), opponent_player):
                    break
                ai_player = "X" if bluePlayer else "O"
                move = get_valid_ai_move(ai_player)
                if move:
                    game_instance.apply_move(move, ai_player)
                    print(move, flush=True)
                else:
                    print("No valid move available so the game is ending", flush=True)
                    break
                time.sleep(1)
        except (EOFError, BrokenPipeError):
            break
        except Exception as e:
            print(f"Unexpected error: {e}", flush=True)
            break

if __name__ == "__main__":
    main()