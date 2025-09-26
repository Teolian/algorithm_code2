from typing import List, Tuple, Optional, Dict
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


def improved_eval_board(board: List[List[List[int]]], me: int) -> int:
    """Улучшенная оценочная функция с учетом связности и контроля."""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 100_000
    if w == opp:
        return -100_000

    score = 0

    # 1. Позиционные бонусы (центр + высота)
    center_bonus = [
        [1, 2, 2, 1],
        [2, 4, 4, 2],
        [2, 4, 4, 2],
        [1, 2, 2, 1]
    ]
    
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p == 0:
                    continue
                pos_score = center_bonus[y][x] + z * 2
                score += pos_score if p == me else -pos_score

    # 2. Анализ потенциала линий с весовыми коэффициентами
    line_values = {3: 1000, 2: 100, 1: 10}  # 3 в ряд, 2 в ряд, 1 в ряду
    
    for line in LINES:
        c0 = c1 = c2 = 0
        accessible = True  # можно ли завершить эту линию
        
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0:
                c0 += 1
                # Проверяем, можно ли поставить фишку в эту позицию
                if z > 0 and board[z-1][y][x] == 0:
                    accessible = False  # фишка повиснет в воздухе
            elif v == 1:
                c1 += 1
            else:
                c2 += 1
        
        # Смешанные линии игнорируем
        if c1 > 0 and c2 > 0:
            continue
            
        # Если линию нельзя завершить, снижаем её ценность
        multiplier = 1.0 if accessible else 0.3
        
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        
        if theirs == 0 and mine > 0:
            bonus = line_values.get(mine, 0) * multiplier
            # Бонус за близость к центру линии
            if is_center_line(line):
                bonus *= 1.5
            score += int(bonus)
        elif mine == 0 and theirs > 0:
            penalty = line_values.get(theirs, 0) * multiplier
            if is_center_line(line):
                penalty *= 1.5
            score -= int(penalty)
    
    # 3. Контроль ключевых позиций
    key_positions = [(1, 1, 0), (2, 2, 0), (1, 2, 0), (2, 1, 0)]
    for x, y, z in key_positions:
        p = board[z][y][x]
        if p == me:
            score += 50
        elif p == opp:
            score -= 50
    
    return score


def is_center_line(line: List[Tuple[int, int, int]]) -> bool:
    """Проверяет, проходит ли линия через центральные позиции."""
    center_positions = {(1, 1), (1, 2), (2, 1), (2, 2)}
    line_xy = {(x, y) for x, y, z in line}
    return bool(line_xy & center_positions)


class MyAI(Alg3D):
    def __init__(self, depth: int = 4):
        self.depth = depth
        self.transposition_table: Dict[str, Tuple[int, int]] = {}
        
        # Расширенный дебютный репертуар
        self.opening_book = {
            # Начальные ходы (приоритет центральным позициям)
            0: [(1, 1), (2, 2), (1, 2), (2, 1)],
            # Ответы на центральные ходы противника
            1: {
                (1, 1): [(2, 2), (1, 2), (2, 1)],
                (2, 2): [(1, 1), (1, 2), (2, 1)],
                (1, 2): [(2, 1), (1, 1), (2, 2)],
                (2, 1): [(1, 2), (1, 1), (2, 2)],
            }
        }

    def board_hash(self, board: List[List[List[int]]]) -> str:
        """Создает хеш для позиции доски."""
        return str(board)

    def _first_legal_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Гарантированный валидный ход с улучшенным приоритетом."""
        # Приоритет: центр -> внутренние позиции -> края -> углы
        order = [
            (1, 1), (2, 2), (1, 2), (2, 1),  # центр
            (0, 1), (1, 0), (3, 2), (2, 3),  # внутренние края
            (0, 2), (2, 0), (3, 1), (1, 3),  # внешние края
            (0, 0), (3, 3), (0, 3), (3, 0),  # углы
        ]
        for x, y in order:
            if drop_z(board, x, y) is not None:
                return (x, y)
        return (0, 0)

    def _validate_move(self, board: List[List[List[int]]], x: int, y: int) -> Tuple[int, int]:
        """Финальная проверка перед возвратом из get_move()."""
        if not (0 <= x < 4 and 0 <= y < 4):
            return self._first_legal_move(board)
        if drop_z(board, x, y) is None:
            return self._first_legal_move(board)
        return (x, y)

    def _immediate_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Есть ли ход, который выигрывает сразу."""
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            if winner(board) == player:
                board[z][y][x] = 0
                return (x, y)
            board[z][y][x] = 0
        return None

    def _find_all_immediate_wins(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """Найти все ходы для немедленной победы."""
        wins = []
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            if winner(board) == player:
                wins.append((x, y))
            board[z][y][x] = 0
        return wins

    def _creates_multiple_threats(self, board: Board, player: int, x: int, y: int) -> int:
        """Подсчитывает количество угроз, создаваемых ходом."""
        z = drop_z(board, x, y)
        if z is None:
            return 0
        
        board[z][y][x] = player
        opp = 3 - player
        
        # Не создавать ход, дающий сопернику немедленную победу
        if self._immediate_win(board, opp) is not None:
            board[z][y][x] = 0
            return -1
        
        threats = len(self._find_all_immediate_wins(board, player))
        board[z][y][x] = 0
        return threats

    def _find_best_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Найти ход, создающий максимальное количество угроз."""
        best_move = None
        max_threats = 1  # Минимум 2 угрозы для форка
        
        for (x, y) in valid_moves(board):
            threats = self._creates_multiple_threats(board, player, x, y)
            if threats > max_threats:
                max_threats = threats
                best_move = (x, y)
        
        return best_move

    def _is_safe(self, board: Board, player: int, x: int, y: int) -> bool:
        """Проверяет безопасность хода."""
        opp = 3 - player
        z = drop_z(board, x, y)
        if z is None:
            return False
        
        board[z][y][x] = player
        safe = self._immediate_win(board, opp) is None
        board[z][y][x] = 0
        return safe

    def _order_moves(self, board: Board, moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Сортирует ходы по перспективности для лучшего отсечения в alpha-beta."""
        def move_priority(move):
            x, y = move
            # Приоритет центральным позициям
            center_dist = abs(x - 1.5) + abs(y - 1.5)
            # Бонус за высоту
            z = drop_z(board, x, y)
            height_bonus = z if z is not None else -1
            return (center_dist, -height_bonus)
        
        return sorted(moves, key=move_priority)

    def _alpha_beta_search(self, board: Board, player: int, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        """Улучшенный alpha-beta поиск с транспозиционной таблицей."""
        # Проверяем транспозиционную таблицу
        board_key = self.board_hash(board)
        if board_key in self.transposition_table:
            cached_score, cached_depth = self.transposition_table[board_key]
            if cached_depth >= depth:
                return cached_score

        # Терминальные состояния
        w = winner(board)
        if w == player:
            return 100_000 - (self.depth - depth)
        if w == (3 - player):
            return -100_000 + (self.depth - depth)
        if depth == 0 or board_full(board):
            score = improved_eval_board(board, player)
            self.transposition_table[board_key] = (score, depth)
            return score

        moves = list(valid_moves(board))
        moves = self._order_moves(board, moves)

        if maximizing:
            max_eval = -1000000
            for x, y in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score = self._alpha_beta_search(board, player, depth - 1, alpha, beta, False)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_key] = (max_eval, depth)
            return max_eval
        else:
            min_eval = 1000000
            opp = 3 - player
            for x, y in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                eval_score = self._alpha_beta_search(board, player, depth - 1, alpha, beta, True)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            self.transposition_table[board_key] = (min_eval, depth)
            return min_eval

    def _get_best_move_ab(self, board: Board, player: int, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Находит лучший ход с помощью alpha-beta поиска."""
        if not candidates:
            return self._first_legal_move(board)

        candidates = self._order_moves(board, candidates)
        best_move = candidates[0]
        best_score = -1000000

        for x, y in candidates:
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            score = self._alpha_beta_search(board, player, self.depth - 1, -1000000, 1000000, False)
            board[z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)

        return best_move

    def _use_opening_book(self, board: Board) -> Optional[Tuple[int, int]]:
        """Использует дебютную библиотеку."""
        pieces = count_pieces(board)
        
        if pieces == 0:
            # Первый ход - выбираем из лучших начальных позиций
            for move in self.opening_book[0]:
                if drop_z(board, *move) is not None:
                    return move
        
        elif pieces == 1:
            # Второй ход - реагируем на ход противника
            for x in range(4):
                for y in range(4):
                    if board[0][y][x] != 0:  # Нашли ход противника
                        opp_move = (x, y)
                        if opp_move in self.opening_book[1]:
                            for response in self.opening_book[1][opp_move]:
                                if drop_z(board, *response) is not None:
                                    return response
        
        return None

    def get_move(
        self,
        board: List[List[List[int]]],
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Главный метод выбора хода с улучшенной стратегией."""
        try:
            # Очищаем транспозиционную таблицу периодически
            if len(self.transposition_table) > 10000:
                self.transposition_table.clear()

            # 1. Дебютная книга
            opening_move = self._use_opening_book(board)
            if opening_move is not None:
                return self._validate_move(board, *opening_move)

            # 2. Немедленная победа
            win_move = self._immediate_win(board, player)
            if win_move is not None:
                return self._validate_move(board, *win_move)

            opp = 3 - player

            # 3. Блокировка немедленной победы противника
            block_move = self._immediate_win(board, opp)
            if block_move is not None:
                return self._validate_move(board, *block_move)

            # 4. Поиск лучшего форка (создание множественных угроз)
            fork_move = self._find_best_fork(board, player)
            if fork_move is not None:
                return self._validate_move(board, *fork_move)

            # 5. Блокировка форков противника
            opp_fork = self._find_best_fork(board, opp)
            if opp_fork is not None:
                return self._validate_move(board, *opp_fork)

            # 6. Alpha-beta поиск среди безопасных ходов
            all_moves = list(valid_moves(board))
            safe_moves = [m for m in all_moves if self._is_safe(board, player, *m)]
            
            candidates = safe_moves if safe_moves else all_moves
            if not candidates:
                return self._first_legal_move(board)

            best_move = self._get_best_move_ab(board, player, candidates)
            return self._validate_move(board, *best_move)

        except Exception:
            return self._first_legal_move(board)