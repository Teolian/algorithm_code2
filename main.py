from typing import List, Tuple
import random
import time
import math

# Константы не изменились
WIN_SCORE = 1000000000
MAX_DEPTH = 4 # Мы можем позволить себе большую глубину, т.к. в начале не думаем

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

        # ### НОВАЯ УЛЬТИМАТИВНАЯ СТРАТЕГИЯ: БАЗА ДАННЫХ ДЕБЮТОВ ###
        
        # Считаем количество фишек на доске, чтобы определить стадию игры
        pieces_on_board = sum(1 for z in range(4) for y in range(4) for x in range(4) if board[z][y][x] != 0)

        # --- СТРАТЕГИЯ ЗА ИГРОКА 1 (ЧЁРНЫЕ): ФОРСИРОВАННАЯ ПОБЕДА ---
        if player == 1:
            # Цель: захватить 4 центральные клетки на нижнем уровне (z=0)
            center_targets = [(1, 1), (1, 2), (2, 1), (2, 2)]
            random.shuffle(center_targets) # Добавим немного случайности в порядок захвата

            for move in center_targets:
                # Если одна из целевых клеток на нижнем уровне свободна, немедленно занимаем её.
                if board[0][move[1]][move[0]] == 0:
                    return move
        
        # --- СТРАТЕГИЯ ЗА ИГРОКА 2 (БЕЛЫЕ): ЛУЧШАЯ ЗАЩИТА ---
        if player == 2 and pieces_on_board < 8:
            # Цель: помешать игроку 1 захватить центр.
            # Мы занимаем центральные клетки, которые еще не заняты.
            center_targets = [(1, 1), (2, 2), (1, 2), (2, 1)] # Приоритет на диагональные
            
            for move in center_targets:
                if board[0][move[1]][move[0]] == 0:
                    return move

        # Если дебютная фаза окончена (центр занят) или мы отклонились от плана,
        # включается наш старый добрый Minimax для поиска лучшего хода в середине игры.

        valid_moves = self._get_valid_moves(board)
        if not valid_moves: return (0, 0)
        if len(valid_moves) == 1: return valid_moves[0]
            
        # Быстрая проверка на победу/блок, чтобы не запускать Minimax зря
        for move in valid_moves:
            z = self._get_z(board, move[0], move[1])
            # Проверяем победный ход
            board[z][move[1]][move[0]] = self.player
            if self._check_winner_at(board, move[0], move[1], z, self.player):
                board[z][move[1]][move[0]] = 0; return move
            board[z][move[1]][move[0]] = 0
            # Проверяем ход для блокировки оппонента
            board[z][move[1]][move[0]] = self.opponent
            if self._check_winner_at(board, move[0], move[1], z, self.opponent):
                board[z][move[1]][move[0]] = 0; return move
            board[z][move[1]][move[0]] = 0

        # Запуск Minimax, если нет очевидных ходов
        best_move, _ = self.minimax(board, MAX_DEPTH, -math.inf, math.inf, True, valid_moves)
        
        return best_move if best_move is not None else random.choice(valid_moves)

    # Minimax и все остальные функции остаются такими же, как в "Threat Hunter" версии.
    # Их задача - правильно играть в миттельшпиле, когда дебют окончен.
    def minimax(self, board, depth, alpha, beta, is_maximizing, valid_moves):
        if time.time() - self.start_time > self.time_limit: return None, 0
        winner = self._check_winner(board)
        if winner == self.player: return None, WIN_SCORE + depth
        if winner == self.opponent: return None, -WIN_SCORE - depth
        if not valid_moves: return None, 0
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
                if current_eval < min_eval:
                    min_eval = current_eval; best_move = move
                beta = min(beta, current_eval)
                if beta <= alpha: break
            return best_move, min_eval

    # Используем оценочную функцию из версии "Threat Hunter"
    def _evaluate_board(self, board):
        my_threats = self.count_threats(board, self.player)
        opponent_threats = self.count_threats(board, self.opponent)
        if my_threats >= 2: return WIN_SCORE
        if opponent_threats >= 2: return -WIN_SCORE
        score = (my_threats * 10000) - (opponent_threats * 50000)
        score += self.evaluate_potential(board, self.player)
        score -= self.evaluate_potential(board, self.opponent)
        return score

    def count_threats(self, board, player):
        threat_count = 0
        for line in self.all_lines:
            player_pieces = 0; empty_cells = 0
            for x, y, z in line:
                if board[z][y][x] == player: player_pieces += 1
                elif board[z][y][x] == 0: empty_cells += 1
            if player_pieces == 3 and empty_cells == 1:
                threat_count += 1
        return threat_count
        
    def evaluate_potential(self, board, player):
        potential_score = 0
        for line in self.all_lines:
            player_pieces = 0; empty_cells = 0; pos_weight = 0
            for x, y, z in line:
                if board[z][y][x] == player:
                    player_pieces += 1; pos_weight += POSITION_WEIGHTS[z][y][x]
                elif board[z][y][x] == 0: empty_cells += 1
            if player_pieces > 0 and player_pieces + empty_cells == 4:
                potential_score += pos_weight
            if player_pieces == 2 and empty_cells == 2:
                potential_score += 200
        return potential_score
    
    # ... Остальные функции без изменений ...
    def _get_move_priority(self, board, move, is_maximizing):
        player = self.player if is_maximizing else self.opponent; opponent = self.opponent if is_maximizing else self.player
        score = 0; z = self._get_z(board, move[0], move[1])
        if z == -1: return -math.inf
        board[z][move[1]][move[0]] = player
        if self._check_winner_at(board, move[0], move[1], z, player): score = WIN_SCORE
        board[z][move[1]][move[0]] = 0
        if score > 0: return score
        board[z][move[1]][move[0]] = opponent
        if self._check_winner_at(board, move[0], move[1], z, opponent): score = WIN_SCORE / 2
        board[z][move[1]][move[0]] = 0
        return score + POSITION_WEIGHTS[z][move[1]][move[0]]
    def _check_winner_at(self, board, x, y, z, player):
        orientations = [[(i, y, z) for i in range(4)],[(x, i, z) for i in range(4)],[(x, y, i) for i in range(4)]]
        if x == y: orientations.append([(i, i, z) for i in range(4)])
        if x + y == 3: orientations.append([(i, 3 - i, z) for i in range(4)])
        if x == z: orientations.append([(i, y, i) for i in range(4)])
        if x + z == 3: orientations.append([(i, y, 3-i) for i in range(4)])
        if y == z: orientations.append([(x, i, i) for i in range(4)])
        if y + z == 3: orientations.append([(x, i, 3-i) for i in range(4)])
        if x == y == z: orientations.append([(i, i, i) for i in range(4)])
        if x == y and x + z == 3: orientations.append([(i, i, 3-i) for i in range(4)])
        if x + y == 3 and y == z: orientations.append([(3-i, i, i) for i in range(4)])
        if x == z and x + y == 3: orientations.append([(i, 3-i, i) for i in range(4)])
        for line in orientations:
            if all(board[c[2]][c[1]][c[0]] == player for c in line): return True
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