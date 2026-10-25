# -*- coding: utf-8 -*-
"""주제 5 · 13페이지 — 같은 칸, 다른 방향에서 접근하면? (숫자만 바꿔 실행)

    python lessons/ch5_13p.py

출발칸 하나만 바꾼다. "A2"(왼쪽)로 다섯 번 → "G2"(오른쪽)로 바꿔 다섯 번.
두 무리의 점이 다른 자리에 모이면 — 백래시다.
"""
from roboid import *

raccoon = Raccoon()

출발칸 = "A2"      # ← "G2" 로 바꿔 다섯 번 더
z_펜 = 4.0         # ch5_12p 와 같은 값 (펜을 4cm 쯤 내밀어 물린다)

출발 = {"A2": (-16, 12), "G2": (8, 12)}[출발칸]

# 펜 물리기 — 팔을 쭉 펴고 고무줄로 감는다 (표시선을 집게 끝에)
raccoon.move_to(0, 25, 12, 20)
raccoon.open_gripper()
input("고무줄로 감았으면 Enter > ")
raccoon.close_gripper()

for i in range(5):
    raccoon.move_to(출발[0], 출발[1], 10)    # 출발점을 거쳐
    raccoon.move_to(-8, 12, 10)              # C2 위로
    raccoon.move_to(-8, 12, z_펜, 20)        # 콕!
    raccoon.beep()
    raccoon.move_to(-8, 12, 10)

raccoon.degree_to(0, -10, -140, 60)
raccoon.dispose()
