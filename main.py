from typing import List, Tuple, Optional
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

LINES = None

def gen_lines():
    """Генерация всех победных линий с приоритизацией"""
    L = []
    # По оси X (горизонтальные в каждом слое)
    for y in range(4):
        for z in range(4):
            L.append([(i, y, z) for i in range(4)])
    # По оси Y (горизонтальные поперек)
    for x in range(4):
        for z in range(4):
            L.append([(x, i, z) for i in range(4)])
    # По оси Z (вертикальные столбцы) - КРИТИЧЕСКИ ВАЖНЫЕ!
    for x in range(4):
        for y in range(4):
            L.append([(x, y, i) for i in range(4)])
    
    # Плоскостные диагонали
    for z in range(4):
        L.append([(i, i, z) for i in range(4)])
        L.append([(i, 3-i, z) for i in range(4)])
    for y in range(4):
        L.append([(i, y, i) for i in range(4)])
        L.append([(i, y, 3-i) for i in range(4)])
    for x in range(4):
        L.append([(x, i, i) for i in range(4)])
        L.append([(x, i, 3-i) for i in range(4)])
    
    # Пространственные диагонали
    space_diags = [
        [(i, i, i) for i in range(4)],
        [(i, i, 3-i) for i in range(4)],
        [(i, 3-i, i) for i in range(4)],
        [(3-i, i, i) for i in range(4)]
    ]
    L.extend(space_diags)
    
    return L

def init_lines():
    global LINES
    if LINES is None:
        LINES = gen_lines()

def drop_z(board: Board, x: int, y: int) -> Optional[int]:
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None

def winner(board: Board) -> int:
    init_lines()
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals.count(1) == 4:
            return 1
        if vals.count(2) == 4:
            return 2
    return 0

def valid_moves(board: Board):
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)

def analyze_threats(board: Board, player: int) -> List[Tuple[int, int, int]]:
    """Анализ всех угроз (3 в ряд с возможностью достроить 4-ю)"""
    init_lines()
    threats = []
    
    for line in LINES:
        c0 = c1 = c2 = 0
        empty_pos = None
        
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0:
                c0 += 1
                if empty_pos is None:
                    empty_pos = (x, y, z)
            elif v == 1:
                c1 += 1
            else:
                c2 += 1
        
        # Угроза = 3 одинаковые + 1 пустая
        mine = c1 if player == 1 else c2
        theirs = c2 if player == 1 else c1
        
        if mine == 3 and c0 == 1 and empty_pos:
            # Проверяем, можно ли поставить в эту позицию
            ex, ey, ez = empty_pos
            if ez == 0:  # на дне
                threats.append((ex, ey, 3))  # высокий приоритет
            else:
                # проверяем, есть ли поддержка снизу
                if board[ez-1][ey][ex] != 0:
                    threats.append((ex, ey, 2))  # средний приоритет
        
        if theirs == 3 and c0 == 1 and empty_pos:
            ex, ey, ez = empty_pos
            if ez == 0:
                threats.append((ex, ey, 5))  # критический блок
            elif board[ez-1][ey][ex] != 0:
                threats.append((ex, ey, 4))  # важный блок
    
    return threats

def find_forks(board: Board, player: int) -> List[Tuple[int, int, int]]:
    """Поиск форков - ходов, создающих 2+ угрозы"""
    forks = []
    
    for (x, y) in valid_moves(board):
        z = drop_z(board, x, y)
        if z is None:
            continue
            
        # Временно ставим фишку
        board[z][y][x] = player
        
        # Считаем угрозы после хода
        threats = analyze_threats(board, player)
        critical_threats = [t for t in threats if t[2] == 3]
        
        # Убираем фишку
        board[z][y][x] = 0
        
        if len(critical_threats) >= 2:
            forks.append((x, y, 6))  # форк - максимальный приоритет
    
    return forks

def evaluate_position(board: Board, me: int) -> int:
    """Улучшенная оценочная функция"""
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 100000
    if w == opp:
        return -100000
    
    init_lines()
    score = 0
    
    # Анализ каждой линии
    for line in LINES:
        c0 = c1 = c2 = 0
        for (x, y, z) in line:
            v = board[z][y][x]
            if v == 0: c0 += 1
            elif v == 1: c1 += 1
            else: c2 += 1
        
        if c1 > 0 and c2 > 0:
            continue
            
        mine = c1 if me == 1 else c2
        theirs = c2 if me == 1 else c1
        
        if theirs == 0:
            if mine == 3: score += 5000
            elif mine == 2: score += 500
            elif mine == 1: score += 50
        elif mine == 0:
            if theirs == 3: score -= 6000
            elif theirs == 2: score -= 600  
            elif theirs == 1: score -= 60
    
    # Контроль центра
    center_bonus = 0
    for x in range(1, 3):
        for y in range(1, 3):
            for z in range(4):
                if board[z][y][x] == me:
                    center_bonus += (z + 1) * 30
                elif board[z][y][x] == opp:
                    center_bonus -= (z + 1) * 25
    
    return score + center_bonus

class MyAI(Alg3D):
    def __init__(self):
        self.move_count = 0

    def get_safe_move(self, board: Board) -> Tuple[int, int]:
        """Безопасный fallback ход"""
        priority = [(1,1), (2,2), (1,2), (2,1), (0,0), (3,3), (0,3), (3,0)]
        for x, y in priority:
            if drop_z(board, x, y) is not None:
                return (x, y)
        
        for x in range(4):
            for y in range(4):
                if drop_z(board, x, y) is not None:
                    return (x, y)
        return (0, 0)

    def minimax(self, board: Board, depth: int, alpha: int, beta: int, 
                maximizing: bool, player: int) -> int:
        """Minimax с alpha-beta pruning"""
        w = winner(board)
        if w == player:
            return 50000 + depth
        elif w != 0:
            return -50000 - depth
        
        if depth == 0:
            return evaluate_position(board, player)
        
        moves = list(valid_moves(board))
        if not moves:
            return evaluate_position(board, player)
        
        # Сортируем ходы: центр первый
        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
        
        if maximizing:
            max_eval = -100000
            for (x, y) in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score = self.minimax(board, depth - 1, alpha, beta, False, player)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 100000
            opp = 3 - player
            for (x, y) in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                eval_score = self.minimax(board, depth - 1, alpha, beta, True, player)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, board: Board, player: int) -> Tuple[int, int]:
        """Поиск лучшего хода через minimax"""
        moves = list(valid_moves(board))
        if not moves:
            return self.get_safe_move(board)
        
        # Сортируем по центральности
        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
        
        best_move = moves[0]
        best_score = -100000
        depth = 4 if len(moves) <= 8 else 3
        
        for (x, y) in moves:
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            score = self.minimax(board, depth - 1, -100000, 100000, False, player)
            board[z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
        
        return best_move

    def get_move(self, board: Board, player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        """Главная функция принятия решений"""
        try:
            self.move_count += 1
            opp = 3 - player
            
            # 1. КРИТИЧНО: Немедленная победа
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                if winner(board) == player:
                    board[z][y][x] = 0
                    return (x, y)
                board[z][y][x] = 0
            
            # 2. КРИТИЧНО: Блокировка победы соперника
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                if winner(board) == opp:
                    board[z][y][x] = 0
                    return (x, y)
                board[z][y][x] = 0
            
            # 3. Анализ угроз и форков
            my_threats = analyze_threats(board, player)
            opp_threats = analyze_threats(board, opp)
            my_forks = find_forks(board, player)
            opp_forks = find_forks(board, opp)
            
            # Создание форка
            if my_forks:
                return (my_forks[0][0], my_forks[0][1])
            
            # Блокировка критических угроз противника
            critical_blocks = [t for t in opp_threats if t[2] >= 4]
            if critical_blocks:
                critical_blocks.sort(key=lambda t: t[2], reverse=True)
                return (critical_blocks[0][0], critical_blocks[0][1])
            
            # Блокировка форков противника
            if opp_forks:
                return (opp_forks[0][0], opp_forks[0][1])
            
            # Реализация собственных угроз
            my_critical = [t for t in my_threats if t[2] >= 2]
            if my_critical:
                my_critical.sort(key=lambda t: t[2], reverse=True)
                return (my_critical[0][0], my_critical[0][1])
            
            # 4. Стратегический minimax
            return self.get_best_move(board, player)
            
        except Exception:
            return self.get_safe_move(board)