from typing import List, Tuple, Optional
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        pass
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Быстрый и агрессивный ИИ с правильной защитой"""
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА - максимальный приоритет
            win_move = self.find_winning_move(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА (исправлена для вертикали!)
            opponent = 3 - player
            block_move = self.find_winning_move(board, opponent)
            if block_move:
                return block_move
                
            # 3. СОЗДАНИЕ ДВОЙНЫХ УГРОЗ - агрессия!
            threat_move = self.find_double_threat(board, player)
            if threat_move:
                return threat_move
                
            # 4. БЛОКИРОВКА ДВОЙНЫХ УГРОЗ ПРОТИВНИКА
            counter_threat = self.find_double_threat(board, opponent)
            if counter_threat:
                return counter_threat
                
            # 5. БЫСТРЫЙ ТАКТИЧЕСКИЙ ХОД (упрощённый)
            tactical_move = self.find_fast_tactical_move(board, player)
            if tactical_move:
                return tactical_move
                
            # 6. СТРАТЕГИЧЕСКИЙ ХОД - контроль центра
            strategic_move = self.find_strategic_move(board, player)
            return strategic_move
            
        except Exception:
            return self.emergency_safe_move(board)

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Быстрый поиск победы - проверяем только реальные позиции"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Пробуем ход
                    board[drop_z][y][x] = player
                    
                    # Быстрая проверка победы от этой позиции
                    is_win = self.check_fast_win(board, x, y, drop_z, player)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if is_win:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def check_fast_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """БЫСТРАЯ проверка победы - только основные направления"""
        try:
            # Только самые важные направления для скорости
            directions = [
                # Основные оси
                [(1, 0, 0), (-1, 0, 0)],   # X
                [(0, 1, 0), (0, -1, 0)],   # Y  
                [(0, 0, 1), (0, 0, -1)],   # Z (вертикаль!)
                
                # Главные диагонали
                [(1, 1, 0), (-1, -1, 0)],   # XY
                [(1, -1, 0), (-1, 1, 0)],   # XY обратная
                [(1, 0, 1), (-1, 0, -1)],   # XZ
                [(0, 1, 1), (0, -1, -1)],   # YZ
                
                # Пространственные (самые мощные)
                [(1, 1, 1), (-1, -1, -1)],  # Главная
                [(1, 1, -1), (-1, -1, 1)],  # Обратная 1
                [(1, -1, 1), (-1, 1, -1)],  # Обратная 2
                [(-1, 1, 1), (1, -1, -1)],  # Обратная 3
            ]
            
            for dir_pair in directions:
                count = 1  # текущая позиция
                
                # Проверяем в обе стороны
                for dx, dy, dz in dir_pair:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                           board[nz][ny][nx] == player):
                        count += 1
                        nx += dx
                        ny += dy
                        nz += dz
                
                if count >= 4:
                    return True
                    
            return False
        except Exception:
            return False

    def find_double_threat(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Быстрый поиск двойных угроз"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Пробуем ход
                    board[drop_z][y][x] = player
                    
                    # Быстро считаем угрозы
                    threat_count = self.count_fast_threats(board, player)
                    
                    board[drop_z][y][x] = 0
                    
                    if threat_count >= 2:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def count_fast_threats(self, board: List[List[List[int]]], player: int) -> int:
        """БЫСТРЫЙ подсчёт угроз - только критические линии"""
        threats = 0
        
        try:
            # Проверяем только самые важные линии для скорости
            critical_lines = self.get_critical_lines()
            
            for line in critical_lines:
                our_count = 0
                empty_pos = None
                blocked = False
                
                for x, y, z in line:
                    if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                        blocked = True
                        break
                        
                    cell = board[z][y][x]
                    if cell == player:
                        our_count += 1
                    elif cell == 0:
                        if empty_pos is None:
                            empty_pos = (x, y, z)
                        else:
                            # Больше одного пустого места - не угроза
                            empty_pos = "multiple"
                    else:
                        blocked = True
                        break
                
                # Быстрая проверка угрозы
                if (not blocked and our_count == 3 and empty_pos and 
                    empty_pos != "multiple"):
                    ex, ey, ez = empty_pos
                    expected_z = self.get_drop_z(board, ex, ey)
                    if expected_z is not None and expected_z == ez:
                        threats += 1
                        
            return threats
        except Exception:
            return 0

    def get_critical_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Только критические линии для быстрого анализа"""
        lines = []
        
        try:
            # 1. Все вертикальные (16) - КРИТИЧНО!
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # 2. Центральные горизонтальные
            for z in range(4):
                # Центральные строки
                for y in [1, 2]:
                    lines.append([(x, y, z) for x in range(4)])
                # Центральные столбцы  
                for x in [1, 2]:
                    lines.append([(x, y, z) for y in range(4)])
            
            # 3. Главные диагонали в каждой плоскости
            for z in range(4):
                lines.append([(i, i, z) for i in range(4)])
                lines.append([(i, 3-i, z) for i in range(4)])
            
            # 4. Пространственные диагонали (самые мощные!)
            lines.append([(i, i, i) for i in range(4)])
            lines.append([(i, i, 3-i) for i in range(4)])
            lines.append([(i, 3-i, i) for i in range(4)])
            lines.append([(3-i, i, i) for i in range(4)])
            
        except Exception:
            pass
            
        return lines

    def find_fast_tactical_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Быстрый тактический анализ - только лучшие позиции"""
        try:
            best_move = None
            best_score = -9999
            opponent = 3 - player
            
            # Проверяем только перспективные позиции
            priority_positions = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (0, 1), (1, 0), (3, 2), (2, 3),  # Околоцентр
            ]
            
            for x, y in priority_positions:
                drop_z = self.get_drop_z(board, x, y)
                if drop_z is None:
                    continue
                    
                # Делаем ход
                board[drop_z][y][x] = player
                
                # Быстрая оценка
                score = self.evaluate_fast(board, player, opponent, x, y, drop_z)
                
                board[drop_z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            # Если не нашли среди приоритетных - берём любую
            if best_move is None:
                for x in range(4):
                    for y in range(4):
                        if self.get_drop_z(board, x, y) is not None:
                            return (x, y)
                        
            return best_move
        except Exception:
            return None

    def evaluate_fast(self, board: List[List[List[int]]], player: int, opponent: int, x: int, y: int, z: int) -> int:
        """Быстрая оценка - только главные факторы"""
        score = 0
        
        try:
            # 1. Позиционные бонусы (быстро)
            center_bonus = 30 - int((abs(x - 1.5) + abs(y - 1.5)) * 8)
            height_bonus = z * 5
            score += center_bonus + height_bonus
            
            # 2. Простая проверка линий (только критические)
            lines_score = self.evaluate_lines_fast(board, player, opponent, x, y, z)
            score += lines_score
            
            # 3. Связность (быстрая проверка соседей)
            neighbors = 0
            for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                    board[nz][ny][nx] == player):
                    neighbors += 1
            score += neighbors * 15
            
            return score
        except Exception:
            return 0

    def evaluate_lines_fast(self, board: List[List[List[int]]], player: int, opponent: int, x: int, y: int, z: int) -> int:
        """Быстрая оценка линий от конкретной позиции"""
        score = 0
        
        try:
            directions = [
                (1, 0, 0), (0, 1, 0), (0, 0, 1),     # Оси
                (1, 1, 0), (1, -1, 0),                # Диагонали XY
                (1, 1, 1), (1, 1, -1)                 # Пространственные
            ]
            
            for dx, dy, dz in directions:
                # Считаем в обе стороны от позиции
                our_count = 1  # текущая позиция
                their_count = 0
                
                # Положительное направление
                for step in range(1, 4):
                    nx, ny, nz = x + dx*step, y + dy*step, z + dz*step
                    if not (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                        break
                    if board[nz][ny][nx] == player:
                        our_count += 1
                    elif board[nz][ny][nx] == opponent:
                        their_count += 1
                        break
                    else:
                        break
                
                # Отрицательное направление
                for step in range(1, 4):
                    nx, ny, nz = x - dx*step, y - dy*step, z - dz*step
                    if not (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                        break
                    if board[nz][ny][nx] == player:
                        our_count += 1
                    elif board[nz][ny][nx] == opponent:
                        their_count += 1
                        break
                    else:
                        break
                
                # Оценка линии
                if their_count == 0:  # Не заблокировано
                    if our_count >= 3:
                        score += 500
                    elif our_count == 2:
                        score += 50
                    else:
                        score += 5
                        
            return score
        except Exception:
            return 0

    def find_strategic_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Быстрый стратегический ход"""
        try:
            # Дебютная книга (упрощённая)
            total_moves = sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)
            
            if total_moves <= 1:
                return (1, 1)  # Всегда центр на первом ходу
            
            # Быстрые приоритеты
            priorities = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (0, 1), (1, 0), (3, 2), (2, 3),  # Околоцентр
                (0, 2), (2, 0), (3, 1), (1, 3),  # Второй круг
                (0, 0), (3, 3), (0, 3), (3, 0)   # Углы
            ]
            
            for x, y in priorities:
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
                    
            return self.emergency_safe_move(board)
        except Exception:
            return self.emergency_safe_move(board)

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

    def emergency_safe_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный ход"""
        try:
            # Быстрые безопасные ходы
            safe_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
            
            for x, y in safe_moves:
                if 0 <= x < 4 and 0 <= y < 4 and self.get_drop_z(board, x, y) is not None:
                    return (x, y)
            
            # Любой валидный ход
            for x in range(4):
                for y in range(4):
                    if self.get_drop_z(board, x, y) is not None:
                        return (x, y)
                        
            return (0, 0)
        except Exception:
            return (0, 0)