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
        """Простой, быстрый и агрессивный ИИ как salmon1 + исправленная защита"""
        
        try:
            # 1. МГНОВЕННАЯ ПОБЕДА
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. МГНОВЕННАЯ БЛОКИРОВКА (исправлена!)
            opponent = 3 - player
            block_move = self.find_win(board, opponent)
            if block_move:
                return block_move
                
            # 3. СОЗДАТЬ УГРОЗУ
            threat_move = self.create_threat(board, player)
            if threat_move:
                return threat_move
                
            # 4. БЛОКИРОВАТЬ УГРОЗУ ПРОТИВНИКА
            counter_move = self.create_threat(board, opponent)
            if counter_move:
                return counter_move
                
            # 5. ЛУЧШАЯ ПОЗИЦИЯ (как salmon1)
            return self.best_position(board, player)
            
        except Exception:
            return self.safe_move(board)

    def find_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Быстрый поиск победы"""
        try:
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    
                    if self.check_win(board, x, y, z, player):
                        board[z][y][x] = 0
                        return (x, y)
                    
                    board[z][y][x] = 0
                    
            return None
        except:
            return None

    def check_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """ИСПРАВЛЕННАЯ проверка победы - включая вертикаль!"""
        try:
            # ВСЕ направления Connect 4
            dirs = [
                (1,0,0), (0,1,0), (0,0,1),      # Оси X,Y,Z - ВКЛЮЧАЯ ВЕРТИКАЛЬ!
                (1,1,0), (1,-1,0),              # Диагонали XY
                (1,0,1), (1,0,-1),              # Диагонали XZ  
                (0,1,1), (0,1,-1),              # Диагонали YZ
                (1,1,1), (1,1,-1), (1,-1,1), (-1,1,1)  # Пространственные
            ]
            
            for dx, dy, dz in dirs:
                count = 1
                
                # Положительное направление
                nx, ny, nz = x + dx, y + dy, z + dz
                while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                       board[nz][ny][nx] == player):
                    count += 1
                    nx += dx
                    ny += dy
                    nz += dz
                
                # Отрицательное направление
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
        except:
            return False

    def create_threat(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Создать угрозу (3 в ряд)"""
        try:
            best_move = None
            best_threats = 0
            
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    threats = self.count_threats(board, player)
                    board[z][y][x] = 0
                    
                    if threats > best_threats:
                        best_threats = threats
                        best_move = (x, y)
            
            return best_move if best_threats > 0 else None
        except:
            return None

    def count_threats(self, board: List[List[List[int]]], player: int) -> int:
        """Быстрый подсчет угроз"""
        threats = 0
        
        try:
            # Проверяем все позиции
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    
                    if self.check_win(board, x, y, z, player):
                        threats += 1
                    
                    board[z][y][x] = 0
                    
            return threats
        except:
            return 0

    def best_position(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Лучшая позиция - как salmon1"""
        try:
            # СТРАТЕГИЯ SALMON1: сначала центр, потом оценка
            moves = self.get_move_priority()
            
            best_move = None
            best_score = -999
            
            for x, y in moves:
                if self.drop_z(board, x, y) is None:
                    continue
                    
                score = self.evaluate_move(board, x, y, player)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move if best_move else (1, 1)
        except:
            return (1, 1)

    def get_move_priority(self) -> List[Tuple[int, int]]:
        """Приоритет ходов как у salmon1"""
        return [
            # Центр (высший приоритет)
            (1, 1), (2, 2), (1, 2), (2, 1),
            # Околоцентр
            (0, 1), (1, 0), (3, 2), (2, 3),
            (0, 2), (2, 0), (3, 1), (1, 3),
            # Углы
            (0, 0), (3, 3), (0, 3), (3, 0)
        ]

    def evaluate_move(self, board: List[List[List[int]]], x: int, y: int, player: int) -> int:
        """Простая оценка хода"""
        try:
            z = self.drop_z(board, x, y)
            if z is None:
                return -999
                
            score = 0
            
            # 1. Центр лучше
            center_dist = abs(x - 1.5) + abs(y - 1.5)
            score += int(20 - center_dist * 5)
            
            # 2. Высота дает преимущество
            score += z * 3
            
            # 3. Проверяем потенциальные линии
            board[z][y][x] = player
            
            # Считаем длинные линии
            for dx, dy, dz in [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,1,1)]:
                line_length = self.get_line_length(board, x, y, z, dx, dy, dz, player)
                if line_length >= 2:
                    score += line_length * 10
                    
            board[z][y][x] = 0
            
            return score
        except:
            return 0

    def get_line_length(self, board: List[List[List[int]]], x: int, y: int, z: int, 
                       dx: int, dy: int, dz: int, player: int) -> int:
        """Длина линии в направлении"""
        try:
            count = 1
            
            # Положительное направление
            nx, ny, nz = x + dx, y + dy, z + dz
            while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                   board[nz][ny][nx] == player):
                count += 1
                nx += dx
                ny += dy
                nz += dz
            
            # Отрицательное направление
            nx, ny, nz = x - dx, y - dy, z - dz
            while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                   board[nz][ny][nx] == player):
                count += 1
                nx -= dx
                ny -= dy
                nz -= dz
            
            return count
        except:
            return 1

    def drop_z(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Где упадет фишка"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except:
            return None

    def safe_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Безопасный ход"""
        try:
            safe_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
            for x, y in safe_moves:
                if self.drop_z(board, x, y) is not None:
                    return (x, y)
            
            for x in range(4):
                for y in range(4):
                    if self.drop_z(board, x, y) is not None:
                        return (x, y)
                        
            return (0, 0)
        except:
            return (0, 0)