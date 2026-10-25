# -*- coding: utf-8 -*-
"""주제 5 — 작업 지도 (골격 · 빈칸 채우기)

    python lessons/05_작업지도_틀.py
    (변환 검사를 먼저 보여 주고, 로봇 연결 여부를 묻는다 — 그냥 Enter = 검사만)

방법 A(딕셔너리)와 방법 B(계산)가 둘 다 들어 있다.
USE 를 "A" 또는 "B" 로 고르고, 그 이유를 한 줄 주석으로 적는 것까지가 과제다.

TODO 는 세 곳뿐이고 문법은 새로 나오는 것이 없다.
    TODO 1  방법 A 딕셔너리에 나머지 칸 채우기 (다섯 칸은 본보기로 채워 둠)
    TODO 2  Z9 처리 — 잘못된 칸 이름이 오면 뭐라고 말하며 멈출 것인가
    TODO 3  검증 — 아래 세 칸을 손으로 계산해 프로그램과 대조 (주석에 적기)
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

USE = "B"        # "A" = 딕셔너리, "B" = 계산.  ← 고른 이유: (여기에 한 줄)

# ── 방법 A · 딕셔너리 ──────────────────────────────
# TODO 1 ─ 본보기 다섯 칸처럼 나머지를 채운다 (전부 36칸. 시간이 없으면 쓸 칸만)
CELLS = {
    "A1": (-16, 8),      # 본보기
    "A4": (-16, 20),     # 본보기
    "E2": (0, 12),       # 본보기
    "E3": (0, 16),       # 본보기
    "I4": (16, 20),      # 본보기
}

# ── 방법 B · 계산 ─────────────────────────────────
X0, Y0, CELL = -16, 8, 4     # 시작 좌표와 칸 간격 — 매트에 인쇄된 눈금 그대로


def cell_to_xy(cell):
    """'C2' -> (-8, 12). 잘못된 이름은 조용히 넘기지 않는다 (Z9 원칙)."""
    cell = cell.strip().upper()
    if len(cell) != 2 or cell[0] not in "ABCDEFGHI" or cell[1] not in "1234":
        # TODO 2 ─ 멈추면서 '무엇이 왜 잘못인지' 를 말하자. 아래 메시지를 고쳐 쓴다.
        raise ValueError(f"(메시지를 고치세요) 이상한 칸: {cell}")
    if USE == "A":
        if cell not in CELLS:
            raise ValueError(f"딕셔너리에 아직 없는 칸: {cell} — TODO 1")
        return CELLS[cell]
    x = X0 + (ord(cell[0]) - ord("A")) * CELL
    y = Y0 + (int(cell[1]) - 1) * CELL
    return x, y


# TODO 3 ─ 검증: 아래 세 칸을 '손으로' 계산해 결과 옆에 적고, 프로그램과 대조한다.
#   C2 = ( ___ , ___ )     G4 = ( ___ , ___ )     A1 = ( ___ , ___ )


def pick_cell(bot, cell, hover=10.0, grasp=1.5):
    """주제 4의 집기 여섯 걸음 중 approach~lift. 이 함수는 완성되어 있다."""
    from roboid import wait
    x, y = cell_to_xy(cell)
    bot.open_gripper()
    bot.move_to(x, y, hover)
    bot.move_to(x, y, grasp, 40)
    bot.close_gripper()
    wait(700)
    bot.move_to(x, y, hover, 60)


def place_cell(bot, cell, hover=10.0, grasp=1.5):
    from roboid import wait
    x, y = cell_to_xy(cell)
    bot.move_to(x, y, hover)
    bot.move_to(x, y, grasp, 40)
    bot.open_gripper()
    wait(500)
    bot.move_to(x, y, hover, 60)


if __name__ == "__main__":
    # 로봇 없이 먼저 — 변환이 맞는지 화면으로 검사
    for c in ["A1", "C2", "E3", "G4", "I4"]:
        print(f"{c} -> {cell_to_xy(c)}")
    print()
    try:
        cell_to_xy("Z9")
    except ValueError as e:
        print("Z9 ->", e)

    ans = input("로봇을 연결했나요? [y = C2 블록을 G1 로 옮기는 실동작 / 그냥 Enter = 여기까지]: ").strip().lower()
    if ans in ("y", "yes", "ㅛ"):
        from roboid import Raccoon, wait
        bot = Raccoon()
        while not bot.is_connected():
            wait(100)
        input("블록 1개를 C2 십자에 놓았으면 Enter > ")
        pick_cell(bot, "C2")
        place_cell(bot, "G1")
        bot.degree_to(0, -10, -140, 60)
        bot.dispose()
