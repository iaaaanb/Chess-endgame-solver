"""
Chess GUI with integrated python-chess engine
Complete playable interface for King + Rook vs King endgame
"""

import pygame
import sys
from chess_engine import ChessEngine


# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 640
BOARD_SIZE = 8
SQUARE_SIZE = WINDOW_SIZE // BOARD_SIZE

# Colors
WHITE_SQUARE = (240, 217, 181)
BLACK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (255, 255, 0, 128)
SELECTED_COLOR = (0, 255, 0, 64)
CHECK_COLOR = (255, 0, 0, 100)
LAST_MOVE_COLOR = (255, 255, 0, 50)

# Piece colors
WHITE_PIECE = (255, 255, 255)
BLACK_PIECE = (40, 40, 40)
PIECE_OUTLINE = (0, 0, 0)


class ChessGUI:
    def __init__(self):
        """Initialize the chess GUI with engine integration."""
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
        pygame.display.set_caption("Chess Endgame Tablebase Solver - KRK Endgame")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Initialize chess engine
        self.engine = ChessEngine()
        self.engine.setup_krk_endgame()
        
        # GUI state
        self.running = True
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        
    def draw_board(self):
        """Draw the chessboard with highlights."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # Base square color
                color = WHITE_SQUARE if (row + col) % 2 == 0 else BLACK_SQUARE
                rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                  SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw last move highlight
                if self.last_move:
                    if self.last_move[0] == (row, col) or self.last_move[1] == (row, col):
                        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                        s.set_alpha(50)
                        s.fill((255, 255, 0))
                        self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Draw check highlight
                state = self.engine.get_game_state()
                if state['is_check']:
                    piece = self.engine.get_piece_at(row, col)
                    if piece and piece[1] == 'K':
                        if (piece[0] == 'white' and state['turn'] == 'white') or \
                           (piece[0] == 'black' and state['turn'] == 'black'):
                            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                            s.set_alpha(100)
                            s.fill((255, 0, 0))
                            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Draw selection
                if self.selected_square == (row, col):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    s.set_alpha(100)
                    s.fill((0, 255, 0))
                    self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                
                # Draw legal move indicators
                if (row, col) in self.legal_moves:
                    # Draw circle for legal moves
                    center = (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                             row * SQUARE_SIZE + SQUARE_SIZE // 2)
                    
                    # Check if this square has a piece (capture)
                    if self.engine.get_piece_at(row, col):
                        pygame.draw.circle(self.screen, (255, 0, 0), center, 
                                         SQUARE_SIZE // 3, 3)
                    else:
                        pygame.draw.circle(self.screen, (100, 100, 100), center, 
                                         SQUARE_SIZE // 6)
                
                # Draw coordinates
                if col == 0:  # Rank numbers on left
                    text = self.small_font.render(str(8 - row), True, (100, 100, 100))
                    self.screen.blit(text, (2, row * SQUARE_SIZE + 2))
                if row == 7:  # File letters on bottom
                    text = self.small_font.render(chr(ord('a') + col), True, (100, 100, 100))
                    self.screen.blit(text, (col * SQUARE_SIZE + SQUARE_SIZE - 15, 
                                           WINDOW_SIZE - 18))
    
    def draw_pieces(self):
        """Draw chess pieces from engine state."""
        board_array = self.engine.get_board_array()
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_array[row][col]
                if piece:
                    self._draw_piece(row, col, piece[0], piece[1])
    
    def _draw_piece(self, row, col, color, piece_type):
        """Draw a chess piece with improved graphics."""
        center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
        
        piece_color = WHITE_PIECE if color == 'white' else BLACK_PIECE
        outline_color = BLACK_PIECE if color == 'white' else WHITE_PIECE
        
        if piece_type == 'K':  # King
            # Crown base
            size = SQUARE_SIZE // 3
            pygame.draw.circle(self.screen, piece_color, (center_x, center_y + 5), size)
            pygame.draw.circle(self.screen, outline_color, (center_x, center_y + 5), size, 2)
            
            # Crown top with cross
            crown_points = [
                (center_x - size, center_y),
                (center_x - size//2, center_y - size//2),
                (center_x, center_y),
                (center_x + size//2, center_y - size//2),
                (center_x + size, center_y)
            ]
            pygame.draw.polygon(self.screen, piece_color, crown_points)
            pygame.draw.polygon(self.screen, outline_color, crown_points, 2)
            
            # Cross on top
            cross_size = size // 3
            pygame.draw.line(self.screen, outline_color,
                           (center_x, center_y - size//2 - cross_size),
                           (center_x, center_y - size//2 + cross_size), 2)
            pygame.draw.line(self.screen, outline_color,
                           (center_x - cross_size//2, center_y - size//2),
                           (center_x + cross_size//2, center_y - size//2), 2)
            
        elif piece_type == 'R':  # Rook
            size = SQUARE_SIZE // 3
            # Tower body
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
        """Draw game information panel below the board."""
        # Background for info panel
        panel_rect = pygame.Rect(0, WINDOW_SIZE, WINDOW_SIZE, 100)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.line(self.screen, (180, 180, 180), 
                        (0, WINDOW_SIZE), (WINDOW_SIZE, WINDOW_SIZE), 2)
        
        # Get game state
        state = self.engine.get_game_state()
        
        # Turn indicator
        turn_text = f"Turn: {state['turn'].capitalize()}"
        turn_surface = self.font.render(turn_text, True, (0, 0, 0))
        self.screen.blit(turn_surface, (10, WINDOW_SIZE + 10))
        
        # Game status
        status = ""
        if state['is_checkmate']:
            winner = 'Black' if state['turn'] == 'white' else 'White'
            status = f"CHECKMATE! {winner} wins!"
            color = (255, 0, 0)
        elif state['is_stalemate']:
            status = "STALEMATE - Draw!"
            color = (128, 128, 0)
        elif state['is_check']:
            status = "CHECK!"
            color = (255, 128, 0)
        else:
            status = "Game in progress"
            color = (0, 128, 0)
        
        status_surface = self.font.render(status, True, color)
        self.screen.blit(status_surface, (10, WINDOW_SIZE + 35))
        
        # Move counter
        move_text = f"Moves: {state['move_count']}"
        move_surface = self.font.render(move_text, True, (0, 0, 0))
        self.screen.blit(move_surface, (10, WINDOW_SIZE + 60))
        
        # Controls
        controls = "R: Reset | U: Undo | ESC: Quit"
        control_surface = self.small_font.render(controls, True, (100, 100, 100))
        self.screen.blit(control_surface, (WINDOW_SIZE - 200, WINDOW_SIZE + 70))
    
    def handle_click(self, pos):
        """Handle mouse clicks on the board."""
        x, y = pos
        
        # Check if click is on the board
        if y >= WINDOW_SIZE:
            return
        
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.selected_square:
                # Try to make a move
                from_row, from_col = self.selected_square
                
                if (row, col) in self.legal_moves:
                    # Make the move
                    if self.engine.make_move(from_row, from_col, row, col):
                        self.last_move = (self.selected_square, (row, col))
                        print(f"Move: {self.engine.get_square_notation(from_row, from_col)}" +
                              f" -> {self.engine.get_square_notation(row, col)}")
                
                # Clear selection
                self.selected_square = None
                self.legal_moves = []
                
            else:
                # Select a piece
                piece = self.engine.get_piece_at(row, col)
                state = self.engine.get_game_state()
                
                if piece and piece[0] == state['turn']:
                    self.selected_square = (row, col)
                    self.legal_moves = self.engine.get_legal_moves_from_square(row, col)
                    print(f"Selected: {self.engine.get_square_notation(row, col)}")
    
    def reset_position(self):
        """Reset to initial endgame position."""
        self.engine.setup_krk_endgame()
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        print("Position reset to initial KRK endgame")
    
    def run(self):
        """Main game loop."""
        print("Chess Endgame Tablebase Solver - KRK Endgame")
        print("=" * 45)
        print("Controls:")
        print("  Click to select and move pieces")
        print("  R - Reset position")
        print("  U - Undo last move")
        print("  ESC - Quit")
        print()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.reset_position()
                    elif event.key == pygame.K_u:
                        if self.engine.undo_move():
                            self.last_move = None
                            print("Move undone")
            
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
    gui = ChessGUI()
    gui.run()


if __name__ == "__main__":
    main()