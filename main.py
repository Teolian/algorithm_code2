from typing import List, Tuple, Optional
import time
# from local_driver import Alg3D, Board # Для локального тестирования  
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.start_time = None
        self.max_time = 8.5  # Оставляем резерв
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """АГРЕССИВНЫЙ ИИ с Negamax и исправленной защитой"""
        
        self.start_time = time.time()
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА
            win_move = self.find_instant_win(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА (ИСПРАВЛЕНА для вертикали!)
            opponent = 3 - player
            block_move = self.find_instant_win(board, opponent)
            if block_move:
                return block_move
            
            # 3. АГРЕССИВНЫЙ NEGAMAX ПОИСК
            aggressive_move = self.negamax_search(board, player)
            if aggressive_move:
                return aggressive_move
                
            # 4. БЫСТРЫЙ ЦЕНТРАЛЬНЫЙ ХОД
            return self.get_center_move(board)
            
        except Exception:
            return self.emergency_move(board)

    def find_instant_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """БЫСТРЫЙ поиск мгновенной победы"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    board[drop_z][y][x] = player
                    
                    # ИСПРАВЛЕННАЯ проверка - включая вертикаль!
                    if self.is_winning_position(board, x, y, drop_z, player):
                        board[drop_z][y][x] = 0
                        return (x, y)
                    
                    board[drop_z][y][x] = 0
                    
            return None
        except Exception:
            return None

    def is_winning_position(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """ПРАВИЛЬНАЯ проверка победы - ВКЛЮЧАЯ ВЕРТИКАЛЬ"""
        try:
            # ВСЕ направления для Connect 4 в 3D
            directions = [
                # ОСНОВНЫЕ ОСИ (включая вертикаль!)
                (1, 0, 0),   # X горизонт
                (0, 1, 0),   # Y горизонт  
                (0, 0, 1),   # Z ВЕРТИКАЛЬ - КРИТИЧНО!
                
                # ПЛОСКОСТНЫЕ ДИАГОНАЛИ
                (1, 1, 0),   # XY диагональ
                (1, -1, 0),  # XY обратная
                (1, 0, 1),   # XZ диагональ
                (1, 0, -1),  # XZ обратная
                (0, 1, 1),   # YZ диагональ
                (0, 1, -1),  # YZ обратная
                
                # ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ
                (1, 1, 1),   # Главная
                (1, 1, -1),  # Обратная 1
                (1, -1, 1),  # Обратная 2
                (-1, 1, 1),  # Обратная 3
            ]
            
            for dx, dy, dz in directions:
                count = 1  # Текущая позиция
                
                # Проверяем в положительном направлении
                nx, ny, nz = x + dx, y + dy, z + dz
                while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                       board[nz][ny][nx] == player):
                    count += 1
                    nx += dx
                    ny += dy 
                    nz += dz
                
                # Проверяем в отрицательном направлении
                nx, ny, nz = x - dx, y - dy, z - dz
                while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                       board[nz][ny][nx] == player):
                    count += 1
                    nx -= dx
                    ny -= dy
                    nz -= dz
                
                if count >= 4:
                    return True
                    
            return False
        except Exception:
            return False

    def negamax_search(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """АГРЕССИВНЫЙ Negamax поиск с итеративным углублением"""
        try:
            best_move = None
            
            # Итеративное углубление для максимальной агрессии
            for depth in range(1, 5):
                if time.time() - self.start_time > 7.0:  # Оставляем время на ход
                    break
                    
                current_best = self.negamax_root(board, player, depth)
                if current_best:
                    best_move = current_best
            
            return best_move
        except Exception:
            return None

    def negamax_root(self, board: List[List[List[int]]], player: int, depth: int) -> Optional[Tuple[int, int]]:
        """Корневой поиск Negamax"""
        try:
            best_move = None
            best_score = float('-inf')
            alpha = float('-inf')
            beta = float('+inf')
            
            # АГРЕССИВНАЯ СОРТИРОВКА ХОДОВ - сначала центр!
            moves = self.get_ordered_moves(board)
            
            for x, y in moves:
                if time.time() - self.start_time > 7.5:
                    break
                    
                drop_z = self.get_drop_z(board, x, y)
                if drop_z is None:
                    continue
                
                # Делаем ход
                board[drop_z][y][x] = player
                
                # Negamax поиск (агрессивнее чем Minimax!)
                score = -self.negamax(board, 3 - player, depth - 1, -beta, -alpha)
                
                board[drop_z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
                
                alpha = max(alpha, score)
                if alpha >= beta:
                    break  # Альфа-бета отсечение
            
            return best_move
        except Exception:
            return None

    def negamax(self, board: List[List[List[int]]], player: int, depth: int, alpha: float, beta: float) -> float:
        """Negamax алгоритм - более агрессивный чем Minimax"""
        try:
            if time.time() - self.start_time > 8.0:
                return 0
                
            if depth == 0:
                return self.evaluate_aggressive(board, player)
            
            # Проверка на мгновенную победу
            if self.has_winning_move(board, player):
                return 10000 + depth  # Бонус за быструю победу
            
            best_score = float('-inf')
            moves = self.get_ordered_moves(board)
            
            for x, y in moves:
                drop_z = self.get_drop_z(board, x, y)
                if drop_z is None:
                    continue
                
                board[drop_z][y][x] = player
                score = -self.negamax(board, 3 - player, depth - 1, -beta, -alpha)
                board[drop_z][y][x] = 0
                
                best_score = max(best_score, score)
                alpha = max(alpha, score)
                
                if alpha >= beta:
                    break
            
            return best_score
        except Exception:
            return 0

    def get_ordered_moves(self, board: List[List[List[int]]]) -> List[Tuple[int, int]]:
        """АГРЕССИВНАЯ сортировка ходов - сначала лучшие позиции"""
        moves = []
        
        # Центр - максимальный приоритет (как у salmon1)
        center_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
        for x, y in center_moves:
            if self.get_drop_z(board, x, y) is not None:
                moves.append((x, y))
        
        # Околоцентральные позиции
        near_center = [(0, 1), (1, 0), (3, 2), (2, 3), (0, 2), (2, 0), (3, 1), (1, 3)]
        for x, y in near_center:
            if self.get_drop_z(board, x, y) is not None:
                moves.append((x, y))
        
        # Углы (последний приоритет)
        corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
        for x, y in corners:
            if self.get_drop_z(board, x, y) is not None:
                moves.append((x, y))
        
        return moves

    def has_winning_move(self, board: List[List[List[int]]], player: int) -> bool:
        """Быстрая проверка на наличие выигрышного хода"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    board[drop_z][y][x] = player
                    win = self.is_winning_position(board, x, y, drop_z, player)
                    board[drop_z][y][x] = 0
                    
                    if win:
                        return True
            return False
        except Exception:
            return False

    def evaluate_aggressive(self, board: List[List[List[int]]], player: int) -> float:
        """АГРЕССИВНАЯ оценка позиции"""
        try:
            score = 0
            opponent = 3 - player
            
            # 1. АГРЕССИВНАЯ оценка линий
            score += self.evaluate_lines_aggressive(board, player, opponent)
            
            # 2. ЦЕНТРАЛЬНЫЙ КОНТРОЛЬ (критично!)
            score += self.evaluate_center_control(board, player, opponent) * 100
            
            # 3. ВЕРТИКАЛЬНОЕ ДОМИНИРОВАНИЕ  
            score += self.evaluate_height_control(board, player, opponent) * 50
            
            # 4. СВЯЗНОСТЬ (агрессивные комбо)
            score += self.evaluate_connectivity_aggressive(board, player) * 30
            
            return score
        except Exception:
            return 0

    def evaluate_lines_aggressive(self, board: List[List[List[int]]], player: int, opponent: int) -> float:
        """Агрессивная оценка линий - награждаем атаку!"""
        score = 0
        
        try:
            # Все выигрышные направления
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if board[z][y][x] != 0:
                            continue
                            
                        # Оцениваем потенциал этой позиции
                        potential = self.evaluate_position_potential(board, x, y, z, player, opponent)
                        score += potential
                        
            return score
        except Exception:
            return 0

    def evaluate_position_potential(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int, opponent: int) -> float:
        """Оценка потенциала конкретной позиции"""
        if self.get_drop_z(board, x, y) != z:
            return 0  # Недостижимая позиция
            
        score = 0
        
        # Временно ставим фишку
        board[z][y][x] = player
        
        # Проверяем все направления
        directions = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,-1,0), 
                     (1,0,1), (1,0,-1), (0,1,1), (0,1,-1),
                     (1,1,1), (1,1,-1), (1,-1,1), (-1,1,1)]
        
        for dx, dy, dz in directions:
            line_score = self.evaluate_line_direction(board, x, y, z, dx, dy, dz, player, opponent)
            score += line_score
        
        board[z][y][x] = 0  # Убираем фишку
        
        return score

    def evaluate_line_direction(self, board: List[List[List[int]]], x: int, y: int, z: int, 
                               dx: int, dy: int, dz: int, player: int, opponent: int) -> float:
        """Оценка линии в конкретном направлении"""
        our_count = 1
        their_count = 0
        empty_count = 0
        
        # Проверяем в обе стороны
        for direction in [1, -1]:
            for step in range(1, 4):
                nx = x + dx * step * direction
                ny = y + dy * step * direction
                nz = z + dz * step * direction
                
                if not (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                    break
                    
                cell = board[nz][ny][nx]
                if cell == player:
                    our_count += 1
                elif cell == opponent:
                    their_count += 1
                    break
                else:
                    empty_count += 1
                    if empty_count > 1:
                        break
        
        # АГРЕССИВНАЯ оценка
        if their_count > 0:
            return 0  # Заблокированная линия
            
        if our_count == 4:
            return 10000  # Победа!
        elif our_count == 3:
            return 500    # Отличная позиция
        elif our_count == 2:
            return 50     # Хорошая позиция
        else:
            return 5      # Базовая позиция

    def evaluate_center_control(self, board: List[List[List[int]]], player: int, opponent: int) -> float:
        """Оценка контроля центра"""
        center_positions = [(1,1), (1,2), (2,1), (2,2)]
        our_center = 0
        their_center = 0
        
        for x, y in center_positions:
            for z in range(4):
                if board[z][y][x] == player:
                    our_center += (z + 1) * 2  # Высота важна!
                elif board[z][y][x] == opponent:
                    their_center += (z + 1) * 2
                    
        return our_center - their_center

    def evaluate_height_control(self, board: List[List[List[int]]], player: int, opponent: int) -> float:
        """Оценка контроля высоты"""
        our_height = 0
        their_height = 0
        
        for x in range(4):
            for y in range(4):
                height = self.get_column_height(board, x, y)
                if height > 0:
                    top_player = board[height-1][y][x]
                    if top_player == player:
                        our_height += height
                    elif top_player == opponent:
                        their_height += height
                        
        return our_height - their_height

    def evaluate_connectivity_aggressive(self, board: List[List[List[int]]], player: int) -> float:
        """Агрессивная оценка связности"""
        connectivity = 0
        
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if board[z][y][x] == player:
                        # Считаем соседей
                        neighbors = 0
                        for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
                            nx, ny, nz = x+dx, y+dy, z+dz
                            if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                                board[nz][ny][nx] == player):
                                neighbors += 1
                        connectivity += neighbors * neighbors  # Квадратичный бонус!
                        
        return connectivity

    def get_center_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Быстрый центральный ход"""
        priorities = [(1, 1), (2, 2), (1, 2), (2, 1)]
        for x, y in priorities:
            if self.get_drop_z(board, x, y) is not None:
                return (x, y)
        return self.emergency_move(board)

    def get_drop_z(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Быстрое определение высоты падения"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except Exception:
            return None

    def get_column_height(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """Высота столбца"""
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return 4

    def emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный ход"""
        for x in range(4):
            for y in range(4):
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
        return (0, 0)