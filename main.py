from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board  # type: ignore


def gen_lines():
    """Полный набор из 76 победных линий для 4x4x4."""
    L = []
    # По оси X (для каждого y,z)
    for y in range(4):
        for z in range(4):
            L.append([(i, y, z) for i in range(4)])
    # По оси Y (для каждого x,z)
    for x in range(4):
        for z in range(4):
            L.append([(x, i, z) for i in range(4)])
    # По оси Z (для каждого x,y)
    for x in range(4):
        for y in range(4):
            L.append([(x, y, i) for i in range(4)])
    # Диагонали в каждой плоскости z
    for z in range(4):
        L.append([(i, i, z) for i in range(4)])
        L.append([(i, 3 - i, z) for i in range(4)])
    # Диагонали в каждой плоскости y (x-z)
    for y in range(4):
        L.append([(i, y, i) for i in range(4)])
        L.append([(i, y, 3 - i) for i in range(4)])
    # Диагонали в каждой плоскости x (y-z)
    for x in range(4):
        L.append([(x, i, i) for i in range(4)])
        L.append([(x, i, 3 - i) for i in range(4)])
    # 4 пространственные диагонали
    L.append([(i, i, i) for i in range(4)])
    L.append([(i, i, 3 - i) for i in range(4)])
    L.append([(i, 3 - i, i) for i in range(4)])
    L.append([(3 - i, i, i) for i in range(4)])
    return L


LINES = gen_lines()


def drop_z(board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
    """Куда «упадёт» фишка в столбце (x,y). None если столбец полон/вне границ."""
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None


def board_full(board: List[List[List[int]]]) -> bool:
    """Заполнено ли поле (смотрим верхний слой)."""
    return all(board[3][y][x] != 0 for x in range(4) for y in range(4))


def winner(board: List[List[List[int]]]) -> int:
    """Победитель: 1 или 2; 0 если ещё нет."""
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0


def valid_moves(board: List[List[List[int]]]):
    """Все допустимые (x,y), где столбец не полон."""
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)


def count_pieces(board: List[List[List[int]]]) -> int:
    """Подсчет общего количества фишек на доске."""
    return sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)


def eval_board(board: List[List[List[int]]], me: int) -> int:
    """Стабильная оценочная функция."""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 50_000
    if w == opp:
        return -50_000

    score = 0

    # Позиционные бонусы
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p == 0:
                    continue
                # Центральный бонус
                cent = 3 - int(abs(x - 1.5) + abs(y - 1.5))
                # Бонус за высоту
                height = z
                pos_score = cent * 2 + height
                score += pos_score if p == me else -pos_score

    # Анализ линий с простой логикой
    for line in LINES:
        c0 = c1 = c2 = 0
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0:
                c0 += 1
            elif v == 1:
                c1 += 1
            else:
                c2 += 1
        
        # Игнорируем смешанные линии
        if c1 > 0 and c2 > 0:
            continue
            
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        
        if theirs == 0:
            if mine == 3:
                score += 500
            elif mine == 2:
                score += 50
            elif mine == 1:
                score += 5
        elif mine == 0:
            if theirs == 3:
                score -= 500
            elif theirs == 2:
                score -= 50
            elif theirs == 1:
                score -= 5
    
    return score


class MyAI(Alg3D):
    def __init__(self, depth: int = 3):  # Уменьшили глубину для стабильности
        self.depth = depth

    def _emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Максимально безопасный аварийный ход."""
        # Простой порядок: центр -> края -> углы
        priority_moves = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0),
        ]
        
        for x, y in priority_moves:
            try:
                if 0 <= x < 4 and 0 <= y < 4:
                    z = drop_z(board, x, y)
                    if z is not None:
                        return (x, y)
            except:
                continue
        
        # Последний шанс - любой валидный ход
        for x in range(4):
            for y in range(4):
                try:
                    if drop_z(board, x, y) is not None:
                        return (x, y)
                except:
                    continue
        
        return (0, 0)  # Абсолютный fallback

    def _validate_move(self, board: List[List[List[int]]], x: int, y: int) -> Tuple[int, int]:
        """Строгая валидация хода."""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return self._emergency_move(board)
            if drop_z(board, x, y) is None:
                return self._emergency_move(board)
            return (x, y)
        except:
            return self._emergency_move(board)

    def _immediate_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Безопасный поиск немедленного выигрыша."""
        try:
            for (x, y) in valid_moves(board):
                try:
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = player
                    if winner(board) == player:
                        board[z][y][x] = 0
                        return (x, y)
                    board[z][y][x] = 0
                except:
                    continue
        except:
            pass
        return None

    def _creates_fork(self, board: Board, player: int, x: int, y: int) -> bool:
        """Безопасная проверка форка."""
        try:
            z = drop_z(board, x, y)
            if z is None:
                return False
            
            board[z][y][x] = player
            
            # Проверяем, не даем ли мы сопернику немедленную победу
            opp = 3 - player
            opp_win = self._immediate_win(board, opp)
            if opp_win is not None:
                board[z][y][x] = 0
                return False
            
            # Считаем наши угрозы
            my_wins = []
            for (mx, my) in valid_moves(board):
                try:
                    mz = drop_z(board, mx, my)
                    if mz is None:
                        continue
                    board[mz][my][mx] = player
                    if winner(board) == player:
                        my_wins.append((mx, my))
                    board[mz][my][mx] = 0
                except:
                    continue
            
            board[z][y][x] = 0
            
            # Форк = минимум 2 разных способа выиграть
            return len(set(my_wins)) >= 2
        except:
            return False

    def _find_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Безопасный поиск форка."""
        try:
            for (x, y) in valid_moves(board):
                if self._creates_fork(board, player, x, y):
                    return (x, y)
        except:
            pass
        return None

    def _is_safe_move(self, board: Board, player: int, x: int, y: int) -> bool:
        """Проверка безопасности хода."""
        try:
            z = drop_z(board, x, y)
            if z is None:
                return False
            
            board[z][y][x] = player
            opp = 3 - player
            safe = self._immediate_win(board, opp) is None
            board[z][y][x] = 0
            return safe
        except:
            return False

    def _minimax_search(self, board: Board, player: int, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        """Ограниченный minimax поиск."""
        try:
            # Проверка терминальных состояний
            w = winner(board)
            if w == player:
                return 25000 - (self.depth - depth)
            if w == (3 - player):
                return -25000 + (self.depth - depth)
            if depth == 0 or board_full(board):
                return eval_board(board, player)
            
            moves = list(valid_moves(board))
            if not moves:
                return eval_board(board, player)
            
            # Ограничиваем количество рассматриваемых ходов для скорости
            if len(moves) > 8:
                # Сортируем по центральности
                moves = sorted(moves, key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))[:8]
            
            if maximizing:
                max_eval = -100000
                for x, y in moves:
                    try:
                        z = drop_z(board, x, y)
                        if z is None:
                            continue
                        board[z][y][x] = player
                        eval_score = self._minimax_search(board, player, depth - 1, alpha, beta, False)
                        board[z][y][x] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                    except:
                        continue
                return max_eval
            else:
                min_eval = 100000
                opp = 3 - player
                for x, y in moves:
                    try:
                        z = drop_z(board, x, y)
                        if z is None:
                            continue
                        board[z][y][x] = opp
                        eval_score = self._minimax_search(board, player, depth - 1, alpha, beta, True)
                        board[z][y][x] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                    except:
                        continue
                return min_eval
        except:
            return eval_board(board, player)

    def _get_best_move(self, board: Board, player: int, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Поиск лучшего хода среди кандидатов."""
        if not candidates:
            return self._emergency_move(board)
        
        try:
            # Сортируем кандидатов по центральности
            candidates = sorted(candidates, key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
            
            best_move = candidates[0]
            best_score = -100000
            
            for x, y in candidates:
                try:
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = player
                    score = self._minimax_search(board, player, min(self.depth - 1, 2), -100000, 100000, False)
                    board[z][y][x] = 0
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                except:
                    continue
            
            return best_move
        except:
            return candidates[0] if candidates else self._emergency_move(board)

    def get_move(
        self,
        board: List[List[List[int]]],
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Максимально стабильный главный метод."""
        try:
            # 1. Дебютная логика - простые центральные ходы
            pieces = count_pieces(board)
            if pieces <= 2:
                for move in [(1, 1), (2, 2), (1, 2), (2, 1)]:
                    try:
                        if drop_z(board, *move) is not None:
                            return self._validate_move(board, *move)
                    except:
                        continue

            # 2. Немедленная победа
            win_move = self._immediate_win(board, player)
            if win_move is not None:
                return self._validate_move(board, *win_move)

            opp = 3 - player

            # 3. Блокировка немедленной победы противника
            block_move = self._immediate_win(board, opp)
            if block_move is not None:
                return self._validate_move(board, *block_move)

            # 4. Попытка создать форк
            fork_move = self._find_fork(board, player)
            if fork_move is not None:
                return self._validate_move(board, *fork_move)

            # 5. Блокировка форка противника
            opp_fork = self._find_fork(board, opp)
            if opp_fork is not None:
                return self._validate_move(board, *opp_fork)

            # 6. Выбор среди безопасных ходов
            all_moves = list(valid_moves(board))
            if not all_moves:
                return self._emergency_move(board)

            safe_moves = []
            for move in all_moves:
                try:
                    if self._is_safe_move(board, player, *move):
                        safe_moves.append(move)
                except:
                    continue

            candidates = safe_moves if safe_moves else all_moves
            
            # 7. Поиск лучшего хода
            best_move = self._get_best_move(board, player, candidates)
            return self._validate_move(board, *best_move)

        except Exception as e:
            # Абсолютный fallback при любой ошибке
            return self._emergency_move(board)