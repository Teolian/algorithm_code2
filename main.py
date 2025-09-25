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
        """Простой, быстрый и надёжный ИИ без сложной рекурсии"""
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА - максимальный приоритет
            win_move = self.find_winning_move(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА
            opponent = 3 - player
            block_move = self.find_winning_move(board, opponent)
            if block_move:
                return block_move
                
            # 3. СОЗДАНИЕ УГРОЗ - ищем ходы, создающие две угрозы сразу
            threat_move = self.find_double_threat(board, player)
            if threat_move:
                return threat_move
                
            # 4. БЛОКИРОВКА УГРОЗ ПРОТИВНИКА
            counter_threat = self.find_double_threat(board, opponent)
            if counter_threat:
                return counter_threat
                
            # 5. ТАКТИЧЕСКИЙ ХОД - простой анализ на 2 хода вперёд
            tactical_move = self.find_tactical_move(board, player)
            if tactical_move:
                return tactical_move
                
            # 6. СТРАТЕГИЧЕСКИЙ ХОД - контроль центра и высоты
            strategic_move = self.find_strategic_move(board, player)
            return strategic_move
            
        except Exception:
            # ЭКСТРЕННЫЙ БЕЗОПАСНЫЙ ХОД
            return self.emergency_safe_move(board)

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленного выигрыша"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Пробуем ход
                    board[drop_z][y][x] = player
                    
                    # Проверяем победу простым способом
                    is_win = self.check_simple_win(board, x, y, drop_z, player)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if is_win:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def find_double_threat(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск хода, создающего две угрозы одновременно"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Пробуем ход
                    board[drop_z][y][x] = player
                    
                    # Считаем угрозы после этого хода
                    threat_count = self.count_immediate_threats(board, player)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    # Если создаём 2+ угрозы - отличный ход!
                    if threat_count >= 2:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def count_immediate_threats(self, board: List[List[List[int]]], player: int) -> int:
        """Подсчёт немедленных угроз (3 в ряд + возможность поставить 4-ю)"""
        threats = 0
        
        try:
            # Проверяем все возможные линии из 4 позиций
            lines = self.get_winning_lines()
            
            for line in lines:
                our_count = 0
                empty_positions = []
                blocked = False
                
                # Анализируем линию
                for x, y, z in line:
                    if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                        blocked = True
                        break
                        
                    cell = board[z][y][x]
                    if cell == player:
                        our_count += 1
                    elif cell == 0:
                        empty_positions.append((x, y, z))
                    else:  # противник
                        blocked = True
                        break
                
                # Угроза = 3 наших + 1 пустое место, которое мы можем заполнить
                if not blocked and our_count == 3 and len(empty_positions) == 1:
                    empty_x, empty_y, empty_z = empty_positions[0]
                    expected_z = self.get_drop_z(board, empty_x, empty_y)
                    if expected_z == empty_z:
                        threats += 1
                        
            return threats
        except Exception:
            return 0

    def find_tactical_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Простой тактический анализ - ищем лучший ход из доступных"""
        try:
            best_move = None
            best_score = -9999
            opponent = 3 - player
            
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Делаем ход
                    board[drop_z][y][x] = player
                    
                    # Простая оценка позиции
                    score = self.evaluate_simple(board, player, opponent)
                    
                    # Добавляем позиционные бонусы
                    score += self.get_position_value(x, y, drop_z)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                        
            return best_move
        except Exception:
            return None

    def evaluate_simple(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Простая оценка позиции без сложных вычислений"""
        score = 0
        
        try:
            lines = self.get_winning_lines()
            
            for line in lines:
                our_count = 0
                their_count = 0
                empty_count = 0
                
                # Быстрый анализ линии
                valid_line = True
                for x, y, z in line:
                    if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                        valid_line = False
                        break
                        
                    cell = board[z][y][x]
                    if cell == player:
                        our_count += 1
                    elif cell == opponent:
                        their_count += 1
                    else:
                        empty_count += 1
                
                if not valid_line or (our_count > 0 and their_count > 0):
                    continue  # заблокированная линия
                
                # Простая система очков
                if our_count == 3 and empty_count == 1:
                    score += 500
                elif their_count == 3 and empty_count == 1:
                    score -= 500  
                elif our_count == 2 and empty_count == 2:
                    score += 50
                elif their_count == 2 and empty_count == 2:
                    score -= 50
                elif our_count == 1 and empty_count == 3:
                    score += 5
                elif their_count == 1 and empty_count == 3:
                    score -= 5
                    
            return score
        except Exception:
            return 0

    def find_strategic_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Стратегический ход - контроль центра"""
        try:
            # Приоритетные позиции (от лучших к худшим)
            priorities = [
                # Центр
                (1, 1), (2, 2), (1, 2), (2, 1),
                # Околоцентральные
                (0, 1), (1, 0), (3, 2), (2, 3),
                (0, 2), (2, 0), (3, 1), (1, 3),
                # Углы
                (0, 0), (3, 3), (0, 3), (3, 0)
            ]
            
            for x, y in priorities:
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
                    
            # Запасной вариант
            return self.emergency_safe_move(board)
        except Exception:
            return self.emergency_safe_move(board)

    def get_position_value(self, x: int, y: int, z: int) -> int:
        """Позиционная ценность хода"""
        try:
            value = 0
            
            # Центр важнее краёв
            center_bonus = 20 - int((abs(x - 1.5) + abs(y - 1.5)) * 5)
            value += center_bonus
            
            # Высота даёт контроль
            height_bonus = z * 3
            value += height_bonus
            
            return value
        except Exception:
            return 0

    def check_simple_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """Простая проверка победы от конкретной позиции"""
        try:
            # Проверяем все направления от данной позиции
            directions = [
                # Вертикальное
                [(0, 0, 1), (0, 0, -1)],
                # Горизонтальные
                [(1, 0, 0), (-1, 0, 0)],
                [(0, 1, 0), (0, -1, 0)],
                # Диагонали в плоскостях
                [(1, 1, 0), (-1, -1, 0)],
                [(1, -1, 0), (-1, 1, 0)],
                [(1, 0, 1), (-1, 0, -1)],
                [(1, 0, -1), (-1, 0, 1)],
                [(0, 1, 1), (0, -1, -1)],
                [(0, 1, -1), (0, -1, 1)],
                # Пространственные диагонали
                [(1, 1, 1), (-1, -1, -1)],
                [(1, 1, -1), (-1, -1, 1)],
                [(1, -1, 1), (-1, 1, -1)],
                [(1, -1, -1), (-1, 1, 1)]
            ]
            
            for dir_pair in directions:
                count = 1  # текущая позиция
                
                # Проверяем в обе стороны направления
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

    def get_winning_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Все выигрышные линии (упрощённая версия)"""
        lines = []
        
        try:
            # Вертикальные
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # Горизонтальные X
            for z in range(4):
                for y in range(4):
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
            
            # Горизонтальные Y
            for z in range(4):
                for x in range(4):
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            # Основные диагонали
            for z in range(4):
                lines.append([(i, i, z) for i in range(4)])
                lines.append([(i, 3-i, z) for i in range(4)])
            
            # Пространственные диагонали  
            lines.append([(i, i, i) for i in range(4)])
            lines.append([(i, i, 3-i) for i in range(4)])
            lines.append([(i, 3-i, i) for i in range(4)])
            lines.append([(3-i, i, i) for i in range(4)])
            
        except Exception:
            pass
            
        return lines

    def get_drop_z(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Находит Z координату, куда упадёт фишка"""
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
        """Экстренный безопасный ход при любых ошибках"""
        try:
            safe_moves = [(1, 1), (2, 2), (1, 2), (2, 1), (0, 0), (1, 0), (0, 1), (3, 3)]
            
            for x, y in safe_moves:
                try:
                    if 0 <= x < 4 and 0 <= y < 4:
                        drop_z = self.get_drop_z(board, x, y)
                        if drop_z is not None:
                            return (x, y)
                except:
                    continue
            
            # Последний шанс - любой валидный ход
            for x in range(4):
                for y in range(4):
                    try:
                        if self.get_drop_z(board, x, y) is not None:
                            return (x, y)
                    except:
                        continue
                        
            return (0, 0)  # Критический случай
        except Exception:
            return (0, 0)