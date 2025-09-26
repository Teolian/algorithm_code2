# main.py — 4x4x4 Connect Four AI (gravity) for local arena
# stdlib only

from typing import List, Tuple, Optional, Dict
import time
import random

Board = List[List[List[int]]]
Coord = Tuple[int, int, int]
Move = Tuple[int, int]

# ---------------------------------------------------------------------
# Winning lines (complete set for 4x4x4)
# ---------------------------------------------------------------------
def _generate_winning_lines() -> List[List[Coord]]:
    L: List[List[Coord]] = []
    rng = range(4)
    # Along axes
    for z in rng:
        for y in rng:
            L.append([(x, y, z) for x in rng])  # X
    for z in rng:
        for x in rng:
            L.append([(x, y, z) for y in rng])  # Y
    for y in rng:
        for x in rng:
            L.append([(x, y, z) for z in rng])  # Z
    # Diagonals in XY planes (fixed z)
    for z in rng:
        L.append([(i, i, z) for i in rng])
        L.append([(i, 3 - i, z) for i in rng])
    # Diagonals in XZ planes (fixed y)
    for y in rng:
        L.append([(i, y, i) for i in rng])
        L.append([(i, y, 3 - i) for i in rng])
    # Diagonals in YZ planes (fixed x)
    for x in rng:
        L.append([(x, i, i) for i in rng])
        L.append([(x, i, 3 - i) for i in rng])
    # Space diagonals
    L.append([(i, i, i) for i in rng])
    L.append([(i, i, 3 - i) for i in rng])
    L.append([(i, 3 - i, i) for i in rng])
    L.append([(3 - i, i, i) for i in rng])
    return L

LINES = _generate_winning_lines()
CENTER_PREF = [
    (1, 1), (2, 1), (1, 2), (2, 2),
    (0, 1), (3, 1), (1, 0), (1, 3),
    (2, 0), (2, 3), (0, 2), (3, 2),
    (0, 0), (3, 0), (0, 3), (3, 3),
]

# ---------------------------------------------------------------------
# Board helpers (gravity: board[z][y][x], z grows upward)
# ---------------------------------------------------------------------
def drop_height(board: Board, x: int, y: int) -> Optional[int]:
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None

def is_col_full(board: Board, x: int, y: int) -> bool:
    return drop_height(board, x, y) is None

def make_move(board: Board, x: int, y: int, player: int) -> Optional[int]:
    z = drop_height(board, x, y)
    if z is None:
        return None
    board[z][y][x] = player
    return z

def undo_move(board: Board, x: int, y: int, z: int) -> None:
    board[z][y][x] = 0

def valid_moves(board: Board):
    for (x, y) in CENTER_PREF:  # center-first ordering
        if not is_col_full(board, x, y):
            yield (x, y)

def list_valid_moves(board: Board):
    for y in range(4):
        for x in range(4):
            if not is_col_full(board, x, y):
                yield (x, y)

def winner(board: Board) -> int:
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0

def serialize(board: Board) -> Tuple[int, ...]:
    t = []
    for z in range(4):
        for y in range(4):
            for x in range(4):
                t.append(board[z][y][x])
    return tuple(t)

# ---------------------------------------------------------------------
# One-move tactics & safety
# ---------------------------------------------------------------------
def wins_if_play(board: Board, player: int, x: int, y: int) -> bool:
    z = make_move(board, x, y, player)
    if z is None:
        return False
    w = winner(board)
    undo_move(board, x, y, z)
    return w == player

def find_win_in_one(board: Board, player: int) -> Optional[Move]:
    for (x, y) in list_valid_moves(board):
        if wins_if_play(board, player, x, y):
            return (x, y)
    return None

def count_opponent_wins_next(board: Board, player: int) -> int:
    opp = 3 - player
    c = 0
    for (x, y) in list_valid_moves(board):
        if wins_if_play(board, opp, x, y):
            c += 1
    return c

def is_safe_move(board: Board, player: int, x: int, y: int) -> bool:
    z = make_move(board, x, y, player)
    if z is None:
        return False
    opp = 3 - player
    ok = True
    for (ox, oy) in list_valid_moves(board):
        if wins_if_play(board, opp, ox, oy):
            ok = False
            break
    undo_move(board, x, y, z)
    return ok

# ---------------------------------------------------------------------
# Evaluation (simple but strong for 4x4x4)
# ---------------------------------------------------------------------
def line_score(vals: List[int], me: int) -> int:
    opp = 3 - me
    c_me = vals.count(me)
    c_opp = vals.count(opp)
    c_emp = vals.count(0)
    if c_me and c_opp:
        return 0
    if c_me == 4:
        return 10_000
    if c_opp == 4:
        return -10_000
    if c_me > 0:
        return (3 ** c_me) * (1 if c_emp else 0)
    if c_opp > 0:
        return -(3 ** c_opp) * (1 if c_emp else 0)
    return 0

def evaluate(board: Board, me: int) -> int:
    sc = 0
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        sc += line_score(vals, me)
    # slight center preference (open columns only)
    for (x, y) in ((1, 1), (2, 1), (1, 2), (2, 2)):
        if drop_height(board, x, y) is not None:
            sc += 1
    return sc

# ---------------------------------------------------------------------
# Alpha-beta with iterative deepening + TT
# ---------------------------------------------------------------------
class AI:
    def __init__(self):
        self.time_limit_s = 2.25  # stay below 3.0s per-move arena limit
        self.start_ts = 0.0
        self.tt: Dict[Tuple[Tuple[int, ...], int, int], int] = {}

    def get_move(self, board: Board, player: int, last_move) -> Tuple[int, int]:
        self.start_ts = time.time()

        # 0) Win in 1
        m = find_win_in_one(board, player)
        if m:
            return m

        # 1) Block opponent's win in 1
        opp = 3 - player
        m = find_win_in_one(board, opp)
        if m:
            return m

        # 2) Safe moves only (do not give opp a win next)
        safe = [(x, y) for (x, y) in valid_moves(board) if is_safe_move(board, player, x, y)]
        if safe:
            # pick move minimizing opponent immediate wins after our move
            best = None
            best_threats = 10**9
            random.shuffle(safe)
            for (x, y) in safe:
                z = make_move(board, x, y, player)
                th = count_opponent_wins_next(board, player)
                undo_move(board, x, y, z)
                if th < best_threats:
                    best_threats = th
                    best = (x, y)
                    if th == 0:
                        break
            if best:
                # try deeper search as tie-breaker within time
                move = self._iterative_search(board, player, first_choice=best, candidates=safe)
                if move:
                    return move
                return best

        # 3) If everything is dangerous, use search to pick the least bad
        candidates = list(valid_moves(board))
        if not candidates:
            return (0, 0)

        move = self._iterative_search(board, player, first_choice=None, candidates=candidates)
        if move:
            return move

        # Fallback: pick a valid move
        return candidates[0]

    # ---------------- search internals ----------------
    def _iterative_search(self, board: Board, player: int,
                          first_choice: Optional[Move],
                          candidates: List[Move]) -> Optional[Move]:
        # order candidates (center-first), maybe prioritize provided first_choice
        ordered = candidates[:]
        if first_choice and first_choice in ordered:
            ordered.remove(first_choice)
            ordered = [first_choice] + ordered

        best_move = None
        best_score = -10**9
        depth = 2
        while True:
            if time.time() - self.start_ts > self.time_limit_s:
                break
            mv, sc = self._search_depth(board, player, ordered, depth)
            if mv is not None:
                best_move, best_score = mv, sc
                # bring best to front for next iteration
                ordered.sort(key=lambda m: 0 if m == best_move else 1)
            depth += 1
            if depth > 6:  # enough for 4x4x4
                break
        return best_move

    def _search_depth(self, board: Board, player: int,
                      moves: List[Move], depth: int):
        best_move = None
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
                score = -self._alphabeta(board, 3 - player, depth - 1, -beta, -alpha, player)
            undo_move(board, x, y, z)

            if score > best_score:
                best_score = score
                best_move = (x, y)
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        return best_move, best_score

    def _alphabeta(self, board: Board, side: int, depth: int,
                   alpha: int, beta: int, me: int) -> int:
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
        moves = list(valid_moves(board))
        # prefer safe moves for the side to move
        moves.sort(key=lambda m: (not is_safe_move(board, side, m[0], m[1]),
                                  CENTER_PREF.index(m)))

        for (x, y) in moves:
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
