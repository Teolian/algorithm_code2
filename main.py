from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board  # type: ignore


def gen_lines():
    """Полный набор из 76 победных линий для 4x4x4."""
    L = []
    # По оси X
    for y in range(4):
        for z in range(4):
            L.append([(i, y, z) for i in range(4)])
    # По оси Y  
    for x in range(4):
        for z in range(4):
            L.append([(x, i, z) for i in range(4)])
    # По оси Z (вертикальные - важны!)
    for x in range(4):
        for y in range(4):
            L.append([(x, y, i) for i in range(4)])
    # Диагонали в плоскостях z
    for z in range(4):
        L.append([(i, i, z) for i in range(4)])
        L.append([(i, 3 - i, z) for i in range(4)])
    # Диагонали в плоскостях y
    for y in range(4):
        L.append([(i, y, i) for i in range(4)])
        L.append([(i, y, 3 - i) for i in range(4)])
    # Диагонали в плоскостях x
    for x in range(4):
        L.append([(x, i, i) for i in range(4)])
        L.append([(x, i, 3 - i) for i in range(4)])
    # Пространственные диагонали
    L.append([(i, i, i) for i in range(4)])
    L.append([(i, i, 3 - i) for i in range(4)])
    L.append([(i, 3 - i, i) for i in range(4)])
    L.append([(3 - i, i, i) for i in range(4)])
    return L


LINES = gen_lines()


def drop_z(board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
    """Куда упадет фишка в столбце (x,y)."""
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None


def winner(board: List[List[List[int]]]) -> int:
    """Есть ли победитель."""
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0


def valid_moves(board: List[List[List[int]]]):
    """Все валидные ходы."""
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)


def simple_eval(board: List[List[List[int]]], me: int) -> int:
    """Простая оценочная функция."""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 10000
    if w == opp:
        return -10000
    
    score = 0
    
    # Простая оценка линий
    for line in LINES:
        c1 = c2 = c0 = 0
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 1:
                c1 += 1
            elif v == 2:
                c2 += 1
            else:
                c0 += 1
        
        # Только чистые линии
        if c1 > 0 and c2 > 0:
            continue
            
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        
        if theirs == 0:
            if mine == 3:
                score += 500
            elif mine == 2:
                score += 50
            elif mine == 1:
                score += 5
        elif mine == 0:
            if theirs == 3:
                score -= 500
            elif theirs == 2:
                score -= 50
            elif theirs == 1:
                score -= 5
    
    return score


class MyAI(Alg3D):
    def __init__(self):
        pass
    
    def safe_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Абсолютно безопасный fallback."""
        moves = [(1,1), (2,2), (1,2), (2,1), (0,1), (1,0), (3,2), (2,3),
                 (0,2), (2,0), (3,1), (1,3), (0,0), (3,3), (0,3), (3,0)]
        
        for x, y in moves:
            if 0 <= x < 4 and 0 <= y < 4:
                if drop_z(board, x, y) is not None:
                    return (x, y)
        
        # Последний шанс
        for x in range(4):
            for y in range(4):
                if drop_z(board, x, y) is not None:
                    return (x, y)
        
        return (0, 0)
    
    def find_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленной победы."""
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
    
    def find_block(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """Поиск критических блокировок."""
        opp = 3 - player
        blocks = []
        
        for line in LINES:
            opp_count = 0
            empty_pos = None
            
            for (x, y, z) in line:
                v = board[z][y][x]
                if v == opp:
                    opp_count += 1
                elif v == 0:
                    if drop_z(board, x, y) == z:
                        empty_pos = (x, y)
            
            if opp_count == 3 and empty_pos is not None:
                blocks.append(empty_pos)
        
        return blocks
    
    def find_fork(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Простой поиск форка."""
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
                
            board[z][y][x] = player
            
            # Считаем победные ходы после этого
            wins = 0
            for (mx, my) in valid_moves(board):
                mz = drop_z(board, mx, my)
                if mz is None:
                    continue
                board[mz][my][mx] = player
                if winner(board) == player:
                    wins += 1
                board[mz][my][mx] = 0
            
            board[z][y][x] = 0
            
            if wins >= 2:
                return (x, y)
        
        return None
    
    def minimax_simple(self, board: Board, player: int, depth: int, maximizing: bool) -> int:
        """Простой minimax."""
        if depth == 0 or winner(board) != 0:
            return simple_eval(board, player)
        
        moves = list(valid_moves(board))
        if not moves:
            return simple_eval(board, player)
        
        # Ограничиваем количество ходов для скорости
        if len(moves) > 6:
            center_moves = sorted(moves, key=lambda m: abs(m[0]-1.5) + abs(m[1]-1.5))
            moves = center_moves[:6]
        
        if maximizing:
            max_eval = -50000
            for x, y in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score = self.minimax_simple(board, player, depth-1, False)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = 50000
            opp = 3 - player
            for x, y in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                eval_score = self.minimax_simple(board, player, depth-1, True)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
            return min_eval
    
    def get_best_simple(self, board: Board, player: int, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Простой поиск лучшего хода."""
        if not candidates:
            return self.safe_move(board)
        
        best_move = candidates[0]
        best_score = -50000
        
        for x, y in candidates:
            z = drop_z(board, x, y)
            if z is None:
                continue
            
            board[z][y][x] = player
            score = self.minimax_simple(board, player, 2, False)
            board[z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
        
        return best_move
    
    def get_move(
        self, 
        board: List[List[List[int]]], 
        player: int, 
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Максимально простая и надежная стратегия."""
        try:
            # 1. Немедленная победа
            win = self.find_win(board, player)
            if win:
                z = drop_z(board, win[0], win[1])
                if z is not None:
                    return win
            
            opp = 3 - player
            
            # 2. Блокировка критических угроз
            blocks = self.find_block(board, player)
            if blocks:
                for block in blocks:
                    z = drop_z(board, block[0], block[1])
                    if z is not None:
                        return block
            
            # 3. Обычная блокировка
            block = self.find_win(board, opp)
            if block:
                z = drop_z(board, block[0], block[1])
                if z is not None:
                    return block
            
            # 4. Попытка форка
            fork = self.find_fork(board, player)
            if fork:
                z = drop_z(board, fork[0], fork[1])
                if z is not None:
                    return fork
            
            # 5. Блокировка форка противника  
            opp_fork = self.find_fork(board, opp)
            if opp_fork:
                z = drop_z(board, opp_fork[0], opp_fork[1])
                if z is not None:
                    return opp_fork
            
            # 6. Лучший ход из доступных
            moves = list(valid_moves(board))
            if moves:
                best = self.get_best_simple(board, player, moves)
                z = drop_z(board, best[0], best[1])
                if z is not None:
                    return best
            
            # 7. Аварийный fallback
            return self.safe_move(board)
            
        except:
            # При любой ошибке - безопасный ход
            return self.safe_move(board)