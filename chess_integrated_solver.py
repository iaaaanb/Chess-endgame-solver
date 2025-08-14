"""
Integrated Chess Endgame Solver with Tablebase
Allows position setup and shows optimal checkmate sequences
"""

import pygame
import sys
import chess
import pickle
import time
import os
from collections import deque


class TablebaseGenerator:
    """Simplified tablebase generator for KRK endgames."""
    
    def __init__(self):
        self.tablebase = {}
        
    def generate_or_load(self):
        """Generate tablebase or load from file if exists."""
        if os.path.exists('krk_tablebase_fixed.pkl'):
            print("Loading existing tablebase...")
            with open('krk_tablebase_fixed.pkl', 'rb') as f:
                self.tablebase = pickle.load(f)
            print(f"Loaded {len(self.tablebase)} positions")
        else:
            print("Generating tablebase (this will take a few minutes)...")
            self.generate_tablebase()
            self.save_tablebase()
    
    def generate_tablebase(self):
        """Generate complete KRK tablebase using backward induction."""
        print("Generating all legal KRK positions...")
        all_positions = self._generate_all_positions()
        print(f"Found {len(all_positions)} legal positions")
        
        # Find checkmates (DTM = 0)
        checkmates = set()
        for fen in all_positions:
            board = chess.Board(fen)
            if board.is_checkmate():
                checkmates.add(fen)
                self.tablebase[fen] = (0, None)
        
        print(f"Found {len(checkmates)} checkmate positions")
        
        # Find stalemates
        for fen in all_positions:
            board = chess.Board(fen)
            if board.is_stalemate():
                self.tablebase[fen] = ('DRAW', None)
        
        # Backward induction
        print("Running backward induction...")
        current_wave = checkmates.copy()
        current_dtm = 0
        
        while current_wave and current_dtm < 50:
            next_wave = set()
            current_dtm += 1
            
            # Process each position in current wave
            for fen in current_wave:
                board = chess.Board(fen)
                
                # Find predecessors
                for test_fen in all_positions:
                    if test_fen in self.tablebase:
                        continue
                        
                    test_board = chess.Board(test_fen)
                    
                    # Check if this position can reach current position
                    for move in test_board.legal_moves:
                        test_board.push(move)
                        if test_board.fen() == fen:
                            # Found a predecessor
                            test_board.pop()
                            
                            # Check if it's a forced mate
                            if self._check_forced_mate(test_board, current_dtm):
                                best_move = self._find_best_move(test_board)
                                self.tablebase[test_fen] = (current_dtm, best_move)
                                next_wave.add(test_fen)
                            break
                        test_board.pop()
            
            if next_wave:
                print(f"DTM {current_dtm}: {len(next_wave)} positions")
            current_wave = next_wave
        
        # Mark remaining as draws
        for fen in all_positions:
            if fen not in self.tablebase:
                self.tablebase[fen] = ('DRAW', None)
    
    def _generate_all_positions(self):
        """Generate all legal KRK positions."""
        positions = set()
        
        for wk in range(64):
            for wr in range(64):
                for bk in range(64):
                    if wk == wr or wk == bk or wr == bk:
                        continue
                    
                    # Check kings not adjacent
                    wk_rank, wk_file = divmod(wk, 8)
                    bk_rank, bk_file = divmod(bk, 8)
                    if abs(wk_rank - bk_rank) <= 1 and abs(wk_file - bk_file) <= 1:
                        continue
                    
                    for turn in [chess.WHITE, chess.BLACK]:
                        board = chess.Board(fen=None)
                        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
                        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                        board.turn = turn
                        
                        # Validate
                        if turn == chess.WHITE:
                            if board.is_attacked_by(chess.BLACK, wk):
                                continue
                        
                        positions.add(board.fen())
        
        return positions
    
    def _check_forced_mate(self, board, dtm):
        """Check if position has forced mate."""
        if board.turn == chess.WHITE:
            # White needs a move leading to mate in dtm-1
            for move in board.legal_moves:
                board.push(move)
                next_fen = board.fen()
                board.pop()
                
                if next_fen in self.tablebase:
                    next_dtm = self.tablebase[next_fen][0]
                    if next_dtm == dtm - 1:
                        return True
            return False
        else:
            # Black: all moves must lead to mate
            if not board.legal_moves:
                return False
            
            for move in board.legal_moves:
                board.push(move)
                next_fen = board.fen()
                board.pop()
                
                if next_fen not in self.tablebase:
                    return False
                
                next_dtm = self.tablebase[next_fen][0]
                if next_dtm == 'DRAW' or next_dtm >= dtm:
                    return False
            
            return True
    
    def _find_best_move(self, board):
        """Find best move for current position."""
        best_move = None
        best_dtm = float('inf')
        
        for move in board.legal_moves:
            board.push(move)
            next_fen = board.fen()
            board.pop()
            
            if next_fen in self.tablebase:
                next_dtm = self.tablebase[next_fen][0]
                if next_dtm != 'DRAW' and next_dtm < best_dtm:
                    best_dtm = next_dtm
                    best_move = move.uci()
        
        return best_move
    
    def save_tablebase(self):
        """Save tablebase to file."""
        with open('krk_tablebase_fixed.pkl', 'wb') as f:
            pickle.dump(self.tablebase, f)
        print("Tablebase saved")
    
    def query(self, fen):
        """Query tablebase for position."""
        if fen in self.tablebase:
            return self.tablebase[fen]
        return (None, None)


# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 640
BOARD_SIZE = 8
SQUARE_SIZE = WINDOW_SIZE // BOARD_SIZE
INFO_HEIGHT = 150

# Colors
WHITE_SQUARE = (240, 217, 181)
BLACK_SQUARE = (181, 136, 99)
SELECTED_COLOR = (0, 255, 0, 100)
BEST_MOVE_COLOR = (0, 255, 255, 100)
CHECK_COLOR = (255, 0, 0, 100)
SETUP_HIGHLIGHT = (255, 255, 0, 100)

# Piece colors
WHITE_PIECE = (255, 255, 255)
BLACK_PIECE = (40, 40, 40)
PIECE_OUTLINE = (0, 0, 0)


class ChessEndgameSolver:
    def __init__(self):
        """Initialize the integrated endgame solver."""
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + INFO_HEIGHT))
        pygame.display.set_caption("KRK Endgame Solver - Optimal Checkmate Finder")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 32)
        
        # Chess board
        self.board = chess.Board(fen=None)
        self.setup_default_position()
        
        # Tablebase
        self.tablebase = TablebaseGenerator()
        self.tablebase.generate_or_load()
        
        # GUI state
        self.running = True
        self.setup_mode = True  # Start in setup mode
        self.selected_square = None
        self.selected_piece = None  # For setup mode
        self.best_move_squares = []  # Highlight best move
        self.auto_play = False
        self.auto_play_delay = 1000  # milliseconds
        self.last_auto_play = 0
        
    def setup_default_position(self):
        """Set up default KRK position."""
        self.board.clear()
        self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        self.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
        self.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        self.board.turn = chess.WHITE
    
    def draw_board(self):
        """Draw the chessboard."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # Base square color
                color = WHITE_SQUARE if (row + col) % 2 == 0 else BLACK_SQUARE
                rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                  SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                
                # Highlight selected square in setup mode
                if self.setup_mode and self.selected_square == (row, col):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    s.set_alpha(100)
                    s.fill((255, 255, 0))
                    self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Highlight best move
                if (row, col) in self.best_move_squares:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    s.set_alpha(100)
                    s.fill((0, 255, 255))
                    self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Check highlight
                if self.board.is_check():
                    square = chess.square(col, 7 - row)
                    piece = self.board.piece_at(square)
                    if piece and piece.piece_type == chess.KING:
                        if piece.color == self.board.turn:
                            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                            s.set_alpha(100)
                            s.fill((255, 0, 0))
                            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Coordinates
                if col == 0:
                    text = self.small_font.render(str(8 - row), True, (100, 100, 100))
                    self.screen.blit(text, (2, row * SQUARE_SIZE + 2))
                if row == 7:
                    text = self.small_font.render(chr(ord('a') + col), True, (100, 100, 100))
                    self.screen.blit(text, (col * SQUARE_SIZE + SQUARE_SIZE - 15, 
                                           WINDOW_SIZE - 18))
    
    def draw_pieces(self):
        """Draw chess pieces."""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - chess.square_rank(square)
                col = chess.square_file(square)
                self._draw_piece(row, col, piece)
    
    def _draw_piece(self, row, col, piece):
        """Draw a single chess piece."""
        center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
        
        piece_color = WHITE_PIECE if piece.color == chess.WHITE else BLACK_PIECE
        outline_color = BLACK_PIECE if piece.color == chess.WHITE else WHITE_PIECE
        
        if piece.piece_type == chess.KING:
            # Crown
            size = SQUARE_SIZE // 3
            pygame.draw.circle(self.screen, piece_color, (center_x, center_y + 5), size)
            pygame.draw.circle(self.screen, outline_color, (center_x, center_y + 5), size, 2)
            
            # Crown points
            crown_points = [
                (center_x - size, center_y),
                (center_x - size//2, center_y - size//2),
                (center_x, center_y),
                (center_x + size//2, center_y - size//2),
                (center_x + size, center_y)
            ]
            pygame.draw.polygon(self.screen, piece_color, crown_points)
            pygame.draw.polygon(self.screen, outline_color, crown_points, 2)
            
            # Cross
            cross_size = size // 3
            pygame.draw.line(self.screen, outline_color,
                           (center_x, center_y - size//2 - cross_size),
                           (center_x, center_y - size//2 + cross_size), 2)
            pygame.draw.line(self.screen, outline_color,
                           (center_x - cross_size//2, center_y - size//2),
                           (center_x + cross_size//2, center_y - size//2), 2)
            
        elif piece.piece_type == chess.ROOK:
            # Tower
            size = SQUARE_SIZE // 3
            body_rect = pygame.Rect(center_x - size, center_y - size//2,
                                   size * 2, size + size//2)
            pygame.draw.rect(self.screen, piece_color, body_rect)
            pygame.draw.rect(self.screen, outline_color, body_rect, 2)
            
            # Battlements
            bw = size // 2
            for i in range(3):
                x = center_x - size + i * bw * 2
                battlement = pygame.Rect(x, center_y - size, bw, size//2)
                pygame.draw.rect(self.screen, piece_color, battlement)
                pygame.draw.rect(self.screen, outline_color, battlement, 2)
            
            # Base
            base_rect = pygame.Rect(center_x - size - 5, center_y + size//2,
                                   size * 2 + 10, size//3)
            pygame.draw.rect(self.screen, piece_color, base_rect)
            pygame.draw.rect(self.screen, outline_color, base_rect, 2)
    
    def draw_info_panel(self):
        """Draw the information panel."""
        # Background
        panel_rect = pygame.Rect(0, WINDOW_SIZE, WINDOW_SIZE, INFO_HEIGHT)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.line(self.screen, (180, 180, 180), 
                        (0, WINDOW_SIZE), (WINDOW_SIZE, WINDOW_SIZE), 2)
        
        y_offset = WINDOW_SIZE + 10
        
        if self.setup_mode:
            # Setup mode instructions
            title = self.big_font.render("SETUP MODE", True, (0, 0, 255))
            self.screen.blit(title, (10, y_offset))
            
            turn_text = f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}"
            turn_surface = self.font.render(turn_text, True, (0, 0, 0))
            self.screen.blit(turn_surface, (10, y_offset + 35))
            
            instructions = [
                "1: White King  2: White Rook  3: Black King",
                "Click square to place/remove piece",
                "T: Toggle turn  SPACE: Start solving  R: Reset"
            ]
            for i, text in enumerate(instructions):
                surf = self.small_font.render(text, True, (50, 50, 50))
                self.screen.blit(surf, (10, y_offset + 60 + i * 20))
            
            # Selected piece indicator
            if self.selected_piece:
                piece_names = {
                    ('white', chess.KING): "White King",
                    ('white', chess.ROOK): "White Rook",
                    ('black', chess.KING): "Black King"
                }
                selected = piece_names.get(self.selected_piece, "")
                surf = self.font.render(f"Selected: {selected}", True, (0, 150, 0))
                self.screen.blit(surf, (350, y_offset + 35))
        else:
            # Solve mode - show tablebase info
            fen = self.board.fen()
            dtm, best_move = self.tablebase.query(fen)
            
            # Status
            if self.board.is_checkmate():
                status = "CHECKMATE!"
                color = (255, 0, 0)
            elif self.board.is_stalemate():
                status = "STALEMATE"
                color = (128, 128, 0)
            elif dtm == 'DRAW':
                status = "DRAW POSITION"
                color = (100, 100, 100)
            elif dtm is not None:
                status = f"MATE IN {dtm} MOVES"
                color = (0, 150, 0)
            else:
                status = "Position not in tablebase"
                color = (150, 0, 0)
            
            status_surf = self.big_font.render(status, True, color)
            self.screen.blit(status_surf, (10, y_offset))
            
            # Turn and best move
            turn_text = f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}"
            turn_surf = self.font.render(turn_text, True, (0, 0, 0))
            self.screen.blit(turn_surf, (10, y_offset + 40))
            
            if best_move:
                move_text = f"Best move: {best_move}"
                move_surf = self.font.render(move_text, True, (0, 0, 255))
                self.screen.blit(move_surf, (10, y_offset + 65))
            
            # Controls
            controls = [
                "SPACE: Play best move  A: Auto-play  S: Setup mode",
                "U: Undo  R: Reset  ESC: Quit"
            ]
            for i, text in enumerate(controls):
                surf = self.small_font.render(text, True, (50, 50, 50))
                self.screen.blit(surf, (10, y_offset + 90 + i * 20))
            
            # Auto-play indicator
            if self.auto_play:
                auto_surf = self.font.render("AUTO-PLAY ON", True, (255, 0, 0))
                self.screen.blit(auto_surf, (500, y_offset + 40))
    
    def handle_click(self, pos):
        """Handle mouse clicks."""
        x, y = pos
        
        if y >= WINDOW_SIZE:
            return
        
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.setup_mode:
                # Place/remove piece
                square = chess.square(col, 7 - row)
                
                if self.selected_piece:
                    # Remove existing piece of same type
                    color, piece_type = self.selected_piece
                    chess_color = chess.WHITE if color == 'white' else chess.BLACK
                    
                    # Remove old piece of same type
                    for sq in chess.SQUARES:
                        piece = self.board.piece_at(sq)
                        if piece and piece.piece_type == piece_type and piece.color == chess_color:
                            self.board.remove_piece_at(sq)
                    
                    # Place new piece
                    self.board.set_piece_at(square, chess.Piece(piece_type, chess_color))
                else:
                    # Remove piece at clicked square
                    self.board.remove_piece_at(square)
                
                self.selected_square = (row, col)
    
    def update_best_move_highlight(self):
        """Update highlighting for best move."""
        self.best_move_squares = []
        
        if not self.setup_mode:
            fen = self.board.fen()
            dtm, best_move = self.tablebase.query(fen)
            
            if best_move:
                # Parse move
                from_sq = chess.parse_square(best_move[:2])
                to_sq = chess.parse_square(best_move[2:4])
                
                from_row = 7 - chess.square_rank(from_sq)
                from_col = chess.square_file(from_sq)
                to_row = 7 - chess.square_rank(to_sq)
                to_col = chess.square_file(to_sq)
                
                self.best_move_squares = [(from_row, from_col), (to_row, to_col)]
    
    def play_best_move(self):
        """Play the best move according to tablebase."""
        fen = self.board.fen()
        dtm, best_move = self.tablebase.query(fen)
        
        if best_move:
            move = chess.Move.from_uci(best_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                print(f"Played: {best_move} (Mate in {dtm})")
                self.update_best_move_highlight()
                return True
        return False
    
    def validate_position(self):
        """Check if current position is valid KRK."""
        pieces = {'wk': 0, 'wr': 0, 'bk': 0}
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                if piece.piece_type == chess.KING:
                    if piece.color == chess.WHITE:
                        pieces['wk'] += 1
                    else:
                        pieces['bk'] += 1
                elif piece.piece_type == chess.ROOK and piece.color == chess.WHITE:
                    pieces['wr'] += 1
        
        return pieces['wk'] == 1 and pieces['wr'] == 1 and pieces['bk'] == 1
    
    def run(self):
        """Main game loop."""
        print("KRK Endgame Solver - Find Optimal Checkmate")
        print("=" * 45)
        print("Setup your position and find the fastest mate!")
        
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # Auto-play
            if self.auto_play and not self.setup_mode:
                if current_time - self.last_auto_play > self.auto_play_delay:
                    if not self.play_best_move():
                        self.auto_play = False
                    self.last_auto_play = current_time
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    
                    elif event.key == pygame.K_r:
                        self.setup_default_position()
                        self.setup_mode = True
                        self.auto_play = False
                        print("Reset to default position")
                    
                    elif event.key == pygame.K_s:
                        self.setup_mode = True
                        self.auto_play = False
                        self.selected_piece = None
                        print("Entered setup mode")
                    
                    elif event.key == pygame.K_SPACE:
                        if self.setup_mode:
                            if self.validate_position():
                                self.setup_mode = False
                                self.update_best_move_highlight()
                                print("Started solving mode")
                            else:
                                print("Invalid position! Need 1 white king, 1 white rook, 1 black king")
                        else:
                            self.play_best_move()
                    
                    elif event.key == pygame.K_t and self.setup_mode:
                        self.board.turn = chess.BLACK if self.board.turn == chess.WHITE else chess.WHITE
                        print(f"Turn set to: {'White' if self.board.turn == chess.WHITE else 'Black'}")
                    
                    elif event.key == pygame.K_a and not self.setup_mode:
                        self.auto_play = not self.auto_play
                        self.last_auto_play = current_time
                        print(f"Auto-play: {'ON' if self.auto_play else 'OFF'}")
                    
                    elif event.key == pygame.K_u and not self.setup_mode:
                        if self.board.move_stack:
                            self.board.pop()
                            self.update_best_move_highlight()
                            print("Move undone")
                    
                    # Piece selection in setup mode
                    elif self.setup_mode:
                        if event.key == pygame.K_1:
                            self.selected_piece = ('white', chess.KING)
                            print("Selected: White King")
                        elif event.key == pygame.K_2:
                            self.selected_piece = ('white', chess.ROOK)
                            print("Selected: White Rook")
                        elif event.key == pygame.K_3:
                            self.selected_piece = ('black', chess.KING)
                            print("Selected: Black King")
            
            # Clear screen
            self.screen.fill((50, 50, 50))
            
            # Draw everything
            self.draw_board()
            self.draw_pieces()
            self.draw_info_panel()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point."""
    solver = ChessEndgameSolver()
    solver.run()


if __name__ == "__main__":
    main()