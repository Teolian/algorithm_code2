from typing import List, Tuple
import random
import time
import math

WIN_SCORE = 1000000000
# ### ИЗМЕНЕНИЕ ### - Начальная глубина 3, но может меняться
MAX_DEPTH = 3 

# ### ИЗМЕНЕНИЕ ### - Сделали центральные клетки еще более ценными
# fmt: off
POSITION_WEIGHTS = [
    [ # Уровень Z = 0 (дно)
        [2, 3, 3, 2],
        [3, 5, 5, 3],
        [3, 5, 5, 3],
        [2, 3, 3, 2]
    ],
    [ # Уровень Z = 1
        [3, 4, 4, 3],
        [4, 6, 6, 4],
        [4, 6, 6, 4],
        [3, 4, 4, 3]
    ],
    [ # Уровень Z = 2
        [3, 4, 4, 3],
        [4, 6, 6, 4],
        [4, 6, 6, 4],
        [3, 4, 4, 3]
    ],
    [ # Уровень Z = 3 (верх)
        [2, 3, 3, 2],
        [3, 5, 5, 3],
        [3, 5, 5, 3],
        [2, 3, 3, 2]
    ]
]
# fmt: on

class MyAI:
    def __init__(self):
        self.player = -1
        self.opponent = -1
        self.start_time = 0
        self.time_limit = 9.8
        self.all_lines = self._get_all_possible_lines()

    def get_move(
        self,
        board: List[List[List[int]]],
        player: int,
        last_move: Tuple[int, int, int],
    ) -> Tuple[int, int]:
        self.start_time = time.time()
        self.player = player
        self.opponent = 2 if player == 1 else 1

        valid_moves = self._get_valid_moves(board)

        if not valid_moves: return (0, 0)
        if len(valid_moves) == 1: return valid_moves[0]
            
        for move in valid_moves:
            z = self._get_z(board, move[0], move[1])
            board[z][move[1]][move[0]] = self.player
            if self._check_winner_at(board, move[0], move[1], z, self.player):
                board[z][move[1]][move[0]] = 0
                return move
            board[z][move[1]][move[0]] = 0
        
        # ### ИЗМЕНЕНИЕ ### - Динамическая глубина поиска
        depth = MAX_DEPTH
        if len(valid_moves) >= 10: # Если ходов много, не рискуем
             depth = 3
        elif len(valid_moves) <= 6: # Если игра близится к концу или вариантов мало, думаем глубже
             depth = 4


        best_move, _ = self.minimax(
            board, depth, -math.inf, math.inf, True, valid_moves
        )
        
        if best_move is None:
            return random.choice(valid_moves)

        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing, valid_moves):
        if time.time() - self.start_time > self.time_limit:
            return None, 0

        winner = self._check_winner(board)
        if winner == self.player: return None, WIN_SCORE + depth
        if winner == self.opponent: return None, -WIN_SCORE - depth
        
        if depth == 0:
            return None, self._evaluate_board(board)

        sorted_moves = sorted(valid_moves, key=lambda m: self._get_move_priority(board, m, is_maximizing), reverse=True)
        best_move = sorted_moves[0]

        if is_maximizing:
            max_eval = -math.inf
            for move in sorted_moves:
                z = self._get_z(board, move[0], move[1])
                board[z][move[1]][move[0]] = self.player
                _, current_eval = self.minimax(board, depth - 1, alpha, beta, False, self._get_valid_moves(board))
                board[z][move[1]][move[0]] = 0
                if time.time() - self.start_time > self.time_limit: break # Проверка таймаута в цикле

                if current_eval > max_eval:
                    max_eval = current_eval
                    best_move = move
                alpha = max(alpha, current_eval)
                if beta <= alpha: break
            return best_move, max_eval
        else:
            min_eval = math.inf
            for move in sorted_moves:
                z = self._get_z(board, move[0], move[1])
                board[z][move[1]][move[0]] = self.opponent
                _, current_eval = self.minimax(board, depth - 1, alpha, beta, True, self._get_valid_moves(board))
                board[z][move[1]][move[0]] = 0
                if time.time() - self.start_time > self.time_limit: break

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move = move
                beta = min(beta, current_eval)
                if beta <= alpha: break
            return best_move, min_eval
            
    def _get_move_priority(self, board, move, is_maximizing):
        player = self.player if is_maximizing else self.opponent
        opponent = self.opponent if is_maximizing else self.player
        score = 0
        z = self._get_z(board, move[0], move[1])
        
        board[z][move[1]][move[0]] = player
        if self._check_winner_at(board, move[0], move[1], z, player): score = WIN_SCORE
        board[z][move[1]][move[0]] = 0
        if score > 0: return score

        board[z][move[1]][move[0]] = opponent
        if self._check_winner_at(board, move[0], move[1], z, opponent): score = WIN_SCORE / 2
        board[z][move[1]][move[0]] = 0
        
        return score + POSITION_WEIGHTS[z][move[1]][move[0]]

    def _evaluate_board(self, board):
        score = 0
        for line in self.all_lines:
            score += self._evaluate_line(line, board)
        return score

    def _evaluate_line(self, line, board):
        my_pieces = 0
        opponent_pieces = 0
        
        for x, y, z in line:
            if board[z][y][x] == self.player: my_pieces += 1
            elif board[z][y][x] == self.opponent: opponent_pieces += 1

        score = 0
        # ### ИЗМЕНЕНИЕ ### - Основная логика против "туннельного зрения"
        is_vertical_line = (line[0][0] == line[1][0] and line[0][1] == line[1][1])
        
        # Понижаем ценность вертикальных линий в 10 раз!
        multiplier = 0.1 if is_vertical_line else 1.0

        if my_pieces == 4: score += 100000
        elif my_pieces == 3 and opponent_pieces == 0: score += 1000 * multiplier
        elif my_pieces == 2 and opponent_pieces == 0: score += 10 * multiplier
        
        if opponent_pieces == 4: score -= 100000
        elif opponent_pieces == 3 and my_pieces == 0: score -= 5000 * multiplier # Блокировка важнее
        elif opponent_pieces == 2 and my_pieces == 0: score -= 50 * multiplier # Блокировка 2-х тоже важна
        
        return score
    
    def _check_winner_at(self, board, x, y, z, player):
        orientations = [
            [(i, y, z) for i in range(4)], # X
            [(x, i, z) for i in range(4)], # Y
            [(x, y, i) for i in range(4)], # Z
        ]
        # XY Diagonals
        if x == y: orientations.append([(i, i, z) for i in range(4)])
        if x + y == 3: orientations.append([(i, 3 - i, z) for i in range(4)])
        # XZ Diagonals
        if x == z: orientations.append([(i, y, i) for i in range(4)])
        if x + z == 3: orientations.append([(i, y, 3-i) for i in range(4)])
        # YZ Diagonals
        if y == z: orientations.append([(x, i, i) for i in range(4)])
        if y + z == 3: orientations.append([(x, i, 3-i) for i in range(4)])
        # 3D Diagonals
        if x == y == z: orientations.append([(i, i, i) for i in range(4)])
        if x == y and x + z == 3: orientations.append([(i, i, 3-i) for i in range(4)])
        if x + y == 3 and y == z: orientations.append([(3-i, i, i) for i in range(4)])
        if x == z and x + y == 3: orientations.append([(i, 3-i, i) for i in range(4)])
        
        for line in orientations:
            if all(board[c[2]][c[1]][c[0]] == player for c in line):
                return True
        return False
    
    def _check_winner(self, board):
        for line in self.all_lines:
            line_values = [board[z][y][x] for x, y, z in line]
            if all(v == 1 for v in line_values): return 1
            if all(v == 2 for v in line_values): return 2
        return 0

    def _get_z(self, board, x, y):
        for z in range(4):
            if board[z][y][x] == 0: return z
        return -1

    def _get_valid_moves(self, board):
        moves = []
        for y in range(4):
            for x in range(4):
                if board[3][y][x] == 0: moves.append((x, y))
        return moves

    def _get_all_possible_lines(self):
        lines = []
        for z in range(4):
            for y in range(4): lines.append([(x, y, z) for x in range(4)])
        for z in range(4):
            for x in range(4): lines.append([(x, y, z) for y in range(4)])
        for y in range(4):
            for x in range(4): lines.append([(x, y, z) for z in range(4)])
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3 - i, z) for i in range(4)])
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3 - i) for i in range(4)])
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3 - i) for i in range(4)])
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3 - i) for i in range(4)])
        lines.append([(i, 3 - i, i) for i in range(4)])
        lines.append([(3 - i, i, i) for i in range(4)])
        return lines