from typing import List, Tuple, Optional
import time

# Попытка взять типы из боевого/локального окружения фреймворка
try:
    from framework import Alg3D, Board  # type: ignore
except Exception:
    try:
        from local_driver import Alg3D, Board  # type: ignore
    except Exception:
        # Фолбэк только для type hints при автономном запуске
        Board = List[List[List[int]]]  # type: ignore
        class Alg3D:  # type: ignore
            pass


# ---------------------- 4x4x4 Connect-Four: утилиты ----------------------

def gen_lines():
    """Полный набор из 76 победных линий для 4x4x4."""
    L = []
    # По оси X (для каждого y, z)
    for y in range(4):
        for z in range(4):
            L.append([(i, y, z) for i in range(4)])
    # По оси Y (для каждого x, z)
    for x in range(4):
        for z in range(4):
            L.append([(x, i, z) for i in range(4)])
    # По оси Z (для каждого x, y)
    for x in range(4):
        for y in range(4):
            L.append([(x, y, i) for i in range(4)])
    # Диагонали в каждой плоскости z (x-y)
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


def drop_z(board: Board, x: int, y: int) -> Optional[int]:
    """Куда «упадёт» фишка в столбце (x,y). None если столбец полон/вне границ."""
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None


def board_full(board: Board) -> bool:
    """Заполнено ли поле (смотрим верхний слой)."""
    return all(board[3][y][x] != 0 for x in range(4) for y in range(4))


def winner(board: Board) -> int:
    """Победитель: 1 или 2; 0 если ещё нет."""
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0


def valid_moves(board: Board):
    """Итератор по всем допустимым (x,y), где столбец не полон."""
    for y in range(4):
        for x in range(4):
            if drop_z(board, x, y) is not None:
                yield (x, y)


def eval_board(board: Board, me: int) -> int:
    """
    Лёгкая эвристика:
    - Немедленные состояния (win/lose) даём большим числом.
    - Небольшой бонус за центр и высоту (z).
    - Линейные потенциалы: открытые линии только моих/их фишек.
    """
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 10_000
    if w == opp:
        return -10_000

    score = 0

    # Центр (ближе к (1.5,1.5)) и высота z — маленькие локальные бонусы
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p == 0:
                    continue
                cent = 3 - int(abs(x - 1.5) + abs(y - 1.5))  # 3..0
                h = z  # 0..3
                s = cent + h
                if p == me:
                    score += s
                else:
                    score -= s

    # Потенциалы линий: открытые (только мои либо только их)
    for line in LINES:
        mine = theirs = empty = 0
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0:
                empty += 1
            elif v == me:
                mine += 1
            else:
                theirs += 1
        # Блокированные линии (оба игрока в линии) — пропускаем
        if mine > 0 and theirs > 0:
            continue
        if theirs == 0:
            # Только мои
            if mine == 3 and empty == 1:
                score += 240
            elif mine == 2 and empty == 2:
                score += 40
            elif mine == 1 and empty == 3:
                score += 4
        elif mine == 0:
            # Только их
            if theirs == 3 and empty == 1:
                score -= 240
            elif theirs == 2 and empty == 2:
                score -= 40
            elif theirs == 1 and empty == 3:
                score -= 4

    return score


# -------------------------------- ИИ --------------------------------

class MyAI(Alg3D):
    def __init__(self, depth: int = 2):
        # depth — максимальная глубина для итеративного заглубления (1..depth)
        self.depth = depth

    # ---------- Лимитер времени (CPU + мягкий по wall) ----------

    class _TimeGuard:
        def __init__(self, cpu_limit: float = 9.5, wall_limit: float = 29.0):
            # CPU-время (то, что учитывает ограничитель сервера)
            self.cpu_start = time.process_time()
            self.cpu_limit = cpu_limit
            # Доп. мягкий ограничитель по «настенным» секундах (на всякий случай)
            self.wall_start = time.perf_counter()
            self.wall_limit = wall_limit

        def over_cpu(self) -> bool:
            return (time.process_time() - self.cpu_start) >= self.cpu_limit

        def over_wall(self) -> bool:
            return (time.perf_counter() - self.wall_start) >= self.wall_limit

        def should_stop(self) -> bool:
            # Жёстко по CPU, мягко по wall
            return self.over_cpu() or self.over_wall()

    # ---------- Безопасные помощники ----------

    def _first_legal_move(self, board: Board) -> Tuple[int, int]:
        """Гарантированный валидный ход (центр-сначала, затем остальные)."""
        order = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0),
        ]
        for x, y in order:
            if drop_z(board, x, y) is not None:
                return (x, y)
        # Если по какой-то причине всё занято (должно ловиться раньше)
        for (x, y) in valid_moves(board):
            return (x, y)
        return (0, 0)

    def _validate_move(self, board: Board, x: int, y: int) -> Tuple[int, int]:
        """Возвращает (x,y) если столбец доступен, иначе — первый валидный."""
        if drop_z(board, x, y) is not None:
            return (x, y)
        return self._first_legal_move(board)

    def get_winning_lines(self):
        return LINES

    # ---------- Примитивы ----------

    def _immediate_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Есть ли ход, который выигрывает сразу."""
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            won = (winner(board) == player)
            board[z][y][x] = 0
            if won:
                return (x, y)
        return None

    def _my_immediate_wins_in_position(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """Вернуть все (x,y), которыми я выиграю немедленно в текущей позиции."""
        wins: List[Tuple[int, int]] = []
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            if winner(board) == player:
                wins.append((x, y))
            board[z][y][x] = 0
        return wins

    def _creates_fork(self, board: Board, player: int, x: int, y: int) -> bool:
        """Проверить, создаёт ли ход (x,y) форк — ≥2 независимых немедленных выигрыша."""
        z = drop_z(board, x, y)
        if z is None:
            return False
        board[z][y][x] = player

        opp = 3 - player
        # Если даём немедленный выигрыш сопернику — это не форк для нас
        opp_win = self._immediate_win(board, opp)
        if opp_win is not None:
            board[z][y][x] = 0
            return False

        my_wins = self._my_immediate_wins_in_position(board, player)
        board[z][y][x] = 0

        if len(my_wins) < 2:
            return False
        # важен не просто счёт, а чтобы были разные столбцы
        cols = {(cx, cy) for (cx, cy) in my_wins}
        return len(cols) >= 2

    def _find_own_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, player, x, y):
                return (x, y)
        return None

    def _find_block_opp_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Если у соперника есть форк-ход, попробуем его заблокировать или контрфоркнуть."""
        opp = 3 - player

        # 1) собрать все их форк-ходы
        opp_forks: List[Tuple[int, int]] = []
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, opp, x, y):
                opp_forks.append((x, y))
        if not opp_forks:
            return None

        # 2) прямой блок: если можно поставить в тот же столбец (x,y), закрывая форк
        for (x, y) in opp_forks:
            z = drop_z(board, x, y)
            if z is not None:
                return (x, y)

        # 3) «мешающий» ход: сделаем такой ход, после которого у opp не останется немедленного форка
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            still_fork = False
            for (ox, oy) in valid_moves(board):
                if self._creates_fork(board, opp, ox, oy):
                    still_fork = True
                    break
            board[z][y][x] = 0
            if not still_fork:
                return (x, y)

        # 4) fallback: хотя бы блокируем один из их форков (если можно)
        return opp_forks[0]

    def _is_safe(self, board: Board, player: int, x: int, y: int) -> bool:
        """После нашего хода соперник не получает немедленную победу."""
        opp = 3 - player
        z = drop_z(board, x, y)
        if z is None:
            return False
        board[z][y][x] = player
        safe = True
        for (ox, oy) in valid_moves(board):
            oz = drop_z(board, ox, oy)
            if oz is None:
                continue
            board[oz][oy][ox] = opp
            if winner(board) == opp:
                safe = False
                board[oz][oy][ox] = 0
                break
            board[oz][oy][ox] = 0
        board[z][y][x] = 0
        return safe

    # ---------- Alpha-Beta + TimeGuard ----------

    def _alpha_beta_best_depth(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        depth: int,
        tg: "_TimeGuard",
    ) -> Tuple[int, int]:
        opp = 3 - player

        # Move ordering: центр сначала
        candidates = sorted(candidates, key=lambda m: (abs(m[0] - 1.5) + abs(m[1] - 1.5)))

        def ab(pl: int, d: int, a: int, b: int) -> int:
            # Ранний выход по лимиту
            if tg.should_stop():
                return eval_board(board, player)

            w = winner(board)
            if w == player:
                return 10_000 - max(0, d)
            if w == opp:
                return -10_000 + max(0, d)
            if d == 0 or board_full(board):
                return eval_board(board, player)

            if pl == player:
                v = -10**9
                for (x, y) in candidates:
                    if tg.should_stop():
                        break
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = pl
                    v = max(v, ab(opp, d - 1, a, b))
                    board[z][y][x] = 0
                    a = max(a, v)
                    if b <= a:
                        break
                return v
            else:
                v = 10**9
                for (x, y) in candidates:
                    if tg.should_stop():
                        break
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = pl
                    v = min(v, ab(player, d - 1, a, b))
                    board[z][y][x] = 0
                    b = min(b, v)
                    if b <= a:
                        break
                return v

        best = candidates[0]
        bestv = -10**9
        for (x, y) in candidates:
            if tg.should_stop():
                break
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            v = ab(opp, depth - 1, -10**9, 10**9)
            board[z][y][x] = 0
            if v > bestv:
                bestv, best = v, (x, y)
        return best

    def _alpha_beta_best_id(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        max_depth: int,
        tg: "_TimeGuard",
    ) -> Tuple[int, int]:
        """Итеративное заглубление: 1..max_depth. Возвращаем лучший-so-far."""
        best_so_far = candidates[0]
        for d in range(1, max_depth + 1):
            if tg.should_stop():
                break
            best_so_far = self._alpha_beta_best_depth(board, player, candidates, d, tg)
        return best_so_far

    # ------------------------ Главная точка входа ------------------------

    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """
        Приоритет: win → block → собственный fork → блок opp-fork → safe → alpha-beta(ID) → fallback.
        Все вычисления под защитой TimeGuard (CPU ~9.5s).
        """
        try:
            tg = self._TimeGuard(cpu_limit=9.5, wall_limit=29.0)

            # 0) микробук (старт: поле пусто) — небольшой приоритет к центру/полуцентру
            if all(board[0][y][x] == 0 for x in range(4) for y in range(4)):
                for pref in [(1, 1), (2, 2), (1, 2), (2, 1)]:
                    if tg.should_stop():
                        break
                    if drop_z(board, *pref) is not None:
                        return self._validate_move(board, *pref)

            # 1) мгновенная победа
            mv = self._immediate_win(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            opp = 3 - player

            # 2) мгновенный блок
            mv = self._immediate_win(board, opp)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 3) собственный форк (двойная угроза)
            mv = self._find_own_fork(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 4) блок чужого форка (или контрфорк)
            mv = self._find_block_opp_fork(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 5) кандидаты (safe-фильтр). Если safe-пусто — берём все валидные.
            cands = [m for m in valid_moves(board) if self._is_safe(board, player, m[0], m[1])]
            if not cands:
                cands = list(valid_moves(board))
            if not cands:  # поле заполнено
                return (0, 0)

            # 6) Итеративное заглубление alpha-beta: 1..self.depth (пока позволяет время)
            x, y = self._alpha_beta_best_id(board, player, cands, self.depth, tg)
            return self._validate_move(board, x, y)

        except Exception:
            # Любая ошибка → гарантированный валидный ход
            return self._first_legal_move(board)
