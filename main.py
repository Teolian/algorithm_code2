from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board  # server
except Exception:
    # local fallback
    from local_driver import Alg3D, Board  # type: ignore

# 4x4x4 gravity 3D Connect-Four (Score Four)

def gen_lines():
    L = []
    # X/Y/Z
    for y in range(4):
        for z in range(4):
            L.append([(i,y,z) for i in range(4)])
    for x in range(4):
        for z in range(4):
            L.append([(x,i,z) for i in range(4)])
    for x in range(4):
        for y in range(4):
            L.append([(x,y,i) for i in range(4)])
    # face diagonals
    for z in range(4):
        L.append([(i,i,z) for i in range(4)])
        L.append([(i,3-i,z) for i in range(4)])
    for y in range(4):
        L.append([(i,y,i) for i in range(4)])
        L.append([(i,y,3-i) for i in range(4)])
    for x in range(4):
        L.append([(x,i,i) for i in range(4)])
        L.append([(x,i,3-i) for i in range(4)])
    # 4 space diagonals
    L.append([(i,i,i) for i in range(4)])
    L.append([(i,i,3-i) for i in range(4)])
    L.append([(i,3-i,i) for i in range(4)])
    L.append([(3-i,i,i) for i in range(4)])
    return L

LINES = gen_lines()

def drop_z(board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
    if not (0<=x<4 and 0<=y<4):
        return None
    for z in range(4):
        if board[z][y][x]==0:
            return z
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

def eval_board(board: List[List[List[int]]], me: int) -> int:
    opp = 3-me
    W = winner(board)
    if W==me: return 10_000
    if W==opp: return -10_000
    score = 0
    # centrality + height
    for x in range(4):
        for y in range(4):
            for z in range(4):
                p = board[z][y][x]
                if p==0: continue
                cent = 3 - int(abs(x-1.5)+abs(y-1.5))
                h = z
                s = cent + h
                score += s if p==me else -s
    # line potential
    for line in LINES:
        c = [0,0,0]
        for (x,y,z) in line:
            c[board[z][y][x]] += 1
        # ignore mixed lines
        if c[1] and c[2]: 
            continue
        mine = c[me]; theirs = c[opp]
        if theirs==0:
            if mine==3: score += 200
            elif mine==2: score += 30
            elif mine==1: score += 4
        elif mine==0:
            if theirs==3: score -= 200
            elif theirs==2: score -= 30
            elif theirs==1: score -= 4
    return score

class MyAI(Alg3D):
    def __init__(self, depth: int = 2):
        self.depth = depth

    def get_move(self, board: Board, player: int, last_move: Tuple[int,int,int]) -> Tuple[int,int]:
        opp = 3-player

        # 1) Immediate win
        for (x,y) in valid_moves(board):
            z = drop_z(board,x,y); board[z][y][x]=player
            if winner(board)==player:
                board[z][y][x]=0; return (x,y)
            board[z][y][x]=0

        # 2) Immediate block
        for (x,y) in valid_moves(board):
            z = drop_z(board,x,y); board[z][y][x]=opp
            if winner(board)==opp:
                board[z][y][x]=0; return (x,y)
            board[z][y][x]=0

        # 3) Safe-move filter (avoid giving opp an instant win)
        def is_safe(x,y):
            z = drop_z(board,x,y); board[z][y][x]=player
            safe = True
            for (ox,oy) in valid_moves(board):
                oz = drop_z(board,ox,oy); board[oz][oy][ox]=opp
                if winner(board)==opp: safe=False
                board[oz][oy][ox]=0
                if not safe: break
            board[z][y][x]=0
            return safe

        cand = [m for m in valid_moves(board) if is_safe(*m)] or list(valid_moves(board))
        cand.sort(key=lambda m: (abs(m[0]-1.5)+abs(m[1]-1.5)))  # center-first

        # 4) Alpha-beta depth-2 on candidates
        best, bestv = cand[0], -10**9
        def ab(pl, d, a, b):
            W = winner(board)
            if W==player: return 10_000 - (2-d)
            if W==opp:    return -10_000 + (2-d)
            if d==0 or board_full(board): return eval_board(board, player)
            if pl==player:
                v = -10**9
                for (x,y) in cand:
                    z = drop_z(board,x,y); board[z][y][x]=pl
                    v = max(v, ab(opp, d-1, a, b))
                    board[z][y][x]=0
                    a = max(a, v)
                    if b<=a: break
                return v
            else:
                v = 10**9
                for (x,y) in cand:
                    z = drop_z(board,x,y); board[z][y][x]=pl
                    v = min(v, ab(player, d-1, a, b))
                    board[z][y][x]=0
                    b = min(b, v)
                    if b<=a: break
                return v

        for (x,y) in cand:
            z = drop_z(board,x,y); board[z][y][x]=player
            v = ab(opp, self.depth-1, -10**9, 10**9)
            board[z][y][x]=0
            if v>bestv:
                bestv, best = v, (x,y)
        return best
