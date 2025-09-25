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
        """МОЛНИЕНОСНО БЫСТРЫЙ ИИ - побеждает скоростью"""
        
        try:
            # 1. МГНОВЕННАЯ ПОБЕДА
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. МГНОВЕННАЯ БЛОКИРОВКА
            opponent = 3 - player
            block_move = self.find_win(board, opponent)
            if block_move:
                return block_move
                
            # 3. СУПЕР БЫСТРАЯ АТАКА
            attack_move = self.lightning_attack(board, player)
            return attack_move
            
        except Exception:
            return self.emergency_move(board)

    def find_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Молниеносный поиск победы"""
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

    def lightning_attack(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """МОЛНИЕНОСНАЯ АТАКА - максимально быстрый выбор"""
        try:
            move_count = self.count_moves(board)
            
            # ДЕБЮТ - ВСЕГДА АГРЕССИВНЫЙ ЦЕНТР
            if move_count <= 4:
                return self.lightning_opening()
            
            # БЫСТРЫЙ ПОИСК ЛУЧШЕГО ХОДА
            best_move = None
            best_score = -999
            
            # Проверяем только лучшие позиции для скорости
            priority_moves = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (1, 0), (0, 1), (3, 2), (2, 3),  # Атака
                (1, 3), (3, 1), (0, 2), (2, 0)   # Контроль
            ]
            
            for x, y in priority_moves:
                z = self.drop_z(board, x, y)
                if z is None:
                    continue
                    
                score = self.fast_score(board, x, y, z, player)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move if best_move else self.emergency_move(board)
        except:
            return self.emergency_move(board)

    def lightning_opening(self) -> Tuple[int, int]:
        """МОЛНИЕНОСНЫЙ ДЕБЮТ - всегда одно и то же для скорости"""
        # Всегда агрессивный центр - без раздумий!
        return (1, 1)

    def fast_score(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """СВЕРХБЫСТРАЯ оценка - только главное"""
        try:
            score = 0
            
            # Центр = сила
            center_dist = abs(x - 1.5) + abs(y - 1.5)
            score += int(30 - center_dist * 10)
            
            # Высота = контроль
            score += z * 6
            
            # Быстрая проверка угроз
            board[z][y][x] = player
            
            # Считаем длинные линии БЫСТРО
            max_line = self.quick_line_check(board, x, y, z, player)
            if max_line >= 3:
                score += 100
            elif max_line >= 2:
                score += 30
            
            board[z][y][x] = 0
            
            return score
        except:
            return 0

    def quick_line_check(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """БЫСТРАЯ проверка линий - только основные направления"""
        try:
            max_length = 1
            
            # Только критичные направления для скорости
            dirs = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,1,1)]
            
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
                
                max_length = max(max_length, count)
            
            return max_length
        except:
            return 1

    def check_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """БЫСТРАЯ проверка победы"""
        try:
            # Все направления для Connect 4
            directions = [
                (1, 0, 0), (0, 1, 0), (0, 0, 1),      # Оси
                (1, 1, 0), (1, -1, 0),                # XY диагонали
                (1, 0, 1), (1, 0, -1),                # XZ диагонали
                (0, 1, 1), (0, 1, -1),                # YZ диагонали
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)  # 3D диагонали
            ]
            
            for dx, dy, dz in directions:
                count = 1
                
                # Проверяем в обе стороны
                for direction in [1, -1]:
                    nx, ny, nz = x + dx * direction, y + dy * direction, z + dz * direction
                    while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                           board[nz][ny][nx] == player):
                        count += 1
                        nx += dx * direction
                        ny += dy * direction
                        nz += dz * direction
                
                if count >= 4:
                    return True
                    
            return False
        except:
            return False

    def count_moves(self, board: List[List[List[int]]]) -> int:
        """БЫСТРЫЙ подсчет ходов"""
        try:
            count = 0
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if board[z][y][x] != 0:
                            count += 1
            return count
        except:
            return 0

    def drop_z(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """БЫСТРОЕ определение высоты падения"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except:
            return None

    def emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """МГНОВЕННЫЙ экстренный ход"""
        try:
            # Быстрые безопасные позиции
            safe = [(1, 1), (2, 2), (1, 2), (2, 1)]
            
            for x, y in safe:
                if self.drop_z(board, x, y) is not None:
                    return (x, y)
            
            # Любой доступный ход
            for x in range(4):
                for y in range(4):
                    if self.drop_z(board, x, y) is not None:
                        return (x, y)
                        
            return (0, 0)
        except:
            return (0, 0)