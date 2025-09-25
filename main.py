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
        """Улучшенный ИИ с правильной защитой по всем направлениям"""
        
        try:
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА - максимальный приоритет
            win_move = self.find_winning_move(board, player)
            if win_move:
                return win_move
                
            # 2. КРИТИЧЕСКАЯ БЛОКИРОВКА - исправлена!
            opponent = 3 - player
            block_move = self.find_winning_move(board, opponent)
            if block_move:
                return block_move
                
            # 3. БЛОКИРОВКА МНОЖЕСТВЕННЫХ УГРОЗ
            critical_block = self.find_critical_block(board, player, opponent)
            if critical_block:
                return critical_block
                
            # 4. СОЗДАНИЕ УГРОЗ - ищем ходы, создающие две угрозы сразу
            threat_move = self.find_double_threat(board, player)
            if threat_move:
                return threat_move
                
            # 5. БЛОКИРОВКА УГРОЗ ПРОТИВНИКА
            counter_threat = self.find_double_threat(board, opponent)
            if counter_threat:
                return counter_threat
                
            # 6. ТАКТИЧЕСКИЙ ХОД - улучшенный анализ
            tactical_move = self.find_tactical_move(board, player)
            if tactical_move:
                return tactical_move
                
            # 7. СТРАТЕГИЧЕСКИЙ ХОД - контроль центра и высоты
            strategic_move = self.find_strategic_move(board, player)
            return strategic_move
            
        except Exception:
            # ЭКСТРЕННЫЙ БЕЗОПАСНЫЙ ХОД
            return self.emergency_safe_move(board)

    def find_critical_block(self, board: List[List[List[int]]], player: int, opponent: int) -> Optional[Tuple[int, int]]:
        """Поиск критически важных блокировок (когда противник создаёт 2+ угрозы)"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Симулируем ход противника
                    board[drop_z][y][x] = opponent
                    
                    # Проверяем, сколько угроз создаст противник
                    threat_count = self.count_immediate_threats(board, opponent)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    # Если противник создаст 2+ угрозы - ОБЯЗАТЕЛЬНО блокируем!
                    if threat_count >= 2:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленного выигрыша - ИСПРАВЛЕНО"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_z(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Пробуем ход
                    board[drop_z][y][x] = player
                    
                    # Проверяем победу ВСЕМИ способами
                    is_win = self.check_complete_win(board, x, y, drop_z, player)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if is_win:
                        return (x, y)
                        
            return None
        except Exception:
            return None

    def check_complete_win(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """ПОЛНАЯ проверка победы по всем 13 направлениям"""
        try:
            # ВСЕ возможные направления в 3D
            directions = [
                # Основные оси
                (1, 0, 0),   # X
                (0, 1, 0),   # Y  
                (0, 0, 1),   # Z (вертикаль!)
                
                # Плоскостные диагонали
                (1, 1, 0),   # XY диагональ
                (1, -1, 0),  # XY обратная диагональ
                (1, 0, 1),   # XZ диагональ
                (1, 0, -1),  # XZ обратная диагональ
                (0, 1, 1),   # YZ диагональ
                (0, 1, -1),  # YZ обратная диагональ
                
                # Пространственные диагонали
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
        """Подсчёт ВСЕХ немедленных угроз (3 в ряд + возможность поставить 4-ю)"""
        threats = 0
        
        try:
            # Проверяем ВСЕ возможные выигрышные линии
            lines = self.get_all_winning_lines()
            
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
                    # ИСПРАВЛЕНО: правильная проверка высоты
                    if expected_z is not None and expected_z == empty_z:
                        threats += 1
                        
            return threats
        except Exception:
            return 0

    def get_all_winning_lines(self) -> List[List[Tuple[int, int, int]]]:
        """ВСЕ 76 выигрышных линий в 3D Connect 4"""
        lines = []
        
        try:
            # 1. ВЕРТИКАЛЬНЫЕ ЛИНИИ (16 штук) - ИСПРАВЛЕНО!
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # 2. ГОРИЗОНТАЛЬНЫЕ ПО X (16 штук)
            for z in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for x in range(4)])
            
            # 3. ГОРИЗОНТАЛЬНЫЕ ПО Y (16 штук)
            for z in range(4):
                for x in range(4):
                    lines.append([(x, y, z) for y in range(4)])
            
            # 4. ДИАГОНАЛИ В ПЛОСКОСТЯХ XY (8 штук)
            for z in range(4):
                # Главная диагональ
                lines.append([(i, i, z) for i in range(4)])
                # Побочная диагональ
                lines.append([(i, 3-i, z) for i in range(4)])
            
            # 5. ДИАГОНАЛИ В ПЛОСКОСТЯХ XZ (8 штук)
            for y in range(4):
                # Главная диагональ
                lines.append([(i, y, i) for i in range(4)])
                # Побочная диагональ
                lines.append([(i, y, 3-i) for i in range(4)])
            
            # 6. ДИАГОНАЛИ В ПЛОСКОСТЯХ YZ (8 штук)
            for x in range(4):
                # Главная диагональ
                lines.append([(x, i, i) for i in range(4)])
                # Побочная диагональ
                lines.append([(x, i, 3-i) for i in range(4)])
            
            # 7. ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ (4 штуки)
            lines.append([(i, i, i) for i in range(4)])           # (0,0,0) → (3,3,3)
            lines.append([(i, i, 3-i) for i in range(4)])         # (0,0,3) → (3,3,0)
            lines.append([(i, 3-i, i) for i in range(4)])         # (0,3,0) → (3,0,3)
            lines.append([(3-i, i, i) for i in range(4)])         # (3,0,0) → (0,3,3)
            
        except Exception:
            pass
            
        return lines

    def find_tactical_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Улучшенный тактический анализ"""
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
                    
                    # Улучшенная оценка позиции
                    score = self.evaluate_advanced(board, player, opponent, x, y, drop_z)
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                        
            return best_move
        except Exception:
            return None

    def evaluate_advanced(self, board: List[List[List[int]]], player: int, opponent: int, x: int, y: int, z: int) -> int:
        """Продвинутая оценка позиции"""
        score = 0
        
        try:
            # 1. Базовая оценка линий
            score += self.evaluate_lines(board, player, opponent)
            
            # 2. Позиционные бонусы
            score += self.get_position_value(x, y, z)
            
            # 3. Связность (соседние фишки)
            score += self.evaluate_connectivity(board, x, y, z, player) * 10
            
            # 4. Контроль центра (критично в 3D!)
            center_control = self.evaluate_center_control(board, player, opponent)
            score += center_control * 50
            
            # 5. Вертикальный контроль
            vertical_control = self.evaluate_vertical_control(board, player, opponent)
            score += vertical_control * 30
            
            return score
        except Exception:
            return 0

    def evaluate_lines(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Оценка всех линий"""
        score = 0
        
        try:
            lines = self.get_all_winning_lines()
            
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
                
                # Улучшенная система очков
                if our_count == 3 and empty_count == 1:
                    score += 1000  # Угроза победы
                elif their_count == 3 and empty_count == 1:
                    score -= 1000  # Угроза противника
                elif our_count == 2 and empty_count == 2:
                    score += 100   # Хорошая позиция
                elif their_count == 2 and empty_count == 2:
                    score -= 100   # Опасная позиция противника
                elif our_count == 1 and empty_count == 3:
                    score += 10
                elif their_count == 1 and empty_count == 3:
                    score -= 10
                    
            return score
        except Exception:
            return 0

    def evaluate_connectivity(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Оценка связности с соседними фишками"""
        connectivity = 0
        
        try:
            # Проверяем все 26 соседних позиций
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    for dz in [-1, 0, 1]:
                        if dx == 0 and dy == 0 and dz == 0:
                            continue
                            
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                            board[nz][ny][nx] == player):
                            connectivity += 1
                            
            return connectivity
        except Exception:
            return 0

    def evaluate_center_control(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Оценка контроля центра"""
        try:
            center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
            our_center = 0
            their_center = 0
            
            for x, y in center_positions:
                for z in range(4):
                    if board[z][y][x] == player:
                        our_center += (z + 1)  # Высота даёт бонус
                    elif board[z][y][x] == opponent:
                        their_center += (z + 1)
                        
            return our_center - their_center
        except Exception:
            return 0

    def evaluate_vertical_control(self, board: List[List[List[int]]], player: int, opponent: int) -> int:
        """Оценка вертикального контроля"""
        try:
            our_vertical = 0
            their_vertical = 0
            
            for x in range(4):
                for y in range(4):
                    column_height = self.get_column_height(board, x, y)
                    if column_height > 0:
                        top_player = board[column_height - 1][y][x]
                        if top_player == player:
                            our_vertical += column_height
                        elif top_player == opponent:
                            their_vertical += column_height
                            
            return our_vertical - their_vertical
        except Exception:
            return 0

    def get_column_height(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """Высота столбца"""
        try:
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return 4
        except Exception:
            return 0

    def find_strategic_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Стратегический ход - УЛУЧШЕННЫЙ"""
        try:
            # Дебютная книга для первых ходов
            total_moves = sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)
            
            if total_moves <= 2:
                # Первые ходы - всегда центр!
                center_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
                for x, y in center_moves:
                    if self.get_drop_z(board, x, y) is not None:
                        return (x, y)
            
            # Приоритетные позиции (обновлённые)
            priorities = [
                # Центр (максимальный приоритет)
                (1, 1), (2, 2), (1, 2), (2, 1),
                # Околоцентральные
                (0, 1), (1, 0), (3, 2), (2, 3),
                (0, 2), (2, 0), (3, 1), (1, 3),
                # Края (меньший приоритет)
                (0, 0), (3, 3), (0, 3), (3, 0)
            ]
            
            for x, y in priorities:
                if self.get_drop_z(board, x, y) is not None:
                    return (x, y)
                    
            return self.emergency_safe_move(board)
        except Exception:
            return self.emergency_safe_move(board)

    def get_position_value(self, x: int, y: int, z: int) -> int:
        """Позиционная ценность хода - УЛУЧШЕНА"""
        try:
            value = 0
            
            # Центр важнее краёв (квадратичная функция)
            center_distance = abs(x - 1.5) + abs(y - 1.5)
            center_bonus = int(50 - center_distance * center_distance * 5)
            value += center_bonus
            
            # Высота даёт контроль (экспоненциальный рост)
            height_bonus = int(10 * (1.5 ** z))
            value += height_bonus
            
            # Углы менее ценны
            if (x, y) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
                value -= 20
                
            return value
        except Exception:
            return 0

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