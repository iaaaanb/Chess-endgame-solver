"""
Chess Engine - Core chess logic using python-chess library
Handles game rules, move generation, and endgame positions
"""

import chess


class ChessEngine:
    """
    Chess engine for endgame tablebase solver.
    Uses python-chess for move generation and rule enforcement.
    """
    
    def __init__(self):
        """Initialize with empty board."""
        self.board = chess.Board(fen=None)
        self.move_history = []
        
    def setup_krk_endgame(self, wk_sq='e1', wr_sq='a1', bk_sq='e8'):
        """
        Set up King + Rook vs King endgame position.
        
        Args:
            wk_sq: White king square (e.g., 'e1')
            wr_sq: White rook square (e.g., 'a1')
            bk_sq: Black king square (e.g., 'e8')
        """
        self.board.clear()
        
        # Place pieces
        self.board.set_piece_at(chess.parse_square(wk_sq), chess.Piece(chess.KING, chess.WHITE))
        self.board.set_piece_at(chess.parse_square(wr_sq), chess.Piece(chess.ROOK, chess.WHITE))
        self.board.set_piece_at(chess.parse_square(bk_sq), chess.Piece(chess.KING, chess.BLACK))
        
        # White to move
        self.board.turn = chess.WHITE
        self.move_history = []
        
    def get_board_array(self):
        """
        Convert board to 8x8 array for GUI display.
        Returns: 8x8 list where each element is None or (color, piece_type)
        """
        board_array = [[None for _ in range(8)] for _ in range(8)]
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - chess.square_rank(square)  # Flip for display (rank 8 at top)
                col = chess.square_file(square)
                color = 'white' if piece.color == chess.WHITE else 'black'
                
                # Map piece types
                piece_map = {
                    chess.PAWN: 'P',
                    chess.KNIGHT: 'N',
                    chess.BISHOP: 'B',
                    chess.ROOK: 'R',
                    chess.QUEEN: 'Q',
                    chess.KING: 'K'
                }
                board_array[row][col] = (color, piece_map[piece.piece_type])
                
        return board_array
    
    def get_legal_moves_from_square(self, row, col):
        """
        Get all legal moves from a given square.
        
        Args:
            row: Board row (0-7, 0 is top)
            col: Board column (0-7, 0 is left)
            
        Returns:
            List of (to_row, to_col) tuples for legal destinations
        """
        # Convert row/col to chess square
        square = chess.square(col, 7 - row)
        
        legal_destinations = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                to_row = 7 - chess.square_rank(move.to_square)
                to_col = chess.square_file(move.to_square)
                legal_destinations.append((to_row, to_col))
                
        return legal_destinations
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """
        Attempt to make a move on the board.
        
        Args:
            from_row, from_col: Source square
            to_row, to_col: Destination square
            
        Returns:
            True if move was legal and executed, False otherwise
        """
        from_square = chess.square(from_col, 7 - from_row)
        to_square = chess.square(to_col, 7 - to_row)
        move = chess.Move(from_square, to_square)
        
        if move in self.board.legal_moves:
            self.move_history.append(move)
            self.board.push(move)
            return True
        return False
    
    def undo_move(self):
        """Undo the last move if possible."""
        if self.move_history:
            self.board.pop()
            self.move_history.pop()
            return True
        return False
    
    def get_game_state(self):
        """
        Get current game state.
        
        Returns:
            Dictionary with game state information
        """
        return {
            'turn': 'white' if self.board.turn == chess.WHITE else 'black',
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'is_insufficient_material': self.board.is_insufficient_material(),
            'move_count': len(self.move_history),
            'fen': self.board.fen()
        }
    
    def get_square_notation(self, row, col):
        """Convert row/col to algebraic notation (e.g., 'e4')."""
        file_letter = chr(ord('a') + col)
        rank_number = 8 - row
        return f"{file_letter}{rank_number}"
    
    def is_square_attacked(self, row, col, by_color):
        """
        Check if a square is attacked by the given color.
        
        Args:
            row, col: Square coordinates
            by_color: 'white' or 'black'
            
        Returns:
            True if square is attacked
        """
        square = chess.square(col, 7 - row)
        color = chess.WHITE if by_color == 'white' else chess.BLACK
        return self.board.is_attacked_by(color, square)
    
    def get_piece_at(self, row, col):
        """
        Get piece at given square.
        
        Returns:
            (color, piece_type) tuple or None if empty
        """
        square = chess.square(col, 7 - row)
        piece = self.board.piece_at(square)
        
        if piece:
            color = 'white' if piece.color == chess.WHITE else 'black'
            piece_map = {
                chess.PAWN: 'P',
                chess.KNIGHT: 'N',
                chess.BISHOP: 'B',
                chess.ROOK: 'R',
                chess.QUEEN: 'Q',
                chess.KING: 'K'
            }
            return (color, piece_map[piece.piece_type])
        return None
    
    def load_fen(self, fen_string):
        """Load a position from FEN notation."""
        try:
            self.board = chess.Board(fen_string)
            self.move_history = []
            return True
        except:
            return False
    
    def get_fen(self):
        """Get current position as FEN string."""
        return self.board.fen()
    
    # Methods for tablebase generation
    
    def encode_position(self):
        """
        Encode current position as a unique identifier for tablebase indexing.
        For KRK endgame: returns tuple of (wk_sq, wr_sq, bk_sq, turn)
        """
        pieces = {'wk': None, 'wr': None, 'bk': None}
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                if piece.piece_type == chess.KING:
                    if piece.color == chess.WHITE:
                        pieces['wk'] = square
                    else:
                        pieces['bk'] = square
                elif piece.piece_type == chess.ROOK and piece.color == chess.WHITE:
                    pieces['wr'] = square
        
        return (pieces['wk'], pieces['wr'], pieces['bk'], self.board.turn)
    
    def generate_all_krk_positions(self):
        """
        Generate all legal KRK positions.
        Returns list of FEN strings.
        """
        positions = []
        
        for wk in range(64):
            for wr in range(64):
                for bk in range(64):
                    # Skip if pieces overlap
                    if wk == wr or wk == bk or wr == bk:
                        continue
                    
                    # Skip if kings are adjacent (illegal)
                    wk_rank, wk_file = divmod(wk, 8)
                    bk_rank, bk_file = divmod(bk, 8)
                    if abs(wk_rank - bk_rank) <= 1 and abs(wk_file - bk_file) <= 1:
                        continue
                    
                    # Create position
                    board = chess.Board(fen=None)
                    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
                    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    
                    # Check both white and black to move
                    for turn in [chess.WHITE, chess.BLACK]:
                        board.turn = turn
                        
                        # Skip if black is in check when it's white's turn
                        # (would mean black moved into check)
                        if turn == chess.WHITE and board.is_attacked_by(chess.WHITE, bk):
                            continue
                        
                        # Skip if white is in check when it's black's turn
                        if turn == chess.BLACK and board.is_attacked_by(chess.BLACK, wk):
                            continue
                        
                        positions.append(board.fen())
        
        return positions


# Standalone functions for tablebase analysis

def count_krk_positions():
    """Count total legal KRK positions."""
    engine = ChessEngine()
    positions = engine.generate_all_krk_positions()
    
    checkmates = 0
    stalemates = 0
    
    for fen in positions:
        engine.load_fen(fen)
        if engine.board.is_checkmate():
            checkmates += 1
        elif engine.board.is_stalemate():
            stalemates += 1
    
    print(f"Total legal KRK positions: {len(positions)}")
    print(f"Checkmate positions: {checkmates}")
    print(f"Stalemate positions: {stalemates}")
    print(f"Active positions: {len(positions) - checkmates - stalemates}")
    
    return len(positions)


if __name__ == "__main__":
    # Test the engine
    engine = ChessEngine()
    engine.setup_krk_endgame()
    
    print("Initial KRK endgame position:")
    print(f"FEN: {engine.get_fen()}")
    print()
    
    state = engine.get_game_state()
    print(f"Turn: {state['turn']}")
    print(f"Check: {state['is_check']}")
    print(f"Checkmate: {state['is_checkmate']}")
    print()
    
    # Count positions
    print("Analyzing KRK endgame space...")
    count_krk_positions()