import random
import time
import sys
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import game

client = genai.Client(api_key="AIzaSyCDK_eV3y7ATB0Mr5ERpwCNFfxgbdcTnE8")
game_instance = game.LaskerMorris()
board = game_instance.positions

def sys_instruct(board):
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

    Here is the number of stones in each players hand: {game_instance.bluepieces if bluePlayer else game_instance.orangepieces}

    Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return "no valid move". Do not include any additional text or explanation."

    You want to prioritize forming mills, these mills are represented by this python array: {game_instance.mills}
    """
    return instructions

def log(x, y):
    if x:
        with open("app.log", "a") as file: 
            file.write(f"AI MOVE: {y}\n")
    else:
        with open("app.log", "a") as file: 
            file.write(f"FEEDBACK MOVE: {y}\n")
        
def validate_move(move, player):
    if player == 'X':
        pieces = game_instance.bluepieces
    elif player == 'O':
        pieces = game_instance.orangepieces
    else:
        return False

    parts = move.split()
    if len(parts) != 3:
        return False

    source, destination, remove = parts

    # 1. **Check if it's a placement move (h1/h2)**
    if source.startswith('h'):
        if pieces <= 0:  # No pieces left in hand
            return False
        if destination not in game_instance.positions:  # Invalid board position
            return False
        if game_instance.positions[destination] is not None:  # Position already occupied
            return False

    # 2. **Check if it's a movement move**
    else:
        if source not in game_instance.positions or destination not in game_instance.positions:
            return False  # Invalid board positions
        
        if game_instance.positions[source] != player:  # Source doesn't belong to player
            return False
        
        if game_instance.positions[destination] is not None:  # Destination occupied
            return False

        # Check if the move is adjacent (unless in flying phase)
        if pieces > 3 and destination not in game_instance.adjacent[source]:
            return False  # Regular moves must be adjacent

    # 3. **If a mill is formed, check capture rules**
    if game_instance.is_mill(move, player):
        if remove not in game_instance.positions or game_instance.positions[remove] != game_instance.opponent(player):
            return False  # Can only remove opponent's piece

        # Check if opponent has non-mill pieces
        opponent_pieces = [pos for pos in game_instance.positions if game_instance.positions[pos] == game_instance.opponent(player)]
        opponent_mill_pieces = [pos for pos in opponent_pieces if any(all(game_instance.positions[p] == game_instance.opponent(player) for p in mill) for mill in game_instance.mills)]

        if remove in opponent_mill_pieces and len(opponent_pieces) != len(opponent_mill_pieces):
            return False  # Cannot remove from a mill unless no other options exist

    return True


def gen_fallback_move(player):
    possible_moves = game_instance.get_moves(player)
    random.shuffle(possible_moves)  # Shuffle to get a random move first

    for move in possible_moves:
        parts = move.split()
        if game_instance.is_mill(move, player):
            parts[2] = game_instance.best_capture(player)  # Assign best capture
        else:
            parts[2] = 'r0'  # Default no capture

        fallback_move = ' '.join(parts)
        
        if validate_move(fallback_move, player):
            return fallback_move  # Return first valid fallback move

    return None  # No valid fallback move found


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
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct(board)),
                        contents=["Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return no valid move. Do not include any additional text or explanation."]
                    )
                    move = response.text.strip()
                    valid = validate_move(move, ai_player)

                    if valid:
                        log(True, move)
                        game_instance.apply_move(move, ai_player)
                        print(move, flush=True)
                    else:
                        fallback_move = gen_fallback_move(ai_player)
                        if fallback_move:
                            valid_fallback = validate_move(fallback_move, ai_player)
                            if valid_fallback:
                                log(False, move)
                                game_instance.apply_move(fallback_move, ai_player)
                                print(fallback_move, flush=True)
                            else:
                                log(False, move)
                                print(f"Fallback move {fallback_move} also invalid", flush=True)
                                break
                        else:
                            print(f"No valid or fallback move available.", flush=True)
                            break
                continue

            else:
                opponent_player = "O" if bluePlayer else "X"
                game_instance.apply_move(game_input.strip(), opponent_player)

                ai_player = "X" if bluePlayer else "O"
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct(board)),
                        contents=["Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return no valid move. Do not include any additional text or explanation."]
                    )
                    move = response.text.strip()
                    valid= validate_move(move, ai_player)

                    if valid:
                        log(True, move)
                        game_instance.apply_move(move, ai_player)
                        print(move, flush=True)
                    else:
                        fallback_move = gen_fallback_move(ai_player)
                        if fallback_move:
                            valid_fallback = validate_move(fallback_move, ai_player)
                            if valid_fallback:
                                log(False, move)
                                game_instance.apply_move(fallback_move, ai_player)
                                print(fallback_move, flush=True)
                            else:
                                log(False, move)
                                print(f"Fallback move {fallback_move}", flush=True)
                                break
                        else:
                            print(f"No valid or fallback move available", flush=True)
                            break
                    time.sleep(3)
                except ClientError as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        fallback_move = gen_fallback_move(ai_player)
                        with open("app.log", "a") as file: 
                            file.write(f"429 ERROR FALLBACK MOVE: {move}\n")
                        game_instance.apply_move(fallback_move, ai_player)
                        print(fallback_move, flush=True)
                        time.sleep(3)
                        continue
                    else:
                        print(f"Oops an unexpected error occurred: {e}", flush=True)
                        break

        except EOFError:
            break
        except BrokenPipeError:
            break
        except Exception as e:
            print(f"EXCEPTION: {e}", flush=True)
            break

if __name__ == "__main__":
    main()