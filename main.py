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
        """3D Connect 4 ИИ с полноценным пространственным анализом"""
        
        try:
            # 1. МГНОВЕННАЯ ПОБЕДА
            win_move = self.find_winning_move(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА
            opponent = 3 - player
            block_move = self.find_winning_move(board, opponent)
            if block_move:
                return block_move
                
            # 3. СОЗДАНИЕ ПРОСТРАНСТВЕННЫХ УГРОЗ
            spatial_threat = self.find_spatial_threat(board, player)
            if spatial_threat:
                return spatial_threat
                
            # 4. БЛОКИРОВКА ПРОСТРАНСТВЕННЫХ УГРОЗ ПРОТИВНИКА  
            spatial_defense = self.find_spatial_threat(board, opponent)
            if spatial_defense:
                return spatial_defense
                
            # 5. ЛУЧШИЙ 3D ТАКТИЧЕСКИЙ ХОД
            best_move = self.find_best_3d_move(board, player)
            return best_move
            
        except Exception:
            return self.emergency_move(board)

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск мгновенной победы с ПОЛНОЙ проверкой всех 76 линий"""
        try:
            for x in range(4):
                for y in range(4):
                    z = self.get_drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    
                    if self.check_complete_win(board, x, y, z, player):
                        board[z][y][x] = 0
                        return (x, y)
                    
                    board[z][y][x] = 0
                    
            return None
        except Exception:
            return None

    def check_complete_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """ПОЛНАЯ проверка победы по всем 13 направлениям в 3D"""
        try:
            # ВСЕ 13 направлений для Connect 4 в кубе 4x4x4
            directions = [
                # 3 основных оси
                (1, 0, 0),   # X
                (0, 1, 0),   # Y  
                (0, 0, 1),   # Z (вертикаль!)
                
                # 6 плоскостных диагоналей
                (1, 1, 0),   # XY диагональ
                (1, -1, 0),  # XY обратная диагональ
                (1, 0, 1),   # XZ диагональ
                (1, 0, -1),  # XZ обратная диагональ
                (0, 1, 1),   # YZ диагональ
                (0, 1, -1),  # YZ обратная диагональ
                
                # 4 пространственных диагонали
                (1, 1, 1),   # Главная пространственная
                (1, 1, -1),  # Пространственная 2
                (1, -1, 1),  # Пространственная 3
                (-1, 1, 1),  # Пространственная 4
            ]
            
            for dx, dy, dz in directions:
                count = 1  # текущая позиция
                
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

    def find_spatial_threat(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск ПРОСТРАНСТВЕННЫХ угроз - ключ к 3D Connect 4"""
        try:
            best_move = None
            max_threats = 0
            
            for x in range(4):
                for y in range(4):
                    z = self.get_drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    # Симулируем ход
                    board[z][y][x] = player
                    
                    # Считаем все виды угроз
                    threats = self.count_all_threats(board, player)
                    
                    board[z][y][x] = 0
                    
                    if threats > max_threats:
                        max_threats = threats
                        best_move = (x, y)
            
            # Возвращаем только если создаем реальные угрозы
            return best_move if max_threats >= 2 else None
        except Exception:
            return None

    def count_all_threats(self, board: List[List[List[int]]], player: int) -> int:
        """Подсчет ВСЕХ видов угроз в 3D пространстве"""
        try:
            threat_count = 0
            
            # Проверяем все возможные выигрышные позиции
            for x in range(4):
                for y in range(4):
                    z = self.get_drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    
                    if self.check_complete_win(board, x, y, z, player):
                        threat_count += 1
                    
                    board[z][y][x] = 0
                    
            return threat_count
        except Exception:
            return 0

    def find_best_3d_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Поиск лучшего хода с полным 3D анализом"""
        try:
            best_move = None
            best_score = -9999
            opponent = 3 - player
            
            for x in range(4):
                for y in range(4):
                    z = self.get_drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    # Полная оценка 3D позиции
                    score = self.evaluate_3d_position(board, x, y, z, player, opponent)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
            
            return best_move if best_move else self.emergency_move(board)
        except Exception:
            return self.emergency_move(board)

    def evaluate_3d_position(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int, opponent: int) -> int:
        """Полная оценка 3D позиции"""
        try:
            score = 0
            
            # Симулируем ход
            board[z][y][x] = player
            
            # 1. Пространственная центральность (3D центр куба)
            center_3d_distance = abs(x - 1.5) + abs(y - 1.5) + abs(z - 1.5)
            score += int(60 - center_3d_distance * 8)
            
            # 2. Анализ всех 13 направлений
            for dx, dy, dz in [(1,0,0), (0,1,0), (0,0,1), 
                              (1,1,0), (1,-1,0), (1,0,1), (1,0,-1),
                              (0,1,1), (0,1,-1), 
                              (1,1,1), (1,1,-1), (1,-1,1), (-1,1,1)]:
                
                line_strength = self.analyze_3d_line(board, x, y, z, dx, dy, dz, player, opponent)
                score += line_strength
            
            # 3. Контроль высоты (важно в 3D)
            if z >= 2:  # Верхние уровни
                score += 15
            
            # 4. Связность в 3D (26 соседей)
            connectivity_3d = self.count_3d_neighbors(board, x, y, z, player)
            score += connectivity_3d * 8
            
            # 5. Блокировка противника
            board[z][y][x] = opponent
            opponent_threats = self.count_all_threats(board, opponent)
            score += opponent_threats * 25  # Бонус за блокировку
            
            board[z][y][x] = 0
            
            return score
        except Exception:
            return 0

    def analyze_3d_line(self, board: List[List[List[int]]], x: int, y: int, z: int, dx: int, dy: int, dz: int, player: int, opponent: int) -> int:
        """Анализ линии в 3D пространстве"""
        try:
            our_count = 1
            their_count = 0
            potential_length = 1
            
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
                        potential_length += 1
                    elif cell == opponent:
                        their_count += 1
                        break
                    else:
                        # Пустое место - можем потенциально занять
                        potential_length += 1
            
            # Оценка линии
            score = 0
            
            if their_count == 0:  # Не заблокировано
                if our_count >= 3:
                    score += 200  # Сильная угроза
                elif our_count == 2 and potential_length >= 4:
                    score += 50   # Хорошая позиция
                elif our_count == 1 and potential_length >= 4:
                    score += 10   # Потенциал
            
            return score
        except Exception:
            return 0

    def count_3d_neighbors(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Подсчет соседей в 3D (все 26 направлений)"""
        try:
            neighbors = 0
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    for dz in [-1, 0, 1]:
                        if dx == 0 and dy == 0 and dz == 0:
                            continue
                            
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                            board[nz][ny][nx] == player):
                            neighbors += 1
                            
            return neighbors
        except Exception:
            return 0

    def get_drop_z(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Определение высоты падения фишки"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except Exception:
            return None

    def emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный ход"""
        try:
            # 3D центр куба - лучшие позиции
            center_positions = [(1, 1), (2, 2), (1, 2), (2, 1)]
            
            for x, y in center_positions:
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
            
            # Любой доступный ход
            for x in range(4):
                for y in range(4):
                    if self.get_drop_z(board, x, y) is not None:
                        return (x, y)
                        
            return (0, 0)
        except Exception:
            return (0, 0)