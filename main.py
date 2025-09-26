from typing import List, Tuple, Optional, Dict, Set
import time

class UltimateConnect4AI:

    def __init__(self, depth: int = 4):
        self.depth = depth
        self.max_time = 8.5  # Оставляем запас
        
        # Основные структуры данных
        self.lines = self._generate_lines()
        self.opening_book = self._create_comprehensive_opening_book()
        self.endgame_patterns = self._create_endgame_patterns()
        
        # Кэши и таблицы
        self.transposition_table = {}
        self.threat_cache = {}
        self.pattern_cache = {}
        self.killer_moves = [[] for _ in range(30)]
        self.history_table = {}
        
        # Веса для эвалуации
        self.weights = {
            'four_in_row': 100000,
            'three_in_row': 1000,
            'two_in_row': 50,
            'one_in_row': 5,
            'center_control': 20,
            'height_advantage': 10,
            'threat_creation': 2000,
            'double_threat': 8000,
            'connectivity': 15
        }

    def _generate_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Генерация всех выигрышных линий с приоритетами"""
        lines = []
        
        # Прямые линии (высокий приоритет)
        for y in range(4):
            for z in range(4):
                lines.append([(x, y, z) for x in range(4)])
        for x in range(4):
            for z in range(4):
                lines.append([(x, y, z) for y in range(4)])
        for x in range(4):
            for y in range(4):
                lines.append([(x, y, z) for z in range(4)])
        
        # Диагонали в плоскостях (средний приоритет)
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        
        # Пространственные диагонали (максимальный приоритет!)
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3-i) for i in range(4)])
        lines.append([(i, 3-i, i) for i in range(4)])
        lines.append([(3-i, i, i) for i in range(4)])
        
        return lines

    def _create_comprehensive_opening_book(self) -> Dict[str, Dict[str, any]]:
        """
        Комплексная дебютная книга на основе принципов 3D Connect 4:
        - Контроль центра критичен
        - Пространственные диагонали - ключ к победе
        - Избегание краевых позиций в начале
        """
        book = {}
        
        # Первый ход (приоритет центральным позициям)
        book["start"] = {
            "moves": [(1, 1), (2, 2), (1, 2), (2, 1)],
            "strategy": "center_control",
            "priority": "high"
        }
        
        # Ответы на центральные ходы противника
        book["center_response"] = {
            # Если противник взял (1,1), контролируем остальной центр
            "1,1": [(2, 2), (1, 2), (2, 1)],
            "2,2": [(1, 1), (1, 2), (2, 1)],
            "1,2": [(2, 1), (1, 1), (2, 2)],
            "2,1": [(1, 2), (1, 1), (2, 2)]
        }
        
        # Ответы на краевые ходы (агрессивно занимаем центр)
        book["edge_response"] = {
            "0,0": [(1, 1), (2, 2)],  # Противник в углу - контролируем главную диагональ
            "3,3": [(2, 2), (1, 1)],
            "0,3": [(1, 2), (2, 1)],  # Контролируем противоположную диагональ
            "3,0": [(2, 1), (1, 2)]
        }
        
        # Паттерны второго хода
        book["second_move_patterns"] = {
            # После 1,1-2,2 готовимся к пространственной диагонали
            "1,1-2,2": {
                "moves": [(0, 0), (3, 3), (1, 2), (2, 1)],
                "strategy": "spatial_diagonal_setup"
            },
            # Смешанная стратегия
            "1,1-1,2": {
                "moves": [(2, 1), (2, 2), (0, 1), (1, 0)],
                "strategy": "flexible_control"
            }
        }
        
        return book

    def _create_endgame_patterns(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Эндшпильные паттерны для быстрого распознавания:
        - Вынужденные последовательности
        - Zugzwang позиции
        - Точные выигрыши
        """
        patterns = {}
        
        # Паттерн "лестница" - вынужденная последовательность
        patterns["ladder"] = [(0, 0), (1, 1), (2, 2), (3, 3)]
        
        # Паттерн "вилка" - двойная угроза
        patterns["fork_horizontal"] = [(1, 1), (1, 2), (2, 1), (2, 2)]
        
        # Паттерн контроля пространственной диагонали
        patterns["spatial_control"] = [(0, 0), (1, 1), (2, 2), (3, 3)]
        
        return patterns

    def _get_board_hash(self, board) -> str:
        """Быстрое хэширование позиции"""
        return ''.join(''.join(''.join(str(cell) for cell in row) for row in layer) for layer in board)

    def _detect_critical_patterns(self, board, player: int) -> List[Dict]:
        """
        Обнаружение критических паттернов:
        - Немедленные угрозы
        - Двойные угрозы (форки)
        - Блокирующие ходы
        - Стратегические паттерны
        """
        board_hash = self._get_board_hash(board)
        cache_key = f"{board_hash}_{player}"
        
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        patterns = []
        
        # 1. Немедленные выигрыши
        for x in range(4):
            for y in range(4):
                if self._can_drop(board, x, y):
                    z = self._drop_level(board, x, y)
                    board[z][y][x] = player
                    if self._check_win(board, player):
                        patterns.append({
                            'type': 'immediate_win',
                            'move': (x, y),
                            'priority': 1000000
                        })
                    board[z][y][x] = 0
        
        # 2. Блокирование противника
        opponent = 3 - player
        for x in range(4):
            for y in range(4):
                if self._can_drop(board, x, y):
                    z = self._drop_level(board, x, y)
                    board[z][y][x] = opponent
                    if self._check_win(board, opponent):
                        patterns.append({
                            'type': 'block_opponent',
                            'move': (x, y),
                            'priority': 500000
                        })
                    board[z][y][x] = 0
        
        # 3. Создание двойных угроз
        for x in range(4):
            for y in range(4):
                if self._can_drop(board, x, y):
                    threats = self._count_threats_after_move(board, x, y, player)
                    if threats >= 2:
                        patterns.append({
                            'type': 'create_fork',
                            'move': (x, y),
                            'priority': 200000,
                            'threat_count': threats
                        })
        
        # 4. Пространственные диагонали
        spatial_moves = self._find_spatial_diagonal_moves(board, player)
        for move, value in spatial_moves:
            patterns.append({
                'type': 'spatial_diagonal',
                'move': move,
                'priority': 50000 + value
            })
        
        self.pattern_cache[cache_key] = patterns
        return patterns

    def _find_spatial_diagonal_moves(self, board, player: int) -> List[Tuple[Tuple[int, int], int]]:
        """Поиск ходов, усиливающих пространственные диагонали"""
        spatial_moves = []
        
        # Четыре пространственные диагонали
        spatial_diagonals = [
            [(i, i, i) for i in range(4)],           # главная 
            [(i, i, 3-i) for i in range(4)],         # x=y, z убывает
            [(i, 3-i, i) for i in range(4)],         # x=z, y убывает  
            [(3-i, i, i) for i in range(4)]          # y=z, x убывает
        ]
        
        for diag in spatial_diagonals:
            value = self._evaluate_spatial_diagonal(board, diag, player)
            if value > 0:
                # Найти лучший ход для этой диагонали
                for x, y, z in diag:
                    if self._can_drop(board, x, y) and self._drop_level(board, x, y) == z:
                        spatial_moves.append(((x, y), value))
        
        return spatial_moves

    def _evaluate_spatial_diagonal(self, board, diagonal: List[Tuple[int, int, int]], player: int) -> int:
        """Оценка важности пространственной диагонали"""
        my_count = 0
        opp_count = 0
        empty_count = 0
        
        for x, y, z in diagonal:
            cell = board[z][y][x]
            if cell == player:
                my_count += 1
            elif cell == 3 - player:
                opp_count += 1
            else:
                empty_count += 1
        
        # Если диагональ заблокирована - не интересна
        if my_count > 0 and opp_count > 0:
            return 0
            
        # Оценка потенциала
        if opp_count == 0:
            return my_count * my_count * 10
        elif my_count == 0:
            return -(opp_count * opp_count * 10)
        
        return 0

    def _count_threats_after_move(self, board, x: int, y: int, player: int) -> int:
        """Подсчет угроз после совершения хода"""
        if not self._can_drop(board, x, y):
            return 0
            
        z = self._drop_level(board, x, y)
        board[z][y][x] = player
        
        threats = 0
        # Проверяем все возможные следующие ходы
        for nx in range(4):
            for ny in range(4):
                if self._can_drop(board, nx, ny):
                    nz = self._drop_level(board, nx, ny)
                    board[nz][ny][nx] = player
                    if self._check_win(board, player):
                        threats += 1
                    board[nz][ny][nx] = 0
        
        board[z][y][x] = 0
        return threats

    def _can_drop(self, board, x: int, y: int) -> bool:
        """Можно ли бросить фишку в столбец"""
        return 0 <= x < 4 and 0 <= y < 4 and board[3][y][x] == 0

    def _drop_level(self, board, x: int, y: int) -> Optional[int]:
        """Уровень, на который упадет фишка"""
        if not self._can_drop(board, x, y):
            return None
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return None

    def _check_win(self, board, player: int) -> bool:
        """Быстрая проверка победы"""
        for line in self.lines:
            if all(board[z][y][x] == player for x, y, z in line):
                return True
        return False

    def _advanced_evaluation(self, board, player: int) -> float:
        """
        Продвинутая функция оценки с учетом всех факторов:
        - Материальный баланс (линии с 1/2/3 фишками)
        - Позиционные факторы (центр, высота, связность)
        - Тактические элементы (угрозы, форки)
        - Стратегические паттерны (контроль диагоналей)
        """
        if self._check_win(board, player):
            return 100000
        if self._check_win(board, 3 - player):
            return -100000
            
        score = 0.0
        
        # 1. Материальная оценка всех линий
        material_score = 0
        for line in self.lines:
            line_cells = [board[z][y][x] for x, y, z in line]
            material_score += self._evaluate_line_material(line_cells, player)
        score += material_score
        
        # 2. Позиционная оценка
        position_score = 0
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    cell = board[z][y][x]
                    if cell != 0:
                        # Центральность (расстояние от (1.5, 1.5))
                        center_dist = ((x - 1.5) ** 2 + (y - 1.5) ** 2) ** 0.5
                        center_value = (3.0 - center_dist) * self.weights['center_control']
                        
                        # Высота (контроль верхних уровней важен)
                        height_value = z * self.weights['height_advantage']
                        
                        total_pos_value = center_value + height_value
                        
                        if cell == player:
                            position_score += total_pos_value
                        else:
                            position_score -= total_pos_value
        score += position_score
        
        # 3. Тактическая оценка (угрозы и форки)
        patterns = self._detect_critical_patterns(board, player)
        tactical_score = 0
        for pattern in patterns:
            if pattern['type'] == 'create_fork':
                tactical_score += self.weights['double_threat']
            elif pattern['type'] == 'spatial_diagonal':
                tactical_score += pattern['priority'] // 10
        score += tactical_score
        
        # 4. Связность (группировка фишек)
        connectivity_score = self._calculate_connectivity(board, player)
        score += connectivity_score * self.weights['connectivity']
        
        return score

    def _evaluate_line_material(self, line_cells: List[int], player: int) -> float:
        """Материальная оценка отдельной линии"""
        my_count = line_cells.count(player)
        opp_count = line_cells.count(3 - player)
        
        # Заблокированная линия не имеет ценности
        if my_count > 0 and opp_count > 0:
            return 0
            
        if opp_count == 0:  # Только наши фишки
            if my_count == 4:
                return self.weights['four_in_row']
            elif my_count == 3:
                return self.weights['three_in_row']
            elif my_count == 2:
                return self.weights['two_in_row']
            elif my_count == 1:
                return self.weights['one_in_row']
        elif my_count == 0:  # Только фишки противника
            if opp_count == 4:
                return -self.weights['four_in_row']
            elif opp_count == 3:
                return -self.weights['three_in_row']
            elif opp_count == 2:
                return -self.weights['two_in_row']
            elif opp_count == 1:
                return -self.weights['one_in_row']
                
        return 0

    def _calculate_connectivity(self, board, player: int) -> float:
        """Расчет связности фишек игрока"""
        connectivity = 0
        directions = [
            (1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1),
            (1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
            (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1),
            (0,1,1), (0,1,-1), (0,-1,1), (0,-1,-1),
            (1,1,1), (1,1,-1), (1,-1,1), (-1,1,1),
            (1,-1,-1), (-1,1,-1), (-1,-1,1), (-1,-1,-1)
        ]
        
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if board[z][y][x] == player:
                        for dx, dy, dz in directions:
                            nx, ny, nz = x+dx, y+dy, z+dz
                            if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and
                                board[nz][ny][nx] == player):
                                connectivity += 1
        
        return connectivity

    def _minimax_with_patterns(self, board, depth: int, alpha: float, beta: float,
                              maximizing: bool, player: int, start_time: float) -> Tuple[float, Optional[Tuple[int, int]]]:
        """Minimax с интеграцией паттернов"""
        if time.time() - start_time > self.max_time:
            return 0, None
            
        # Проверка на критические паттерны сначала
        patterns = self._detect_critical_patterns(board, player if maximizing else 3-player)
        
        # Если есть немедленный выигрыш или блокировка - используем их
        for pattern in sorted(patterns, key=lambda p: p['priority'], reverse=True):
            if pattern['priority'] > 400000:  # Критические паттерны
                return pattern['priority'], pattern['move']
        
        if depth == 0 or self._check_terminal(board):
            return self._advanced_evaluation(board, player), None
            
        valid_moves = [(x, y) for x in range(4) for y in range(4) if self._can_drop(board, x, y)]
        if not valid_moves:
            return 0, None
            
        # Сортировка ходов по паттернам
        move_scores = {}
        for pattern in patterns:
            move_scores[pattern['move']] = move_scores.get(pattern['move'], 0) + pattern['priority']
        
        valid_moves.sort(key=lambda move: move_scores.get(move, 0), reverse=True)
        
        best_move = valid_moves[0]
        
        if maximizing:
            max_eval = float('-inf')
            for x, y in valid_moves:
                z = self._drop_level(board, x, y)
                board[z][y][x] = player
                
                eval_score, _ = self._minimax_with_patterns(board, depth-1, alpha, beta, False, player, start_time)
                board[z][y][x] = 0
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (x, y)
                    
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
                    
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for x, y in valid_moves:
                z = self._drop_level(board, x, y)
                board[z][y][x] = 3 - player
                
                eval_score, _ = self._minimax_with_patterns(board, depth-1, alpha, beta, True, player, start_time)
                board[z][y][x] = 0
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (x, y)
                    
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
                    
            return min_eval, best_move

    def _check_terminal(self, board) -> bool:
        """Проверка терминальной позиции"""
        # Есть победитель
        for player in [1, 2]:
            if self._check_win(board, player):
                return True
        
        # Доска заполнена
        return all(board[3][y][x] != 0 for x in range(4) for y in range(4))

    def get_move(self, board, player: int, last_move) -> Tuple[int, int]:
        """
        Главная функция - объединяет все стратегии:
        1. Дебютная книга (первые ходы)
        2. Критические паттерны (выигрыш/блокировка/форки)
        3. Продвинутый поиск с оценкой паттернов
        4. Fallback на центральные позиции
        """
        try:
            start_time = time.time()
            
            # 1. Дебютная книга для первых ходов
            moves_played = sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)
            
            if moves_played <= 4:  # Первые 2 хода каждого игрока
                if moves_played == 0:  # Первый ход партии
                    return self.opening_book["start"]["moves"][0]
                elif moves_played == 1:  # Ответ на первый ход
                    # Найти ход противника
                    opp_move = None
                    for x in range(4):
                        for y in range(4):
                            if board[0][y][x] != 0:
                                opp_move = f"{x},{y}"
                                break
                    
                    if opp_move in self.opening_book["center_response"]:
                        return self.opening_book["center_response"][opp_move][0]
                    elif opp_move in self.opening_book["edge_response"]:
                        return self.opening_book["edge_response"][opp_move][0]
            
            # 2. Анализ критических паттернов
            patterns = self._detect_critical_patterns(board, player)
            
            # Немедленная победа - высший приоритет
            for pattern in patterns:
                if pattern['type'] == 'immediate_win':
                    return pattern['move']
            
            # Блокировка противника - второй приоритет  
            for pattern in patterns:
                if pattern['type'] == 'block_opponent':
                    return pattern['move']
                    
            # Создание форка - третий приоритет
            for pattern in patterns:
                if pattern['type'] == 'create_fork':
                    return pattern['move']
            
            # 3. Основной поиск с итеративным углублением
            best_move = None
            best_score = float('-inf')
            
            for depth in range(1, self.depth + 1):
                if time.time() - start_time > self.max_time * 0.8:
                    break
                    
                try:
                    score, move = self._minimax_with_patterns(board, depth, float('-inf'), float('inf'), 
                                                            True, player, start_time)
                    if move and score > best_score:
                        best_score = score
                        best_move = move
                        
                    if score > 50000:  # Найден выигрышный ход
                        break
                except:
                    break
            
            if best_move and self._can_drop(board, best_move[0], best_move[1]):
                return best_move
            
            # 4. Fallback - центральные позиции
            center_order = [(1,1), (2,2), (1,2), (2,1), (0,1), (1,0), (3,2), (2,3)]
            for x, y in center_order:
                if self._can_drop(board, x, y):
                    return (x, y)
            
            # 5. Последний резерв - любая валидная позиция
            for x in range(4):
                for y in range(4):
                    if self._can_drop(board, x, y):
                        return (x, y)
                        
            return (0, 0)
            
        except Exception:
            # Аварийный режим
            center_order = [(1,1), (2,2), (1,2), (2,1)]
            for x, y in center_order:
                if self._can_drop(board, x, y):
                    return (x, y)
            return (0, 0)

# Алиасы для совместимости
MyAI = UltimateConnect4AI

def create_optimized_ai(depth=4):
    return UltimateConnect4AI(depth=depth)