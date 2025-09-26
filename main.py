from typing import List, Tuple, Optional, Dict
import time
import random

# Попытка взять типы из боевого/локального окружения фреймворка
try:
    from framework import Alg3D, Board  # type: ignore
except Exception:
    try:
        from local_driver import Alg3D, Board  # type: ignore
    except Exception:
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
                score += 260
            elif mine == 2 and empty == 2:
                score += 44
            elif mine == 1 and empty == 3:
                score += 4
        elif mine == 0:
            # Только их
            if theirs == 3 and empty == 1:
                score -= 260
            elif theirs == 2 and empty == 2:
                score -= 44
            elif theirs == 1 and empty == 3:
                score -= 4

    return score


# -------------------------------- ИИ --------------------------------

class MyAI(Alg3D):
    """
    Надёжная версия:
      • TimeGuard (CPU + soft-wall)
      • Итеративное заглубление
      • Zobrist + TT (исправлены TT-флаги)
      • PVS + аспирационные окна (с защитой)
      • Win/Block-first ordering
      • Жёсткие фоллбеки на каждом уровне
    """
    TT_EXACT = 0
    TT_LOWER = 1
    TT_UPPER = -1

    def __init__(self, depth: int = 4, tt_capacity: int = 200_000):
        self.depth = depth

        # --- Zobrist ---
        self._zobrist_ready = False
        self._piece_key = None  # type: ignore
        self._stm_key = 0
        self._zobrist_init()

        # --- TT ---
        self.tt: Dict[int, Tuple[int, int, int, Optional[Tuple[int, int]]]] = {}
        self.tt_capacity = tt_capacity

        # killer moves
        self.killers: List[List[Optional[Tuple[int, int]]]] = [[None, None] for _ in range(32)]

        # root aspiration
        self._last_root_score: Optional[int] = None

    # ---------- Лимитер времени ----------

    class _TimeGuard:
        def __init__(self, cpu_limit: float = 9.5, wall_limit: float = 29.0):
            self.cpu_start = time.process_time()
            self.cpu_limit = cpu_limit
            self.wall_start = time.perf_counter()
            self.wall_limit = wall_limit

        def over_cpu(self) -> bool:
            return (time.process_time() - self.cpu_start) >= self.cpu_limit

        def over_wall(self) -> bool:
            return (time.perf_counter() - self.wall_start) >= self.wall_limit

        def should_stop(self) -> bool:
            return self.over_cpu() or self.over_wall()

    # ---------- Zobrist ----------

    def _zobrist_init(self):
        if self._zobrist_ready:
            return
        rnd = random.Random(0xC0FFEE)
        self._piece_key = [[[[
            rnd.getrandbits(64) for _ in range(2)
        ] for _ in range(4)] for _ in range(4)] for _ in range(4)]  # type: ignore
        self._stm_key = rnd.getrandbits(64)
        self._zobrist_ready = True

    def _hash_board_full(self, board: Board, side_to_move: int) -> int:
        h = 0
        for z in range(4):
            for y in range(4):
                for x in range(4):
                    v = board[z][y][x]
                    if v == 1 or v == 2:
                        h ^= self._piece_key[z][y][x][v - 1]  # type: ignore
        if side_to_move == 2:
            h ^= self._stm_key
        return h

    @staticmethod
    def _mulberry32(x: int) -> int:
        x = (x + 0x6D2B79F5) & 0xFFFFFFFF
        t = x
        t = (t ^ (t >> 15)) * (t | 1)
        t ^= t + ((t ^ (t >> 7)) * (t | 61))
        return t ^ (t >> 14)

    def _tt_store(self, key: int, depth: int, flag: int, value: int, best_move: Optional[Tuple[int, int]], alpha0: int, beta0: int):
        if len(self.tt) >= self.tt_capacity:
            victim = self._mulberry32(key)
            idx = victim % (len(self.tt) or 1)
            k = next(iter(self.tt))
            for i, kk in enumerate(list(self.tt.keys())):
                if i == idx:
                    k = kk
                    break
            self.tt.pop(k, None)
        prev = self.tt.get(key)
        if (prev is None) or (depth >= prev[0]):
            # Корректная установка флага на основе ИСХОДНЫХ границ
            if value <= alpha0:
                flag = MyAI.TT_UPPER
            elif value >= beta0:
                flag = MyAI.TT_LOWER
            else:
                flag = MyAI.TT_EXACT
            self.tt[key] = (depth, flag, value, best_move)

    def _tt_probe(self, key: int):
        return self.tt.get(key, None)

    # ---------- Безопасные помощники ----------

    def _first_legal_move(self, board: Board) -> Tuple[int, int]:
        order = [
            (1, 1), (2, 2), (1, 2), (2, 1),
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            (0, 0), (3, 3), (0, 3), (3, 0),
        ]
        for x, y in order:
            if drop_z(board, x, y) is not None:
                return (x, y)
        for (x, y) in valid_moves(board):
            return (x, y)
        return (0, 0)

    def _validate_move(self, board: Board, x: int, y: int) -> Tuple[int, int]:
        if drop_z(board, x, y) is not None:
            return (x, y)
        return self._first_legal_move(board)

    def get_winning_lines(self):
        return LINES

    # ---------- Примитивы ----------

    def _immediate_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
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

    def _creates_fork(self, board: Board, player: int, x: int, y: int) -> bool:
        z = drop_z(board, x, y)
        if z is None:
            return False
        board[z][y][x] = player
        opp = 3 - player
        if self._immediate_win(board, opp) is not None:
            board[z][y][x] = 0
            return False
        # посчитаем количество разных немедленных побед после нашего хода
        wins = 0
        seen_cols = set()
        for (cx, cy) in valid_moves(board):
            cz = drop_z(board, cx, cy)
            if cz is None:
                continue
            board[cz][cy][cx] = player
            if winner(board) == player and (cx, cy) not in seen_cols:
                wins += 1
                seen_cols.add((cx, cy))
            board[cz][cy][cx] = 0
            if wins >= 2:
                break
        board[z][y][x] = 0
        return wins >= 2

    # ---------- Killer moves ----------

    def _push_killer(self, depth_idx: int, mv: Tuple[int, int]):
        if depth_idx < 0 or depth_idx >= len(self.killers):
            return
        arr = self.killers[depth_idx]
        if arr[0] != mv:
            arr[1] = arr[0]
            arr[0] = mv

    # ---------- Порядок ходов ----------

    def _order_moves(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        tt_move: Optional[Tuple[int, int]],
        depth_idx: int,
    ) -> List[Tuple[int, int]]:
        """Win-first → simple-Block-first → PV → killers → центр."""
        opp = 3 - player
        base = list(candidates)
        if not base:
            return []

        def center_key(m):
            return (abs(m[0] - 1.5) + abs(m[1] - 1.5))

        win_moves: List[Tuple[int, int]] = []
        block_moves: List[Tuple[int, int]] = []
        others: List[Tuple[int, int]] = []

        for m in base:
            x, y = m
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            if winner(board) == player:
                win_moves.append(m)
            else:
                # simple block: если соперник имел немедленный выигрыш, а теперь нет — значит блок
                had = self._immediate_win(board, opp)
                board[z][y][x] = 0
                if had is None:
                    # соперник всё равно не выигрывал немедленно — это не блок; пойдёт в others
                    others.append(m)
                else:
                    # после снятия хода проверим, был ли немедленный выигрыш до нашего хода
                    # (дешёво: просто проверим на исходной доске)
                    if self._immediate_win(board, opp) is not None:
                        block_moves.append(m)
                    else:
                        others.append(m)
                continue
            board[z][y][x] = 0

        killers_here = self.killers[depth_idx] if 0 <= depth_idx < len(self.killers) else [None, None]
        seen = set()
        ordered: List[Tuple[int, int]] = []

        for m in win_moves:
            if m not in seen:
                ordered.append(m); seen.add(m)

        for m in block_moves:
            if m not in seen:
                ordered.append(m); seen.add(m)

        if tt_move and (tt_move in base) and (tt_move not in seen):
            ordered.append(tt_move); seen.add(tt_move)

        for km in killers_here:
            if km and (km in base) and (km not in seen):
                ordered.append(km); seen.add(km)

        rest = [m for m in base if m not in seen]
        rest.sort(key=center_key)
        ordered.extend(rest)
        return ordered

    # ---------- Alpha-Beta + PVS + TT ----------

    def _alpha_beta_best_depth(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        depth: int,
        tg: "_TimeGuard",
        alpha_init: int = -10**9,
        beta_init: int = 10**9,
    ) -> Tuple[int, int, int]:
        """Возвращает (best_x, best_y, best_score) на заданной глубине."""
        try:
            opp = 3 - player
            if not candidates:
                # на всякий случай: вернём первый валидный
                for m in valid_moves(board):
                    return m[0], m[1], eval_board(board, player)
                return 0, 0, eval_board(board, player)

            root_key = self._hash_board_full(board, player)
            tt_entry = self._tt_probe(root_key)
            tt_move = tt_entry[3] if tt_entry is not None else None

            ordered = self._order_moves(board, player, candidates, tt_move, depth_idx=0)
            if not ordered:
                ordered = list(candidates)

            best = ordered[0]
            bestv = -10**9

            def ab(pl: int, d: int, a: int, b: int, key: int, depth_idx: int, pv_node: bool) -> int:
                if tg.should_stop():
                    return eval_board(board, player)

                w = winner(board)
                if w == player:
                    return 10_000 - max(0, d)
                if w == opp:
                    return -10_000 + max(0, d)

                if d == 0 or board_full(board):
                    # микро threat extension на горизонте
                    if d == 0 and (
                        self._immediate_win(board, player) is not None or
                        self._immediate_win(board, opp) is not None
                    ):
                        d = 1
                    else:
                        return eval_board(board, player)

                # TT
                entry = self._tt_probe(key)
                if entry is not None:
                    edepth, eflag, evalue, _emv = entry
                    if edepth >= d:
                        if eflag == MyAI.TT_EXACT:
                            return evalue
                        elif eflag == MyAI.TT_LOWER:
                            a = max(a, evalue)
                        elif eflag == MyAI.TT_UPPER:
                            b = min(b, evalue)
                        if a >= b:
                            return evalue

                local_tt_move = entry[3] if entry is not None else None
                moves = list(valid_moves(board))
                if not moves:
                    return eval_board(board, player)

                moves = self._order_moves(board, pl, moves, local_tt_move, depth_idx) or moves

                best_local_val = -10**9 if pl == player else 10**9
                best_local_move: Optional[Tuple[int, int]] = None

                first = True
                a0, b0 = a, b  # запомним ИСХОДНЫЕ границы для TT-флагов
                for (x, y) in moves:
                    if tg.should_stop():
                        break
                    z = drop_z(board, x, y)
                    if z is None:
                        continue
                    board[z][y][x] = pl
                    new_key = key ^ self._piece_key[z][y][x][pl - 1] ^ self._stm_key  # type: ignore

                    if first or pv_node:
                        val = ab(3 - pl, d - 1, a, b, new_key, depth_idx + 1, pv_node=True)
                        first = False
                    else:
                        val = ab(3 - pl, d - 1, a, a + 1, new_key, depth_idx + 1, pv_node=False)
                        if a < val < b:
                            val = ab(3 - pl, d - 1, a, b, new_key, depth_idx + 1, pv_node=True)

                    board[z][y][x] = 0

                    if pl == player:
                        if val > best_local_val:
                            best_local_val = val
                            best_local_move = (x, y)
                        if val > a:
                            a = val
                        if a >= b:
                            if best_local_move is not None:
                                self._push_killer(depth_idx, best_local_move)
                            break
                    else:
                        if val < best_local_val:
                            best_local_val = val
                            best_local_move = (x, y)
                        if val < b:
                            b = val
                        if a >= b:
                            if best_local_move is not None:
                                self._push_killer(depth_idx, best_local_move)
                            break

                # сохранить в TT с правильным флагом
                if not tg.should_stop():
                    self._tt_store(key, d, MyAI.TT_EXACT, best_local_val, best_local_move, a0, b0)

                return best_local_val

            a, b = alpha_init, beta_init
            first = True
            a0_root, b0_root = a, b  # исходные корневые границы

            for (x, y) in ordered:
                if tg.should_stop():
                    break
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                child_key = root_key ^ self._piece_key[z][y][x][player - 1] ^ self._stm_key  # type: ignore

                if first:
                    v = ab(3 - player, depth - 1, a, b, child_key, 1, pv_node=True)
                    first = False
                else:
                    v = ab(3 - player, depth - 1, a, a + 1, child_key, 1, pv_node=False)
                    if a < v < b:
                        v = ab(3 - player, depth - 1, a, b, child_key, 1, pv_node=True)

                board[z][y][x] = 0
                if v > bestv:
                    bestv, best = v, (x, y)
                if v > a:
                    a = v

            if not tg.should_stop():
                # корневую запись — тоже по исходным границам
                self._tt_store(root_key, depth, MyAI.TT_EXACT, bestv, best, a0_root, b0_root)

            return best[0], best[1], bestv

        except Exception:
            # в случае любой ошибки вернём безопасный ход
            for m in valid_moves(board):
                return m[0], m[1], 0
            return 0, 0, 0

    def _alpha_beta_best_id(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        max_depth: int,
        tg: "_TimeGuard",
    ) -> Tuple[int, int]:
        """Итеративное заглубление с аспирационными окнами и тотальным фоллбеком."""
        best_xy = candidates[0] if candidates else self._first_legal_move(board)
        score_guess = self._last_root_score if self._last_root_score is not None else 0
        self.killers = [[None, None] for _ in range(32)]

        for d in range(1, max_depth + 1):
            if tg.should_stop():
                break

            # узкое окно вокруг прошлого значения
            window = 100
            alpha = score_guess - window
            beta = score_guess + window

            x, y, val = self._alpha_beta_best_depth(board, player, candidates, d, tg, alpha_init=alpha, beta_init=beta)

            # если оценка вышла за рамки аспирации — пересчёт полным окном
            if not tg.should_stop() and (val <= alpha or val >= beta):
                x, y, val = self._alpha_beta_best_depth(board, player, candidates, d, tg)

            if not tg.should_stop():
                best_xy = (x, y)
                score_guess = val
                self._last_root_score = val

        return best_xy

    # ------------------------ Главная точка входа ------------------------

    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """
        Приоритет: win → block → own fork → block opp fork → safe → ID+PVS+TT → fallback.
        Все вычисления под защитой TimeGuard (CPU ~9.5s).
        """
        try:
            tg = self._TimeGuard(cpu_limit=9.5, wall_limit=29.0)

            # 0) стартовая книга: небольшой приоритет к центру/полуцентру
            try:
                if all(board[0][y][x] == 0 for x in range(4) for y in range(4)):
                    for pref in [(1, 1), (2, 2), (1, 2), (2, 1)]:
                        if tg.should_stop():
                            break
                        if drop_z(board, *pref) is not None:
                            return self._validate_move(board, *pref)
            except Exception:
                pass  # не критично

            # 1) мгновенная победа
            mv = self._immediate_win(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            opp = 3 - player

            # 2) мгновенный блок
            mv = self._immediate_win(board, opp)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 3) собственный форк
            try:
                for (x, y) in valid_moves(board):
                    if self._creates_fork(board, player, x, y):
                        return self._validate_move(board, x, y)
            except Exception:
                pass  # просто пропустим форки, если что-то пошло не так

            # 4) блок чужого форка (облегчённо)
            try:
                for (x, y) in valid_moves(board):
                    if self._creates_fork(board, opp, x, y):
                        if drop_z(board, x, y) is not None:
                            return self._validate_move(board, x, y)
                        break
            except Exception:
                pass

            # 5) кандидаты (safe). Если пусто — берём все валидные.
            cands = []
            try:
                cands = [m for m in valid_moves(board) if self._is_safe(board, player, m[0], m[1])]
            except Exception:
                cands = []
            if not cands:
                cands = list(valid_moves(board))
            if not cands:
                return (0, 0)

            # 6) Итеративное заглубление + PVS + TT
            x, y = self._alpha_beta_best_id(board, player, cands, self.depth, tg)
            return self._validate_move(board, x, y)

        except Exception:
            # Любая ошибка → гарантированный валидный ход
            return self._first_legal_move(board)
