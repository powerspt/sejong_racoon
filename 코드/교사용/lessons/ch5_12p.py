# -*- coding: utf-8 -*-
"""주제 5 · 12페이지 — 반복정밀도 측정 (숫자만 바꿔 실행)

    python lessons/ch5_12p.py

z_펜 높이로 10번 반복해 C2 에 점 10개를 찍는다.
칸을 바꾸려면 x, y 를 — 먼 칸 A4 = (-16, 20), 가까운 칸 E1 = (0, 8).

**펜은 고무줄이 잡는다.** 집게의 쥐는 힘으로는 눌리는 순간 미끄러진다.
집게는 닫아 두기만 하고 하중은 고무줄이 받는다.

높이는 **펜에 그어 둔 표시선**으로 맞춘다 — 펜 끝에서 z_펜 만큼 위에 색연필로
선을 하나 긋고, 그 선이 집게 끝에 오도록 끼워 감는다. 그러면 종이에 닿는 집게
높이가 곧 z_펜 이다. z 는 **집게 끝** 높이지 펜 끝이 아니다.

**1.5 아래로는 내리지 않는다** — 거기는 집게 손가락이 책상에 닿는 높이다.
"""
from roboid import *

raccoon = Raccoon()

x, y = -8, 12     # C2 칸
z_펜 = 4.0        # ← 펜을 4cm 쯤 내밀어 물렸을 때의 값 (1.5 아래 금지)

# 펜 물리기 — 팔을 쭉 펴고 고무줄로 감는다 (표시선을 집게 끝에)
raccoon.move_to(0, 25, 12, 20)
raccoon.open_gripper()
input("고무줄로 감았으면 Enter > ")
raccoon.close_gripper()

for i in range(10):
    raccoon.move_to(x, y, 10)
    raccoon.move_to(x, y, z_펜, 20)   # 콕!
    raccoon.beep()
    raccoon.move_to(x, y, 10)
    raccoon.degree_to(0, -10, -140, 60)   # 홈에서 다시 출발

raccoon.dispose()
