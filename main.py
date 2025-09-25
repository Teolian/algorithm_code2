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
        """ИСПРАВЛЕННЫЙ ИИ - правильная физика + агрессия"""
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА
            opponent = 3 - player
            block_move = self.find_win(board, opponent)
            if block_move:
                return block_move
                
            # 3. СОЗДАНИЕ ДВОЙНЫХ УГРОЗ
            double_threat = self.find_double_threat(board, player)
            if double_threat:
                return double_threat
                
            # 4. БЛОКИРОВКА ДВОЙНЫХ УГРОЗ ПРОТИВНИКА
            block_double = self.find_double_threat(board, opponent)
            if block_double:
                return block_double
                
            # 5. ЛУЧШИЙ СТРАТЕГИЧЕСКИЙ ХОД
            return self.find_best_move(board, player)
            
        except Exception:
            return self.emergency_move(board)

    def find_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск выигрышного хода"""
        try:
            for x in range(4):
                for y in range(4):
                    # ИСПРАВЛЕНО: правильная проверка возможности хода
                    if not self.can_place(board, x, y):
                        continue
                        
                    z = self.get_drop_z(board, x, y)
                    
                    # Симулируем ход
                    board[z][y][x] = player
                    
                    # Проверяем победу
                    if self.is_win(board, x, y, z, player):
                        board[z][y][x] = 0
                        return (x, y)
                    
                    board[z][y][x] = 0
                    
            return None
        except Exception:
            return None

    def find_double_threat(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск хода, создающего двойную угрозу"""
        try:
            for x in range(4):
                for y in range(4):
                    if not self.can_place(board, x, y):
                        continue
                        
                    z = self.get_drop_z(board, x, y)
                    
                    # Симулируем ход
                    board[z][y][x] = player
                    
                    # Считаем угрозы после хода
                    threats = self.count_threats(board, player)
                    
                    board[z][y][x] = 0
                    
                    # Если создаем 2+ угрозы - отличный ход!
                    if threats >= 2:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def count_threats(self, board: List[List[List[int]]], player: int) -> int:
        """Подсчет угроз (позиций где можем выиграть следующим ходом)"""
        try:
            threat_count = 0
            
            for x in range(4):
                for y in range(4):
                    if not self.can_place(board, x, y):
                        continue
                        
                    z = self.get_drop_z(board, x, y)
                    
                    board[z][y][x] = player
                    
                    if self.is_win(board, x, y, z, player):
                        threat_count += 1
                    
                    board[z][y][x] = 0
                    
            return threat_count
        except Exception:
            return 0

    def find_best_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Лучший стратегический ход"""
        try:
            best_move = None
            best_score = -9999
            
            # Порядок проверки - сначала лучшие позиции
            move_order = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (0, 1), (1, 0), (3, 2), (2, 3),  # Околоцентр  
                (0, 2), (2, 0), (3, 1), (1, 3),  # Вторая линия
                (0, 0), (3, 3), (0, 3), (3, 0)   # Углы
            ]
            
            for x, y in move_order:
                if not self.can_place(board, x, y):
                    continue
                    
                score = self.evaluate_move(board, x, y, player)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move if best_move else self.emergency_move(board)
        except Exception:
            return self.emergency_move(board)

    def evaluate_move(self, board: List[List[List[int]]], x: int, y: int, player: int) -> int:
        """Оценка качества хода"""
        try:
            z = self.get_drop_z(board, x, y)
            score = 0
            
            # Симулируем ход
            board[z][y][x] = player
            
            # 1. Центральные позиции лучше
            center_dist = abs(x - 1.5) + abs(y - 1.5)
            score += int(40 - center_dist * 10)
            
            # 2. Высота дает преимущество
            score += z * 5
            
            # 3. Анализ линий
            score += self.analyze_lines(board, x, y, z, player)
            
            # 4. Связность с другими фишками
            score += self.count_connections(board, x, y, z, player) * 8
            
            board[z][y][x] = 0
            
            return score
        except Exception:
            return 0

    def analyze_lines(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Анализ линий от данной позиции"""
        try:
            score = 0
            opponent = 3 - player
            
            # Все направления в 3D
            directions = [
                (1, 0, 0), (0, 1, 0), (0, 0, 1),      # Оси
                (1, 1, 0), (1, -1, 0),                # XY диагонали
                (1, 0, 1), (1, 0, -1),                # XZ диагонали  
                (0, 1, 1), (0, 1, -1),                # YZ диагонали
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)  # 3D диагонали
            ]
            
            for dx, dy, dz in directions:
                our_count = 1
                their_count = 0
                empty_count = 0
                
                # Проверяем в обе стороны от позиции
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
                            if step < 3:  # Смотрим только ближайшие пустые места
                                continue
                            break
                
                # Оценка линии
                if their_count == 0:  # Не заблокировано противником
                    if our_count >= 3:
                        score += 100
                    elif our_count == 2:
                        score += 20
                    else:
                        score += 2
                        
            return score
        except Exception:
            return 0

    def count_connections(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Подсчет соседних фишек того же игрока"""
        try:
            connections = 0
            
            # Проверяем все 6 соседних позиций
            neighbors = [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]
            
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                    board[nz][ny][nx] == player):
                    connections += 1
                    
            return connections
        except Exception:
            return 0

    def is_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """ПРАВИЛЬНАЯ проверка победы"""
        try:
            # Все возможные направления для Connect 4
            directions = [
                (1, 0, 0), (0, 1, 0), (0, 0, 1),      # Основные оси
                (1, 1, 0), (1, -1, 0),                # XY диагонали
                (1, 0, 1), (1, 0, -1),                # XZ диагонали
                (0, 1, 1), (0, 1, -1),                # YZ диагонали
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)  # 3D диагонали
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

    def can_place(self, board: List[List[List[int]]], x: int, y: int) -> bool:
        """КРИТИЧЕСКИ ВАЖНО: проверка возможности размещения фишки"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return False
                
            # Проверяем, есть ли свободное место в колонне (x, y)
            for z in range(4):
                if board[z][y][x] == 0:
                    return True
                    
            return False  # Колонна полная
        except Exception:
            return False

    def get_drop_z(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """ИСПРАВЛЕНО: правильная физика падения"""
        try:
            # ВАЖНО: фишка падает на самый нижний доступный уровень
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return 0  # Fallback (не должно произойти если can_place вернул True)
        except Exception:
            return 0

    def emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный безопасный ход"""
        try:
            # Пробуем центральные позиции
            emergency_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
            
            for x, y in emergency_moves:
                if self.can_place(board, x, y):
                    return (x, y)
            
            # Пробуем любую доступную позицию
            for x in range(4):
                for y in range(4):
                    if self.can_place(board, x, y):
                        return (x, y)
                        
            # Крайний случай
            return (0, 0)
        except Exception:
            return (0, 0)