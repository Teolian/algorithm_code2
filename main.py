from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

class MyAI(Alg3D):
    def __init__(self, depth: int = 4):
        self.depth = depth
        self.lines = self._generate_lines()
        self.center_positions = [(1,1), (2,2), (1,2), (2,1)]
        self.corner_positions = [(0,0), (0,3), (3,0), (3,3)]
        self.edge_positions = [(0,1), (1,0), (2,3), (3,2), (0,2), (2,0), (3,1), (1,3)]

    def _generate_lines(self):
        lines = []
        for y in range(4):
            for z in range(4):
                lines.append([(x, y, z) for x in range(4)])
        for x in range(4):
            for z in range(4):
                lines.append([(x, y, z) for y in range(4)])
        for x in range(4):
            for y in range(4):
                lines.append([(x, y, z) for z in range(4)])
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3-i) for i in range(4)])
        lines.append([(i, 3-i, i) for i in range(4)])
        lines.append([(3-i, i, i) for i in range(4)])
        return lines

    def _drop_z(self, board, x, y):
        if not (0 <= x < 4 and 0 <= y < 4):
            return None
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return None

    def _winner(self, board):
        for line in self.lines:
            vals = [board[z][y][x] for (x, y, z) in line]
            if vals.count(1) == 4:
                return 1
            if vals.count(2) == 4:
                return 2
        return 0

    def _valid_moves(self, board):
        return [(x, y) for x in range(4) for y in range(4) if board[3][y][x] == 0]

    def _find_threats(self, board, player):
        threats = []
        for x, y in self._valid_moves(board):
            z = self._drop_z(board, x, y)
            if z is not None:
                board[z][y][x] = player
                if self._winner(board) == player:
                    threats.append((x, y))
                board[z][y][x] = 0
        return threats

    def _find_forks(self, board, player):
        forks = []
        for x, y in self._valid_moves(board):
            z = self._drop_z(board, x, y)
            if z is not None:
                board[z][y][x] = player
                opp_threats = self._find_threats(board, 3 - player)
                if not opp_threats:
                    my_threats = self._find_threats(board, player)
                    if len(my_threats) >= 2:
                        unique_threats = set(my_threats)
                        if len(unique_threats) >= 2:
                            forks.append((x, y))
                board[z][y][x] = 0
        return forks

    def _create_trap_pattern(self, board, player):
        trap_moves = []
        
        spatial_diagonals = [
            [(0,0,0), (1,1,1), (2,2,2), (3,3,3)],
            [(0,0,3), (1,1,2), (2,2,1), (3,3,0)],
            [(0,3,0), (1,2,1), (2,1,2), (3,0,3)],
            [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]
        ]
        
        for diag in spatial_diagonals:
            my_count = 0
            opp_count = 0
            empty_positions = []
            
            for x, y, z in diag:
                cell_val = board[z][y][x]
                if cell_val == player:
                    my_count += 1
                elif cell_val == 3 - player:
                    opp_count += 1
                else:
                    if self._drop_z(board, x, y) == z:
                        empty_positions.append((x, y))
            
            if my_count >= 1 and opp_count == 0 and len(empty_positions) >= 2:
                for pos in empty_positions[:2]:
                    trap_moves.append(pos)
        
        return trap_moves

    def _block_spatial_diagonal(self, board, player):
        opponent = 3 - player
        spatial_diagonals = [
            [(0,0,0), (1,1,1), (2,2,2), (3,3,3)],
            [(0,0,3), (1,1,2), (2,2,1), (3,3,0)],
            [(0,3,0), (1,2,1), (2,1,2), (3,0,3)],
            [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]
        ]
        
        for diag in spatial_diagonals:
            opp_count = 0
            block_positions = []
            
            for x, y, z in diag:
                cell_val = board[z][y][x]
                if cell_val == opponent:
                    opp_count += 1
                elif cell_val == 0 and self._drop_z(board, x, y) == z:
                    block_positions.append((x, y))
            
            if opp_count >= 2 and block_positions:
                return block_positions[0]
        
        return None

    def _evaluate_advanced(self, board, player):
        winner = self._winner(board)
        if winner == player:
            return 50000
        if winner == 3 - player:
            return -50000

        score = 0
        opponent = 3 - player

        for line in self.lines:
            vals = [board[z][y][x] for (x, y, z) in line]
            my_count = vals.count(player)
            opp_count = vals.count(opponent)
            empty_count = vals.count(0)
            
            if my_count > 0 and opp_count > 0:
                continue
            
            if opp_count == 0 and my_count > 0:
                if my_count == 3:
                    score += 5000
                elif my_count == 2:
                    score += 500
                elif my_count == 1:
                    score += 50
            elif my_count == 0 and opp_count > 0:
                if opp_count == 3:
                    score -= 4000
                elif opp_count == 2:
                    score -= 400
                elif opp_count == 1:
                    score -= 40

        my_threats = len(self._find_threats(board, player))
        opp_threats = len(self._find_threats(board, opponent))
        my_forks = len(self._find_forks(board, player))
        opp_forks = len(self._find_forks(board, opponent))
        
        score += (my_threats - opp_threats) * 1000
        score += (my_forks - opp_forks) * 3000

        spatial_diagonals = [
            [(0,0,0), (1,1,1), (2,2,2), (3,3,3)],
            [(0,0,3), (1,1,2), (2,2,1), (3,3,0)],
            [(0,3,0), (1,2,1), (2,1,2), (3,0,3)],
            [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]
        ]
        
        for diag in spatial_diagonals:
            vals = [board[z][y][x] for (x, y, z) in diag]
            my_count = vals.count(player)
            opp_count = vals.count(opponent)
            
            if my_count > 0 and opp_count == 0:
                score += my_count * my_count * 200
            elif opp_count > 0 and my_count == 0:
                score -= opp_count * opp_count * 150

        for x in range(4):
            for y in range(4):
                for z in range(4):
                    cell = board[z][y][x]
                    if cell != 0:
                        center_bonus = 4 - int(abs(x - 1.5) + abs(y - 1.5))
                        height_bonus = z * 2
                        total = center_bonus + height_bonus
                        if cell == player:
                            score += total
                        else:
                            score -= total
        
        return score

    def _minimax(self, board, depth, alpha, beta, maximizing, player):
        winner = self._winner(board)
        if winner != 0:
            if winner == player:
                return 50000 - (self.depth - depth), None
            else:
                return -50000 + (self.depth - depth), None
        
        if depth == 0:
            return self._evaluate_advanced(board, player), None

        moves = self._valid_moves(board)
        if not moves:
            return 0, None

        def move_priority(move):
            x, y = move
            priority = 0
            
            if (x, y) in self.center_positions:
                priority += 1000
            elif (x, y) in self.corner_positions:
                priority += 100
            
            center_dist = abs(x - 1.5) + abs(y - 1.5)
            priority += int((4 - center_dist) * 50)
            
            z = self._drop_z(board, x, y)
            if z is not None:
                board[z][y][x] = player if maximizing else (3 - player)
                if self._winner(board) == (player if maximizing else (3 - player)):
                    priority += 100000
                threats = len(self._find_threats(board, player if maximizing else (3 - player)))
                priority += threats * 10000
                board[z][y][x] = 0
            
            return priority

        moves.sort(key=move_priority, reverse=True)
        best_move = moves[0]
        
        if maximizing:
            max_eval = float('-inf')
            for x, y in moves:
                z = self._drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, False, player)
                board[z][y][x] = 0
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (x, y)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for x, y in moves:
                z = self._drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = 3 - player
                eval_score, _ = self._minimax(board, depth - 1, alpha, beta, True, player)
                board[z][y][x] = 0
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (x, y)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def _get_opening_move(self, board, player):
        moves_played = sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)
        
        if moves_played == 0:
            return (1, 1)
        
        if moves_played == 1:
            if board[0][0][0] != 0:
                return (3, 3)
            elif board[0][3][3] != 0:
                return (0, 0)
            elif board[0][3][0] != 0:
                return (0, 3)
            elif board[0][0][3] != 0:
                return (3, 0)
            else:
                return (2, 2)
        
        if moves_played == 2:
            center_occupied = any(board[0][y][x] != 0 for x, y in self.center_positions)
            if not center_occupied:
                return (1, 1)
            
            corner_pattern = []
            for x, y in self.corner_positions:
                if board[0][y][x] != 0:
                    corner_pattern.append((x, y))
            
            if len(corner_pattern) >= 1:
                available_centers = [(x, y) for x, y in self.center_positions if board[0][y][x] == 0]
                if available_centers:
                    return available_centers[0]
        
        return None

    def _safe_fallback(self, board):
        priority_order = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0)
        ]
        
        for x, y in priority_order:
            if self._drop_z(board, x, y) is not None:
                return (x, y)
        return (0, 0)

    def get_move(self, board: List[List[List[int]]], player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        try:
            opening_move = self._get_opening_move(board, player)
            if opening_move and self._drop_z(board, opening_move[0], opening_move[1]) is not None:
                return opening_move

            my_wins = self._find_threats(board, player)
            if my_wins:
                return my_wins[0]

            opp_wins = self._find_threats(board, 3 - player)
            if opp_wins:
                return opp_wins[0]

            spatial_block = self._block_spatial_diagonal(board, player)
            if spatial_block:
                return spatial_block

            my_forks = self._find_forks(board, player)
            if my_forks:
                return my_forks[0]

            trap_moves = self._create_trap_pattern(board, player)
            if trap_moves:
                for move in trap_moves:
                    if self._drop_z(board, move[0], move[1]) is not None:
                        return move

            _, best_move = self._minimax(board, self.depth, float('-inf'), float('inf'), True, player)
            
            if best_move and self._drop_z(board, best_move[0], best_move[1]) is not None:
                return best_move
            
            return self._safe_fallback(board)

        except:
            return self._safe_fallback(board)

    def get_winning_lines(self):
        return self.lines