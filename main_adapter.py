# main_adapter.py — адаптер к твоему main.py
import importlib

_base = importlib.import_module("main")  # грузим твой файл main.py из той же папки

class AI:
    def __init__(self):
        # если в main.py класс называется MyAI — меняй тут
        self.impl = _base.MyAI()
    def get_move(self, board, player, last_move):
        return self.impl.get_move(board, player, last_move)
