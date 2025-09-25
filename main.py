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
        """СУПЕР-АГРЕССИВНЫЙ ИИ - стратегия salmon1 + исправления"""
        
        try:
            # 1. МГНОВЕННАЯ ПОБЕДА
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. БЛОКИРОВКА КРИТИЧЕСКИХ УГРОЗ
            opponent = 3 - player
            critical_block = self.find_critical_threats(board, opponent)
            if critical_block:
                return critical_block
                
            # 3. АГРЕССИВНАЯ АТАКА - как salmon1
            attack_move = self.aggressive_attack(board, player)
            if attack_move:
                return attack_move
                
            # 4. БЛОКИРОВКА ОБЫЧНЫХ УГРОЗ
            block_move = self.find_win(board, opponent)
            if block_move:
                return block_move
                
            # 5. СТРАТЕГИЧЕСКИЙ ХОД - копируем salmon1
            return self.salmon_strategy(board, player)
            
        except Exception:
            return self.safe_move(board)

    def find_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск мгновенной победы"""
        try:
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    
                    if self.check_win_fast(board, x, y, z, player):
                        board[z][y][x] = 0
                        return (x, y)
                    
                    board[z][y][x] = 0
                    
            return None
        except:
            return None

    def find_critical_threats(self, board: List[List[List[int]]], opponent: int) -> Optional[Tuple[int, int]]:
        """Поиск критических угроз противника (2+ угрозы одновременно)"""
        try:
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    # Симулируем ход противника
                    board[z][y][x] = opponent
                    
                    # Считаем угрозы, которые создаст противник
                    threat_count = self.count_winning_moves(board, opponent)
                    
                    board[z][y][x] = 0
                    
                    # Если создает 2+ угрозы - ОБЯЗАТЕЛЬНО блокируем!
                    if threat_count >= 2:
                        return (x, y)
                        
            return None
        except:
            return None

    def aggressive_attack(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """АГРЕССИВНАЯ АТАКА - как salmon1"""
        try:
            best_move = None
            best_score = -999
            
            # Проверяем все позиции на агрессивность
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    # Оцениваем агрессивность хода
                    score = self.evaluate_aggression(board, x, y, z, player)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
            
            # Возвращаем только если ход действительно агрессивный
            return best_move if best_score > 50 else None
        except:
            return None

    def evaluate_aggression(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Оценка агрессивности хода"""
        try:
            board[z][y][x] = player
            score = 0
            
            # 1. Сколько угроз создаем
            threats = self.count_winning_moves(board, player)
            score += threats * 100
            
            # 2. Длинные линии (агрессивно!)
            max_line = self.get_max_line_length(board, x, y, z, player)
            if max_line >= 3:
                score += max_line * 50
            elif max_line == 2:
                score += 25
            
            # 3. Центральность (как salmon1)
            center_bonus = self.get_center_bonus(x, y)
            score += center_bonus
            
            # 4. Высота дает контроль
            score += z * 10
            
            # 5. Связность с другими фишками
            neighbors = self.count_neighbors(board, x, y, z, player)
            score += neighbors * 15
            
            board[z][y][x] = 0
            return score
        except:
            return 0

    def salmon_strategy(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Стратегия salmon1 - центр и контроль"""
        try:
            # Анализируем общее состояние игры
            move_count = self.count_total_moves(board)
            
            # Дебютная стратегия
            if move_count <= 4:
                return self.opening_strategy(board)
            
            # Мидгейм - агрессивная борьба за центр
            if move_count <= 20:
                return self.midgame_strategy(board, player)
            
            # Эндгейм - точные ходы
            return self.endgame_strategy(board, player)
            
        except:
            return self.safe_move(board)

    def opening_strategy(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Дебютная стратегия - как salmon1"""
        # salmon1 всегда начинает с центра
        center_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
        
        for x, y in center_moves:
            if self.drop_z(board, x, y) is not None:
                return (x, y)
        
        return (1, 1)

    def midgame_strategy(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Мидгейм - агрессивная борьба"""
        try:
            best_move = None
            best_score = -999
            
            # Приоритетные позиции для атаки
            priority_moves = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (0, 1), (1, 0), (3, 2), (2, 3),  # Околоцентр
                (1, 3), (3, 1), (0, 2), (2, 0),  # Контроль краев
            ]
            
            for x, y in priority_moves:
                if self.drop_z(board, x, y) is None:
                    continue
                    
                score = self.evaluate_position(board, x, y, player)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move if best_move else self.safe_move(board)
        except:
            return self.safe_move(board)

    def endgame_strategy(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Эндгейм - точные ходы"""
        return self.find_best_tactical_move(board, player)

    def evaluate_position(self, board: List[List[List[int]]], x: int, y: int, player: int) -> int:
        """Полная оценка позиции"""
        try:
            z = self.drop_z(board, x, y)
            if z is None:
                return -999
                
            board[z][y][x] = player
            score = 0
            
            # 1. Потенциальные угрозы
            threats = self.count_winning_moves(board, player)
            score += threats * 200
            
            # 2. Максимальная длина линии
            max_line = self.get_max_line_length(board, x, y, z, player)
            score += max_line * 30
            
            # 3. Центральность (критично!)
            score += self.get_center_bonus(x, y)
            
            # 4. Высота
            score += z * 8
            
            # 5. Блокировка противника
            opponent = 3 - player
            board[z][y][x] = opponent
            opponent_threats = self.count_winning_moves(board, opponent)
            score += opponent_threats * 150  # Бонус за блокировку
            
            board[z][y][x] = 0
            return score
        except:
            return 0

    def find_best_tactical_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Лучший тактический ход"""
        try:
            best_move = None
            best_score = -999
            
            for x in range(4):
                for y in range(4):
                    if self.drop_z(board, x, y) is None:
                        continue
                        
                    score = self.evaluate_position(board, x, y, player)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
            
            return best_move if best_move else self.safe_move(board)
        except:
            return self.safe_move(board)

    def check_win_fast(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """БЫСТРАЯ проверка победы"""
        try:
            # Все направления для Connect 4 в 3D
            directions = [
                (1,0,0), (0,1,0), (0,0,1),                    # Оси
                (1,1,0), (1,-1,0), (1,0,1), (1,0,-1),         # Плоскостные диагонали
                (0,1,1), (0,1,-1),                            # YZ диагонали
                (1,1,1), (1,1,-1), (1,-1,1), (-1,1,1)        # Пространственные
            ]
            
            for dx, dy, dz in directions:
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

    def count_winning_moves(self, board: List[List[List[int]]], player: int) -> int:
        """Подсчет выигрышных ходов"""
        try:
            count = 0
            for x in range(4):
                for y in range(4):
                    z = self.drop_z(board, x, y)
                    if z is None:
                        continue
                        
                    board[z][y][x] = player
                    if self.check_win_fast(board, x, y, z, player):
                        count += 1
                    board[z][y][x] = 0
                    
            return count
        except:
            return 0

    def get_max_line_length(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Максимальная длина линии от позиции"""
        try:
            max_length = 1
            
            directions = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,1,1)]
            
            for dx, dy, dz in directions:
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

    def get_center_bonus(self, x: int, y: int) -> int:
        """Бонус за центральность"""
        center_distance = abs(x - 1.5) + abs(y - 1.5)
        return int(50 - center_distance * 12)

    def count_neighbors(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Подсчет соседних фишек"""
        try:
            count = 0
            for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                    board[nz][ny][nx] == player):
                    count += 1
            return count
        except:
            return 0

    def count_total_moves(self, board: List[List[List[int]]]) -> int:
        """Общее количество ходов"""
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
        """Определение высоты падения"""
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
            # Приоритет - центр
            for x, y in [(1, 1), (2, 2), (1, 2), (2, 1)]:
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