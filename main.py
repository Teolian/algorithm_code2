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
    """
    Улучшения:
      • TimeGuard (CPU + soft-wall)
      • Итеративное заглубление
      • Zobrist-хэш + маленькая транспозиционная таблица (TT) с depth-aware записями
      • Move ordering: PV-move из TT → killer-moves → центр-сначала
    """
    # TT-флаги
    TT_EXACT = 0
    TT_LOWER = 1
    TT_UPPER = -1

    def __init__(self, depth: int = 3, tt_capacity: int = 200_000):
        # depth — максимальная глубина для итеративного заглубления (1..depth)
        self.depth = depth

        # --- Zobrist ---
        self._zobrist_ready = False
        self._piece_key = None  # type: ignore
        self._stm_key = 0
        self._zobrist_init()

        # --- маленькая транспозиционная таблица ---
        self.tt: Dict[int, Tuple[int, int, int, Optional[Tuple[int, int]]]] = {}
        self.tt_capacity = tt_capacity

        # killer moves (на глубины 0..31 храним по 2 убийцы)
        self.killers: List[List[Optional[Tuple[int, int]]]] = [[None, None] for _ in range(32)]

    # ---------- Лимитер времени (CPU + мягкий по wall) ----------

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
        # ключи для (z,y,x, piece) где piece in {1,2} → индекс 0/1
        self._piece_key = [[[[
            rnd.getrandbits(64) for _ in range(2)
        ] for _ in range(4)] for _ in range(4)] for _ in range(4)]  # type: ignore
        self._stm_key = rnd.getrandbits(64)
        self._zobrist_ready = True

    def _hash_board_full(self, board: Board, side_to_move: int) -> int:
        """Полный Zobrist-хэш позиции."""
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
        # маленький микс-рандом для вытеснения из TT (дёшево и стабильно)
        x = (x + 0x6D2B79F5) & 0xFFFFFFFF
        t = x
        t = (t ^ (t >> 15)) * (t | 1)
        t ^= t + ((t ^ (t >> 7)) * (t | 61))
        return t ^ (t >> 14)

    def _tt_store(self, key: int, depth: int, flag: int, value: int, best_move: Optional[Tuple[int, int]]):
        if len(self.tt) >= self.tt_capacity:
            # простое вытеснение: псевдослучайный ключ
            victim = self._mulberry32(key)  # 32-бит
            # преобразуем в индекс по модулю размера, затем получаем произвольный ключ через итерацию
            idx = victim % (len(self.tt) or 1)
            # удалить любой элемент на позиции idx (O(n), но размер небольшой)
            k = next(iter(self.tt))
            for i, kk in enumerate(self.tt.keys()):
                if i == idx:
                    k = kk
                    break
            self.tt.pop(k, None)
        self.tt[key] = (depth, flag, value, best_move)

    def _tt_probe(self, key: int):
        return self.tt.get(key, None)

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

    # ---------- Примитивы (так же, как раньше) ----------

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

    def _my_immediate_wins_in_position(self, board: Board, player: int) -> List[Tuple[int, int]]:
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
        z = drop_z(board, x, y)
        if z is None:
            return False
        board[z][y][x] = player

        opp = 3 - player
        opp_win = self._immediate_win(board, opp)
        if opp_win is not None:
            board[z][y][x] = 0
            return False

        my_wins = self._my_immediate_wins_in_position(board, player)
        board[z][y][x] = 0

        if len(my_wins) < 2:
            return False
        cols = {(cx, cy) for (cx, cy) in my_wins}
        return len(cols) >= 2

    def _find_own_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, player, x, y):
                return (x, y)
        return None

    def _find_block_opp_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        opp = 3 - player
        opp_forks: List[Tuple[int, int]] = []
        for (x, y) in valid_moves(board):
            if self._creates_fork(board, opp, x, y):
                opp_forks.append((x, y))
        if not opp_forks:
            return None
        for (x, y) in opp_forks:
            z = drop_z(board, x, y)
            if z is not None:
                return (x, y)
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
        return opp_forks[0]

    def _is_safe(self, board: Board, player: int, x: int, y: int) -> bool:
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

    # ---------- Killer moves helpers ----------

    def _push_killer(self, depth_idx: int, mv: Tuple[int, int]):
        arr = self.killers[depth_idx]
        if arr[0] != mv:
            arr[1] = arr[0]
            arr[0] = mv

    # ---------- Alpha-Beta + TT + TimeGuard ----------

    def _order_moves(
        self,
        candidates: List[Tuple[int, int]],
        tt_move: Optional[Tuple[int, int]],
        depth_idx: int,
    ) -> List[Tuple[int, int]]:
        # Начинаем с PV-move (из TT), затем killer-moves для этой глубины,
        # потом оставшиеся по центр-сначала.
        killers_here = [mv for mv in self.killers[depth_idx] if mv is not None]
        base = list(candidates)

        def center_key(m):
            return (abs(m[0] - 1.5) + abs(m[1] - 1.5))

        seen = set()
        ordered: List[Tuple[int, int]] = []
        if tt_move and tt_move in base:
            ordered.append(tt_move)
            seen.add(tt_move)
        for km in killers_here:
            if km in base and km not in seen:
                ordered.append(km)
                seen.add(km)
        rest = [m for m in base if m not in seen]
        rest.sort(key=center_key)
        ordered.extend(rest)
        return ordered

    def _alpha_beta_best_depth(
        self,
        board: Board,
        player: int,
        candidates: List[Tuple[int, int]],
        depth: int,
        tg: "_TimeGuard",
    ) -> Tuple[int, int]:
        opp = 3 - player

        # текущий корневой хэш
        root_key = self._hash_board_full(board, player)

        # возможный PV-move из TT (лучший предыдущий на этой позиции)
        tt_entry = self._tt_probe(root_key)
        tt_move = tt_entry[3] if tt_entry is not None else None

        best = candidates[0]
        bestv = -10**9

        ordered = self._order_moves(candidates, tt_move, depth_idx=0)

        def ab(pl: int, d: int, a: int, b: int, key: int, depth_idx: int) -> int:
            if tg.should_stop():
                return eval_board(board, player)

            w = winner(board)
            if w == player:
                return 10_000 - max(0, d)
            if w == opp:
                return -10_000 + max(0, d)
            if d == 0 or board_full(board):
                return eval_board(board, player)

            # TT probe
            entry = self._tt_probe(key)
            if entry is not None:
                edepth, eflag, evalue, _emove = entry
                if edepth >= d:
                    if eflag == MyAI.TT_EXACT:
                        return evalue
                    elif eflag == MyAI.TT_LOWER:
                        a = max(a, evalue)
                    elif eflag == MyAI.TT_UPPER:
                        b = min(b, evalue)
                    if a >= b:
                        return evalue

            # упорядочим ходы с учётом TT/killers
            local_tt_move = entry[3] if entry is not None else None
            moves = list(valid_moves(board))
            if not moves:
                return eval_board(board, player)  # ничья/пат

            moves = self._order_moves(moves, local_tt_move, depth_idx)

            best_local_val = -10**9 if pl == player else 10**9
            best_local_move: Optional[Tuple[int, int]] = None
            cut = False

            for (x, y) in moves:
                if tg.should_stop():
                    break
                z = drop_z(board, x, y)
                if z is None:
                    continue

                # применяем ход
                board[z][y][x] = pl

                # инкрементальный хэш: XOR с ключом фигуры и смена стороны
                new_key = key ^ self._piece_key[z][y][x][pl - 1] ^ self._stm_key  # type: ignore

                if pl == player:
                    val = ab(3 - pl, d - 1, a, b, new_key, depth_idx + 1)
                    board[z][y][x] = 0
                    if val > best_local_val:
                        best_local_val = val
                        best_local_move = (x, y)
                    a = max(a, val)
                    if a >= b:
                        # beta-cutoff → killer
                        if best_local_move is not None:
                            self._push_killer(depth_idx, best_local_move)
                        cut = True
                        break
                else:
                    val = ab(3 - pl, d - 1, a, b, new_key, depth_idx + 1)
                    board[z][y][x] = 0
                    if val < best_local_val:
                        best_local_val = val
                        best_local_move = (x, y)
                    b = min(b, val)
                    if a >= b:
                        # beta-cutoff на ветке соперника тоже даёт killer (наш последний удачный ход)
                        if best_local_move is not None:
                            self._push_killer(depth_idx, best_local_move)
                        cut = True
                        break

            # сохранить в TT
            if not tg.should_stop():
                flag = MyAI.TT_EXACT
                if best_local_val <= a:
                    # верхняя граница (в классике: если значение <= alpha до обновления alpha)
                    flag = MyAI.TT_UPPER
                if best_local_val >= b:
                    # нижняя граница (если значение >= beta)
                    flag = MyAI.TT_LOWER
                self._tt_store(key, d, flag, best_local_val, best_local_move)

            return best_local_val

        for (x, y) in ordered:
            if tg.should_stop():
                break
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            child_key = root_key ^ self._piece_key[z][y][x][player - 1] ^ self._stm_key  # type: ignore
            v = ab(opp, depth - 1, -10**9, 10**9, child_key, 1)
            board[z][y][x] = 0
            if v > bestv:
                bestv, best = v, (x, y)

        # Корневую запись тоже можно положить (для PV-move на следующий шаг)
        if not tg.should_stop():
            self._tt_store(root_key, depth, MyAI.TT_EXACT, bestv, best)

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
        # сбрасываем killers для свежего поиска
        self.killers = [[None, None] for _ in range(32)]
        # небольшой прогрев TT корнем
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
        Приоритет: win → block → собственный fork → блок opp-fork → safe → alpha-beta(ID+TT) → fallback.
        Все вычисления под защитой TimeGuard (CPU ~9.5s).
        """
        try:
            tg = self._TimeGuard(cpu_limit=9.5, wall_limit=29.0)

            # 0) стартовая книга: небольшой приоритет к центру/полуцентру
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

            # 3) собственный форк
            mv = self._find_own_fork(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 4) блок чужого форка
            mv = self._find_block_opp_fork(board, player)
            if mv is not None:
                return self._validate_move(board, mv[0], mv[1])

            # 5) кандидаты (safe). Если пусто — берём все валидные.
            cands = [m for m in valid_moves(board) if self._is_safe(board, player, m[0], m[1])]
            if not cands:
                cands = list(valid_moves(board))
            if not cands:
                return (0, 0)

            # 6) Итеративное заглубление + TT
            x, y = self._alpha_beta_best_id(board, player, cands, self.depth, tg)
            return self._validate_move(board, x, y)

        except Exception:
            return self._first_legal_move(board)
