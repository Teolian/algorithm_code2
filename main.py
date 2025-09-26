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
    # По оси Z (для каждого x,y) - КРИТИЧЕСКИ ВАЖНЫЕ ВЕРТИКАЛЬНЫЕ ЛИНИИ
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
    # 4 пространственные диагонали - ОЧЕНЬ ОПАСНЫЕ
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


def is_critical_line(line: List[Tuple[int, int, int]]) -> bool:
    """Определяет критически важные линии."""
    # Вертикальные линии (по Z)
    if all(x == line[0][0] and y == line[0][1] for x, y, z in line):
        return True
    # Пространственные диагонали
    if (line == [(0,0,0), (1,1,1), (2,2,2), (3,3,3)] or
        line == [(0,0,3), (1,1,2), (2,2,1), (3,3,0)] or
        line == [(0,3,0), (1,2,1), (2,1,2), (3,0,3)] or
        line == [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]):
        return True
    # Центральные диагонали в плоскостях
    center_diagonals = [
        [(1,1,z), (2,2,z)] for z in range(4)
    ] + [
        [(1,2,z), (2,1,z)] for z in range(4)
    ]
    for partial in center_diagonals:
        if all(pos in line for pos in partial):
            return True
    return False


def eval_board_aggressive(board: List[List[List[int]]], me: int) -> int:
    """Агрессивная оценочная функция с акцентом на атаку."""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 100_000
    if w == opp:
        return -100_000

    score = 0

    # 1. Контроль центра (более агрессивно)
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for x, y in center_positions:
        for z in range(4):
            p = board[z][y][x]
            if p == me:
                score += 100 + z * 20  # Больше бонусов за центр
            elif p == opp:
                score -= 80 + z * 15

    # 2. Анализ линий с агрессивными весами
    for line in LINES:
        c0 = c1 = c2 = 0
        line_accessible = True
        
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0:
                c0 += 1
                # Проверяем доступность позиции
                actual_z = drop_z(board, x, y)
                if actual_z != z and actual_z is not None:
                    line_accessible = False
            elif v == 1:
                c1 += 1
            else:
                c2 += 1
        
        if c1 > 0 and c2 > 0:  # Смешанные линии игнорируем
            continue
            
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        
        # Агрессивные веса для атакующей игры
        multiplier = 4.0 if is_critical_line(line) else 1.0
        if not line_accessible:
            multiplier *= 0.3
        
        if theirs == 0:
            if mine == 3:
                score += int(2000 * multiplier)  # ОЧЕНЬ агрессивно стремимся к победе
            elif mine == 2:
                score += int(300 * multiplier)   # Сильно поощряем развитие атак
            elif mine == 1:
                score += int(40 * multiplier)
        elif mine == 0:
            if theirs == 3:
                score -= int(2500 * multiplier)  # Критично блокировать
            elif theirs == 2:
                score -= int(200 * multiplier)   # Блокировать развитие
            elif theirs == 1:
                score -= int(30 * multiplier)

    # 3. Бонус за создание множественных угроз
    my_threats = count_immediate_threats(board, me)
    opp_threats = count_immediate_threats(board, opp)
    score += my_threats * 500 - opp_threats * 600

    # 4. Эндгеймный бонус - более агрессивная игра в конце
    pieces = count_pieces(board)
    if pieces > 40:  # Поздняя стадия игры
        score *= 1.5  # Усиливаем все оценки
    
    return score


def count_immediate_threats(board: List[List[List[int]]], player: int) -> int:
    """Подсчет количества немедленных угроз (ходов на победу)."""
    threats = 0
    try:
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            if winner(board) == player:
                threats += 1
            board[z][y][x] = 0
    except:
        pass
    return threats


class MyAI(Alg3D):
    def __init__(self, depth: int = 4):  # Увеличиваем глубину для лучшего планирования
        self.depth = depth
        self.game_phase = "opening"  # opening, middle, endgame

    def _emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Аварийный ход с приоритетом центру."""
        priority_moves = [
            (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
            (0, 1), (1, 0), (3, 2), (2, 3),  # Около центра
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0),  # Углы
        ]
        
        for x, y in priority_moves:
            try:
                if 0 <= x < 4 and 0 <= y < 4 and drop_z(board, x, y) is not None:
                    return (x, y)
            except:
                continue
        
        for x in range(4):
            for y in range(4):
                try:
                    if drop_z(board, x, y) is not None:
                        return (x, y)
                except:
                    continue
        return (0, 0)

    def _validate_move(self, board: List[List[List[int]]], x: int, y: int) -> Tuple[int, int]:
        """Валидация с фокусом на агрессивность."""
        try:
            if not (0 <= x < 4 and 0 <= y < 4) or drop_z(board, x, y) is None:
                return self._emergency_move(board)
            return (x, y)
        except:
            return self._emergency_move(board)

    def _find_all_wins(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """Найти все немедленные победы."""
        wins = []
        try:
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                if winner(board) == player:
                    wins.append((x, y))
                board[z][y][x] = 0
        except:
            pass
        return wins

    def _find_winning_threats(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """Найти ходы, создающие множественные угрозы на победу."""
        threat_moves = []
        try:
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                
                board[z][y][x] = player
                
                # Проверяем, не дает ли этот ход сопернику немедленную победу
                opp = 3 - player
                opp_wins = self._find_all_wins(board, opp)
                if opp_wins:
                    board[z][y][x] = 0
                    continue
                
                # Подсчитываем наши угрозы после этого хода
                my_wins = self._find_all_wins(board, player)
                board[z][y][x] = 0
                
                if len(my_wins) >= 2:  # Создает форк
                    threat_moves.append((x, y, len(my_wins)))
                elif len(my_wins) >= 1:  # Создает угрозу
                    threat_moves.append((x, y, len(my_wins)))
        except:
            pass
        
        # Сортируем по количеству создаваемых угроз (убывание)
        threat_moves.sort(key=lambda x: x[2], reverse=True)
        return [(x, y) for x, y, _ in threat_moves]

    def _find_critical_defense(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Критическая защита - блокировка 3-в-ряд противника."""
        opp = 3 - player
        critical_blocks = []
        
        try:
            for line in LINES:
                opp_count = 0
                my_count = 0
                empty_spot = None
                
                for (x, y, z) in line:
                    v = board[z][y][x]
                    if v == opp:
                        opp_count += 1
                    elif v == player:
                        my_count += 1
                    elif v == 0:
                        actual_z = drop_z(board, x, y)
                        if actual_z == z:  # Фишка упадет именно сюда
                            empty_spot = (x, y)
                
                # Критически важно блокировать 3-в-ряд
                if opp_count == 3 and my_count == 0 and empty_spot:
                    priority = 3 if is_critical_line(line) else 2
                    critical_blocks.append((empty_spot, priority))
                # Также важно блокировать сильные 2-в-ряд
                elif opp_count == 2 and my_count == 0 and empty_spot and is_critical_line(line):
                    critical_blocks.append((empty_spot, 1))
        except:
            pass
        
        if critical_blocks:
            critical_blocks.sort(key=lambda x: x[1], reverse=True)
            return critical_blocks[0][0]
        return None

    def _alpha_beta_search(self, board: Board, player: int, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        """Агрессивный alpha-beta с улучшенной оценкой."""
        try:
            w = winner(board)
            if w == player:
                return 50000 - (self.depth - depth)
            if w == (3 - player):
                return -50000 + (self.depth - depth)
            if depth == 0 or board_full(board):
                return eval_board_aggressive(board, player)
            
            moves = list(valid_moves(board))
            if not moves:
                return eval_board_aggressive(board, player)
            
            # Умная сортировка ходов для лучшего отсечения
            def move_priority(move):
                x, y = move
                # Приоритет центру и создающим угрозы ходам
                center_dist = abs(x - 1.5) + abs(y - 1.5)
                return center_dist
            
            moves = sorted(moves, key=move_priority)
            
            # Ограничиваем количество рассматриваемых ходов для скорости
            if len(moves) > 10:
                moves = moves[:10]
            
            if maximizing:
                max_eval = -200000
                for x, y in moves:
                    try:
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
                    except:
                        continue
                return max_eval
            else:
                min_eval = 200000
                opp = 3 - player
                for x, y in moves:
                    try:
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
                    except:
                        continue
                return min_eval
        except:
            return eval_board_aggressive(board, player)

    def _get_best_move_aggressive(self, board: Board, player: int, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Агрессивный поиск лучшего хода."""
        if not candidates:
            return self._emergency_move(board)
        
        try:
            best_move = candidates[0]
            best_score = -200000
            
            for x, y in candidates:
                try:
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = player
                    
                    # Используем полную глубину для более точного анализа
                    score = self._alpha_beta_search(board, player, self.depth - 1, -200000, 200000, False)
                    board[z][y][x] = 0
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                except:
                    continue
            
            return best_move
        except:
            return candidates[0] if candidates else self._emergency_move(board)

    def _update_game_phase(self, board: Board):
        """Определение фазы игры для адаптации стратегии."""
        pieces = count_pieces(board)
        if pieces <= 8:
            self.game_phase = "opening"
        elif pieces <= 35:
            self.game_phase = "middle"
        else:
            self.game_phase = "endgame"
            self.depth = min(5, self.depth + 1)  # Увеличиваем глубину в эндгейме

    def get_move(
        self,
        board: List[List[List[int]]],
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Агрессивная стратегия с акцентом на быструю победу."""
        try:
            self._update_game_phase(board)
            
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА - наивысший приоритет
            win_moves = self._find_all_wins(board, player)
            if win_moves:
                return self._validate_move(board, *win_moves[0])
            
            opp = 3 - player
            
            # 2. КРИТИЧЕСКАЯ ЗАЩИТА (блокировка 3-в-ряд)
            critical_defense = self._find_critical_defense(board, player)
            if critical_defense:
                return self._validate_move(board, *critical_defense)
            
            # 3. АГРЕССИВНЫЕ УГРОЗЫ (создание форков и множественных угроз)
            threat_moves = self._find_winning_threats(board, player)
            if threat_moves:
                # В эндгейме предпочитаем самые сильные угрозы
                if self.game_phase == "endgame":
                    return self._validate_move(board, *threat_moves[0])
                # В других фазах проверяем безопасность
                for move in threat_moves[:3]:  # Рассматриваем топ-3 угрозы
                    x, y = move
                    z = drop_z(board, x, y)
                    if z is not None:
                        board[z][y][x] = player
                        opp_wins = self._find_all_wins(board, opp)
                        board[z][y][x] = 0
                        if not opp_wins:  # Безопасный агрессивный ход
                            return self._validate_move(board, *move)
            
            # 4. Блокировка обычных угроз противника
            opp_wins = self._find_all_wins(board, opp)
            if opp_wins:
                return self._validate_move(board, *opp_wins[0])
            
            # 5. Блокировка угроз противника
            opp_threats = self._find_winning_threats(board, opp)
            if opp_threats:
                return self._validate_move(board, *opp_threats[0])
            
            # 6. Агрессивный поиск лучшего хода
            all_moves = list(valid_moves(board))
            if not all_moves:
                return self._emergency_move(board)
            
            # В разных фазах игры разная стратегия отбора кандидатов
            if self.game_phase == "opening":
                # В дебюте предпочитаем центральные ходы
                candidates = sorted(all_moves, key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))[:8]
            else:
                # В середине и эндгейме рассматриваем все ходы, но сортируем агрессивно
                candidates = all_moves
            
            best_move = self._get_best_move_aggressive(board, player, candidates)
            return self._validate_move(board, *best_move)
            
        except Exception:
            return self._emergency_move(board)