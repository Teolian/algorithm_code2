from typing import List, Tuple, Optional, Dict
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

# Предкомпилированные линии для скорости
LINES = [
    # Вертикальные столбцы (критически важные!)
    [(0,0,0),(0,0,1),(0,0,2),(0,0,3)], [(0,1,0),(0,1,1),(0,1,2),(0,1,3)], [(0,2,0),(0,2,1),(0,2,2),(0,2,3)], [(0,3,0),(0,3,1),(0,3,2),(0,3,3)],
    [(1,0,0),(1,0,1),(1,0,2),(1,0,3)], [(1,1,0),(1,1,1),(1,1,2),(1,1,3)], [(1,2,0),(1,2,1),(1,2,2),(1,2,3)], [(1,3,0),(1,3,1),(1,3,2),(1,3,3)],
    [(2,0,0),(2,0,1),(2,0,2),(2,0,3)], [(2,1,0),(2,1,1),(2,1,2),(2,1,3)], [(2,2,0),(2,2,1),(2,2,2),(2,2,3)], [(2,3,0),(2,3,1),(2,3,2),(2,3,3)],
    [(3,0,0),(3,0,1),(3,0,2),(3,0,3)], [(3,1,0),(3,1,1),(3,1,2),(3,1,3)], [(3,2,0),(3,2,1),(3,2,2),(3,2,3)], [(3,3,0),(3,3,1),(3,3,2),(3,3,3)],
    
    # Горизонтальные X (в каждом слое)
    [(0,0,0),(1,0,0),(2,0,0),(3,0,0)], [(0,1,0),(1,1,0),(2,1,0),(3,1,0)], [(0,2,0),(1,2,0),(2,2,0),(3,2,0)], [(0,3,0),(1,3,0),(2,3,0),(3,3,0)],
    [(0,0,1),(1,0,1),(2,0,1),(3,0,1)], [(0,1,1),(1,1,1),(2,1,1),(3,1,1)], [(0,2,1),(1,2,1),(2,2,1),(3,2,1)], [(0,3,1),(1,3,1),(2,3,1),(3,3,1)],
    [(0,0,2),(1,0,2),(2,0,2),(3,0,2)], [(0,1,2),(1,1,2),(2,1,2),(3,1,2)], [(0,2,2),(1,2,2),(2,2,2),(3,2,2)], [(0,3,2),(1,3,2),(2,3,2),(3,3,2)],
    [(0,0,3),(1,0,3),(2,0,3),(3,0,3)], [(0,1,3),(1,1,3),(2,1,3),(3,1,3)], [(0,2,3),(1,2,3),(2,2,3),(3,2,3)], [(0,3,3),(1,3,3),(2,3,3),(3,3,3)],
    
    # Горизонтальные Y
    [(0,0,0),(0,1,0),(0,2,0),(0,3,0)], [(1,0,0),(1,1,0),(1,2,0),(1,3,0)], [(2,0,0),(2,1,0),(2,2,0),(2,3,0)], [(3,0,0),(3,1,0),(3,2,0),(3,3,0)],
    [(0,0,1),(0,1,1),(0,2,1),(0,3,1)], [(1,0,1),(1,1,1),(1,2,1),(1,3,1)], [(2,0,1),(2,1,1),(2,2,1),(2,3,1)], [(3,0,1),(3,1,1),(3,2,1),(3,3,1)],
    [(0,0,2),(0,1,2),(0,2,2),(0,3,2)], [(1,0,2),(1,1,2),(1,2,2),(1,3,2)], [(2,0,2),(2,1,2),(2,2,2),(2,3,2)], [(3,0,2),(3,1,2),(3,2,2),(3,3,2)],
    [(0,0,3),(0,1,3),(0,2,3),(0,3,3)], [(1,0,3),(1,1,3),(1,2,3),(1,3,3)], [(2,0,3),(2,1,3),(2,2,3),(2,3,3)], [(3,0,3),(3,1,3),(3,2,3),(3,3,3)],
    
    # Диагонали плоскостные
    [(0,0,0),(1,1,0),(2,2,0),(3,3,0)], [(0,3,0),(1,2,0),(2,1,0),(3,0,0)],
    [(0,0,1),(1,1,1),(2,2,1),(3,3,1)], [(0,3,1),(1,2,1),(2,1,1),(3,0,1)],
    [(0,0,2),(1,1,2),(2,2,2),(3,3,2)], [(0,3,2),(1,2,2),(2,1,2),(3,0,2)],
    [(0,0,3),(1,1,3),(2,2,3),(3,3,3)], [(0,3,3),(1,2,3),(2,1,3),(3,0,3)],
    
    [(0,0,0),(0,1,1),(0,2,2),(0,3,3)], [(0,0,3),(0,1,2),(0,2,1),(0,3,0)],
    [(1,0,0),(1,1,1),(1,2,2),(1,3,3)], [(1,0,3),(1,1,2),(1,2,1),(1,3,0)],
    [(2,0,0),(2,1,1),(2,2,2),(2,3,3)], [(2,0,3),(2,1,2),(2,2,1),(2,3,0)],
    [(3,0,0),(3,1,1),(3,2,2),(3,3,3)], [(3,0,3),(3,1,2),(3,2,1),(3,3,0)],
    
    [(0,0,0),(1,0,1),(2,0,2),(3,0,3)], [(0,0,3),(1,0,2),(2,0,1),(3,0,0)],
    [(0,1,0),(1,1,1),(2,1,2),(3,1,3)], [(0,1,3),(1,1,2),(2,1,1),(3,1,0)],
    [(0,2,0),(1,2,1),(2,2,2),(3,2,3)], [(0,2,3),(1,2,2),(2,2,1),(3,2,0)],
    [(0,3,0),(1,3,1),(2,3,2),(3,3,3)], [(0,3,3),(1,3,2),(2,3,1),(3,3,0)],
    
    # ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ (победные комбо!)
    [(0,0,0),(1,1,1),(2,2,2),(3,3,3)],  # главная
    [(0,0,3),(1,1,2),(2,2,1),(3,3,0)],  # инвертированная Z
    [(0,3,0),(1,2,1),(2,1,2),(3,0,3)],  # инвертированная Y
    [(3,0,0),(2,1,1),(1,2,2),(0,3,3)]   # инвертированная X
]

# Быстрые lookup-таблицы
SPACE_DIAG_INDICES = set(range(72, 76))  # последние 4 линии
VERTICAL_INDICES = set(range(0, 16))     # первые 16 линий

def drop_z(board: Board, x: int, y: int) -> Optional[int]:
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None

def winner(board: Board) -> int:
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals == [1,1,1,1]:
            return 1
        if vals == [2,2,2,2]:
            return 2
    return 0

def valid_moves(board: Board):
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)

def count_pattern(line_vals: List[int], player: int) -> Tuple[int, int, bool]:
    """Быстрый подсчет паттерна в линии"""
    mine = line_vals.count(player)
    opp = line_vals.count(3 - player)
    empty = line_vals.count(0)
    is_threat = (mine == 3 and empty == 1)
    return mine, opp, is_threat

def eval_fast(board: Board, me: int) -> int:
    """Ультрабыстрая оценка"""
    w = winner(board)
    if w == me: return 100000
    if w != 0: return -100000
    
    score = 0
    my_threats = 0
    opp_threats = 0
    
    for i, line in enumerate(LINES):
        vals = [board[z][y][x] for (x, y, z) in line]
        mine, opp_count, is_my_threat = count_pattern(vals, me)
        opp, my_count, is_opp_threat = count_pattern(vals, 3 - me)
        
        # Смешанные линии игнорируем
        if mine > 0 and opp > 0:
            continue
            
        multiplier = 3 if i in SPACE_DIAG_INDICES else 1
        
        if mine > 0:
            if is_my_threat:
                score += 6000 * multiplier
                my_threats += multiplier
            elif mine == 2:
                score += 400 * multiplier
            elif mine == 1:
                score += 40 * multiplier
        elif opp > 0:
            if is_opp_threat:
                score -= 5500 * multiplier
                opp_threats += multiplier
            elif opp == 2:
                score -= 350 * multiplier
            elif opp == 1:
                score -= 35 * multiplier
    
    # Агрессивность
    score += (my_threats - opp_threats) * 1000
    
    # Центр
    center_control = 0
    for pos in [(1,1,1), (1,1,2), (2,2,1), (2,2,2), (1,2,1), (2,1,2)]:
        x, y, z = pos
        if board[z][y][x] == me:
            center_control += 100
        elif board[z][y][x] == (3-me):
            center_control -= 90
    
    return score + center_control

class MyAI(Alg3D):
    def __init__(self):
        self.move_count = 0
        # Агрессивная дебютная книга
        self.openings = {
            1: [(1,1), (2,2)],  # центральное доминирование
            3: [(1,2), (2,1), (0,0)],  # контроль диагоналей
            5: [(3,3), (0,3), (3,0)]   # углы для блокировки
        }

    def find_critical_move(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Поиск критически важного хода (победа/блок/форк) за один проход"""
        my_wins = []
        opp_wins = []
        my_threats = []
        opp_threats = []
        
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
                
            # Проверяем мою победу
            board[z][y][x] = player
            if winner(board) == player:
                board[z][y][x] = 0
                return (x, y)  # мгновенный возврат победы
            
            # Считаем мои угрозы после хода
            my_new_threats = 0
            for i, line in enumerate(LINES):
                vals = [board[z2][y2][x2] for (x2, y2, z2) in line]
                if vals.count(player) == 3 and vals.count(0) == 1:
                    my_new_threats += (3 if i in SPACE_DIAG_INDICES else 1)
            
            if my_new_threats >= 2:  # форк найден
                board[z][y][x] = 0
                return (x, y)
                
            board[z][y][x] = 0
            
            # Проверяем блок победы соперника
            opp = 3 - player
            board[z][y][x] = opp
            if winner(board) == opp:
                opp_wins.append((x, y))
            board[z][y][x] = 0
        
        # Блокируем победу соперника
        if opp_wins:
            return opp_wins[0]
            
        return None

    def minimax_fast(self, board: Board, depth: int, alpha: int, beta: int, 
                    maximizing: bool, player: int) -> int:
        """Оптимизированный minimax"""
        w = winner(board)
        if w == player: return 50000 + depth
        elif w != 0: return -50000 - depth
        if depth == 0: return eval_fast(board, player)
        
        moves = list(valid_moves(board))
        if not moves: return eval_fast(board, player)
        
        # Быстрая сортировка: центр важнее
        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
        
        if maximizing:
            max_eval = -200000
            for (x, y) in moves[:8]:  # ограничиваем ветвление для скорости
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = player
                eval_score = self.minimax_fast(board, depth - 1, alpha, beta, False, player)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = 200000
            opp = 3 - player
            for (x, y) in moves[:8]:  # ограничиваем для скорости
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = opp
                eval_score = self.minimax_fast(board, depth - 1, alpha, beta, True, player)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval

    def get_move(self, board: Board, player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        """Главная функция - скорость + точность"""
        try:
            self.move_count += 1
            
            # Дебютная книга для быстрого старта
            if self.move_count in self.openings:
                for move in self.openings[self.move_count]:
                    if drop_z(board, *move) is not None:
                        return move
            
            # Критические ходы (победа/блок/форк)
            critical = self.find_critical_move(board, player)
            if critical:
                return critical
            
            # Быстрый стратегический поиск
            moves = list(valid_moves(board))
            if not moves:
                return (1, 1)
                
            moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
            best_move = moves[0]
            best_score = -200000
            
            # Адаптивная глубина: меньше ходов = больше просчет
            depth = 4 if len(moves) <= 6 else 3 if len(moves) <= 10 else 2
            
            for (x, y) in moves[:10]:  # топ-10 ходов для скорости
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = player
                score = self.minimax_fast(board, depth - 1, -200000, 200000, False, player)
                board[z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move
            
        except Exception:
            # Безопасный fallback
            for move in [(1,1), (2,2), (1,2), (2,1), (0,0)]:
                if drop_z(board, *move) is not None:
                    return move
            return (0, 0)