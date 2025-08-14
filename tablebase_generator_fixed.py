"""
Fixed KRK Endgame Tablebase Generator
Uses correct backward induction to compute exact Distance-to-Mate (DTM)
"""

import chess
import pickle
import time


class TablebaseGenerator:
    """
    Generates complete KRK endgame tablebase using backward induction.
    Computes exact mate distances for ~40,000 legal positions.
    """
    
    def __init__(self):
        self.tablebase = {}  # FEN -> (dtm, best_move)
        
    def generate_krk_tablebase(self):
        """
        Main tablebase generation using backward induction.
        Works backwards from checkmate positions.
        """
        print("=" * 60)
        print("KRK Endgame Tablebase Generator (FIXED)")
        print("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Generate all legal positions
        print("\n1. Generating all legal KRK positions...")
        all_positions = self._generate_all_positions()
        print(f"   Found {len(all_positions)} legal positions")
        
        # Step 2: Find checkmate positions (DTM = 0)
        print("\n2. Finding checkmate positions (DTM = 0)...")
        checkmates = 0
        for fen in all_positions:
            board = chess.Board(fen)
            if board.is_checkmate():
                self.tablebase[fen] = (0, None)
                checkmates += 1
        print(f"   Found {checkmates} checkmate positions")
        
        # Step 3: Find stalemate positions
        print("\n3. Finding stalemate positions...")
        stalemates = 0
        for fen in all_positions:
            board = chess.Board(fen)
            if board.is_stalemate():
                self.tablebase[fen] = ('DRAW', None)
                stalemates += 1
        print(f"   Found {stalemates} stalemate positions")
        
        # Step 4: Backward induction - the FIXED version
        print("\n4. Running backward induction (this will take 2-3 minutes)...")
        self._backward_induction_fixed(all_positions)
        
        # Step 5: Statistics
        print("\n5. Tablebase Statistics:")
        self._print_statistics()
        
        elapsed = time.time() - start_time
        print(f"\nTablebase generation completed in {elapsed:.2f} seconds")
        
        return self.tablebase
    
    def _generate_all_positions(self):
        """Generate all legal KRK positions."""
        positions = []
        
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
                        
                        # Skip invalid positions
                        if turn == chess.WHITE:
                            # White can't be in check on white's turn
                            if board.is_attacked_by(chess.BLACK, wk_sq):
                                continue
                        
                        positions.append(board.fen())
        
        return positions
    
    def _backward_induction_fixed(self, all_positions):
        """
        Fixed backward induction algorithm.
        Works backwards from checkmates to find all mate distances.
        """
        current_dtm = 0
        positions_found_last_iteration = True
        
        while positions_found_last_iteration and current_dtm < 50:
            positions_found_last_iteration = False
            current_dtm += 1
            new_positions = []
            
            # Check each unknown position
            for fen in all_positions:
                if fen in self.tablebase:
                    continue  # Already know this position
                
                board = chess.Board(fen)
                
                if board.turn == chess.WHITE:
                    # White to move: need at least one move leading to mate in dtm-1
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
                    
                    # If we found a move to a position with mate, this is mate in dtm
                    if best_move and best_dtm == current_dtm - 1:
                        self.tablebase[fen] = (current_dtm, best_move)
                        new_positions.append(fen)
                        positions_found_last_iteration = True
                
                else:  # Black to move
                    # Black to move: ALL moves must lead to mate
                    all_moves_lose = True
                    worst_dtm = 0
                    
                    if not board.legal_moves:
                        continue  # No legal moves (should be checkmate/stalemate)
                    
                    for move in board.legal_moves:
                        board.push(move)
                        next_fen = board.fen()
                        board.pop()
                        
                        if next_fen not in self.tablebase:
                            all_moves_lose = False
                            break
                        
                        next_dtm = self.tablebase[next_fen][0]
                        if next_dtm == 'DRAW':
                            all_moves_lose = False
                            break
                        
                        # Track the longest resistance
                        if next_dtm > worst_dtm:
                            worst_dtm = next_dtm
                    
                    # If all moves lead to mate, this position is also mate
                    if all_moves_lose and worst_dtm == current_dtm - 1:
                        # Find the move that delays mate the longest
                        best_defense = None
                        for move in board.legal_moves:
                            board.push(move)
                            next_fen = board.fen()
                            board.pop()
                            
                            if next_fen in self.tablebase:
                                next_dtm = self.tablebase[next_fen][0]
                                if next_dtm == worst_dtm:
                                    best_defense = move.uci()
                                    break
                        
                        self.tablebase[fen] = (current_dtm, best_defense)
                        new_positions.append(fen)
                        positions_found_last_iteration = True
            
            if new_positions:
                print(f"   DTM {current_dtm}: {len(new_positions)} positions")
        
        # Mark remaining positions as draws
        draws = 0
        for fen in all_positions:
            if fen not in self.tablebase:
                self.tablebase[fen] = ('DRAW', None)
                draws += 1
        
        if draws > 0:
            print(f"   Marked {draws} remaining positions as draws")
    
    def _print_statistics(self):
        """Print tablebase statistics."""
        total = len(self.tablebase)
        draws = sum(1 for dtm, _ in self.tablebase.values() if dtm == 'DRAW')
        mates = total - draws
        
        print(f"   Total positions: {total}")
        print(f"   Positions with mate: {mates}")
        print(f"   Draw positions: {draws}")
        
        # Find maximum DTM
        max_dtm = 0
        dtm_counts = {}
        for dtm, _ in self.tablebase.values():
            if dtm != 'DRAW':
                if dtm > max_dtm:
                    max_dtm = dtm
                if dtm not in dtm_counts:
                    dtm_counts[dtm] = 0
                dtm_counts[dtm] += 1
        
        if max_dtm > 0:
            print(f"   Maximum DTM: {max_dtm}")
            
            # Distribution
            print("\n   DTM Distribution (first 10):")
            for dtm in sorted(dtm_counts.keys())[:10]:
                print(f"     DTM {dtm:2d}: {dtm_counts[dtm]:5d} positions")
    
    def save_tablebase(self, filename='krk_tablebase_fixed.pkl'):
        """Save tablebase to file."""
        with open(filename, 'wb') as f:
            pickle.dump(self.tablebase, f)
        print(f"\nTablebase saved to {filename}")
    
    def load_tablebase(self, filename='krk_tablebase_fixed.pkl'):
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


def test_specific_positions():
    """Test some specific positions."""
    generator = TablebaseGenerator()
    
    # Try to load existing tablebase
    try:
        generator.load_tablebase('krk_tablebase_fixed.pkl')
        print("Loaded existing tablebase")
    except:
        print("No existing tablebase found")
        return
    
    test_positions = [
        ("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "Default starting position"),
        ("7k/R7/7K/8/8/8/8/8 b - - 0 1", "Black king cornered"),
        ("8/8/8/4k3/8/8/R7/4K3 w - - 0 1", "Central position"),
        ("k7/8/1K6/8/8/8/8/R7 w - - 0 1", "Near corner mate"),
    ]
    
    print("\nTesting specific positions:")
    print("-" * 40)
    for fen, description in test_positions:
        result = generator.query_position(fen)
        print(f"{description}:")
        print(f"  FEN: {fen}")
        print(f"  Result: {result}")
        print()


def main():
    """Generate the complete KRK tablebase."""
    print("KRK Endgame Tablebase Generator (FIXED VERSION)")
    print("-" * 50)
    
    generator = TablebaseGenerator()
    
    # Check if we need to generate
    import os
    if os.path.exists('krk_tablebase_fixed.pkl'):
        print("\nFixed tablebase already exists!")
        print("Delete 'krk_tablebase_fixed.pkl' if you want to regenerate.")
        test_specific_positions()
    else:
        print("\nGenerating complete KRK tablebase...")
        print("This will take 2-3 minutes. Please be patient!")
        print()
        
        generator.generate_krk_tablebase()
        generator.save_tablebase('krk_tablebase_fixed.pkl')
        
        print("\n" + "=" * 60)
        print("SUCCESS! Tablebase generated and saved.")
        print("=" * 60)
        
        test_specific_positions()


if __name__ == "__main__":
    main()