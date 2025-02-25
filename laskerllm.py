import random
import time
import sys
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import game


game = game.LaskerMorris()
board = game.positions

bluePlayer = True # Boolean tracking whether or not to use blue as the player

def sys_instruct():
    instructions= f"""
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

    Here is the number of stones in each players hand: {game.bluepieces if bluePlayer else game.orangepieces}

    Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return "no valid move". Do not include any additional text or explanation."
    """
    return instructions

client = genai.Client(api_key="AIzaSyCDK_eV3y7ATB0Mr5ERpwCNFfxgbdcTnE8")

def validate_move(move, player):
    parts = move.split()
    if len(parts) != 3:
        return False, "Invalid move format"

    source, destination, remove = parts

    if source.startswith("h"):
        if player == 'X' and game.bluepieces <= 0:
            return False, "Nothing left in hand!"
        if player == 'O' and game.orangepieces <= 0:
            return False, "Nothing left in hand!"
        if destination not in game.positions:
            return False, "Invalid destination"
        if game.positions[destination] is not None:
            return False, "Destination is not empty"

        # this is here to check for mills and removals
        game_copy = game.copy()
        game_copy.positions[destination] = player
        if game_copy.is_mill(destination, player):
            if remove == "r0":
                return False, "Mill formed, removal required"
            if remove not in game.positions:
                return False, "Invalid removal position"
            if game_copy.positions[remove] != game_copy.opponent(player):
                return False, "STOP you cannot remove your own piece silly"
            if game_copy.is_opponent_piece_in_mill(remove, game_copy.opponent(player)) and not game_copy.all_opponent_pieces_in_mill(game_copy.opponent(player)):
                return False, "STOP cannot remove opponent's piece from mill cause there are other pieces are available!!!"

        return True, None
    else:
        if source not in game.positions or destination not in game.positions:
            return False, "STOP invalid source or destination"
        if game.positions[source] != player:
            return False, "That is not your piece!!!"
        if game.positions[destination] is not None:
            return False, "OOOO this destination is not empty"
        if destination not in game.adjacent[source]:
            return False, "OOOO this destination is not adjacent"

        # this is here to check for mills and removals
        game_copy = game.copy()
        game_copy.positions[source] = None
        game_copy.positions[destination] = player
        if game_copy.is_mill(destination, player):
            if remove == "r0":
                return False, "Mill formed, removal required"
            if remove not in game.positions:
                return False, "Invalid removal position"
            if game_copy.positions[remove] != game_copy.opponent(player):
                return False, "Cannot remove your own piece"
            if game_copy.is_opponent_piece_in_mill(remove, game_copy.opponent(player)) and not game_copy.all_opponent_pieces_in_mill(game_copy.opponent(player)):
                return False, "Cannot remove opponent's piece from mill when other pieces are available"

        return True, None

def gen_fallback_move(player):
    possible_moves = []
    if player == 'X' and game.bluepieces > 0:
        for dest in game.positions:
            if game.positions[dest] is None:
                possible_moves.append(f"h1 {dest} r0")
    elif player == 'O' and game.orangepieces > 0:
        for dest in game.positions:
            if game.positions[dest] is None:
                possible_moves.append(f"h2 {dest} r0")
    else:
        for source, piece in game.positions.items():
            if piece == player:
                for dest in game.adjacent[source]:
                    if game.positions[dest] is None:
                        possible_moves.append(f"{source} {dest} r0")

    if possible_moves:
        return random.choice(possible_moves)
    else:
        return None

# Game loop - INTEGRATE THIS WITH REFEREE
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
                            system_instruction=sys_instruct()),
                        contents=[f"""Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). {"Note that the player is in flying phase." if game.is_able_to_fly("blue") else ""} If no valid move is possible, return no valid move. Do not include any additional text or explanation."""]
                    )
                    move = response.text.strip()
                    valid, error_message = validate_move(move, ai_player)

                    if valid:
                        game.apply_move(move, ai_player)
                        print(move, flush=True)
                    else:
                        fallback_move = gen_fallback_move(ai_player)
                        if fallback_move:
                            valid_fallback, fallback_error = validate_move(fallback_move, ai_player)
                            if valid_fallback:
                                game.apply_move(fallback_move, ai_player)
                                print(fallback_move, flush=True)
                            else:
                                print(f"Fallback move {fallback_move} also invalid: {fallback_error}", flush=True)
                                break
                        else:
                            print(f"No valid or fallback move available. Original error: {error_message}", flush=True)
                            break
                continue

            else:
                opponent_player = "O" if bluePlayer else "X"
                game.apply_move(game_input.strip(), opponent_player)

                ai_player = "X" if bluePlayer else "O"
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct()),
                        contents=[f"""Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). {"Note that the player is in flying phase." if game.is_able_to_fly("orange") else ""} If no valid move is possible, return no valid move. Do not include any additional text or explanation."""]
                    )
                    move = response.text.strip()

                    valid, error_message = validate_move(move, ai_player)

                    if valid:
                        game.apply_move(move, ai_player)
                        print(move, flush=True)
                    else:
                        fallback_move = gen_fallback_move(ai_player)
                        if fallback_move:
                            valid_fallback, fallback_error = validate_move(fallback_move, ai_player)
                            if valid_fallback:
                                game.apply_move(fallback_move, ai_player)
                                print(fallback_move, flush=True)
                            else:
                                print(f"Fallback move {fallback_move} also invalid: {fallback_error}", flush=True)
                                break
                        else:
                            print(f"No valid or fallback move available: {error_message}", flush=True)
                            break
                    time.sleep(1)
                except ClientError as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        print("Oh my goodness the rate limit exceeded again im so angry!!!", flush=True)
                        time.sleep(10)
                        continue
                    else:
                        print(f"Opps an unexpected error occurred: {e}", flush=True)
                        break


        except EOFError:
            break
        except BrokenPipeError:
            break
        except Exception as e:
            print(f"Opps an unexpected error occurred: {e}", flush=True)
            break

if __name__ == "__main__":
    main()