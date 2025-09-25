from typing import List, Tuple, Optional
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Простой, быстрый и абсолютно стабильный ИИ"""
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. БЛОКИРОВКА ПРОТИВНИКА  
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
            return self.best_strategic_move(board, player)
            
        except:
            # ЭКСТРЕННЫЙ БЕЗОПАСНЫЙ ХОД
            return self.emergency_move()

    def find_win(self, board, player):
        """Поиск выигрышного хода"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.drop_pos(board, x, y)
                    if drop_z is not None:
                        # Пробуем ход
                        board[drop_z][y][x] = player
                        win = self.check_win_simple(board, player)
                        board[drop_z][y][x] = 0  # откат
                        if win:
                            return (x, y)
            return None
        except:
            return None

    def find_double_threat(self, board, player):
        """Поиск хода, создающего две угрозы"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.drop_pos(board, x, y)
                    if drop_z is not None:
                        # Пробуем ход
                        board[drop_z][y][x] = player
                        threats = self.count_threats(board, player)
                        board[drop_z][y][x] = 0  # откат
                        
                        if threats >= 2:  # Двойная угроза!
                            return (x, y)
            return None
        except:
            return None

    def count_threats(self, board, player):
        """Подсчёт угроз (3 в ряд + возможность поставить 4-ю)"""
        try:
            threats = 0
            
            # Вертикальные угрозы
            for x in range(4):
                for y in range(4):
                    count = 0
                    empty_z = -1
                    for z in range(4):
                        if board[z][y][x] == player:
                            count += 1
                        elif board[z][y][x] == 0 and empty_z == -1:
                            empty_z = z
                    
                    if count == 3 and empty_z != -1:
                        # Проверяем, можем ли поставить в empty_z
                        if empty_z == 0 or board[empty_z-1][y][x] != 0:
                            threats += 1
            
            # Горизонтальные угрозы X
            for z in range(4):
                for y in range(4):
                    for start_x in range(1):  # только 0-3
                        count = 0
                        empty_pos = []
                        for i in range(4):
                            cell = board[z][y][start_x + i]
                            if cell == player:
                                count += 1
                            elif cell == 0:
                                empty_pos.append((start_x + i, y, z))
                        
                        if count == 3 and len(empty_pos) == 1:
                            ex, ey, ez = empty_pos[0]
                            if self.drop_pos(board, ex, ey) == ez:
                                threats += 1
            
            # Горизонтальные угрозы Y
            for z in range(4):
                for x in range(4):
                    for start_y in range(1):  # только 0-3
                        count = 0
                        empty_pos = []
                        for i in range(4):
                            cell = board[z][start_y + i][x]
                            if cell == player:
                                count += 1
                            elif cell == 0:
                                empty_pos.append((x, start_y + i, z))
                        
                        if count == 3 and len(empty_pos) == 1:
                            ex, ey, ez = empty_pos[0]
                            if self.drop_pos(board, ex, ey) == ez:
                                threats += 1
            
            return threats
        except:
            return 0

    def best_strategic_move(self, board, player):
        """Лучший стратегический ход"""
        try:
            best_score = -999
            best_move = None
            
            # Оцениваем все доступные ходы
            for x in range(4):
                for y in range(4):
                    drop_z = self.drop_pos(board, x, y)
                    if drop_z is not None:
                        score = self.evaluate_move(board, x, y, drop_z, player)
                        if score > best_score:
                            best_score = score
                            best_move = (x, y)
            
            return best_move if best_move else (1, 1)
        except:
            return (1, 1)

    def evaluate_move(self, board, x, y, z, player):
        """Оценка хода"""
        try:
            score = 0
            
            # Приоритет центру
            center_score = 20 - abs(x - 1.5) * 5 - abs(y - 1.5) * 5
            score += center_score
            
            # Высота важна
            score += z * 3
            
            # Пробуем ход и оцениваем позицию
            board[z][y][x] = player
            
            # Считаем наши угрозы после хода
            our_threats = self.count_simple_threats(board, player)
            opponent_threats = self.count_simple_threats(board, 3 - player)
            
            score += our_threats * 100
            score -= opponent_threats * 90
            
            board[z][y][x] = 0  # откат
            
            return score
        except:
            return 0

    def count_simple_threats(self, board, player):
        """Упрощённый подсчёт угроз"""
        try:
            threats = 0
            
            # Только вертикальные (самые важные)
            for x in range(4):
                for y in range(4):
                    count = 0
                    for z in range(4):
                        if board[z][y][x] == player:
                            count += 1
                    if count == 3:
                        # Проверяем, есть ли место для 4-й
                        for z in range(4):
                            if board[z][y][x] == 0:
                                threats += 1
                                break
            
            return threats
        except:
            return 0

    def check_win_simple(self, board, player):
        """Простая проверка победы"""
        try:
            # Вертикальные
            for x in range(4):
                for y in range(4):
                    if all(board[z][y][x] == player for z in range(4)):
                        return True
            
            # Горизонтальные X
            for z in range(4):
                for y in range(4):
                    if all(board[z][y][x] == player for x in range(4)):
                        return True
            
            # Горизонтальные Y
            for z in range(4):
                for x in range(4):
                    if all(board[z][y][x] == player for y in range(4)):
                        return True
            
            # Диагонали XY
            for z in range(4):
                if all(board[z][i][i] == player for i in range(4)):
                    return True
                if all(board[z][i][3-i] == player for i in range(4)):
                    return True
            
            # Диагонали XZ  
            for y in range(4):
                if all(board[i][y][i] == player for i in range(4)):
                    return True
                if all(board[i][y][3-i] == player for i in range(4)):
                    return True
            
            # Диагонали YZ
            for x in range(4):
                if all(board[i][i][x] == player for i in range(4)):
                    return True
                if all(board[i][3-i][x] == player for i in range(4)):
                    return True
            
            # 3D диагонали
            if all(board[i][i][i] == player for i in range(4)):
                return True
            if all(board[i][i][3-i] == player for i in range(4)):
                return True
            if all(board[i][3-i][i] == player for i in range(4)):
                return True
            if all(board[3-i][i][i] == player for i in range(4)):
                return True
            
            return False
        except:
            return False

    def drop_pos(self, board, x, y):
        """Позиция падения фишки"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except:
            return None

    def emergency_move(self):
        """Экстренный ход"""
        return (1, 1)