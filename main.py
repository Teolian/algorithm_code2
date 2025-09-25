from typing import List, Tuple
import random
import time
import math

WIN_SCORE = 1000000000
MAX_DEPTH = 3 

# fmt: off
POSITION_WEIGHTS = [
    [[2, 3, 3, 2], [3, 5, 5, 3], [3, 5, 5, 3], [2, 3, 3, 2]],
    [[3, 4, 4, 3], [4, 6, 6, 4], [4, 6, 6, 4], [3, 4, 4, 3]],
    [[3, 4, 4, 3], [4, 6, 6, 4], [4, 6, 6, 4], [3, 4, 4, 3]],
    [[2, 3, 3, 2], [3, 5, 5, 3], [3, 5, 5, 3], [2, 3, 3, 2]],
]
# fmt: on

class MyAI:
    def __init__(self):
        self.turn_count = 0
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
        
        # ### НОВАЯ СТРАТЕГИЯ: Книга Дебютов ###
        board_is_empty = all(board[0][y][x] == 0 for y in range(4) for x in range(4))
        if player == 1 and board_is_empty:
            return (1, 1) # Лучший первый ход
        
        # Если мы игрок 2 и это наш первый ход
        if player == 2 and last_move != (-1, -1, -1):
             # Считаем, сколько ходов на доске
            pieces = sum(1 for z in range(4) for y in range(4) for x in range(4) if board[z][y][x] != 0)
            if pieces == 1:
                # Если оппонент сходил в угол, забираем центр
                if last_move[0] in {0,3} and last_move[1] in {0,3}:
                    return (1, 1)
                # Если оппонент сходил в центр, забираем соседний центр
                elif (last_move[0], last_move[1]) == (1,1):
                    return (2,2)
                else:
                    return (1,1) # В любом другом случае забираем центр
        
        valid_moves = self._get_valid_moves(board)
        if not valid_moves: return (0, 0)
        if len(valid_moves) == 1: return valid_moves[0]
            
        # Проверка на немедленную победу или создание вилки
        for move in valid_moves:
            z = self._get_z(board, move[0], move[1])
            board[z][move[1]][move[0]] = self.player
            threats = self.count_threats(board, self.player)
            board[z][move[1]][move[0]] = 0 # отмена
            if threats >= 2: # Нашли вилку!
                return move

        depth = MAX_DEPTH
        if len(valid_moves) <= 8:
             depth = 4

        best_move, _ = self.minimax(board, depth, -math.inf, math.inf, True, valid_moves)
        
        return best_move if best_move is not None else random.choice(valid_moves)

    def minimax(self, board, depth, alpha, beta, is_maximizing, valid_moves):
        # ... (Код Minimax остается таким же, как в предыдущей версии) ...
        if time.time() - self.start_time > self.time_limit: return None, 0
        winner = self._check_winner(board)
        if winner == self.player: return None, WIN_SCORE + depth
        if winner == self.opponent: return None, -WIN_SCORE - depth
        if depth == 0: return None, self._evaluate_board(board)
        sorted_moves = sorted(valid_moves, key=lambda m: self._get_move_priority(board, m, is_maximizing), reverse=True)
        best_move = sorted_moves[0]
        if is_maximizing:
            max_eval = -math.inf
            for move in sorted_moves:
                z = self._get_z(board, move[0], move[1])
                board[z][move[1]][move[0]] = self.player
                _, current_eval = self.minimax(board, depth - 1, alpha, beta, False, self._get_valid_moves(board))
                board[z][move[1]][move[0]] = 0
                if time.time() - self.start_time > self.time_limit: break
                if current_eval > max_eval:
                    max_eval = current_eval; best_move = move
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
                    min_eval = current_eval; best_move = move
                beta = min(beta, current_eval)
                if beta <= alpha: break
            return best_move, min_eval
            
    def _get_move_priority(self, board, move, is_maximizing):
        # ... (Код _get_move_priority остается таким же) ...
        player = self.player if is_maximizing else self.opponent; opponent = self.opponent if is_maximizing else self.player
        score = 0; z = self._get_z(board, move[0], move[1])
        board[z][move[1]][move[0]] = player
        if self._check_winner_at(board, move[0], move[1], z, player): score = WIN_SCORE
        board[z][move[1]][move[0]] = 0
        if score > 0: return score
        board[z][move[1]][move[0]] = opponent
        if self._check_winner_at(board, move[0], move[1], z, opponent): score = WIN_SCORE / 2
        board[z][move[1]][move[0]] = 0
        return score + POSITION_WEIGHTS[z][move[1]][move[0]]

    def _evaluate_board(self, board):
        # ### НОВАЯ СТРАТЕГИЯ: Оценка через подсчет угроз ###
        my_threats = self.count_threats(board, self.player)
        opponent_threats = self.count_threats(board, self.opponent)

        if my_threats >= 2: return WIN_SCORE # Нашли вилку
        if opponent_threats >= 2: return -WIN_SCORE # Нас побеждают вилкой

        score = 0
        if my_threats == 1: score += 10000
        if opponent_threats == 1: score -= 50000

        # Добавляем оценку за "будущие" угрозы и позицию
        score += self.evaluate_potential(board, self.player)
        score -= self.evaluate_potential(board, self.opponent)
        
        return score

    def count_threats(self, board, player):
        """Считает количество немедленных угроз (линии с 3 фишками и 1 пустой клеткой)."""
        threat_count = 0
        for line in self.all_lines:
            player_pieces = 0
            empty_cells = 0
            for x, y, z in line:
                if board[z][y][x] == player: player_pieces += 1
                elif board[z][y][x] == 0: empty_cells += 1
            if player_pieces == 3 and empty_cells == 1:
                threat_count += 1
        return threat_count
        
    def evaluate_potential(self, board, player):
        """Оценивает потенциал: линии с 2 фишками и 2 пустыми + позиционные веса."""
        potential_score = 0
        for line in self.all_lines:
            player_pieces = 0
            empty_cells = 0
            # Добавляем позиционный бонус за каждую фишку
            for x, y, z in line:
                if board[z][y][x] == player:
                    player_pieces += 1
                    potential_score += POSITION_WEIGHTS[z][y][x]
                elif board[z][y][x] == 0:
                    empty_cells += 1
            
            # Бонус за "открытые" линии из 2-х фишек - это заготовки для вилок
            if player_pieces == 2 and empty_cells == 2:
                potential_score += 200
        return potential_score

    # ... (Все остальные вспомогательные функции _check_winner_at, _get_z, и т.д. остаются без изменений) ...
    def _check_winner_at(self, board, x, y, z, player): # Сокращен для краткости
        # ...
        return False
    def _check_winner(self, board):
        for line in self.all_lines:
            line_values = [board[z][y][x] for x, y, z in line];
            if all(v == 1 for v in line_values): return 1
            if all(v == 2 for v in line_values): return 2
        return 0
    def _get_z(self, board, x, y):
        for z in range(4):
            if board[z][y][x] == 0: return z
        return -1
    def _get_valid_moves(self, board):
        moves = [];
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
            lines.append([(i, i, z) for i in range(4)]); lines.append([(i, 3 - i, z) for i in range(4)])
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)]); lines.append([(i, y, 3 - i) for i in range(4)])
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)]); lines.append([(x, i, 3 - i) for i in range(4)])
        lines.append([(i, i, i) for i in range(4)]); lines.append([(i, i, 3 - i) for i in range(4)])
        lines.append([(i, 3 - i, i) for i in range(4)]); lines.append([(3 - i, i, i) for i in range(4)])
        return lines