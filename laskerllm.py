from google import genai
from google.genai import types
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

    Here is the current board state in the form of a python dictionary: {board}

    Here is the number of stones in each players hand: {game.bluepieces if bluePlayer else game.orangepieces}

    The current player is: {"blue" if bluePlayer else "orange"}

    Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return "no valid move". Do not include any additional text or explanation."
    """
    return instructions

client = genai.Client(api_key="AIzaSyCDK_eV3y7ATB0Mr5ERpwCNFfxgbdcTnE8")

# Game loop - INTEGRATE THIS WITH REFEREE
for i in range(3):
    player = "X" if bluePlayer else "O"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct()),
        contents=["Provide a single valid move in the format A B C, where A is the source, B is the destination, and C is the stone to remove (or r0 if not returning a stone). If no valid move is possible, return no valid move. Do not include any additional text or explanation."]
    )

    move = response.text  # Access the text content
    if move:
        game.apply_move(move, player)
        print(f"Best Move: {move} Iteration: {i + 1} Player: {player}")
    else:
        print("API returned no move.")
    bluePlayer = not bluePlayer
    