from typing import List, Tuple, Optional, Set
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

LINES = None

def gen_lines():
    """76 линий для 4x4x4 с приоритетом пространственных диагоналей"""
    L = []
    # Обычные линии (по осям)
    for y in range(4):
        for z in range(4):
            L.append([(i, y, z) for i in range(4)])
    for x in range(4):
        for z in range(4):
            L.append([(x, i, z) for i in range(4)])
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
    
    # КРИТИЧЕСКИ ВАЖНЫЕ: пространственные диагонали
    space_diags = [
        [(i, i, i) for i in range(4)],           # главная
        [(i, i, 3-i) for i in range(4)],         # инвертированная Z
        [(i, 3-i, i) for i in range(4)],         # инвертированная Y
        [(3-i, i, i) for i in range(4)]          # инвертированная X
    ]
    L.extend(space_diags)
    
    return L, space_diags[:]

def drop_z(board: Board, x: int, y: int) -> Optional[int]:
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None

def board_full(board: Board) -> bool:
    return all(board[3][y][x] != 0 for x in range(4) for y in range(4))

def winner(board: Board) -> int:
    global LINES
    if LINES is None:
        LINES, _ = gen_lines()
    
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

def eval_position_aggressive(board: Board, me: int) -> int:
    """Агрессивная оценка с упором на атаку"""
    global LINES, SPACE_DIAGS
    if LINES is None:
        LINES, SPACE_DIAGS = gen_lines()
    
    opp = 3 - me
    w = winner(board)
    if w == me:
        return 100000
    if w == opp:
        return -100000

    score = 0
    my_threats = 0
    opp_threats = 0
    my_forks = 0
    
    # Анализ каждой линии
    for i, line in enumerate(LINES):
        is_space_diag = i >= len(LINES) - 4  # последние 4 - пространственные
        
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
        weight = 3 if is_space_diag else 1  # пространственные диагонали важнее
        
        if theirs == 0:
            if mine == 3:
                score += 8000 * weight
                my_threats += 2 if is_space_diag else 1
            elif mine == 2:
                score += 800 * weight
                if c0 >= 2:  # можем развить угрозу
                    my_threats += 1
            elif mine == 1:
                score += 80 * weight
        elif mine == 0:
            if theirs == 3:
                score -= 7500 * weight
                opp_threats += 2 if is_space_diag else 1
            elif theirs == 2:
                score -= 750 * weight
            elif theirs == 1:
                score -= 75 * weight

    # Контроль центральных позиций (ключевые точки пространственных диагоналей)
    center_points = [(1,1,1), (1,1,2), (2,2,1), (2,2,2)]
    for (x,y,z) in center_points:
        v = board[z][y][x]
        if v == me:
            score += 150
        elif v == opp:
            score -= 140

    # Бонус за высоту (контроль верхних слоев)
    for z in range(2, 4):
        for y in range(4):
            for x in range(4):
                if board[z][y][x] == me:
                    score += z * 25
                elif board[z][y][x] == opp:
                    score -= z * 20

    # Штраф за пассивность, бонус за агрессию
    threat_balance = my_threats - opp_threats
    score += threat_balance * 500
    
    return score

class MyAI(Alg3D):
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.move_count = 0
        
        # Агрессивный дебютник: центр + ключевые точки
        self.opening_book = {
            0: [(1,1), (2,2)],  # центр
            1: [(1,2), (2,1)],  # около центра
            2: [(0,0), (3,3), (0,3), (3,0)],  # углы для блокировки
        }

    def get_safe_move(self, board: Board) -> Tuple[int, int]:
        """Гарантированно валидный ход"""
        priority_order = [
            (1,1), (2,2), (1,2), (2,1),  # центр
            (0,1), (1,0), (3,2), (2,3),  # края
            (0,0), (3,3), (0,3), (3,0)   # углы
        ]
        for x, y in priority_order:
            if drop_z(board, x, y) is not None:
                return (x, y)
        return (0, 0)

    def find_immediate_win(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Поиск мгновенной победы"""
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

    def count_threats(self, board: Board, player: int, move: Tuple[int, int]) -> int:
        """Подсчет угроз после хода"""
        global LINES
        if LINES is None:
            LINES, _ = gen_lines()
            
        x, y = move
        z = drop_z(board, x, y)
        if z is None:
            return 0
        
        board[z][y][x] = player
        threats = 0
        
        for line in LINES:
            c0 = c1 = c2 = 0
            for (lx, ly, lz) in line:
                v = board[lz][ly][lx]
                if v == 0: c0 += 1
                elif v == 1: c1 += 1
                else: c2 += 1
            
            mine = c1 if player == 1 else c2
            theirs = c2 if player == 1 else c1
            
            if theirs == 0 and mine == 3 and c0 == 1:
                threats += 1
                
        board[z][y][x] = 0
        return threats

    def find_fork_move(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """Поиск форка (двойной угрозы)"""
        best_move = None
        max_threats = 0
        
        for (x, y) in valid_moves(board):
            threats = self.count_threats(board, player, (x, y))
            if threats >= 2:  # форк найден
                if threats > max_threats:
                    max_threats = threats
                    best_move = (x, y)
        
        return best_move

    def is_dangerous_move(self, board: Board, player: int, move: Tuple[int, int]) -> bool:
        """Проверка, не дает ли ход сопернику преимущество"""
        opp = 3 - player
        x, y = move
        z = drop_z(board, x, y)
        if z is None:
            return True
            
        board[z][y][x] = player
        
        # Проверяем, может ли оппонент выиграть сразу
        opp_win = self.find_immediate_win(board, opp)
        if opp_win:
            board[z][y][x] = 0
            return True
            
        # Проверяем, получает ли оппонент форк
        opp_fork = self.find_fork_move(board, opp)
        if opp_fork:
            board[z][y][x] = 0
            return True
            
        board[z][y][x] = 0
        return False

    def minimax_alpha_beta(self, board: Board, depth: int, alpha: int, beta: int, 
                          is_maximizing: bool, player: int) -> int:
        """Minimax с alpha-beta отсечением"""
        w = winner(board)
        if w == player:
            return 100000 - (self.depth - depth)
        if w == (3 - player):
            return -100000 + (self.depth - depth)
        if depth == 0 or board_full(board):
            return eval_position_aggressive(board, player)

        moves = list(valid_moves(board))
        # Сортируем ходы: центральные первыми
        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))

        if is_maximizing:
            max_eval = -200000
            for (x, y) in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score = self.minimax_alpha_beta(board, depth - 1, alpha, beta, 
                                                   False, player)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 200000
            opp = 3 - player
            for (x, y) in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                eval_score = self.minimax_alpha_beta(board, depth - 1, alpha, beta, 
                                                   True, player)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, board: Board, player: int) -> Tuple[int, int]:
        """Поиск лучшего хода через minimax"""
        moves = list(valid_moves(board))
        moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
        
        best_move = moves[0] if moves else (0, 0)
        best_score = -200000
        
        for (x, y) in moves:
            z = drop_z(board, x, y)
            if z is None:
                continue
            board[z][y][x] = player
            score = self.minimax_alpha_beta(board, self.depth - 1, -200000, 200000, 
                                          False, player)
            board[z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
        
        return best_move

    def get_move(self, board: Board, player: int, 
                last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        """Главная функция выбора хода"""
        try:
            # Дебютная книга
            if self.move_count < 3 and self.move_count in self.opening_book:
                for move in self.opening_book[self.move_count]:
                    if drop_z(board, *move) is not None:
                        self.move_count += 1
                        return move
            
            self.move_count += 1
            opp = 3 - player
            
            # 1. Немедленная победа
            win_move = self.find_immediate_win(board, player)
            if win_move:
                return win_move
            
            # 2. Блокировка победы соперника
            block_move = self.find_immediate_win(board, opp)
            if block_move:
                return block_move
            
            # 3. Создание форка (двойной угрозы)
            fork_move = self.find_fork_move(board, player)
            if fork_move and not self.is_dangerous_move(board, player, fork_move):
                return fork_move
            
            # 4. Блокировка форка соперника
            opp_fork = self.find_fork_move(board, opp)
            if opp_fork:
                return opp_fork
            
            # 5. Лучший ход через minimax
            return self.get_best_move(board, player)
            
        except Exception:
            return self.get_safe_move(board)