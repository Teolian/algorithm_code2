
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4x4x4 Connect-4 Arena Tester (macOS/Python 3.13 safe) — debug-able
- Две игры: каждый бот ходит первым по разу.
- 10 секунд на ход (wall-clock). Таймаут/ошибка/невалидный ход => форс-ход.
- Матчевый победитель: больше побед; при равенстве — меньше ходов до побед;
  при новом равенстве — меньшая суммарная "мысленная" длительность победившей стороны.

НОВОЕ:
- --debug: выводит каждый ход (кто, (x,y,z), причина, время), итог по форс-ходам.
- Исправление для сабпроцесса: рабочая директория воркера = директория файла бота
  (чтобы относительные импорты/файлы у бота работали одинаково).
"""

import argparse
import importlib.util
import os
import time
import traceback
from copy import deepcopy
from multiprocessing import Process, Queue, set_start_method

SIZE = 4
EMPTY, P1, P2 = 0, 1, 2

DIRECTIONS = [
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, -1, 0),
    (1, 0, 1), (1, 0, -1),
    (0, 1, 1), (0, 1, -1),
    (1, 1, 1), (1, -1, 1), (1, 1, -1), (1, -1, -1),
]

def in_bounds(x, y, z):
    return 0 <= x < SIZE and 0 <= y < SIZE and 0 <= z < SIZE

def generate_all_lines():
    lines = []
    for z in range(SIZE):
        for y in range(SIZE):
            for x in range(SIZE):
                for dx, dy, dz in DIRECTIONS:
                    x2 = x + (SIZE - 1) * dx
                    y2 = y + (SIZE - 1) * dy
                    z2 = z + (SIZE - 1) * dz
                    if in_bounds(x2, y2, z2):
                        line = [(x + i*dx, y + i*dy, z + i*dz) for i in range(SIZE)]
                        lines.append(line)
    seen = set()
    unique = []
    for line in lines:
        key = tuple(line)
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return unique

ALL_LINES = generate_all_lines()

def check_winner(board):
    for line in ALL_LINES:
        v = board[line[0][2]][line[0][1]][line[0][0]]
        if v == EMPTY:
            continue
        for (x, y, z) in line[1:]:
            if board[z][y][x] != v:
                break
        else:
            return v
    return EMPTY

def column_height(board, x, y):
    for z in range(SIZE):
        if board[z][y][x] == EMPTY:
            return z
    return None

def force_fallback_move(board):
    for y in range(SIZE):
        for x in range(SIZE):
            if column_height(board, x, y) is not None:
                return (x, y)
    return None

def apply_move(board, player, move):
    reason = None
    try:
        x, y = move
    except Exception:
        x, y = -1, -1
    if not (0 <= x < SIZE and 0 <= y < SIZE):
        reason = "invalid_out_of_range"
        mv = force_fallback_move(board)
        if mv is None:
            return None, reason
        x, y = mv
    z = column_height(board, x, y)
    if z is None:
        if reason is None:
            reason = "invalid_full_column"
        mv = force_fallback_move(board)
        if mv is None:
            return None, reason
        x, y = mv
        z = column_height(board, x, y)
        if z is None:
            return None, reason
    board[z][y][x] = player
    return (x, y, z), reason

# === worker helpers (pickle-safe) ===
def _load_bot_callable(bot_path):
    bot_path = os.path.abspath(bot_path)
    spec = importlib.util.spec_from_file_location("bot_module_" + os.path.basename(bot_path), bot_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {bot_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, "get_move", None)
    if callable(func):
        return func
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type):
            try:
                inst = obj()
                if hasattr(inst, "get_move") and callable(inst.get_move):
                    return inst.get_move
            except TypeError:
                pass
    raise RuntimeError(f"{bot_path}: no callable get_move(board) found")

def _worker_get_move(bot_path, board, q):
    try:
        # Сделаем рабочей директорией папку бота (для относительных импортов/файлов)
        bot_abs = os.path.abspath(bot_path)
        bot_dir = os.path.dirname(bot_abs)
        if bot_dir:
            os.chdir(bot_dir)
            if bot_dir not in os.sys.path:
                os.sys.path.insert(0, bot_dir)

        get_move_callable = _load_bot_callable(bot_abs)
        mv = get_move_callable(deepcopy(board))
        q.put(("ok", mv))
    except Exception as e:
        q.put(("error", f"exception: {e}\n{traceback.format_exc()}"))

def timed_get_move(bot_path, board, timeout_sec=10.0):
    q = Queue()
    p = Process(target=_worker_get_move, args=(bot_path, board, q))
    start = time.perf_counter()
    p.start()
    p.join(timeout=timeout_sec)
    elapsed = time.perf_counter() - start
    if p.is_alive():
        p.terminate()
        p.join(0.1)
        return False, "timeout", elapsed
    if q.empty():
        return False, "no_result", elapsed
    status, payload = q.get()
    if status == "ok":
        return True, payload, elapsed
    else:
        return False, payload, elapsed

def play_game(botA_path, botB_path, first_player=1, per_move_sec=10.0, max_plies=SIZE*SIZE*SIZE, debug=False):
    board = [[[EMPTY for _ in range(SIZE)] for _ in range(SIZE)] for _ in range(SIZE)]
    if first_player == 1:
        Pmap = {P1: botA_path, P2: botB_path}
        names = {P1: os.path.basename(botA_path), P2: os.path.basename(botB_path)}
    else:
        Pmap = {P1: botB_path, P2: botA_path}
        names = {P1: os.path.basename(botB_path), P2: os.path.basename(botA_path)}

    current = P1
    plies = 0
    time_p1 = 0.0
    time_p2 = 0.0
    forced_p1 = 0
    forced_p2 = 0

    while plies < max_plies:
        bot_path = Pmap[current]
        ok, result, elapsed = timed_get_move(bot_path, board, per_move_sec)
        if current == P1:
            time_p1 += elapsed
        else:
            time_p2 += elapsed

        reason = None
        if not ok:
            reason = f"forced_{result}"
            if current == P1: forced_p1 += 1
            else: forced_p2 += 1
            move = force_fallback_move(board)
            if move is None:
                if debug:
                    print(f"[DEBUG] Ход {plies+1}: P{current} {names[current]} — {reason}; Доска полная → ничья")
                return 0, plies, reason, time_p1, time_p2, forced_p1, forced_p2
        else:
            move = result

        placed, invalid_reason = apply_move(board, current, move)
        if invalid_reason is not None:
            if current == P1: forced_p1 += 1
            else: forced_p2 += 1
            reason = invalid_reason if reason is None else f"{reason}|{invalid_reason}"
        if placed is None:
            if debug:
                print(f"[DEBUG] Ход {plies+1}: P{current} {names[current]} — {reason or 'invalid'}; full_draw")
            return 0, plies, reason or "full_draw", time_p1, time_p2, forced_p1, forced_p2

        plies += 1
        if debug:
            x, y, z = placed
            print(f"[DEBUG] Ход {plies}: P{current} {names[current]} → ({x},{y},{z}); {reason or 'ok'}; t={elapsed:.3f}s")

        winner = check_winner(board)
        if winner != EMPTY:
            if debug:
                print(f"[DEBUG] Победа: P{winner} {names[winner]} на ходу {plies}")
            return winner, plies, "ok", time_p1, time_p2, forced_p1, forced_p2

        current = P2 if current == P1 else P1

    if debug:
        print("[DEBUG] max_plies_reached")
    return 0, plies, "max_plies_reached", time_p1, time_p2, forced_p1, forced_p2

def main():
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    ap = argparse.ArgumentParser(description="4x4x4 Connect-4 Arena Tester")
    ap.add_argument("botA", help="Путь к первому боту .py")
    ap.add_argument("botB", help="Путь ко второму боту .py")
    ap.add_argument("--per-move", type=float, default=10.0, help="Секунд на ход (по умолчанию 10.0)")
    ap.add_argument("--debug", action="store_true", help="Подробный вывод по каждому ходу")
    args = ap.parse_args()

    botA_path = os.path.abspath(args.botA)
    botB_path = os.path.abspath(args.botB)
    nameA = os.path.basename(botA_path)
    nameB = os.path.basename(botB_path)

    w1, p1, _r1, t1_p1, t1_p2, f1_p1, f1_p2 = play_game(botA_path, botB_path, first_player=1, per_move_sec=args.per_move, debug=args.debug)
    w2, p2, _r2, t2_p1, t2_p2, f2_p1, f2_p2 = play_game(botA_path, botB_path, first_player=2, per_move_sec=args.per_move, debug=args.debug)

    def winner_name(game_idx, w):
        if w == 0:
            return "ничья"
        if game_idx == 1:
            return nameA if w == P1 else nameB
        else:
            return nameB if w == P1 else nameA

    print(f"Игра 1: {nameA} (черные) vs {nameB} (белые) — победитель: {winner_name(1, w1)} — ходы: {p1}")
    print(f"Игра 2: {nameB} (черные) vs {nameA} (белые) — победитель: {winner_name(2, w2)} — ходы: {p2}")

    # Короткая сводка по форс-ходам (полезно заметить, если боты вообще не ходят)
    if args.debug:
        print(f"[DEBUG] Игра 1: forced P1={f1_p1}, P2={f1_p2}")
        print(f"[DEBUG] Игра 2: forced P1={f2_p1}, P2={f2_p2}")

    a_wins = (1 if winner_name(1, w1) == nameA else 0) + (1 if winner_name(2, w2) == nameA else 0)
    b_wins = (1 if winner_name(1, w1) == nameB else 0) + (1 if winner_name(2, w2) == nameB else 0)

    if a_wins != b_wins:
        overall = nameA if a_wins > b_wins else nameB
    else:
        a_plies_win = (p1 if winner_name(1, w1) == nameA else 0) + (p2 if winner_name(2, w2) == nameA else 0)
        b_plies_win = (p1 if winner_name(1, w1) == nameB else 0) + (p2 if winner_name(2, w2) == nameB else 0)
        if a_plies_win != b_plies_win:
            overall = nameA if a_plies_win < b_plies_win else nameB
        else:
            a_time_win = (t1_p1 if winner_name(1, w1) == nameA else 0.0) + (t2_p2 if winner_name(2, w2) == nameA else 0.0)
            b_time_win = (t1_p2 if winner_name(1, w1) == nameB else 0.0) + (t2_p1 if winner_name(2, w2) == nameB else 0.0)
            if a_time_win == 0.0 and b_time_win == 0.0:
                overall = "ничья по матчам"
            elif a_time_win == 0.0:
                overall = nameB
            elif b_time_win == 0.0:
                overall = nameA
            else:
                overall = nameA if a_time_win < b_time_win else (nameB if b_time_win < a_time_win else "ничья по матчам")

    print(f"Матч: {overall}")

if __name__ == "__main__":
    main()
