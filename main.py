from typing import List, Tuple, Optional, Set, Dict
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

LINES = [
    # Вертикальные столбцы (ПРИОРИТЕТ #1)
    [(0,0,0),(0,0,1),(0,0,2),(0,0,3)], [(0,1,0),(0,1,1),(0,1,2),(0,1,3)], [(0,2,0),(0,2,1),(0,2,2),(0,2,3)], [(0,3,0),(0,3,1),(0,3,2),(0,3,3)],
    [(1,0,0),(1,0,1),(1,0,2),(1,0,3)], [(1,1,0),(1,1,1),(1,1,2),(1,1,3)], [(1,2,0),(1,2,1),(1,2,2),(1,2,3)], [(1,3,0),(1,3,1),(1,3,2),(1,3,3)],
    [(2,0,0),(2,0,1),(2,0,2),(2,0,3)], [(2,1,0),(2,1,1),(2,1,2),(2,1,3)], [(2,2,0),(2,2,1),(2,2,2),(2,2,3)], [(2,3,0),(2,3,1),(2,3,2),(2,3,3)],
    [(3,0,0),(3,0,1),(3,0,2),(3,0,3)], [(3,1,0),(3,1,1),(3,1,2),(3,1,3)], [(3,2,0),(3,2,1),(3,2,2),(3,2,3)], [(3,3,0),(3,3,1),(3,3,2),(3,3,3)],
    
    # Горизонтальные по X
    [(0,0,0),(1,0,0),(2,0,0),(3,0,0)], [(0,1,0),(1,1,0),(2,1,0),(3,1,0)], [(0,2,0),(1,2,0),(2,2,0),(3,2,0)], [(0,3,0),(1,3,0),(2,3,0),(3,3,0)],
    [(0,0,1),(1,0,1),(2,0,1),(3,0,1)], [(0,1,1),(1,1,1),(2,1,1),(3,1,1)], [(0,2,1),(1,2,1),(2,2,1),(3,2,1)], [(0,3,1),(1,3,1),(2,3,1),(3,3,1)],
    [(0,0,2),(1,0,2),(2,0,2),(3,0,2)], [(0,1,2),(1,1,2),(2,1,2),(3,1,2)], [(0,2,2),(1,2,2),(2,2,2),(3,2,2)], [(0,3,2),(1,3,2),(2,3,2),(3,3,2)],
    [(0,0,3),(1,0,3),(2,0,3),(3,0,3)], [(0,1,3),(1,1,3),(2,1,3),(3,1,3)], [(0,2,3),(1,2,3),(2,2,3),(3,2,3)], [(0,3,3),(1,3,3),(2,3,3),(3,3,3)],
    
    # Горизонтальные по Y
    [(0,0,0),(0,1,0),(0,2,0),(0,3,0)], [(1,0,0),(1,1,0),(1,2,0),(1,3,0)], [(2,0,0),(2,1,0),(2,2,0),(2,3,0)], [(3,0,0),(3,1,0),(3,2,0),(3,3,0)],
    [(0,0,1),(0,1,1),(0,2,1),(0,3,1)], [(1,0,1),(1,1,1),(1,2,1),(1,3,1)], [(2,0,1),(2,1,1),(2,2,1),(2,3,1)], [(3,0,1),(3,1,1),(3,2,1),(3,3,1)],
    [(0,0,2),(0,1,2),(0,2,2),(0,3,2)], [(1,0,2),(1,1,2),(1,2,2),(1,3,2)], [(2,0,2),(2,1,2),(2,2,2),(2,3,2)], [(3,0,2),(3,1,2),(3,2,2),(3,3,2)],
    [(0,0,3),(0,1,3),(0,2,3),(0,3,3)], [(1,0,3),(1,1,3),(1,2,3),(1,3,3)], [(2,0,3),(2,1,3),(2,2,3),(2,3,3)], [(3,0,3),(3,1,3),(3,2,3),(3,3,3)],
    
    # Диагонали в плоскостях Z
    [(0,0,0),(1,1,0),(2,2,0),(3,3,0)], [(0,3,0),(1,2,0),(2,1,0),(3,0,0)],
    [(0,0,1),(1,1,1),(2,2,1),(3,3,1)], [(0,3,1),(1,2,1),(2,1,1),(3,0,1)],
    [(0,0,2),(1,1,2),(2,2,2),(3,3,2)], [(0,3,2),(1,2,2),(2,1,2),(3,0,2)],
    [(0,0,3),(1,1,3),(2,2,3),(3,3,3)], [(0,3,3),(1,2,3),(2,1,3),(3,0,3)],
    
    # Диагонали в плоскостях Y  
    [(0,0,0),(0,1,1),(0,2,2),(0,3,3)], [(0,0,3),(0,1,2),(0,2,1),(0,3,0)],
    [(1,0,0),(1,1,1),(1,2,2),(1,3,3)], [(1,0,3),(1,1,2),(1,2,1),(1,3,0)],
    [(2,0,0),(2,1,1),(2,2,2),(2,3,3)], [(2,0,3),(2,1,2),(2,2,1),(2,3,0)],
    [(3,0,0),(3,1,1),(3,2,2),(3,3,3)], [(3,0,3),(3,1,2),(3,2,1),(3,3,0)],
    
    # Диагонали в плоскостях X
    [(0,0,0),(1,0,1),(2,0,2),(3,0,3)], [(0,0,3),(1,0,2),(2,0,1),(3,0,0)],
    [(0,1,0),(1,1,1),(2,1,2),(3,1,3)], [(0,1,3),(1,1,2),(2,1,1),(3,1,0)],
    [(0,2,0),(1,2,1),(2,2,2),(3,2,3)], [(0,2,3),(1,2,2),(2,2,1),(3,2,0)],
    [(0,3,0),(1,3,1),(2,3,2),(3,3,3)], [(0,3,3),(1,3,2),(2,3,1),(3,3,0)],
    
    # ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ (ключевые для 3D!)
    [(0,0,0),(1,1,1),(2,2,2),(3,3,3)],  # главная
    [(0,0,3),(1,1,2),(2,2,1),(3,3,0)],  # инвертированная по Z
    [(0,3,0),(1,2,1),(2,1,2),(3,0,3)],  # инвертированная по Y
    [(3,0,0),(2,1,1),(1,2,2),(0,3,3)]   # инвертированная по X
]

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
        if vals == [1,1,1,1]: return 1
        if vals == [2,2,2,2]: return 2
    return 0

def valid_moves(board: Board):
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)

class ThreatAnalyzer:
    """Анализатор угроз на основе исследований Connect 4"""
    
    @staticmethod
    def analyze_all_threats(board: Board, player: int) -> Dict[str, List[Tuple[int, int, int]]]:
        """Анализ всех типов угроз по исследованиям"""
        threats = {
            'openings': [],      # Немедленно реализуемые угрозы
            'major_threats': [], # 3 в ряд с возможностью достроить
            'minor_threats': [], # 2 в ряд с потенциалом
            'blocks_needed': [], # Блокировки соперника
            'forks': []          # Двойные угрозы
        }
        
        opp = 3 - player
        
        for line_idx, line in enumerate(LINES):
            vals = [board[z][y][x] for (x, y, z) in line]
            my_count = vals.count(player)
            opp_count = vals.count(opp)
            empty_count = vals.count(0)
            
            if my_count > 0 and opp_count > 0:
                continue  # Смешанная линия
            
            # Анализ моих угроз
            if my_count == 3 and empty_count == 1:
                empty_pos = None
                for i, (x, y, z) in enumerate(line):
                    if vals[i] == 0:
                        empty_pos = (x, y, z)
                        break
                
                if empty_pos:
                    ex, ey, ez = empty_pos
                    # Проверяем реализуемость угрозы
                    if ez == 0 or (ez > 0 and board[ez-1][ey][ex] != 0):
                        weight = 5 if line_idx < 16 else 3  # Вертикальные приоритетнее
                        if line_idx >= 72:  # Пространственные диагонали
                            weight = 6
                        threats['openings'].append((ex, ey, weight))
                        
            elif my_count == 2 and empty_count == 2:
                weight = 2 if line_idx < 16 else 1
                if line_idx >= 72:
                    weight = 3
                # Находим пустые позиции
                for i, (x, y, z) in enumerate(line):
                    if vals[i] == 0:
                        if z == 0 or (z > 0 and board[z-1][y][x] != 0):
                            threats['major_threats'].append((x, y, weight))
            
            # Анализ угроз соперника
            if opp_count == 3 and empty_count == 1:
                empty_pos = None
                for i, (x, y, z) in enumerate(line):
                    if vals[i] == 0:
                        empty_pos = (x, y, z)
                        break
                
                if empty_pos:
                    ex, ey, ez = empty_pos
                    if ez == 0 or (ez > 0 and board[ez-1][ey][ex] != 0):
                        weight = 10 if line_idx < 16 else 8  # Блокировка критична
                        if line_idx >= 72:
                            weight = 12
                        threats['blocks_needed'].append((ex, ey, weight))
        
        return threats
    
    @staticmethod
    def find_fork_moves(board: Board, player: int) -> List[Tuple[int, int, int]]:
        """Поиск ходов создающих форк (2+ угрозы одновременно)"""
        forks = []
        
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            
            # Временно ставим фишку
            board[z][y][x] = player
            threats = ThreatAnalyzer.analyze_all_threats(board, player)
            board[z][y][x] = 0
            
            # Если после хода у нас 2+ немедленные угрозы = форк
            if len(threats['openings']) >= 2:
                forks.append((x, y, 15))  # Максимальный приоритет
        
        return forks

def eval_threat_based(board: Board, me: int) -> int:
    """Оценка основанная на системе угроз"""
    w = winner(board)
    if w == me: return 100000
    if w != 0: return -100000
    
    score = 0
    my_threats = ThreatAnalyzer.analyze_all_threats(board, me)
    opp_threats = ThreatAnalyzer.analyze_all_threats(board, 3-me)
    
    # Бонусы за мои угрозы
    for _, _, weight in my_threats['openings']:
        score += weight * 2000
    for _, _, weight in my_threats['major_threats']:
        score += weight * 400
    for _, _, weight in my_threats['minor_threats']:
        score += weight * 50
    
    # Штрафы за угрозы соперника  
    for _, _, weight in opp_threats['openings']:
        score -= weight * 1800
    for _, _, weight in opp_threats['major_threats']:
        score -= weight * 360
    for _, _, weight in opp_threats['minor_threats']:
        score -= weight * 45
    
    # Центральный контроль
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for (cx, cy) in center_positions:
        for z in range(4):
            if board[z][cy][cx] == me:
                score += (z + 1) * 100
            elif board[z][cy][cx] == (3-me):
                score -= (z + 1) * 90
    
    return score

class MyAI(Alg3D):
    def __init__(self):
        self.move_count = 0
        # Агрессивная дебютная книга по исследованиям
        self.openings = [
            (1, 1), (2, 2),  # Центральное доминирование
            (1, 2), (2, 1),  # Контроль диагоналей
            (0, 0), (3, 3)   # Углы для блокировки пространственных
        ]

    def get_critical_move(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Поиск критически важного хода"""
        # 1. Немедленная победа
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None: continue
            board[z][y][x] = player
            if winner(board) == player:
                board[z][y][x] = 0
                return (x, y)
            board[z][y][x] = 0
        
        # 2. Критическая блокировка
        opp = 3 - player
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None: continue
            board[z][y][x] = opp
            if winner(board) == opp:
                board[z][y][x] = 0
                return (x, y)
            board[z][y][x] = 0
        
        # 3. Форки (двойные угрозы)
        forks = ThreatAnalyzer.find_fork_moves(board, player)
        if forks:
            forks.sort(key=lambda f: f[2], reverse=True)
            return (forks[0][0], forks[0][1])
        
        # 4. Блокировка форков соперника
        opp_forks = ThreatAnalyzer.find_fork_moves(board, opp)
        if opp_forks:
            return (opp_forks[0][0], opp_forks[0][1])
        
        return None

    def minimax_threats(self, board: Board, depth: int, alpha: int, beta: int, 
                       maximizing: bool, player: int) -> int:
        """Minimax оптимизированный под анализ угроз"""
        w = winner(board)
        if w == player: return 50000 + depth
        elif w != 0: return -50000 - depth
        if depth == 0: return eval_threat_based(board, player)
        
        moves = list(valid_moves(board))
        if not moves: return eval_threat_based(board, player)
        
        # Сортировка ходов: центр + угрозы первыми
        def move_priority(move):
            x, y = move
            center_bonus = -(abs(x - 1.5) + abs(y - 1.5))  # Чем ближе к центру, тем лучше
            
            # Бонус за угрозы
            z = drop_z(board, x, y)
            if z is not None:
                threat_bonus = 0
                current_player = player if maximizing else (3 - player)
                board[z][y][x] = current_player
                threats = ThreatAnalyzer.analyze_all_threats(board, current_player)
                threat_bonus = len(threats['openings']) * 100 + len(threats['major_threats']) * 10
                board[z][y][x] = 0
                return center_bonus + threat_bonus
            return center_bonus
        
        moves.sort(key=move_priority, reverse=True)
        
        if maximizing:
            max_eval = -200000
            for (x, y) in moves[:8]:  # Ограничиваем для скорости
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = player
                eval_score = self.minimax_threats(board, depth - 1, alpha, beta, False, player)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = 200000
            opp = 3 - player
            for (x, y) in moves[:8]:
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = opp
                eval_score = self.minimax_threats(board, depth - 1, alpha, beta, True, player)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval

    def get_move(self, board: Board, player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        """Главная функция на основе threat management"""
        try:
            self.move_count += 1
            
            # Дебютная книга
            if self.move_count <= len(self.openings):
                preferred = self.openings[self.move_count - 1]
                if drop_z(board, *preferred) is not None:
                    return preferred
            
            # Критические ходы (победа/блок/форк)
            critical = self.get_critical_move(board, player)
            if critical:
                return critical
            
            # Анализ угроз для стратегического выбора
            my_threats = ThreatAnalyzer.analyze_all_threats(board, player)
            opp_threats = ThreatAnalyzer.analyze_all_threats(board, 3 - player)
            
            # Блокировка критических угроз оппонента
            if opp_threats['blocks_needed']:
                blocks = sorted(opp_threats['blocks_needed'], key=lambda b: b[2], reverse=True)
                return (blocks[0][0], blocks[0][1])
            
            # Реализация собственных угроз
            if my_threats['openings']:
                openings = sorted(my_threats['openings'], key=lambda o: o[2], reverse=True)
                return (openings[0][0], openings[0][1])
            
            # Стратегический minimax с анализом угроз
            moves = list(valid_moves(board))
            if not moves:
                return (1, 1)
            
            best_move = moves[0]
            best_score = -200000
            depth = 3  # Баланс скорость/точность
            
            # Топ-8 ходов для скорости
            moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
            
            for (x, y) in moves[:8]:
                z = drop_z(board, x, y)
                if z is None: continue
                board[z][y][x] = player
                score = self.minimax_threats(board, depth - 1, -200000, 200000, False, player)
                board[z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move
            
        except Exception:
            # Безопасный fallback
            for move in self.openings:
                if drop_z(board, *move) is not None:
                    return move
            return (1, 1)