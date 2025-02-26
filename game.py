import copy
import random

class LaskerMorris:
    def __init__(self):
        # Board positions as nodes with valid moves (graph adjacency list)
        self.adjacent = {
            "a7": ["a4", "d7"], "d7": ["a7", "g7", "d6"], "g7": ["d7", "g4"],
            "b6": ["b4", "d6"], "d6": ["d7", "b6", "f6", "d5"], "f6": ["d6", "f4"],
            "c5": ["d5", "c4"], "d5": ["d6", "c5", "e5"], "e5": ["d5", "e4"],
            "a4": ["a7", "b4", "a1"], "b4": ["b6", "a4", "c4", "b2"], "c4": ["c5", "b4", "c3"],
            "e4": ["e5", "f4", "e3"], "f4": ["f6", "e4", "g4", "f2"], "g4": ["g7", "f4", "g1"],
            "c3": ["c4", "d3"], "d3": ["c3", "e3", "d2"], "e3": ["e4", "d3"],
            "b2": ["b4", "d2"], "d2": ["d3", "b2", "f2", "d1"], "f2": ["f4", "d2"],
            "a1": ["a4", "d1"], "d1": ["d2", "a1", "g1"], "g1": ["g4", "d1"]
        }

        # Mills (winning sets)
        self.mills = [
            ["a7", "d7", "g7"], ["b6", "d6", "f6"], ["c5", "d5", "e5"],
            ["a4", "b4", "c4"], ["e4", "f4", "g4"],
            ["c3", "d3", "e3"], ["b2", "d2", "f2"], ["a1", "d1", "g1"],
            ["a7", "a4", "a1"], ["b6", "b4", "b2"], ["c5", "c4", "c3"],
            ["d7", "d6", "d5"], ["d3", "d2", "d1"],
            ["e5", "e4", "e3"], ["f6", "f4", "f2"], ["g7", "g4", "g1"]
        ]

        # Track board positions
        self.positions = {pos: None for pos in self.adjacent.keys()}
        self.bluepieces = 10
        self.orangepieces = 10
        self.phase = "Placing"
        self.move_history = []
        self.stalemate_count = 0
        self.stalemate_threshold = 20


    def display(self):
        board_layout = [
            f"{self.get_symbol('a7')}--------{self.get_symbol('d7')}--------{self.get_symbol('g7')}",
            f"|        |        |",
            f"|  {self.get_symbol('b6')}-----{self.get_symbol('d6')}-----{self.get_symbol('f6')}  |",
            f"|  |     |     |  |",
            f"|  |  {self.get_symbol('c5')}--{self.get_symbol('d5')}--{self.get_symbol('e5')}  |  |",
            f"|  |  |     |  |  |",
            f"{self.get_symbol('a4')}--{self.get_symbol('b4')}--{self.get_symbol('c4')}     {self.get_symbol('e4')}--{self.get_symbol('f4')}--{self.get_symbol('g4')}",
            f"|  |  |     |  |  |",
            f"|  |  {self.get_symbol('c3')}--{self.get_symbol('d3')}--{self.get_symbol('e3')}  |  |",
            f"|  |     |     |  |",
            f"|  {self.get_symbol('b2')}-----{self.get_symbol('d2')}-----{self.get_symbol('f2')}  |",
            f"|        |        |",
            f"{self.get_symbol('a1')}--------{self.get_symbol('d1')}--------{self.get_symbol('g1')}",
        ]

        for line in board_layout:
            print(line)
        print()

    def get_symbol(self, pos):
        # Returns the symbol of a position or a placeholder if empty.
        return self.positions[pos] if self.positions[pos] else "+"

    # Board Interactions #
    def place(self, position, player):
    # Only place if the position is empty and the player still has stones to place
        if position in self.positions and self.positions[position] is None:
            if player == 'X' and self.bluepieces > 0:
                self.bluepieces -= 1
                self.positions[position] = player
                return True
            elif player == 'O' and self.orangepieces > 0:
                self.orangepieces -= 1
                self.positions[position] = player
                return True
        return False  # Invalid placement


    def move(self, start, end, player):
        if self.positions.get(start) != player:
            return False
        if self.positions.get(end) is not None:
            return False
        remaining_stones = sum(1 for pos in self.positions if self.positions[pos] == player)
        if remaining_stones > 3:
            if end not in self.adjacent.get(start, []):
                return False

        # Flying Phase
        self.positions[start] = None
        self.positions[end] = player
        return True

    def capture(self, pos, player):
        if pos in self.positions and self.positions[pos] == self.opponent(player):
            self.positions[pos] = None
            return True
        return False
    
    def update_phase(self):
        blue_stones_on_board = sum(1 for pos in self.positions if self.positions[pos] == 'X')
        orange_stones_on_board = sum(1 for pos in self.positions if self.positions[pos] == 'O')
        blue_total = blue_stones_on_board + self.bluepieces
        orange_total = orange_stones_on_board + self.orangepieces

        # When all stones are placed move to Moving Phase
        if self.phase == "Placing" and self.bluepieces == 0 and self.orangepieces == 0:
            self.phase = "Moving"

        # When a player has only 3 pieces left on the board move to Flying Phase
        elif self.phase == "Moving":
            if blue_stones_on_board == 3 or orange_stones_on_board == 3:
                self.phase = "Flying"

    def validate_move(self, move, player):
        parts = move.split()
        if len(parts) != 3:
            return False

        source, destination, remove = parts
        if source.startswith("h"):
            if (player == 'X' and self.bluepieces <= 0) or (player == 'O' and self.orangepieces <= 0):
                return False
            if destination not in self.positions or self.positions[destination] is not None:
                return False

            # Mill validation
            temp_game = self.copy()
            temp_game.positions[destination] = player
            if temp_game.is_mill(destination, player):
                if remove == "r0":
                    return False
                if remove not in self.positions or temp_game.positions[remove] != temp_game.opponent(player):
                    return False
                if temp_game.is_opponent_piece_in_mill(remove, temp_game.opponent(player)) and not temp_game.all_opponent_pieces_in_mill(temp_game.opponent(player)):
                    return False
            elif remove != "r0":
                return False
            return True

        # Moving a piece
        if self.positions.get(source) != player or self.positions.get(destination) is not None:
            return False

        # Check flying phase
        player_stones = sum(1 for pos in self.positions if self.positions[pos] == player)
        if player_stones > 3 and destination not in self.adjacent.get(source, []):
            return False

        # Mill validation after moving
        temp_game = self.copy()
        temp_game.positions[source] = None
        temp_game.positions[destination] = player
        if temp_game.is_mill(destination, player):
            if remove == "r0":
                return False
            if remove not in self.positions or temp_game.positions[remove] != temp_game.opponent(player):
                return False
            if temp_game.is_opponent_piece_in_mill(remove, temp_game.opponent(player)) and not temp_game.all_opponent_pieces_in_mill(temp_game.opponent(player)):
                return False
        elif remove != "r0":
            return False

        return True

    # total number of stones a player has
    def count_stones(self, player):
        return sum(1 for pos in self.positions if self.positions[pos] == player) + (self.bluepieces if player == 'X' else self.orangepieces)

    # any valid moves
    def player_has_valid_moves(self, player):
        for source, piece in self.positions.items():
            if piece == player:
                for dest in self.adjacent.get(source, []):
                    if self.positions[dest] is None:
                        return True
        return False

    # check to see if game should end yay!
    def is_game_over(self, last_move_player):
        opponent = self.opponent(last_move_player)
        if self.count_stones(last_move_player) <= 2:
            return True
        if self.player_has_valid_moves(last_move_player) is False:
            return True
        if self.stalemate_count >= self.stalemate_threshold:
            return True
        return False

    def apply_move(self, move, player):
        if not self.validate_move(move, player):
            return False

        source, destination, remove = move.split()
        opponent_player = self.opponent(player)

        # placing piece from hand
        if source.startswith("h"):
            if player == 'X':
                self.bluepieces -= 1
            else:
                self.orangepieces -= 1
            self.positions[destination] = player
        else:
            # moving piece on the board
            self.positions[source] = None
            self.positions[destination] = player

        # check for mills and removals
        if self.is_mill(destination, player):
            self.stalemate_count = 0
            self.capture(remove, player)
        else:
            self.stalemate_count += 1
        self.update_phase()
        return not self.is_game_over(player)


    def opponent(self, player):
        # Return opposite player (X -> O) (O -> X)
        return 'X' if player == 'O' else 'O'
    # Board Interactions #

    def copy(self):
        new_game = LaskerMorris()
        new_game.positions = copy.deepcopy(self.positions)
        new_game.bluepieces = self.bluepieces
        new_game.orangepieces = self.orangepieces
        return new_game

    def is_mill(self, position, player):
      # checks if a mill is formed
        for mill in self.mills:
            if position in mill:
                if all(self.positions[p] == player for p in mill):
                    return True
        return False
    
    def is_opponent_piece_in_mill(self, position, opponent_player):
      # checks if an opponent piece is in a mill
        for mill in self.mills:
          if position in mill:
            if all(self.positions[p] == opponent_player for p in mill):
              return True
        return False

    def all_opponent_pieces_in_mill(self, opponent_player):
      # checks if all opponent pieces are in a mill
      opponent_pieces = [pos for pos, piece in self.positions.items() if piece == opponent_player]
      if not opponent_pieces:
        return False

      for piece in opponent_pieces:
        if not self.is_opponent_piece_in_mill(piece, opponent_player):
          return False
      return True
    
    def best_capture(self, player):
        opponent = self.opponent(player)
        possible_captures = []

        for pos in self.positions:
            if self.positions[pos] == opponent:
               possible_captures.append(pos)

        if possible_captures:
            return random.choice(possible_captures)
        else:
            return None
        

