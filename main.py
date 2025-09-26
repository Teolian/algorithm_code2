from typing import List, Tuple, Optional, Set, Dict
try:
    from framework import Alg3D, Board
except Exception:
    from local_driver import Alg3D, Board

LINES = [
    # Вертикальные (0-15)
    [(0,0,0),(0,0,1),(0,0,2),(0,0,3)], [(0,1,0),(0,1,1),(0,1,2),(0,1,3)], [(0,2,0),(0,2,1),(0,2,2),(0,2,3)], [(0,3,0),(0,3,1),(0,3,2),(0,3,3)],
    [(1,0,0),(1,0,1),(1,0,2),(1,0,3)], [(1,1,0),(1,1,1),(1,1,2),(1,1,3)], [(1,2,0),(1,2,1),(1,2,2),(1,2,3)], [(1,3,0),(1,3,1),(1,3,2),(1,3,3)],
    [(2,0,0),(2,0,1),(2,0,2),(2,0,3)], [(2,1,0),(2,1,1),(2,1,2),(2,1,3)], [(2,2,0),(2,2,1),(2,2,2),(2,2,3)], [(2,3,0),(2,3,1),(2,3,2),(2,3,3)],
    [(3,0,0),(3,0,1),(3,0,2),(3,0,3)], [(3,1,0),(3,1,1),(3,1,2),(3,1,3)], [(3,2,0),(3,2,1),(3,2,2),(3,2,3)], [(3,3,0),(3,3,1),(3,3,2),(3,3,3)],
    # Горизонтальные X (16-31)
    [(0,0,0),(1,0,0),(2,0,0),(3,0,0)], [(0,1,0),(1,1,0),(2,1,0),(3,1,0)], [(0,2,0),(1,2,0),(2,2,0),(3,2,0)], [(0,3,0),(1,3,0),(2,3,0),(3,3,0)],
    [(0,0,1),(1,0,1),(2,0,1),(3,0,1)], [(0,1,1),(1,1,1),(2,1,1),(3,1,1)], [(0,2,1),(1,2,1),(2,2,1),(3,2,1)], [(0,3,1),(1,3,1),(2,3,1),(3,3,1)],
    [(0,0,2),(1,0,2),(2,0,2),(3,0,2)], [(0,1,2),(1,1,2),(2,1,2),(3,1,2)], [(0,2,2),(1,2,2),(2,2,2),(3,2,2)], [(0,3,2),(1,3,2),(2,3,2),(3,3,2)],
    [(0,0,3),(1,0,3),(2,0,3),(3,0,3)], [(0,1,3),(1,1,3),(2,1,3),(3,1,3)], [(0,2,3),(1,2,3),(2,2,3),(3,2,3)], [(0,3,3),(1,3,3),(2,3,3),(3,3,3)],
    # Горизонтальные Y (32-47)
    [(0,0,0),(0,1,0),(0,2,0),(0,3,0)], [(1,0,0),(1,1,0),(1,2,0),(1,3,0)], [(2,0,0),(2,1,0),(2,2,0),(2,3,0)], [(3,0,0),(3,1,0),(3,2,0),(3,3,0)],
    [(0,0,1),(0,1,1),(0,2,1),(0,3,1)], [(1,0,1),(1,1,1),(1,2,1),(1,3,1)], [(2,0,1),(2,1,1),(2,2,1),(2,3,1)], [(3,0,1),(3,1,1),(3,2,1),(3,3,1)],
    [(0,0,2),(0,1,2),(0,2,2),(0,3,2)], [(1,0,2),(1,1,2),(1,2,2),(1,3,2)], [(2,0,2),(2,1,2),(2,2,2),(2,3,2)], [(3,0,2),(3,1,2),(3,2,2),(3,3,2)],
    [(0,0,3),(0,1,3),(0,2,3),(0,3,3)], [(1,0,3),(1,1,3),(1,2,3),(1,3,3)], [(2,0,3),(2,1,3),(2,2,3),(2,3,3)], [(3,0,3),(3,1,3),(3,2,3),(3,3,3)],
    # Диагонали плоскостные (48-71)
    [(0,0,0),(1,1,0),(2,2,0),(3,3,0)], [(0,3,0),(1,2,0),(2,1,0),(3,0,0)],
    [(0,0,1),(1,1,1),(2,2,1),(3,3,1)], [(0,3,1),(1,2,1),(2,1,1),(3,0,1)],
    [(0,0,2),(1,1,2),(2,2,2),(3,3,2)], [(0,3,2),(1,2,2),(2,1,2),(3,0,2)],
    [(0,0,3),(1,1,3),(2,2,3),(3,3,3)], [(0,3,3),(1,2,3),(2,1,3),(3,0,3)],
    [(0,0,0),(0,1,1),(0,2,2),(0,3,3)], [(0,0,3),(0,1,2),(0,2,1),(0,3,0)],
    [(1,0,0),(1,1,1),(1,2,2),(1,3,3)], [(1,0,3),(1,1,2),(1,2,1),(1,3,0)],
    [(2,0,0),(2,1,1),(2,2,2),(2,3,3)], [(2,0,3),(2,1,2),(2,2,1),(2,3,0)],
    [(3,0,0),(3,1,1),(3,2,2),(3,3,3)], [(3,0,3),(3,1,2),(3,2,1),(3,3,0)],
    [(0,0,0),(1,0,1),(2,0,2),(3,0,3)], [(0,0,3),(1,0,2),(2,0,1),(3,0,0)],
    [(0,1,0),(1,1,1),(2,1,2),(3,1,3)], [(0,1,3),(1,1,2),(2,1,1),(3,1,0)],
    [(0,2,0),(1,2,1),(2,2,2),(3,2,3)], [(0,2,3),(1,2,2),(2,2,1),(3,2,0)],
    [(0,3,0),(1,3,1),(2,3,2),(3,3,3)], [(0,3,3),(1,3,2),(2,3,1),(3,3,0)],
    # ПРОСТРАНСТВЕННЫЕ ДИАГОНАЛИ (72-75)
    [(0,0,0),(1,1,1),(2,2,2),(3,3,3)],
    [(0,0,3),(1,1,2),(2,2,1),(3,3,0)],
    [(0,3,0),(1,2,1),(2,1,2),(3,0,3)],
    [(3,0,0),(2,1,1),(1,2,2),(0,3,3)]
]

def drop_z(board: Board, x: int, y: int) -> Optional[int]:
    if not (0 <= x < 4 and 0 <= y < 4):
        return None
    for z in range(4):
        if board[z][y][x] == 0:
            return z
    return None

def winner(board: Board) -> int:
    for line in LINES:
        vals = [board[z][y][x] for (x, y, z) in line]
        if vals == [1,1,1,1]: return 1
        if vals == [2,2,2,2]: return 2
    return 0

def valid_moves(board: Board):
    for x in range(4):
        for y in range(4):
            if board[3][y][x] == 0:
                yield (x, y)

def board_to_pattern(board: Board) -> str:
    """Конвертация доски в паттерн для Opening Book"""
    pattern = ""
    for z in range(4):
        for y in range(4):
            for x in range(4):
                pattern += str(board[z][y][x])
    return pattern

class OpeningBook:
    """Дебютная книга основанная на анализе сильных игроков"""
    
    def __init__(self):
        # Стратегии против различных первых ходов
        self.responses = {
            # Если противник играет углы
            (0, 0): [(1, 1), (2, 2), (1, 2)],  # Занимаем центр
            (0, 3): [(1, 2), (2, 1), (1, 1)],
            (3, 0): [(2, 1), (1, 2), (2, 2)],
            (3, 3): [(2, 2), (1, 1), (2, 1)],
            
            # Если противник играет центр - контрдиагонали
            (1, 1): [(2, 2), (3, 3), (0, 0)],
            (2, 2): [(1, 1), (0, 0), (3, 3)],
            (1, 2): [(2, 1), (0, 3), (3, 0)],
            (2, 1): [(1, 2), (3, 0), (0, 3)],
            
            # Если противник играет края
            (0, 1): [(1, 1), (0, 2), (1, 2)],
            (0, 2): [(1, 2), (0, 1), (1, 1)],
            (1, 0): [(1, 1), (2, 0), (1, 2)],
            (2, 0): [(2, 1), (1, 0), (2, 2)],
            (3, 1): [(2, 1), (3, 2), (2, 2)],
            (3, 2): [(3, 1), (2, 2), (2, 1)],
            (1, 3): [(1, 2), (2, 3), (1, 1)],
            (2, 3): [(2, 2), (1, 3), (2, 1)]
        }
        
        # Оптимальные первые ходы при игре первым
        self.first_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
        
        # Паттерны выигрышных позиций
        self.winning_patterns = [
            # Пространственная диагональ угроза
            [(0,0,0), (1,1,1), (2,2,2)],  # Нужен (3,3,3)
            [(1,1,1), (2,2,2), (3,3,3)],  # Нужен (0,0,0)
            # Вертикальные угрозы
            [(0,0,0), (0,0,1), (0,0,2)],  # Нужен (0,0,3)
            [(1,1,0), (1,1,1), (1,1,2)],  # Нужен (1,1,3)
        ]

    def get_response(self, opp_move: Tuple[int, int], board: Board) -> Optional[Tuple[int, int]]:
        """Получить ответ из дебютной книги"""
        if opp_move in self.responses:
            for move in self.responses[opp_move]:
                if drop_z(board, *move) is not None:
                    return move
        return None
    
    def get_first_move(self, board: Board) -> Tuple[int, int]:
        """Оптимальный первый ход"""
        for move in self.first_moves:
            if drop_z(board, *move) is not None:
                return move
        return (1, 1)

class PatternRecognizer:
    """Распознавание тактических паттернов"""
    
    @staticmethod
    def find_immediate_threats(board: Board, player: int) -> List[Tuple[int, int, int]]:
        """Поиск немедленных угроз (3 в ряд + пустое место)"""
        threats = []
        
        for line_idx, line in enumerate(LINES):
            vals = [board[z][y][x] for (x, y, z) in line]
            my_count = vals.count(player)
            empty_count = vals.count(0)
            opp_count = vals.count(3 - player)
            
            if my_count == 3 and empty_count == 1 and opp_count == 0:
                # Находим пустое место
                for i, (x, y, z) in enumerate(line):
                    if vals[i] == 0:
                        # Проверяем реализуемость
                        if z == 0 or (z > 0 and board[z-1][y][x] != 0):
                            weight = 10
                            if line_idx < 16:  # Вертикальные
                                weight = 15
                            elif line_idx >= 72:  # Пространственные
                                weight = 12
                            threats.append((x, y, weight))
                        break
        
        return threats
    
    @staticmethod
    def find_fork_opportunities(board: Board, player: int) -> List[Tuple[int, int, int]]:
        """Поиск возможностей создать форк"""
        forks = []
        
        for (x, y) in valid_moves(board):
            z = drop_z(board, x, y)
            if z is None:
                continue
            
            # Временно ставим фишку
            board[z][y][x] = player
            
            # Подсчитываем угрозы после хода
            new_threats = PatternRecognizer.find_immediate_threats(board, player)
            
            board[z][y][x] = 0
            
            if len(new_threats) >= 2:
                total_weight = sum(t[2] for t in new_threats)
                forks.append((x, y, total_weight))
        
        return forks
    
    @staticmethod
    def analyze_position_strength(board: Board, player: int) -> int:
        """Анализ силы позиции"""
        score = 0
        
        # Контроль центра
        center_positions = [(1,1,1), (1,1,2), (2,2,1), (2,2,2), (1,2,1), (2,1,2)]
        for (x, y, z) in center_positions:
            if board[z][y][x] == player:
                score += 200
            elif board[z][y][x] == (3 - player):
                score -= 150
        
        # Контроль пространственных диагоналей
        space_diag_positions = [(0,0,0), (1,1,1), (2,2,2), (3,3,3),
                               (0,0,3), (1,1,2), (2,2,1), (3,3,0),
                               (0,3,0), (1,2,1), (2,1,2), (3,0,3),
                               (3,0,0), (2,1,1), (1,2,2), (0,3,3)]
        for (x, y, z) in space_diag_positions:
            if board[z][y][x] == player:
                score += 150
            elif board[z][y][x] == (3 - player):
                score -= 120
        
        # Анализ каждой линии
        for line_idx, line in enumerate(LINES):
            vals = [board[z][y][x] for (x, y, z) in line]
            my_count = vals.count(player)
            opp_count = vals.count(3 - player)
            empty_count = vals.count(0)
            
            if my_count > 0 and opp_count == 0:
                weight = 1
                if line_idx < 16:  # Вертикальные
                    weight = 2
                elif line_idx >= 72:  # Пространственные
                    weight = 3
                
                if my_count == 3:
                    score += 5000 * weight
                elif my_count == 2:
                    score += 500 * weight
                elif my_count == 1:
                    score += 50 * weight
            
            elif opp_count > 0 and my_count == 0:
                weight = 1
                if line_idx < 16:
                    weight = 2
                elif line_idx >= 72:
                    weight = 3
                
                if opp_count == 3:
                    score -= 4500 * weight
                elif opp_count == 2:
                    score -= 450 * weight
                elif opp_count == 1:
                    score -= 45 * weight
        
        return score

class MyAI(Alg3D):
    def __init__(self):
        self.move_count = 0
        self.opening_book = OpeningBook()
        self.game_phase = "opening"  # opening, middle, endgame
        self.opponent_pattern = []

    def detect_game_phase(self, board: Board) -> str:
        """Определение фазы игры"""
        total_pieces = sum(1 for z in range(4) for y in range(4) for x in range(4) if board[z][y][x] != 0)
        
        if total_pieces <= 12:
            return "opening"
        elif total_pieces <= 40:
            return "middle"
        else:
            return "endgame"

    def minimax_pattern(self, board: Board, depth: int, alpha: int, beta: int, 
                       maximizing: bool, player: int) -> int:
        """Minimax с паттерн-анализом"""
        w = winner(board)
        if w == player:
            return 100000 + depth
        elif w != 0:
            return -100000 - depth
        
        if depth == 0:
            return PatternRecognizer.analyze_position_strength(board, player)
        
        moves = list(valid_moves(board))
        if not moves:
            return PatternRecognizer.analyze_position_strength(board, player)
        
        # Умная сортировка ходов
        def move_priority(move):
            x, y = move
            z = drop_z(board, x, y)
            if z is None:
                return -1000
            
            # Центральность
            center_score = -(abs(x - 1.5) + abs(y - 1.5)) * 10
            
            # Высота (выше лучше)
            height_score = z * 5
            
            # Потенциал угроз
            board[z][y][x] = player if maximizing else (3 - player)
            threat_score = len(PatternRecognizer.find_immediate_threats(board, player if maximizing else (3 - player))) * 100
            board[z][y][x] = 0
            
            return center_score + height_score + threat_score
        
        moves.sort(key=move_priority, reverse=True)
        
        if maximizing:
            max_eval = -200000
            for (x, y) in moves[:10]:  # Топ-10 ходов
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                eval_score = self.minimax_pattern(board, depth - 1, alpha, beta, False, player)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 200000
            opp = 3 - player
            for (x, y) in moves[:10]:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                eval_score = self.minimax_pattern(board, depth - 1, alpha, beta, True, player)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_move(self, board: Board, player: int, last_move: Tuple[int, int, int]) -> Tuple[int, int]:
        """Главная функция с Opening Book + Pattern Recognition"""
        try:
            self.move_count += 1
            self.game_phase = self.detect_game_phase(board)
            opp = 3 - player
            
            # OPENING BOOK
            if self.game_phase == "opening":
                # Первый ход - из книги
                if self.move_count == 1:
                    return self.opening_book.get_first_move(board)
                
                # Ответ на ход противника из книги
                if last_move and last_move[0] is not None:
                    opp_move = (last_move[0], last_move[1])
                    book_response = self.opening_book.get_response(opp_move, board)
                    if book_response:
                        return book_response
            
            # ТАКТИЧЕСКИЙ АНАЛИЗ
            
            # 1. Немедленная победа
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                if winner(board) == player:
                    board[z][y][x] = 0
                    return (x, y)
                board[z][y][x] = 0
            
            # 2. Блокировка победы противника
            for (x, y) in valid_moves(board):
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = opp
                if winner(board) == opp:
                    board[z][y][x] = 0
                    return (x, y)
                board[z][y][x] = 0
            
            # 3. Создание форка
            my_forks = PatternRecognizer.find_fork_opportunities(board, player)
            if my_forks:
                my_forks.sort(key=lambda f: f[2], reverse=True)
                return (my_forks[0][0], my_forks[0][1])
            
            # 4. Блокировка форка противника
            opp_forks = PatternRecognizer.find_fork_opportunities(board, opp)
            if opp_forks:
                opp_forks.sort(key=lambda f: f[2], reverse=True)
                return (opp_forks[0][0], opp_forks[0][1])
            
            # 5. Блокировка критических угроз
            opp_threats = PatternRecognizer.find_immediate_threats(board, opp)
            if opp_threats:
                opp_threats.sort(key=lambda t: t[2], reverse=True)
                return (opp_threats[0][0], opp_threats[0][1])
            
            # 6. Реализация собственных угроз
            my_threats = PatternRecognizer.find_immediate_threats(board, player)
            if my_threats:
                my_threats.sort(key=lambda t: t[2], reverse=True)
                return (my_threats[0][0], my_threats[0][1])
            
            # 7. Стратегический minimax
            moves = list(valid_moves(board))
            if not moves:
                return (1, 1)
            
            best_move = moves[0]
            best_score = -200000
            
            # Адаптивная глубина
            depth = 4 if len(moves) <= 8 else 3 if len(moves) <= 12 else 2
            
            for (x, y) in moves:
                z = drop_z(board, x, y)
                if z is None:
                    continue
                board[z][y][x] = player
                score = self.minimax_pattern(board, depth - 1, -200000, 200000, False, player)
                board[z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move
            
        except Exception:
            # Надежный fallback
            return self.opening_book.get_first_move(board)