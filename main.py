# main.py — 4x4x4 Connect Four (gravity) AI for contest runner
# stdlib only

from typing import List, Tuple, Optional, Dict
import time
import random

Board = List[List[List[int]]]
Coord = Tuple[int, int, int]
Move  = Tuple[int, int]

# ---------------------------------------------------------------------
# Lines (complete set for 4x4x4)
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
CENTER_PREF: List[Move] = [
    (1, 1), (2, 1), (1, 2), (2, 2),
    (0, 1), (3, 1), (1, 0), (1, 3),
    (2, 0), (2, 3), (0, 2), (3, 2),
    (0, 0), (3, 0), (0, 3), (3, 3),
]

# ---------------------------------------------------------------------
# Utils: tuple->list for immutable boards from runner
# ---------------------------------------------------------------------
def to_mutable_board(board):
    """Convert nested tuple board[z][y][x] to mutable lists, if needed."""
    if isinstance(board, list):
        return board
    return [ [ list(row) for row in layer ] for layer in board ]

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
# One-move tactics, safety and fork logic
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

def creates_fork(board: Board, player: int, x: int, y: int) -> bool:
    """After my move, do I have >=2 distinct wins-in-1? (and not give opp instant win)"""
    z = make_move(board, x, y, player)
    if z is None:
        return False
    opp = 3 - player
    # forbid suicidal fork that gives opp instant mate
    for (ox, oy) in list_valid_moves(board):
        if wins_if_play(board, opp, ox, oy):
            undo_move(board, x, y, z)
            return False
    # count my threats
    threats = 0
    for (mx, my) in list_valid_moves(board):
        if wins_if_play(board, player, mx, my):
            threats += 1
            if threats >= 2:
                undo_move(board, x, y, z)
                return True
    undo_move(board, x, y, z)
    return False

def find_own_fork(board: Board, player: int) -> Optional[Move]:
    for (x, y) in valid_moves(board):
        if creates_fork(board, player, x, y):
            return (x, y)
    return None

def find_block_opp_fork(board: Board, player: int) -> Optional[Move]:
    """Try to refute opponent's fork by: win now > own fork > direct block > interference."""
    opp = 3 - player
    # if I can win now — do it
    m = find_win_in_one(board, player)
    if m:
        return m
    # If I can create my fork now — often the best reply to opponent's fork
    mf = find_own_fork(board, player)
    if mf:
        return mf

    # Collect opp fork squares
    opp_forks = []
    for (x, y) in list_valid_moves(board):
        if creates_fork(board, opp, x, y):
            opp_forks.append((x, y))
    if not opp_forks:
        return None

    # Try direct blocks (play exactly there)
    for (x, y) in opp_forks:
        if is_safe_move(board, player, x, y):
            return (x, y)
    # Interference: pick a move that minimizes opp immediate wins next
    cand = list(valid_moves(board))
    if not cand:
        return None
    best, best_th = None, 10**9
    for (x, y) in cand:
        z = make_move(board, x, y, player)
        th = count_opponent_wins_next(board, player)
        undo_move(board, x, y, z)
        if th < best_th:
            best_th = th
            best = (x, y)
    return best

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
# AI with Iterative Deepening + Transposition Table
# ---------------------------------------------------------------------
TTEntry = Tuple[int, int, int, Optional[Move]]  # (depth, value, flag, best_move)
# flag: 0=EXACT, 1=LOWERBOUND, 2=UPPERBOUND

class AI:
    def __init__(self):
        self.soft_time_limit = 2.35  # keep below server CPU limit per move (~3s)
        self.start_ts = 0.0
        self.tt: Dict[Tuple[Tuple[int, ...], int], TTEntry] = {}
        self.last_pv_move: Optional[Move] = None

    # -------- time ----------
    def time_up(self) -> bool:
        return (time.time() - self.start_ts) > self.soft_time_limit

    # -------- public ----------
    def get_move(self, board, player: int, last_move) -> Tuple[int, int]:
        try:
            # важная защита от неизменяемых структур на боевом раннере
            board = to_mutable_board(board)

            self.start_ts = time.time()
            self.last_pv_move = None

            # Opening: if empty board, take center-ish
            if self._is_empty(board):
                for m in [(1,1),(2,2),(1,2),(2,1)]:
                    if drop_height(board, *m) is not None:
                        return m

            # Immediate tactics
            m = find_win_in_one(board, player)
            if m:
                return m
            opp = 3 - player
            m = find_win_in_one(board, opp)
            if m:
                return m

            # Forks
            m = find_own_fork(board, player)
            if m:
                return m
            m = find_block_opp_fork(board, player)
            if m:
                return m

            # Safe candidates first
            safe = [(x, y) for (x, y) in valid_moves(board) if is_safe_move(board, player, x, y)]
            candidates = safe if safe else list(valid_moves(board))
            if not candidates:
                return (0, 0)

            # Iterative deepening + TT
            best_move = candidates[0]
            best_score = -10**9
            order = self._order_moves(board, player, candidates)
            depth = 2
            while depth <= 8:
                if self.time_up():
                    break
                mv, sc = self._search_root(board, player, order, depth)
                if mv is not None:
                    best_move, best_score = mv, sc
                    self.last_pv_move = mv
                    order = self._order_moves(board, player, candidates, pv=mv)
                depth += 1

            return best_move

        except Exception:
            # абсолютный фолбек — чтобы не было 異常終了
            for y in range(4):
                for x in range(4):
                    if drop_height(board, x, y) is not None:
                        return (x, y)
            return (0, 0)

    # -------- helpers ----------
    def _is_empty(self, board: Board) -> bool:
        for z in range(4):
            for y in range(4):
                for x in range(4):
                    if board[z][y][x] != 0:
                        return False
        return True

    def _order_moves(self, board: Board, player: int, moves: List[Move], pv: Optional[Move]=None) -> List[Move]:
        ordered = moves[:]
        # PV to front if provided
        if pv and pv in ordered:
            ordered.remove(pv)
            ordered = [pv] + ordered
        # prefer safe + center
        def key(m: Move):
            safe = 0 if is_safe_move(board, player, m[0], m[1]) else 1
            center_rank = CENTER_PREF.index(m) if m in CENTER_PREF else 99
            return (safe, center_rank)
        ordered.sort(key=key)
        return ordered

    # -------- search ----------
    def _search_root(self, board: Board, player: int, moves: List[Move], depth: int):
        alpha = -10**9
        beta  =  10**9
        best_move = None
        best_score = -10**9

        for (x, y) in moves:
            if self.time_up():
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
                best_move  = (x, y)
            if best_score > alpha:
                alpha = best_score

        return best_move, best_score

    def _alphabeta(self, board: Board, side: int, depth: int, alpha: int, beta: int, me: int) -> int:
        if self.time_up():
            return evaluate(board, me)

        w = winner(board)
        if w != 0:
            return 20000 if w == me else -20000
        if depth <= 0:
            return evaluate(board, me)

        key = (serialize(board), side)
        if key in self.tt:
            tt_depth, tt_val, tt_flag, tt_move = self.tt[key]
            if tt_depth >= depth:
                if tt_flag == 0:       # EXACT
                    return tt_val
                elif tt_flag == 1:     # LOWERBOUND
                    alpha = max(alpha, tt_val)
                elif tt_flag == 2:     # UPPERBOUND
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val
        else:
            tt_move = None

        orig_alpha, orig_beta = alpha, beta

        best = -10**9
        best_move = None
        moves = list(valid_moves(board))
        # PV/TT move ordering
        if tt_move and tt_move in moves:
            moves.remove(tt_move)
            moves = [tt_move] + moves
        moves = self._order_moves(board, side, moves)

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
                best_move = (x, y)
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        # store to TT
        if best <= -10**9 // 2:
            val = evaluate(board, me)
        else:
            val = best
        if val <= orig_alpha:
            tt_flag = 2  # UPPERBOUND
        elif val >= orig_beta:
            tt_flag = 1  # LOWERBOUND
        else:
            tt_flag = 0  # EXACT
        self.tt[key] = (depth, val, tt_flag, best_move)
        return val
