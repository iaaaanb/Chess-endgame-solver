import pygame
import sys

# Constants
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
WHITE_SQUARE = (240, 217, 181)
BLACK_SQUARE = (181, 136, 99)

def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("Chess Endgame Solver")
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Draw chessboard
        for row in range(8):
            for col in range(8):
                color = WHITE_SQUARE if (row + col) % 2 == 0 else BLACK_SQUARE
                rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(screen, color, rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()