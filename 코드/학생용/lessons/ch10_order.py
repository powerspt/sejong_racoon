# -*- coding: utf-8 -*-
"""주제 10 — 순서를 바꾸면 얼마나 빨라질까 (리스트만 바꿔 실행)

    python lessons/ch10_order.py

칸들 리스트에 적은 순서대로 칸 위 10cm 를 돌고, 걸린 시간을 찍는다.
같은 여섯 칸을 순서만 바꿔 두 번 돌려 시간을 견준다.
로봇이 연결돼 있어야 한다. 팔 주변 30cm 를 비운다 — 집게는 비워 둔다.
"""
import time

from roboid import *

# ════════ 여기만 바꿔 본다 ════════════════════════════
칸들 = ["A4", "G2", "I3", "B2", "H4", "C3"]   # ← 이 리스트의 순서 = 도는 순서
# 2회차 — 같은 여섯 칸을 기준(왼쪽에서 오른쪽, 가까운 순서 …)을 정해 다시 늘어놓는다
# ════════════════════════════════════════════════════

X = [-16, -12, -8, -4, 0, 4, 8, 12, 16]   # A3 열 A~I
Y = [8, 12, 16, 20]                       # 행 1~4
Z = 10                                    # 칸 위 10cm (z 는 집게 끝 기준, 책상 = 0)


def cell_to_xy(칸):
    """칸 이름을 좌표로 — 주제 5의 변환과 같다. 없는 칸이면 멈춘다."""
    if len(칸) != 2 or not ("A" <= 칸[0] <= "I") or 칸[1] not in "1234":
        raise ValueError(f"없는 칸: {칸}")
    return X[ord(칸[0]) - ord("A")], Y[int(칸[1]) - 1]


raccoon = Raccoon()          # 연결하면서 집게가 열리고 Home 으로 간다
raccoon.lock_horz()          # 집게는 수평 — C1~G1 · E2 는 수평으로 못 간다

# 못 가는 칸이 섞여 있으면 돌기 전에 알려 주고 끝낸다
못가는 = [칸 for 칸 in 칸들 if not raccoon.can_move_to(*cell_to_xy(칸), Z)]
if 못가는:
    print("수평 집게로 못 가는 칸:", " ".join(못가는), "— 다른 칸으로 바꾼다")
else:
    시작 = time.time()
    for 칸 in 칸들:
        x, y = cell_to_xy(칸)
        th1 = raccoon.xyz_to_degree(x, y, Z)[0]
        raccoon.degree_to(th1, -10, -70, -10)   # 팔을 세우고 그 칸 쪽으로 돈 뒤 (바로 가면 먼 칸에서 바닥을 스친다)
        raccoon.move_to(x, y, Z)          # 칸 위 10cm
        print(f"  {칸}  {time.time() - 시작:5.1f}초")
    print(f"순서 {' '.join(칸들)} — 모두 {time.time() - 시작:.1f}초")
    raccoon.degree_to(0, -10, -140, 60)   # Home
raccoon.dispose()
