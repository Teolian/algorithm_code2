from typing import List, Tuple, Optional
try:
    # боевое окружение (сервер)
    from framework import Alg3D, Board
except Exception:
    # локальная отладка (если запускаешь через local_driver.py)
    from local_driver import Alg3D, Board  # type: ignore


# ---------- 4x4x4 Connect-Four с гравитацией: утилиты ----------

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


def eval_board(board: List[List[List[int]]], me: int) -> int:
    """Лёгкая оценка: центр+высота + потенциалы линий (1/2/3 в ряд)."""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 10_000
    if w == opp:
        return -10_000

    score = 0

    # Центр и высота
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p == 0:
                    continue
                cent = 3 - int(abs(x - 1.5) + abs(y - 1.5))  # ближе к центру — лучше
                h = z                                       # выше — немного лучше
                s = cent + h
                score += s if p == me else -s

    # Потенциалы линий
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
        # игнорим смешанные линии
        if c1 > 0 and c2 > 0:
            continue
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        if theirs == 0:
            if mine == 3:
                score += 240  # чуть усилили
            elif mine == 2:
                score += 40
            elif mine == 1:
                score += 4
        elif mine == 0:
            if theirs == 3:
                score -= 240
            elif theirs == 2:
                score -= 40
            elif theirs == 1:
                score -= 4
    return score


# ------------------------------- ИИ -------------------------------

class MyAI(Alg3D):
    def __init__(self, depth: int = 2):
        self.depth = depth

    # --- безопасные помощники ---

    def _first_legal_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Гарантированный валидный ход (центр-сначала, затем углы)."""
        order = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0),
        ]
        for x, y in order:
            if drop_z(board, x, y) is not None:
                return (x, y)
        # поле переполнено — вернём что угодно
        return (0, 0)

    def _validate_move(self, board: List[List[List[int]]], x: int, y: int) -> Tuple[int, int]:
        """Финальная проверка перед возвратом из get_move()."""
        if not (0 <= x < 4 and 0 <= y < 4):
            return self._first_legal_move(board)
        if drop_z(board, x, y) is None:
            return self._first_legal_move(board)
        return (x, y)

    def get_winning_lines(self):
        return LINES

    # --- примитивы ---

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

    def _my_immediate_wins_in_position(self, board: Board, player: int) -> List[Tuple[int,int]]:
        """Вернуть все (x,y), которыми я выиграю немедленно в текущей позиции."""
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

    def _creates_fork(self, board: Board, player: int, x: int, y: int) -> bool:
        """
        Проверка «двойной угрозы» (fork):
        после нашего хода у нас ≥2 разных немедленных выигрыша (если бы мы ходили сразу).
        Оппонент может закрыть только один.
        """
        z = drop_z(board, x, y)
        if z is None:
            return False
        board[z][y][x] = player

        # Безопасность: не отдаём opp немедленный win
        opp = 3 - player
        opp_win = self._immediate_win(board, opp)
        if opp_win is not None:
            board[z][y][x] = 0
            return False

        my_wins = self._my_immediate_wins_in_position(board, player)
        board[z][y][x] = 0
        # Должно быть как минимум 2 в разных столбцах
        if len(my_wins) < 2:
            return False
        cols = {(cx, cy) for (cx, cy) in my_wins}
        return len(cols) >= 2

    def _find_own_fork(self, board: Board, player: int) -> Optional[Tuple[int,int]]:
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, player, x, y):
                return (x, y)
        return None

    def _find_block_opp_fork(self, board: Board, player: int) -> Optional[Tuple[int,int]]:
        """Если у соперника есть форк-ход, попробуем его заблокировать или контрфоркнуть."""
        opp = 3 - player

        # Список всех opp-форков
        opp_forks = []
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, opp, x, y):
                opp_forks.append((x, y))
        if not opp_forks:
            return None

        # 1) Если есть ход, который уничтожает ВСЕ opp-форки (или создаёт наш мгновенный win/форк)
        #    — берём такой.
        # 1a) наш немедленный win/форк — приоритет
        my_win = self._immediate_win(board, player)
        if my_win:
            return my_win
        my_fork = self._find_own_fork(board, player)
        if my_fork:
            return my_fork

        # 1b) блок: попробуем походить в один из opp-форк-столбцов
        for (bx, by) in opp_forks:
            z = drop_z(board, bx, by)
            if z is not None:
                # простой блок
                return (bx, by)

        # 2) если не можем прямым блоком — ищем «мешающий» ход:
        #    ход, после которого у opp не останется немедленного форка
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            # после нашего хода у opp ещё есть форк?
            still_fork = False
            for (ox, oy) in valid_moves(board):
                if self._creates_fork(board, opp, ox, oy):
                    still_fork = True
                    break
            board[z][y][x] = 0
            if not still_fork:
                return (x, y)

        # fallback: хотя бы блокируем один из их форков
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
            if not safe:
                break
        board[z][y][x] = 0
        return safe

    # --- мини alpha-beta (d=2) ---

    def _alpha_beta_best(self, board: Board, player: int, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        opp = 3 - player

        # центр-сначала
        candidates = sorted(candidates, key=lambda m: (abs(m[0] - 1.5) + abs(m[1] - 1.5)))

        def ab(pl: int, d: int, a: int, b: int) -> int:
            w = winner(board)
            if w == player:
                return 10_000 - (2 - d)
            if w == opp:
                return -10_000 + (2 - d)
            if d == 0 or board_full(board):
                return eval_board(board, player)

            if pl == player:
                v = -10**9
                for (x, y) in candidates:
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
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            v = ab(opp, self.depth - 1, -10**9, 10**9)
            board[z][y][x] = 0
            if v > bestv:
                bestv, best = v, (x, y)
        return best

    # --- главный метод ---

    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Приоритет: win → block → собственный fork → блок opp-fork → safe → alpha-beta(d=2) → fallback."""
        try:
            # 0) микробук (старт белыми) — чуть чаще даёт зацепку под форк
            #    не жёстко, просто небольшой приоритет
            if all(board[0][y][x] == 0 for x in range(4) for y in range(4)):
                for pref in [(1,1), (2,2), (1,2), (2,1)]:
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

            # 5) кандидаты (safe-filter). Если safe-пусто — берём все валидные
            cands = [m for m in valid_moves(board) if self._is_safe(board, player, m[0], m[1])]
            if not cands:
                cands = list(valid_moves(board))
            if not cands:
                return (0, 0)  # поле заполнено

            # 6) лёгкий alpha-beta на 2 полухода по кандидатам
            x, y = self._alpha_beta_best(board, player, cands)
            return self._validate_move(board, x, y)

        except Exception:
            # Любая ошибка → гарантированный валидный ход
            return self._first_legal_move(board)
