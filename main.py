
from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board  # type: ignore

# ======== geometry (76 lines) ========
def gen_lines():
    L = []
    for y in range(4):
        for z in range(4):
            L.append([(i,y,z) for i in range(4)])
    for x in range(4):
        for z in range(4):
            L.append([(x,i,z) for i in range(4)])
    for x in range(4):
        for y in range(4):
            L.append([(x,y,i) for i in range(4)])
    for z in range(4):
        L.append([(i,i,z) for i in range(4)])
        L.append([(i,3-i,z) for i in range(4)])
    for y in range(4):
        L.append([(i,y,i) for i in range(4)])
        L.append([(i,y,3-i) for i in range(4)])
    for x in range(4):
        L.append([(x,i,i) for i in range(4)])
        L.append([(x,i,3-i) for i in range(4)])
    L.append([(i,i,i) for i in range(4)])
    L.append([(i,i,3-i) for i in range(4)])
    L.append([(i,3-i,i) for i in range(4)])
    L.append([(3-i,i,i) for i in range(4)])
    return L

LINES = gen_lines()

def drop_z(board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
    if not (0<=x<4 and 0<=y<4): return None
    for z in range(4):
        if board[z][y][x]==0: return z
    return None

def board_full(board: List[List[List[int]]]) -> bool:
    return all(board[3][y][x]!=0 for x in range(4) for y in range(4))

def winner(board: List[List[List[int]]]) -> int:
    for line in LINES:
        vals = [board[z][y][x] for (x,y,z) in line]
        if vals.count(1)==4: return 1
        if vals.count(2)==4: return 2
    return 0

def valid_moves(board):
    for x in range(4):
        for y in range(4):
            if board[3][y][x]==0:
                yield (x,y)

# ======== evaluation ========
def eval_board(board: List[List[List[int]]], me: int) -> int:
    opp = 3-me
    W = winner(board)
    if W==me: return 10_000
    if W==opp: return -10_000
    score = 0
    # center + height
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p==0: continue
                cent = 3 - int(abs(x-1.5)+abs(y-1.5))
                h = z
                score += (cent+h) if p==me else -(cent+h)
    # line potentials, stronger weights
    for line in LINES:
        c=[0,0,0]
        for (x,y,z) in line:
            c[board[z][y][x]]+=1
        if c[1] and c[2]: 
            continue
        mine = c[me]; theirs = c[opp]
        if theirs==0:
            if mine==3: score += 260
            elif mine==2: score += 42
            elif mine==1: score += 5
        elif mine==0:
            if theirs==3: score -= 260
            elif theirs==2: score -= 42
            elif theirs==1: score -= 5
    return score

# ======== AI ========
class MyAI(Alg3D):
    def __init__(self):
        # iterative-deepening & pruning limits (под лимиты сервера можно ослабить/усилить)
        self.time_budget_ms = 1800
        self.node_budget = 60000
        # zobrist
        import random
        random.seed(424242)
        self.zkeys = [[[[random.getrandbits(64) for _ in range(3)] for _ in range(4)] for _ in range(4)] for _ in range(4)]
        self.TT = {}
        self.killers = {}  # (depth) -> list of killer moves

    # -------- safety helpers --------
    def _first_legal_move(self, board: List[List[List[int]]]):
        order = [(1,1),(2,2),(1,2),(2,1),
                 (0,1),(1,0),(3,2),(2,3),
                 (0,2),(2,0),(3,1),(1,3),
                 (0,0),(3,3),(0,3),(3,0)]
        for x,y in order:
            if drop_z(board,x,y) is not None: return (x,y)
        for x,y in valid_moves(board): return (x,y)
        return (0,0)
    def _validate_move(self, board, x, y):
        if not (0<=x<4 and 0<=y<4): return self._first_legal_move(board)
        if drop_z(board,x,y) is None: return self._first_legal_move(board)
        return (x,y)

    # -------- tactics --------
    def _immediate_win(self, board, player):
        for (x,y) in valid_moves(board):
            z = drop_z(board,x,y)
            if z is None: continue
            board[z][y][x]=player
            if winner(board)==player:
                board[z][y][x]=0; return (x,y)
            board[z][y][x]=0
        return None
    def _my_immediate_wins_in_position(self, board, player):
        wins=[]
        for (x,y) in valid_moves(board):
            z=drop_z(board,x,y)
            if z is None: continue
            board[z][y][x]=player
            if winner(board)==player: wins.append((x,y))
            board[z][y][x]=0
        return wins
    def _creates_fork(self, board, player, x, y):
        z=drop_z(board,x,y)
        if z is None: return False
        board[z][y][x]=player
        opp=3-player
        # avoid giving immediate loss
        if self._immediate_win(board, opp): 
            board[z][y][x]=0; return False
        my_wins=self._my_immediate_wins_in_position(board, player)
        board[z][y][x]=0
        if len(my_wins)<2: return False
        return len(set(my_wins))>=2
    def _find_own_fork(self, board, player):
        for (x,y) in valid_moves(board):
            if self._creates_fork(board, player, x, y):
                return (x,y)
        return None
    def _find_block_opp_fork(self, board, player):
        opp=3-player
        opp_forks=[(x,y) for (x,y) in valid_moves(board) if self._creates_fork(board, opp, x, y)]
        if not opp_forks: return None
        # prefer direct block (in that column)
        for (bx,by) in opp_forks:
            if drop_z(board,bx,by) is not None: return (bx,by)
        # else any move that removes all forks
        for (x,y) in valid_moves(board):
            z=drop_z(board,x,y)
            if z is None: continue
            board[z][y][x]=player
            still=False
            for (ox,oy) in valid_moves(board):
                if self._creates_fork(board, opp, ox, oy): still=True; break
            board[z][y][x]=0
            if not still: return (x,y)
        return opp_forks[0]
    def _is_safe(self, board, player, x, y):
        opp=3-player
        z=drop_z(board,x,y)
        if z is None: return False
        board[z][y][x]=player
        safe=True
        for (ox,oy) in valid_moves(board):
            oz=drop_z(board,ox,oy)
            if oz is None: continue
            board[oz][oy][ox]=opp
            if winner(board)==opp: safe=False
            board[oz][oy][ox]=0
            if not safe: break
        board[z][y][x]=0
        return safe

    # -------- search --------
    def _hash(self, board):
        h=0
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    v=board[z][y][x]
                    if v!=0:
                        h ^= self.zkeys[x][y][z][v]
        return h

    def _order_moves(self, board, player, moves, depth):
        # center-first
        moves = list(moves)
        moves.sort(key=lambda m: (abs(m[0]-1.5)+abs(m[1]-1.5)))
        # killer heuristic
        killers = self.killers.get(depth, [])
        if killers:
            def score(m):
                return -1 if m in killers else 0
            moves.sort(key=score)
        return moves

    def _ab(self, board, player, depth, alpha, beta, me, start_time, nodes, root_moves, ply):
        # time/node guards
        import time as _t
        if nodes[0] >= self.node_budget or (_t.time()*1000 - start_time) > self.time_budget_ms:
            return eval_board(board, me)
        W = winner(board)
        if W==me:   return 10000-(self.max_depth-depth)
        if W==3-me: return -10000+(self.max_depth-depth)
        if depth==0 or board_full(board):
            return eval_board(board, me)

        # TT probe
        h = self._hash(board) ^ (depth<<1) ^ (player<<2)
        tt = self.TT.get(h)
        if tt and tt["depth"] >= depth:
            return tt["value"]

        moves = root_moves if ply==0 else list(valid_moves(board))
        # optional safe-filter at shallower depths
        if ply<=1:
            safe = [m for m in moves if self._is_safe(board, player, *m)]
            moves = safe or moves
        moves = self._order_moves(board, player, moves, depth)

        best = -10**9 if player==me else 10**9
        best_move = None
        for (x,y) in moves:
            z = drop_z(board,x,y)
            if z is None: continue
            board[z][y][x]=player
            nodes[0]+=1
            val = self._ab(board, 3-player, depth-1, alpha, beta, me, start_time, nodes, root_moves, ply+1)
            board[z][y][x]=0
            if player==me:
                if val>best: best, best_move = val, (x,y)
                if best>alpha: alpha = best
                if alpha>=beta:
                    # store killer
                    ks = self.killers.get(depth, [])
                    if best_move and best_move not in ks:
                        self.killers[depth] = [best_move] + ks[:1]
                    break
            else:
                if val<best: best, best_move = val, (x,y)
                if best<beta: beta = best
                if alpha>=beta:
                    ks = self.killers.get(depth, [])
                    if best_move and best_move not in ks:
                        self.killers[depth] = [best_move] + ks[:1]
                    break

        # TT store
        self.TT[h] = {"depth": depth, "value": best}
        return best

    def _search_best(self, board, player, candidates, start_time):
        # iterative deepening to 3 plies
        best = candidates[0]; bestv = -10**9
        import time as _t
        for d in [2,3]:
            self.max_depth = d
            # aspiration-like: small window around previous best
            alpha = -10**9; beta = 10**9
            for (x,y) in candidates:
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x]=player
                nodes=[0]
                val = self._ab(board, 3-player, d-1, alpha, beta, player, start_time, nodes, candidates, 0)
                board[z][y][x]=0
                if val>bestv:
                    bestv, best = val, (x,y)
                if (_t.time()*1000 - start_time) > self.time_budget_ms or nodes[0]>=self.node_budget:
                    break
            if (_t.time()*1000 - start_time) > self.time_budget_ms:
                break
        return best

    # -------- main --------
    def get_move(self, board: Board, player: int, last_move: Tuple[int,int,int]) -> Tuple[int,int]:
        import time as _t
        start = _t.time()*1000
        try:
            # opening bias (первые ходы в центр)
            empty = True
            for x in range(4):
                for y in range(4):
                    if board[0][y][x]!=0:
                        empty=False; break
                if not empty: break
            if empty:
                for pref in [(1,1),(2,2),(1,2),(2,1)]:
                    if drop_z(board, *pref) is not None:
                        return self._validate_move(board, *pref)

            # 1) immediate win / block
            mv = self._immediate_win(board, player)
            if mv: return self._validate_move(board, *mv)
            mv = self._immediate_win(board, 3-player)
            if mv: return self._validate_move(board, *mv)

            # 2) own fork / block opp fork
            mv = self._find_own_fork(board, player)
            if mv: return self._validate_move(board, *mv)
            mv = self._find_block_opp_fork(board, player)
            if mv: return self._validate_move(board, *mv)

            # 3) build candidate set (safe first)
            cand = [m for m in valid_moves(board) if self._is_safe(board, player, *m)]
            if not cand:
                cand = list(valid_moves(board))
            if not cand:
                return (0,0)
            cand.sort(key=lambda m: (abs(m[0]-1.5)+abs(m[1]-1.5)))

            # 4) search
            self.TT.clear(); self.killers.clear()
            best = self._search_best(board, player, cand, start)
            return self._validate_move(board, *best)
        except Exception:
            return self._first_legal_move(board)
