"""
KRK Endgame Tablebase Generator
Uses backward induction to compute exact Distance-to-Mate (DTM) for all positions
"""

import chess
import pickle
import time
from collections import deque


class TablebaseGenerator:
    """
    Generates complete KRK endgame tablebase using backward induction.
    Computes exact mate distances for ~40,000 legal positions.
    """
    
    def __init__(self):
        self.tablebase = {}  # FEN -> (dtm, best_move)
        self.positions_by_dtm = {}  # dtm -> set of FENs
        
    def generate_krk_tablebase(self):
        """
        Main tablebase generation using backward induction.
        Works backwards from checkmate positions.
        """
        print("=" * 60)
        print("KRK Endgame Tablebase Generator")
        print("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Find all legal positions
        print("\n1. Generating all legal KRK positions...")
        all_positions = self._generate_all_positions()
        print(f"   Found {len(all_positions)} legal positions")
        
        # Step 2: Find checkmate positions (DTM = 0)
        print("\n2. Finding checkmate positions (DTM = 0)...")
        checkmates = self._find_checkmates(all_positions)
        print(f"   Found {len(checkmates)} checkmate positions")
        
        # Step 3: Find stalemate positions (DTM = DRAW)
        print("\n3. Finding stalemate positions...")
        stalemates = self._find_stalemates(all_positions)
        print(f"   Found {len(stalemates)} stalemate positions")
        
        # Mark stalemates as draws
        for fen in stalemates:
            self.tablebase[fen] = ('DRAW', None)
        
        # Step 4: Backward induction
        print("\n4. Running backward induction...")
        self._backward_induction(all_positions, checkmates)
        
        # Step 5: Statistics
        print("\n5. Tablebase Statistics:")
        self._print_statistics()
        
        elapsed = time.time() - start_time
        print(f"\nTablebase generation completed in {elapsed:.2f} seconds")
        
        return self.tablebase
    
    def _generate_all_positions(self):
        """Generate all legal KRK positions."""
        positions = set()
        
        for wk_sq in range(64):
            for wr_sq in range(64):
                for bk_sq in range(64):
                    # Skip overlapping pieces
                    if wk_sq == wr_sq or wk_sq == bk_sq or wr_sq == bk_sq:
                        continue
                    
                    # Skip adjacent kings (illegal)
                    wk_rank, wk_file = divmod(wk_sq, 8)
                    bk_rank, bk_file = divmod(bk_sq, 8)
                    if abs(wk_rank - bk_rank) <= 1 and abs(wk_file - bk_file) <= 1:
                        continue
                    
                    # Create position for both turns
                    for turn in [chess.WHITE, chess.BLACK]:
                        board = chess.Board(fen=None)
                        board.set_piece_at(wk_sq, chess.Piece(chess.KING, chess.WHITE))
                        board.set_piece_at(wr_sq, chess.Piece(chess.ROOK, chess.WHITE))
                        board.set_piece_at(bk_sq, chess.Piece(chess.KING, chess.BLACK))
                        board.turn = turn
                        
                        # Validate position
                        if self._is_valid_position(board):
                            positions.add(board.fen())
        
        return positions
    
    def _is_valid_position(self, board):
        """Check if position is legal (no impossible checks)."""
        # White can't be in check if it's white's turn
        if board.turn == chess.WHITE:
            wk_sq = board.king(chess.WHITE)
            if board.is_attacked_by(chess.BLACK, wk_sq):
                return False
        # Black can't be in check if it's black's turn (unless it's checkmate)
        else:
            bk_sq = board.king(chess.BLACK)
            # Allow positions where black is in check only if it's a legal position
            # (black could have moved into check is impossible)
            pass
        
        return True
    
    def _find_checkmates(self, positions):
        """Find all checkmate positions (DTM = 0)."""
        checkmates = set()
        
        for fen in positions:
            board = chess.Board(fen)
            if board.is_checkmate():
                checkmates.add(fen)
                self.tablebase[fen] = (0, None)
                
                # Store in DTM lookup
                if 0 not in self.positions_by_dtm:
                    self.positions_by_dtm[0] = set()
                self.positions_by_dtm[0].add(fen)
        
        return checkmates
    
    def _find_stalemates(self, positions):
        """Find all stalemate positions."""
        stalemates = set()
        
        for fen in positions:
            board = chess.Board(fen)
            if board.is_stalemate():
                stalemates.add(fen)
        
        return stalemates
    
    def _backward_induction(self, all_positions, checkmates):
        """
        Main backward induction algorithm.
        Works backwards from checkmates to find all mate distances.
        """
        # Positions we know the DTM for
        known_positions = set(checkmates)
        known_positions.update(self.tablebase.keys())  # Include draws
        
        # Current wave of positions to process
        current_wave = checkmates.copy()
        current_dtm = 0
        
        print(f"   DTM 0: {len(checkmates)} positions")
        
        while current_wave and current_dtm < 50:  # 50-move rule limit
            next_wave = set()
            current_dtm += 1
            
            # For each position in current wave, find predecessors
            for fen in current_wave:
                board = chess.Board(fen)
                
                # Find all positions that can reach this position in one move
                predecessors = self._find_predecessors(board, all_positions)
                
                for pred_fen in predecessors:
                    if pred_fen not in known_positions:
                        pred_board = chess.Board(pred_fen)
                        
                        # Check if this predecessor has a forced mate
                        if self._has_forced_mate(pred_board, current_dtm):
                            self.tablebase[pred_fen] = (current_dtm, self._find_best_move(pred_board))
                            known_positions.add(pred_fen)
                            next_wave.add(pred_fen)
                            
                            # Store in DTM lookup
                            if current_dtm not in self.positions_by_dtm:
                                self.positions_by_dtm[current_dtm] = set()
                            self.positions_by_dtm[current_dtm].add(pred_fen)
            
            if next_wave:
                print(f"   DTM {current_dtm}: {len(next_wave)} positions")
            
            current_wave = next_wave
        
        # Mark remaining positions as draws or unknown
        for fen in all_positions:
            if fen not in self.tablebase:
                board = chess.Board(fen)
                if board.is_insufficient_material():
                    self.tablebase[fen] = ('DRAW', None)
                else:
                    # Position doesn't lead to mate within 50 moves
                    self.tablebase[fen] = ('DRAW', None)
    
    def _find_predecessors(self, board, all_positions):
        """Find all positions that can reach the given position in one move."""
        predecessors = set()
        
        # We need to "unmake" moves to find predecessors
        # This is complex, so we'll use a different approach:
        # Check all positions to see if they can reach this position
        
        target_fen = board.fen()
        
        for fen in all_positions:
            test_board = chess.Board(fen)
            for move in test_board.legal_moves:
                test_board.push(move)
                if test_board.fen() == target_fen:
                    predecessors.add(fen)
                test_board.pop()
        
        return predecessors
    
    def _has_forced_mate(self, board, dtm):
        """
        Check if position has forced mate in 'dtm' moves.
        For white: all moves must lead to mate in <= dtm
        For black: at least one move must lead to mate in dtm-1
        """
        if board.turn == chess.WHITE:
            # White to move: need a move leading to mate in dtm-1
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
            # Black to move: ALL moves must lead to mate in <= dtm
            if not board.legal_moves:
                return False
                
            all_lead_to_mate = True
            for move in board.legal_moves:
                board.push(move)
                next_fen = board.fen()
                board.pop()
                
                if next_fen not in self.tablebase:
                    all_lead_to_mate = False
                    break
                    
                next_dtm = self.tablebase[next_fen][0]
                if next_dtm == 'DRAW' or next_dtm >= dtm:
                    all_lead_to_mate = False
                    break
            
            return all_lead_to_mate
    
    def _find_best_move(self, board):
        """Find the best move for the current position."""
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
    
    def _print_statistics(self):
        """Print tablebase statistics."""
        total = len(self.tablebase)
        draws = sum(1 for dtm, _ in self.tablebase.values() if dtm == 'DRAW')
        mates = total - draws
        
        print(f"   Total positions: {total}")
        print(f"   Positions with mate: {mates}")
        print(f"   Draw positions: {draws}")
        
        if self.positions_by_dtm:
            max_dtm = max(dtm for dtm in self.positions_by_dtm.keys() if isinstance(dtm, int))
            print(f"   Maximum DTM: {max_dtm}")
            
            # Distribution
            print("\n   DTM Distribution:")
            for dtm in sorted(self.positions_by_dtm.keys()):
                if isinstance(dtm, int) and dtm <= 10:
                    count = len(self.positions_by_dtm[dtm])
                    print(f"     DTM {dtm:2d}: {count:5d} positions")
    
    def save_tablebase(self, filename='krk_tablebase.pkl'):
        """Save tablebase to file."""
        with open(filename, 'wb') as f:
            pickle.dump(self.tablebase, f)
        print(f"Tablebase saved to {filename}")
    
    def load_tablebase(self, filename='krk_tablebase.pkl'):
        """Load tablebase from file."""
        with open(filename, 'rb') as f:
            self.tablebase = pickle.load(f)
        print(f"Tablebase loaded from {filename}")
        return self.tablebase
    
    def query_position(self, fen):
        """Query the tablebase for a specific position."""
        if fen in self.tablebase:
            dtm, best_move = self.tablebase[fen]
            if dtm == 'DRAW':
                return "Position is a draw"
            else:
                return f"Mate in {dtm} moves. Best move: {best_move}"
        else:
            return "Position not found in tablebase"


def test_tablebase():
    """Test the tablebase generator with a simple example."""
    print("Testing KRK Tablebase Generator")
    print("-" * 40)
    
    generator = TablebaseGenerator()
    
    # Generate small test (this will take a while for full tablebase)
    # For testing, you might want to limit the positions
    generator.generate_krk_tablebase()
    
    # Save the tablebase
    generator.save_tablebase()
    
    # Test some positions
    test_positions = [
        "4k3/8/8/8/8/8/8/R3K3 w - - 0 1",  # Starting position
        "7k/R7/7K/8/8/8/8/8 b - - 0 1",      # Black king in corner
    ]
    
    print("\nTesting specific positions:")
    for fen in test_positions:
        result = generator.query_position(fen)
        print(f"Position: {fen}")
        print(f"Result: {result}")
        print()


if __name__ == "__main__":
    test_tablebase()