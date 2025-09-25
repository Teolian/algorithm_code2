from typing import List, Tuple
import random
import time
import math

# --- Константы для оценочной функции ---
WIN_SCORE = 1000000000  # Огромное число для гарантированной победы
MAX_DEPTH = 3  # Глубина поиска Minimax. 3 - хороший баланс скорости и силы. 4 - может быть слишком медленно.

# Позиционные веса. Центр доски намного важнее краев.
# fmt: off
POSITION_WEIGHTS = [
    [ # Уровень Z = 0 (дно)
        [1, 2, 2, 1],
        [2, 3, 3, 2],
        [2, 3, 3, 2],
        [1, 2, 2, 1]
    ],
    [ # Уровень Z = 1
        [2, 3, 3, 2],
        [3, 4, 4, 3],
        [3, 4, 4, 3],
        [2, 3, 3, 2]
    ],
    [ # Уровень Z = 2
        [2, 3, 3, 2],
        [3, 4, 4, 3],
        [3, 4, 4, 3],
        [2, 3, 3, 2]
    ],
    [ # Уровень Z = 3 (верх)
        [1, 2, 2, 1],
        [2, 3, 3, 2],
        [2, 3, 3, 2],
        [1, 2, 2, 1]
    ]
]
# fmt: on

class MyAI:
    def __init__(self):
        self.player = -1
        self.opponent = -1
        self.start_time = 0
        self.time_limit = 9.8  # Оставляем запас от 10 секунд
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

        # Если ходов нет или один, не тратим время на поиск
        if not valid_moves:
            return (0, 0)
        if len(valid_moves) == 1:
            return valid_moves[0]
            
        # Проверка на немедленную победу, чтобы не запускать Minimax зря
        for move in valid_moves:
            z = self._get_z(board, move[0], move[1])
            board[z][move[1]][move[0]] = self.player
            if self._check_winner_at(board, move[0], move[1], z, self.player):
                board[z][move[1]][move[0]] = 0 # Отменяем ход
                return move
            board[z][move[1]][move[0]] = 0 # Отменяем ход
        
        # Запуск Minimax
        best_move, _ = self.minimax(
            board, MAX_DEPTH, -math.inf, math.inf, True, valid_moves
        )
        
        # Если по какой-то причине Minimax не вернул ход, делаем случайный
        if best_move is None:
            return random.choice(valid_moves)

        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing, valid_moves):
        """
        Реализация алгоритма Minimax с альфа-бета отсечением.
        """
        if time.time() - self.start_time > self.time_limit:
            return None, 0 # Таймаут

        # Проверка на терминальное состояние (победа/поражение)
        winner = self._check_winner(board)
        if winner == self.player:
            return None, WIN_SCORE + depth # Победа тем быстрее, чем лучше
        if winner == self.opponent:
            return None, -WIN_SCORE - depth # Поражение тем быстрее, чем хуже
        
        if depth == 0:
            return None, self._evaluate_board(board)

        # Оптимизация: сортируем ходы, чтобы сначала проверять самые перспективные
        # Это значительно повышает эффективность альфа-бета отсечения
        sorted_moves = sorted(valid_moves, key=lambda m: self._get_move_priority(board, m, is_maximizing), reverse=True)

        best_move = sorted_moves[0]

        if is_maximizing:
            max_eval = -math.inf
            for move in sorted_moves:
                z = self._get_z(board, move[0], move[1])
                board[z][move[1]][move[0]] = self.player
                
                _, current_eval = self.minimax(board, depth - 1, alpha, beta, False, self._get_valid_moves(board))
                
                board[z][move[1]][move[0]] = 0 # Отмена хода

                if current_eval > max_eval:
                    max_eval = current_eval
                    best_move = move
                alpha = max(alpha, current_eval)
                if beta <= alpha:
                    break
            return best_move, max_eval
        else: # is_minimizing
            min_eval = math.inf
            for move in sorted_moves:
                z = self._get_z(board, move[0], move[1])
                board[z][move[1]][move[0]] = self.opponent
                
                _, current_eval = self.minimax(board, depth - 1, alpha, beta, True, self._get_valid_moves(board))
                
                board[z][move[1]][move[0]] = 0 # Отмена хода

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move = move
                beta = min(beta, current_eval)
                if beta <= alpha:
                    break
            return best_move, min_eval
            
    def _get_move_priority(self, board, move, is_maximizing):
        """Простая оценка хода для сортировки, чтобы улучшить альфа-бета отсечение."""
        player = self.player if is_maximizing else self.opponent
        opponent = self.opponent if is_maximizing else self.player
        score = 0
        z = self._get_z(board, move[0], move[1])
        
        # Проверка на победу
        board[z][move[1]][move[0]] = player
        if self._check_winner_at(board, move[0], move[1], z, player):
            score = WIN_SCORE
        board[z][move[1]][move[0]] = 0
        if score > 0: return score

        # Проверка на блокировку победы противника
        board[z][move[1]][move[0]] = opponent
        if self._check_winner_at(board, move[0], move[1], z, opponent):
            score = WIN_SCORE / 2
        board[z][move[1]][move[0]] = 0
        if score > 0: return score
        
        return POSITION_WEIGHTS[z][move[1]][move[0]]


    def _evaluate_board(self, board):
        """
        Главная оценочная функция. Оценивает позицию с точки зрения текущего игрока.
        """
        score = 0
        for line in self.all_lines:
            score += self._evaluate_line(line, board)
        return score

    def _evaluate_line(self, line, board):
        """
        Оценивает одну линию (4 клетки).
        """
        my_pieces = 0
        opponent_pieces = 0
        empty_cells = 0

        for x, y, z in line:
            if board[z][y][x] == self.player:
                my_pieces += 1
            elif board[z][y][x] == self.opponent:
                opponent_pieces += 1
            else:
                empty_cells += 1

        score = 0
        if my_pieces == 4:
            score += 100000
        elif my_pieces == 3 and empty_cells == 1:
            score += 1000
        elif my_pieces == 2 and empty_cells == 2:
            score += 10
        
        if opponent_pieces == 4:
            score -= 100000
        elif opponent_pieces == 3 and empty_cells == 1:
            score -= 5000 # Блокировка важнее, чем создание своей угрозы
        elif opponent_pieces == 2 and empty_cells == 2:
            score -= 5

        return score
    
    def _check_winner_at(self, board, x, y, z, player):
        """Оптимизированная проверка победителя только для линий, проходящих через последнюю поставленную фишку."""
        # Проверка по X
        if all(board[z][y][i] == player for i in range(4)): return True
        # Проверка по Y
        if all(board[z][i][x] == player for i in range(4)): return True
        # Проверка по Z
        if all(board[i][y][x] == player for i in range(4)): return True
        # Проверка диагоналей в плоскости XY
        if x == y and all(board[z][i][i] == player for i in range(4)): return True
        if x + y == 3 and all(board[z][i][3 - i] == player for i in range(4)): return True
        # Проверка диагоналей в плоскости XZ
        if x == z and all(board[i][y][i] == player for i in range(4)): return True
        if x + z == 3 and all(board[i][y][3-i] == player for i in range(4)): return True
        # Проверка диагоналей в плоскости YZ
        if y == z and all(board[i][i][x] == player for i in range(4)): return True
        if y + z == 3 and all(board[i][3-i][x] == player for i in range(4)): return True
        # Проверка 4-х главных пространственных диагоналей
        if x == y == z and all(board[i][i][i] == player for i in range(4)): return True
        if x == y and x + z == 3 and all(board[3 - i][i][i] == player for i in range(4)): return True
        if x == z and x + y == 3 and all(board[i][3 - i][i] == player for i in range(4)): return True
        if y == z and y + x == 3 and all(board[i][i][3 - i] == player for i in range(4)): return True

        return False
    
    def _check_winner(self, board):
        """Полная проверка победителя по всей доске."""
        for line in self.all_lines:
            line_values = [board[z][y][x] for x, y, z in line]
            if all(v == 1 for v in line_values):
                return 1
            if all(v == 2 for v in line_values):
                return 2
        return 0

    def _get_z(self, board, x, y):
        """Возвращает z-координату, куда упадет фишка в колонке (x, y)."""
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return -1 # Колонка заполнена

    def _get_valid_moves(self, board):
        """Возвращает список всех доступных ходов (x, y)."""
        moves = []
        for y in range(4):
            for x in range(4):
                if board[3][y][x] == 0: # Проверяем только верхний слой
                    moves.append((x, y))
        return moves

    def _get_all_possible_lines(self):
        """
        Генерирует и кэширует все 76 возможных выигрышных линий на доске 4x4x4.
        Вызывается один раз при инициализации.
        """
        lines = []
        # Все горизонтальные линии (вдоль оси X)
        for z in range(4):
            for y in range(4):
                lines.append([(x, y, z) for x in range(4)])
        # Все вертикальные линии (вдоль оси Y)
        for z in range(4):
            for x in range(4):
                lines.append([(x, y, z) for y in range(4)])
        # Все "столбы" (вдоль оси Z)
        for y in range(4):
            for x in range(4):
                lines.append([(x, y, z) for z in range(4)])

        # Диагонали в плоскостях XY
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3 - i, z) for i in range(4)])
        # Диагонали в плоскостях XZ
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3 - i) for i in range(4)])
        # Диагонали в плоскостях YZ
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3 - i) for i in range(4)])

        # 4 главные пространственные диагонали
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3 - i) for i in range(4)])
        lines.append([(i, 3 - i, i) for i in range(4)])
        lines.append([(3 - i, i, i) for i in range(4)])
        
        return lines