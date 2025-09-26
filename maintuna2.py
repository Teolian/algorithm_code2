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
        """
        Ультра-простой ИИ - минимум кода, максимум эффективности
        Философия: делать простые вещи идеально
        """
        
        try:
            # 1. ВЫИГРАТЬ - если можем победить за один ход, делаем это
            win_move = self.find_win(board, player)
            if win_move:
                return win_move
                
            # 2. ЗАБЛОКИРОВАТЬ - если противник может выиграть, блокируем
            block_move = self.find_win(board, 3 - player)  # opponent = 3 - player
            if block_move:
                return block_move
                
            # 3. ЦЕНТР - играем в центральные позиции (они статистически лучше)
            center_move = self.play_center(board)
            if center_move:
                return center_move
                
            # 4. ЛЮБОЙ ХОД - играем в любое доступное место
            return self.any_move(board)
            
        except:
            # Даже если что-то сломалось, всегда возвращаем валидный ход
            return (1, 1)

    def find_win(self, board, player):
        """Ищем выигрышный ход для указанного игрока"""
        for x in range(4):
            for y in range(4):
                # Находим куда упадёт фишка
                z = self.drop_z(board, x, y)
                if z is not None:
                    # Ставим фишку и проверяем победу
                    board[z][y][x] = player
                    if self.is_win(board, player):
                        board[z][y][x] = 0  # убираем фишку обратно
                        return (x, y)
                    board[z][y][x] = 0  # убираем фишку обратно
        return None

    def is_win(self, board, player):
        """Проверяем есть ли победа для игрока"""
        
        # Вертикальные линии (4 в столбце)
        for x in range(4):
            for y in range(4):
                if all(board[z][y][x] == player for z in range(4)):
                    return True
        
        # Горизонтальные линии по X (4 в ряду)
        for z in range(4):
            for y in range(4):
                if all(board[z][y][x] == player for x in range(4)):
                    return True
        
        # Горизонтальные линии по Y (4 в ряду)
        for z in range(4):
            for x in range(4):
                if all(board[z][y][x] == player for y in range(4)):
                    return True
        
        # Диагонали в плоскости XY
        for z in range(4):
            # Главная диагональ
            if all(board[z][i][i] == player for i in range(4)):
                return True
            # Побочная диагональ
            if all(board[z][i][3-i] == player for i in range(4)):
                return True
        
        # Диагонали в плоскости XZ
        for y in range(4):
            if all(board[i][y][i] == player for i in range(4)):
                return True
            if all(board[i][y][3-i] == player for i in range(4)):
                return True
        
        # Диагонали в плоскости YZ
        for x in range(4):
            if all(board[i][i][x] == player for i in range(4)):
                return True
            if all(board[i][3-i][x] == player for i in range(4)):
                return True
        
        # Пространственные диагонали (через весь куб)
        if all(board[i][i][i] == player for i in range(4)):
            return True
        if all(board[i][i][3-i] == player for i in range(4)):
            return True
        if all(board[i][3-i][i] == player for i in range(4)):
            return True
        if all(board[3-i][i][i] == player for i in range(4)):
            return True
        
        return False

    def drop_z(self, board, x, y):
        """Находим на какую высоту Z упадёт фишка в позиции (x,y)"""
        if x < 0 or x >= 4 or y < 0 or y >= 4:
            return None
        
        for z in range(4):  # начинаем снизу
            if board[z][y][x] == 0:  # если место свободно
                return z
        return None  # столбец полный

    def play_center(self, board):
        """Играем в центральные позиции"""
        # Центральные позиции в порядке приоритета
        center_positions = [
            (1, 1),  # самый центр
            (2, 2),  # тоже центр
            (1, 2),  # рядом с центром
            (2, 1),  # рядом с центром
        ]
        
        for x, y in center_positions:
            if self.drop_z(board, x, y) is not None:
                return (x, y)
        return None

    def any_move(self, board):
        """Играем в любое доступное место"""
        for x in range(4):
            for y in range(4):
                if self.drop_z(board, x, y) is not None:
                    return (x, y)
        return (0, 0)  # если всё заполнено (не должно случиться)