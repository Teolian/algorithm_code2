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
        """Простой, быстрый и надёжный ИИ + исправленный дебют"""
        
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
                
            # 5. УЛУЧШЕННЫЙ ТАКТИЧЕСКИЙ ХОД (исправлена дебютная игра)
            tactical_move = self.find_tactical_move(board, player)
            if tactical_move:
                return tactical_move
                
            # 6. СТРАТЕГИЧЕСКИЙ ХОД - контроль центра и высоты
            strategic_move = self.find_strategic_move(board)
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

    def find_tactical_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """УЛУЧШЕННЫЙ тактический анализ с исправленным дебютом"""
        try:
            move_count = self.count_total_moves(board)
            
            # ИСПРАВЛЕН ДЕБЮТ - более агрессивная игра первым ходом
            if move_count <= 6:
                return self.improved_opening_strategy(board, player, move_count)
            
            # Обычная тактика для мидгейма и эндгейма
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
                    
                    # НОВОЕ: бонус за контроль верхних уровней колонок
                    score += self.evaluate_height_control(board, x, y, drop_z, player)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                        
            return best_move
        except Exception:
            return None

    def improved_opening_strategy(self, board: List[List[List[int]]], player: int, move_count: int) -> Optional[Tuple[int, int]]:
        """ИСПРАВЛЕННАЯ дебютная стратегия"""
        try:
            # Первый ход - всегда центр
            if move_count == 0:
                return (1, 1)
            
            # Второй ход - контролируем центр и создаем угрозы
            if move_count <= 2:
                # Если центр свободен - берем
                if self.get_drop_z(board, 1, 1) is not None:
                    return (1, 1)
                # Иначе - другой центр
                for x, y in [(2, 2), (1, 2), (2, 1)]:
                    if self.get_drop_z(board, x, y) is not None:
                        return (x, y)
            
            # Дебютные ходы 3-6: более агрессивная стратегия
            # Ищем позиции, которые создают максимум возможностей
            best_move = None
            best_potential = 0
            
            opening_positions = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # Центр
                (1, 0), (0, 1), (3, 2), (2, 3),  # Сильные позиции
                (1, 3), (3, 1), (0, 2), (2, 0)   # Контроль
            ]
            
            for x, y in opening_positions:
                drop_z = self.get_drop_z(board, x, y)
                if drop_z is None:
                    continue
                    
                # Оценка потенциала позиции в дебюте
                potential = self.evaluate_opening_potential(board, x, y, drop_z, player)
                
                if potential > best_potential:
                    best_potential = potential
                    best_move = (x, y)
            
            return best_move
        except Exception:
            return None

    def evaluate_opening_potential(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Оценка потенциала позиции в дебюте"""
        try:
            score = 0
            
            # Центральность критична в дебюте
            center_distance = abs(x - 1.5) + abs(y - 1.5)
            score += int(50 - center_distance * 15)
            
            # Высота в дебюте менее важна, но все же дает бонус
            score += z * 3
            
            # НОВОЕ: оценка количества линий, которые мы можем контролировать
            board[z][y][x] = player
            
            line_potential = 0
            directions = [
                (1, 0, 0), (0, 1, 0), (0, 0, 1),
                (1, 1, 0), (1, -1, 0), 
                (1, 0, 1), (0, 1, 1),
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)
            ]
            
            for dx, dy, dz in directions:
                # Считаем потенциал линии в этом направлении
                potential_length = self.count_line_potential(board, x, y, z, dx, dy, dz, player)
                if potential_length >= 4:  # Может стать выигрышной
                    line_potential += potential_length
            
            score += line_potential * 3
            
            # ВАЖНО: избегаем позиций, которые дают противнику преимущество
            opponent = 3 - player
            board[z][y][x] = opponent  # Симулируем ход противника
            opponent_threats = self.count_immediate_threats(board, opponent)
            score -= opponent_threats * 20  # Штраф за предоставление возможностей противнику
            
            board[z][y][x] = 0  # Убираем симуляцию
            
            return score
        except Exception:
            return 0

    def count_line_potential(self, board: List[List[List[int]]], x: int, y: int, z: int, dx: int, dy: int, dz: int, player: int) -> int:
        """Подсчет потенциала линии в направлении"""
        try:
            count = 1  # Текущая позиция
            
            # Проверяем в положительном направлении
            for step in range(1, 4):
                nx, ny, nz = x + dx * step, y + dy * step, z + dz * step
                if not (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                    break
                cell = board[nz][ny][nx]
                if cell == player:
                    count += 1
                elif cell == 0:
                    count += 1  # Потенциально можем занять
                else:
                    break  # Заблокировано противником
            
            # Проверяем в отрицательном направлении
            for step in range(1, 4):
                nx, ny, nz = x - dx * step, y - dy * step, z - dz * step
                if not (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                    break
                cell = board[nz][ny][nx]
                if cell == player:
                    count += 1
                elif cell == 0:
                    count += 1  # Потенциально можем занять
                else:
                    break  # Заблокировано противником
            
            return min(count, 7)  # Максимум 7 (больше не нужно для оценки)
        except Exception:
            return 1

    def evaluate_height_control(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """НОВОЕ: оценка контроля высоты - решает проблему с верхними уровнями"""
        try:
            score = 0
            
            # Если мы занимаем верхний уровень колонки - большой бонус
            if z == 3:  # Самый верх
                score += 15
            elif z == 2:  # Предпоследний уровень
                score += 8
            
            # Проверяем, контролируем ли мы доступ к верхним уровням
            # в соседних колонках
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 4 and 0 <= ny < 4:
                    neighbor_height = self.get_column_height(board, nx, ny)
                    if neighbor_height < 4:  # Колонка не полная
                        # Если мы можем контролировать эту колонку с нашей высоты
                        if z >= neighbor_height:
                            score += 3
            
            return score
        except Exception:
            return 0

    def count_total_moves(self, board: List[List[List[int]]]) -> int:
        """Подсчет общего количества ходов"""
        try:
            count = 0
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if board[z][y][x] != 0:
                            count += 1
            return count
        except Exception:
            return 0

    def get_column_height(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """Высота колонки"""
        try:
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return 4
        except Exception:
            return 0

    # Остальные методы остаются как в оригинальном salmon1
    def count_immediate_threats(self, board: List[List[List[int]]], player: int) -> int:
        """Подсчёт немедленных угроз (3 в ряд + возможность поставить 4-ю)"""
        threats = 0
        
        try:
            lines = self.get_winning_lines()
            
            for line in lines:
                our_count = 0
                empty_positions = []
                blocked = False
                
                for x, y, z in line:
                    if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                        blocked = True
                        break
                        
                    cell = board[z][y][x]
                    if cell == player:
                        our_count += 1
                    elif cell == 0:
                        empty_positions.append((x, y, z))
                    else:
                        blocked = True
                        break
                
                if not blocked and our_count == 3 and len(empty_positions) == 1:
                    empty_x, empty_y, empty_z = empty_positions[0]
                    expected_z = self.get_drop_z(board, empty_x, empty_y)
                    if expected_z is not None and expected_z == empty_z:
                        threats += 1
                        
            return threats
        except Exception:
            return 0

    def evaluate_simple(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Простая оценка позиции без сложных вычислений"""
        score = 0
        
        try:
            lines = self.get_winning_lines()
            
            for line in lines:
                our_count = 0
                their_count = 0
                empty_count = 0
                
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
                    continue
                
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

    def get_position_value(self, x: int, y: int, z: int) -> int:
        """Позиционная ценность хода"""
        try:
            value = 0
            
            center_bonus = 20 - int((abs(x - 1.5) + abs(y - 1.5)) * 5)
            value += center_bonus
            
            height_bonus = z * 3
            value += height_bonus
            
            return value
        except Exception:
            return 0

    def find_strategic_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Стратегический ход - контроль центра"""
        try:
            priorities = [
                (1, 1), (2, 2), (1, 2), (2, 1),
                (0, 1), (1, 0), (3, 2), (2, 3),
                (0, 2), (2, 0), (3, 1), (1, 3),
                (0, 0), (3, 3), (0, 3), (3, 0)
            ]
            
            for x, y in priorities:
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
                    
            return self.emergency_safe_move(board)
        except Exception:
            return self.emergency_safe_move(board)

    def check_simple_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """Простая проверка победы от конкретной позиции"""
        try:
            directions = [
                [(0, 0, 1), (0, 0, -1)],
                [(1, 0, 0), (-1, 0, 0)],
                [(0, 1, 0), (0, -1, 0)],
                [(1, 1, 0), (-1, -1, 0)],
                [(1, -1, 0), (-1, 1, 0)],
                [(1, 0, 1), (-1, 0, -1)],
                [(1, 0, -1), (-1, 0, 1)],
                [(0, 1, 1), (0, -1, -1)],
                [(0, 1, -1), (0, -1, 1)],
                [(1, 1, 1), (-1, -1, -1)],
                [(1, 1, -1), (-1, -1, 1)],
                [(1, -1, 1), (-1, 1, -1)],
                [(1, -1, -1), (-1, 1, 1)]
            ]
            
            for dir_pair in directions:
                count = 1
                
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
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            for z in range(4):
                for y in range(4):
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
            
            for z in range(4):
                for x in range(4):
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            for z in range(4):
                lines.append([(i, i, z) for i in range(4)])
                lines.append([(i, 3-i, z) for i in range(4)])
            
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
            
            for x in range(4):
                for y in range(4):
                    try:
                        if self.get_drop_z(board, x, y) is not None:
                            return (x, y)
                    except:
                        continue
                        
            return (0, 0)
        except Exception:
            return (0, 0)