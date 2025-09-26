from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

class MyAI(Alg3D):
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.lines = self._generate_lines()

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
        moves = []
        for x in range(4):
            for y in range(4):
                if board[3][y][x] == 0:
                    moves.append((x, y))
        return moves

    def _evaluate(self, board, player):
        winner = self._winner(board)
        if winner == player:
            return 10000
        if winner == 3 - player:
            return -10000

        score = 0
        for line in self.lines:
            vals = [board[z][y][x] for (x, y, z) in line]
            my_count = vals.count(player)
            opp_count = vals.count(3 - player)
            
            if my_count > 0 and opp_count > 0:
                continue
            
            if opp_count == 0:
                if my_count == 3:
                    score += 100
                elif my_count == 2:
                    score += 10
                elif my_count == 1:
                    score += 1
            else:
                if opp_count == 3:
                    score -= 100
                elif opp_count == 2:
                    score -= 10
                elif opp_count == 1:
                    score -= 1

        for x in range(4):
            for y in range(4):
                for z in range(4):
                    cell = board[z][y][x]
                    if cell != 0:
                        center_bonus = 2 - int(abs(x - 1.5) + abs(y - 1.5))
                        height_bonus = z
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
                return 10000 - (self.depth - depth), None
            else:
                return -10000 + (self.depth - depth), None
        
        if depth == 0:
            return self._evaluate(board, player), None

        moves = self._valid_moves(board)
        if not moves:
            return 0, None

        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))

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

    def _safe_move(self, board):
        priority_order = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0)
        ]
        
        for x, y in priority_order:
            if 0 <= x < 4 and 0 <= y < 4 and self._drop_z(board, x, y) is not None:
                return (x, y)
        
        for x in range(4):
            for y in range(4):
                if self._drop_z(board, x, y) is not None:
                    return (x, y)
        
        return (0, 0)

    def get_move(self, board: List[List[List[int]]], player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        try:
            for x, y in self._valid_moves(board):
                z = self._drop_z(board, x, y)
                if z is not None:
                    board[z][y][x] = player
                    if self._winner(board) == player:
                        board[z][y][x] = 0
                        return (x, y)
                    board[z][y][x] = 0

            for x, y in self._valid_moves(board):
                z = self._drop_z(board, x, y)
                if z is not None:
                    board[z][y][x] = 3 - player
                    if self._winner(board) == 3 - player:
                        board[z][y][x] = 0
                        return (x, y)
                    board[z][y][x] = 0

            _, best_move = self._minimax(board, self.depth, float('-inf'), float('inf'), True, player)
            
            if best_move and self._drop_z(board, best_move[0], best_move[1]) is not None:
                return best_move
            
            return self._safe_move(board)

        except:
            return self._safe_move(board)

    def get_winning_lines(self):
        return self.lines