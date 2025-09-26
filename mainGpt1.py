# main.py
# 4x4x4 Connect Four with gravity — Alpha-Beta + эвристика + защита от «один в ход»
from typing import List, Tuple, Optional, Dict
import time
import math
import random

try:
    # боевое окружение
    from framework import Alg3D, Board
except Exception:
    # локальная отладка (python local_driver.py)
    from local_driver import Alg3D, Board  # type: ignore


Coord = Tuple[int, int, int]
Move = Tuple[int, int]  # (x, y)


def _generate_winning_lines() -> List[List[Coord]]:
    """Полный набор из 76 выигрышных линий для 4x4×4."""
    L: List[List[Coord]] = []
    rng = range(4)

    # 1) По осям
    for z in rng:
        for y in rng:
            L.append([(x, y, z) for x in rng])  # по X
    for z in rng:
        for x in rng:
            L.append([(x, y, z) for y in rng])  # по Y
    for y in rng:
        for x in rng:
            L.append([(x, y, z) for z in rng])  # по Z

    # 2) Диагонали в слоях XY (фикс. z)
    for z in rng:
        L.append([(i, i, z) for i in rng])
        L.append([(i, 3 - i, z) for i in rng])

    # 3) Диагонали в сечениях XZ (фикс. y)
    for y in rng:
        L.append([(i, y, i) for i in rng])
        L.append([(i, y, 3 - i) for i in rng])

    # 4) Диагонали в сечениях YZ (фикс. x)
    for x in rng:
        L.append([(x, i, i) for i in rng])
        L.append([(x, i, 3 - i) for i in rng])

    # 5) Главные пространственные диагонали
    L.append([(i, i, i) for i in rng])
    L.append([(i, i, 3 - i) for i in rng])
    L.append([(i, 3 - i, i) for i in rng])
    L.append([(3 - i, i, i) for i in rng])

    return L


LINES = _generate_winning_lines()
CENTER_PREF = [(1, 1), (2, 1), (1, 2), (2, 2), (0, 1), (3, 1), (1, 0), (1, 3),
               (2, 0), (2, 3), (0, 2), (3, 2), (0, 0), (3, 0), (0, 3), (3, 3)]


def is_column_full(board: Board, x: int, y: int) -> bool:
    for z in range(4):
        if board[z][y][x] == 0:
            return False
    return True


def drop_height(board: Board, x: int, y: int) -> Optional[int]:
    """Возвращает z, куда упадёт фишка (или None, если колонка заполнена)."""
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None


def make_move(board: Board, x: int, y: int, player: int) -> Optional[int]:
    """Ставит камень player в (x, y) с гравитацией. Возвращает z либо None, если нельзя."""
    z = drop_height(board, x, y)
    if z is None:
        return None
    board[z][y][x] = player
    return z


def undo_move(board: Board, x: int, y: int, z: int) -> None:
    board[z][y][x] = 0


def valid_moves(board: Board):
    """Все (x, y), где ещё есть свободное место по z."""
    for (x, y) in CENTER_PREF:  # центр сначала — лучшее упорядочивание
        if not is_column_full(board, x, y):
            yield (x, y)


def winner(board: Board) -> int:
    """0 — нет, 1/2 — победитель."""
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0


def serialize(board: Board) -> Tuple[int, ...]:
    """Плотная сериализация для Zobrist-like кэша (транспоз-таблицы)."""
    out = []
    for z in range(4):
        for y in range(4):
            for x in range(4):
                out.append(board[z][y][x])
    return tuple(out)


def line_score(vals: List[int], me: int) -> int:
    """Эвристика по строке из 4: экспоненциально за свои, сильно наказываем за чужие."""
    opp = 3 - me
    c_me = vals.count(me)
    c_opp = vals.count(opp)
    c_emp = vals.count(0)
    if c_me and c_opp:
        return 0  # смешанная линия бесполезна
    if c_me == 4:
        return 10_000
    if c_opp == 4:
        return -10_000
    # полу- и четвертки — экспоненциальные веса
    if c_me > 0:
        return (3 ** c_me) * (1 if c_emp else 0)
    if c_opp > 0:
        return -(3 ** c_opp) * (1 if c_emp else 0)
    return 0


def evaluate(board: Board, me: int) -> int:
    """Суммарная оценка по всем линиям + лёгкий центр-бонус."""
    sc = 0
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        sc += line_score(vals, me)
    # центровые колонки поощряем слегка
    for (x, y) in ((1, 1), (2, 1), (1, 2), (2, 2)):
        z = drop_height(board, x, y)
        if z is not None:
            sc += 1
    return sc


class MyAI(Alg3D):
    def __init__(self):
        self.time_limit_s = 2.25  # оставить запас от жесткого лимита CPU ~3s
        self.start_ts = 0.0
        self.tt: Dict[Tuple[Tuple[int, ...], int, int], int] = {}  # (pos, player, depth) -> score

    # ------------ публичный интерфейс ------------
    def get_move(self, board: Board, player: int, last_move) -> Tuple[int, int]:
        self.start_ts = time.time()

        # 1) быстрые выигрыши в один ход
        win = self._find_winning_move(board, player)
        if win is not None:
            return win

        # 2) обязательная защита от матов в 1 ход
        bl = self._block_opponent_threat(board, player)
        if bl is not None:
            return bl

        # 3) фильтр «безопасных» ходов (не допускают мата в 1 ответ)
        candidates = [m for m in valid_moves(board) if self._is_safe(board, player, *m)]
        if not candidates:
            candidates = list(valid_moves(board))
        if not candidates:
            return (0, 0)  # без вариантов — теоретически заполнено поле

        # 4) итеративное погружение alpha-beta с упорядочиванием кандидатов
        best = candidates[0]
        best_score = -10**9
        depth = 2
        random.shuffle(candidates)  # чтобы не быть предсказуемым на равных
        while True:
            if time.time() - self.start_ts > self.time_limit_s:
                break
            move, score = self._search_depth(board, player, candidates, depth)
            if move is not None:
                best, best_score = move, score
                # лёгкая переупорядочивка по последнему скорам
                candidates.sort(key=lambda m: 0 if m != best else -1)
            depth += 1
            if depth > 6:  # на 4×4×4 глубже редко нужно при грамотной эвристике
                break

        # 5) запасной план — валидный ход точно
        return self._validate_move(board, best[0], best[1])

    # ------------ поиск ------------
    def _search_depth(self, board: Board, player: int, moves: List[Move], depth: int):
        best_move: Optional[Move] = None
        best_score = -10**9
        alpha = -10**9
        beta = 10**9

        for (x, y) in moves:
            if time.time() - self.start_ts > self.time_limit_s:
                break
            z = make_move(board, x, y, player)
            if z is None:
                continue
            w = winner(board)
            if w == player:
                score = 20000 - (depth * 10)
            else:
                score = -self._alphabeta(board, 3 - player, depth - 1, alpha, beta, player)
            undo_move(board, x, y, z)

            if score > best_score:
                best_score = score
                best_move = (x, y)
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break

        return best_move, best_score

    def _alphabeta(self, board: Board, side: int, depth: int, alpha: int, beta: int, me: int) -> int:
        if time.time() - self.start_ts > self.time_limit_s:
            return evaluate(board, me)

        w = winner(board)
        if w != 0:
            return 20000 if w == me else -20000
        if depth <= 0:
            return evaluate(board, me)

        key = (serialize(board), side, depth)
        if key in self.tt:
            return self.tt[key]

        best = -10**9
        # упорядочивание: центр и безопасные сначала
        mv = list(valid_moves(board))
        mv.sort(key=lambda m: (not self._is_safe(board, side, m[0], m[1]), CENTER_PREF.index(m)))

        for (x, y) in mv:
            z = make_move(board, x, y, side)
            if z is None:
                continue
            w2 = winner(board)
            if w2 == side:
                score = 20000 - (depth * 10)
            else:
                score = -self._alphabeta(board, 3 - side, depth - 1, -beta, -alpha, me)
            undo_move(board, x, y, z)

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best == -10**9:
            best = evaluate(board, me)
        self.tt[key] = best
        return best

    # ------------ тактика «в один ход» ------------
    def _find_winning_move(self, board: Board, player: int) -> Optional[Move]:
        for (x, y) in valid_moves(board):
            z = make_move(board, x, y, player)
            if z is None:
                continue
            w = winner(board)
            undo_move(board, x, y, z)
            if w == player:
                return (x, y)
        return None

    def _block_opponent_threat(self, board: Board, player: int) -> Optional[Move]:
        opp = 3 - player
        for (x, y) in valid_moves(board):
            z = make_move(board, x, y, opp)
            if z is None:
                continue
            w = winner(board)
            undo_move(board, x, y, z)
            if w == opp:
                return (x, y)  # немедленно перекрыть
        return None

    def _is_safe(self, board: Board, player: int, x: int, y: int) -> bool:
        """Ход не отдаёт мат сопернику в 1 ответ."""
        z = make_move(board, x, y, player)
        if z is None:
            return False
        opp = 3 - player
        ok = True
        for (ox, oy) in valid_moves(board):
            oz = make_move(board, ox, oy, opp)
            if oz is None:
                continue
            if winner(board) == opp:
                ok = False
                undo_move(board, ox, oy, oz)
                break
            undo_move(board, ox, oy, oz)
        undo_move(board, x, y, z)
        return ok

    # ------------ утилиты безопасности ------------
    def _validate_move(self, board: Board, x: int, y: int) -> Move:
        # гарантируем валидность согласно правилам проверки
        z = drop_height(board, x, y)
        if z is not None:
            return (x, y)
        for (ax, ay) in valid_moves(board):
            return (ax, ay)
        return (0, 0)

# Экспортируемый класс
AI = MyAI