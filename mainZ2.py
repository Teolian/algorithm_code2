from typing import List, Tuple, Optional
import time
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.board_size = 4
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Исправленный ИИ с правильной логикой Connect 4"""
        
        try:
            # 1. Проверяем, можем ли выиграть немедленно
            winning_move = self.find_immediate_win(board, player)
            if winning_move:
                return winning_move
                
            # 2. КРИТИЧНО: блокируем выигрыш противника
            opponent = 3 - player
            block_move = self.find_immediate_win(board, opponent)
            if block_move:
                return block_move
                
            # 3. Ищем лучший стратегический ход
            best_move = self.find_best_strategic_move(board, player)
            if best_move:
                return best_move
                
            # 4. Запасной ход
            return self.safe_fallback_move(board)
            
        except Exception:
            return self.emergency_move(board)

    def find_immediate_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленного выигрыша или блокировки"""
        
        for x in range(4):
            for y in range(4):
                # Находим, куда упадёт фишка
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                # Проверяем, выиграем ли мы этим ходом
                board[drop_z][y][x] = player
                if self.check_winner_simple(board, player):
                    board[drop_z][y][x] = 0  # откатываем
                    return (x, y)
                board[drop_z][y][x] = 0  # откатываем
                
        return None

    def get_drop_position(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Находит позицию Z, куда упадёт фишка в колонке (x, y)"""
        if not (0 <= x < 4 and 0 <= y < 4):
            return None
            
        for z in range(4):  # начинаем снизу (z=0)
            if board[z][y][x] == 0:
                return z
        return None  # колонка полная

    def check_winner_simple(self, board: List[List[List[int]]], player: int) -> bool:
        """Простая и надёжная проверка победителя"""
        
        # 1. ВЕРТИКАЛЬНЫЕ ЛИНИИ (самые важные в Connect 4!)
        for x in range(4):
            for y in range(4):
                count = 0
                for z in range(4):
                    if board[z][y][x] == player:
                        count += 1
                    else:
                        count = 0
                    if count >= 4:
                        return True
        
        # 2. ГОРИЗОНТАЛЬНЫЕ ЛИНИИ в плоскости XY
        for z in range(4):
            # По оси X
            for y in range(4):
                count = 0
                for x in range(4):
                    if board[z][y][x] == player:
                        count += 1
                    else:
                        count = 0
                    if count >= 4:
                        return True
            
            # По оси Y  
            for x in range(4):
                count = 0
                for y in range(4):
                    if board[z][y][x] == player:
                        count += 1
                    else:
                        count = 0
                    if count >= 4:
                        return True
        
        # 3. ДИАГОНАЛИ в плоскости XY
        for z in range(4):
            # Главная диагональ
            if all(board[z][i][i] == player for i in range(4)):
                return True
            # Побочная диагональ  
            if all(board[z][i][3-i] == player for i in range(4)):
                return True
        
        # 4. ДИАГОНАЛИ в плоскости XZ
        for y in range(4):
            # Главная диагональ XZ
            if all(board[i][y][i] == player for i in range(4)):
                return True
            # Побочная диагональ XZ
            if all(board[i][y][3-i] == player for i in range(4)):
                return True
        
        # 5. ДИАГОНАЛИ в плоскости YZ
        for x in range(4):
            # Главная диагональ YZ
            if all(board[i][i][x] == player for i in range(4)):
                return True
            # Побочная диагональ YZ
            if all(board[i][3-i][x] == player for i in range(4)):
                return True
        
        # 6. ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ
        # Главная диагональ куба
        if all(board[i][i][i] == player for i in range(4)):
            return True
        # Другие пространственные диагонали
        if all(board[i][i][3-i] == player for i in range(4)):
            return True
        if all(board[i][3-i][i] == player for i in range(4)):
            return True
        if all(board[3-i][i][i] == player for i in range(4)):
            return True
        
        return False

    def find_best_strategic_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск лучшего стратегического хода"""
        
        best_score = float('-inf')
        best_move = None
        opponent = 3 - player
        
        # Оцениваем все доступные ходы
        for x in range(4):
            for y in range(4):
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                
                # Делаем пробный ход
                board[drop_z][y][x] = player
                
                # Оцениваем позицию
                score = self.evaluate_position_advanced(board, player, opponent)
                
                # Добавляем бонусы
                score += self.get_position_bonus(x, y, drop_z)
                
                board[drop_z][y][x] = 0  # откатываем
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
        
        return best_move

    def evaluate_position_advanced(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Продвинутая оценка позиции"""
        score = 0
        
        # Оцениваем все возможные линии из 4 позиций
        all_lines = self.get_all_possible_lines()
        
        for line in all_lines:
            our_count = 0
            their_count = 0
            empty_count = 0
            
            for x, y, z in line:
                if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                    break
                
                cell = board[z][y][x]
                if cell == player:
                    our_count += 1
                elif cell == opponent:
                    their_count += 1
                else:
                    empty_count += 1
            else:  # если цикл завершился без break
                # Оцениваем линию только если она не заблокирована
                if our_count > 0 and their_count > 0:
                    continue  # заблокированная линия
                
                # Система очков
                if our_count == 3 and empty_count == 1:
                    # Проверяем, реально ли мы можем сделать выигрышный ход
                    if self.can_complete_line(board, line, player):
                        score += 1000  # очень сильная позиция
                elif their_count == 3 and empty_count == 1:
                    if self.can_complete_line(board, line, opponent):
                        score -= 1000  # нужно блокировать
                elif our_count == 2 and empty_count == 2:
                    score += 100
                elif their_count == 2 and empty_count == 2:
                    score -= 100
                elif our_count == 1 and empty_count == 3:
                    score += 10
                elif their_count == 1 and empty_count == 3:
                    score -= 10
        
        return score

    def can_complete_line(self, board: List[List[List[int]]], line: List[Tuple[int, int, int]], player: int) -> bool:
        """Проверяет, можем ли мы реально завершить линию (учитывает гравитацию)"""
        for x, y, z in line:
            if board[z][y][x] == 0:  # пустая позиция
                # Проверяем, можем ли мы туда реально поставить фишку
                expected_z = self.get_drop_position(board, x, y)
                if expected_z == z:
                    return True
        return False

    def get_all_possible_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Получает все возможные выигрышные линии"""
        lines = []
        
        # 1. Вертикальные
        for x in range(4):
            for y in range(4):
                lines.append([(x, y, z) for z in range(4)])
        
        # 2. Горизонтальные в плоскости XY
        for z in range(4):
            # По X
            for y in range(4):
                for x in range(1):  # начинаем с x=0, берём 4 подряд
                    lines.append([(x+i, y, z) for i in range(4)])
            # По Y
            for x in range(4):
                for y in range(1):  # начинаем с y=0, берём 4 подряд
                    lines.append([(x, y+i, z) for i in range(4)])
        
        # 3. Диагонали в плоскости XY
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        
        # 4. Диагонали в плоскости XZ
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        
        # 5. Диагонали в плоскости YZ
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        
        # 6. Пространственные диагонали
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3-i) for i in range(4)])
        lines.append([(i, 3-i, i) for i in range(4)])
        lines.append([(3-i, i, i) for i in range(4)])
        
        return lines

    def get_position_bonus(self, x: int, y: int, z: int) -> int:
        """Бонусы за позицию"""
        bonus = 0
        
        # Центр важнее краёв
        center_distance = abs(x - 1.5) + abs(y - 1.5)
        bonus += int((3 - center_distance) * 10)
        
        # Более высокие позиции могут быть полезны для блокировки
        bonus += z * 2
        
        return bonus

    def safe_fallback_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Безопасный запасной ход"""
        # Приоритет центральным позициям
        preferred_moves = [
            (1, 1), (2, 2), (1, 2), (2, 1),  # центр
            (1, 0), (2, 0), (0, 1), (0, 2),  # околоцентральные
            (3, 1), (3, 2), (1, 3), (2, 3),
            (0, 0), (3, 0), (0, 3), (3, 3)   # углы
        ]
        
        for x, y in preferred_moves:
            if self.get_drop_position(board, x, y) is not None:
                return (x, y)
        
        # Любой доступный ход
        for x in range(4):
            for y in range(4):
                if self.get_drop_position(board, x, y) is not None:
                    return (x, y)
        
        return (0, 0)

    def emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный ход при ошибках"""
        return (1, 1)