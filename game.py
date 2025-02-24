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
        # Places a piece for a player ('X' or 'O') if the position is empty.
        if player == 'X' and self.bluepieces > 0:
            if self.positions[position] is None:
                self.bluepieces -= 1
                self.positions[position] = player
                return True
        elif player == 'O' and self.orangepieces > 0:
            if self.positions[position] is None:
                self.orangepieces -= 1
                self.positions[position] = player
                return True
        return False

    def move(self, start, end, player):
        # Moves a piece if the move is valid.
        if self.positions[start] == player and self.positions[end] is None and end in self.adjacent[start]:
            self.positions[start] = None
            self.positions[end] = player
            return True
        return False

    def capture(self, pos, player):
        if self.positions[pos] == self.opponent(player):
            self.positions[pos] = None
            return True
        return False
    
    def apply_move(self, move, player):
        parts = move.split()
        if len(parts) == 3:
            if parts[0].startswith("h"):
                return self.place(parts[1], player)
            else:
                return self.move(parts[0], parts[1], player)
        return False
    
    def opponent(self, player):
        # Return opposite player (X -> O) (O -> X)
        return 'X' if player == 'O' else 'O'
    # Board Interactions #
