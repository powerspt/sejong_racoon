# -*- coding: utf-8 -*-
"""주제 5 · 13페이지 — 같은 칸, 다른 방향에서 접근하면? (숫자만 바꿔 실행)

    python lessons/ch5_13p.py

출발칸 하나만 바꾼다. "A2"(왼쪽)로 다섯 번 → "G2"(오른쪽)로 바꿔 다섯 번.
두 무리의 점이 다른 자리에 모이면 — 백래시(톱니 사이 틈 때문에 방향을 바꾸면 생기는 어긋남)다.
"""
from roboid import *

raccoon = Raccoon()

출발칸 = "A2"      # ← "G2" 로 바꿔 다섯 번 더
z_펜 = 4.0         # ch5_12p 와 같은 값 (눕힌 집게 아래 면에서 펜이 3.5cm 쯤 나오게 물린다)

# 출발칸 이름으로 좌표를 꺼낸다 — "A2" 면 (-16, 12), "G2" 면 (8, 12)
출발 = {"A2": (-16, 12), "G2": (8, 12)}[출발칸]

# 펜 물리기 — 집게는 눕힌 채, 턱 사이에 펜을 세워 넣고 고무줄로 감는다
#   팔을 세운 자세에서 물린다 — 바로 앞으로 뻗으면 가는 길에 집게가 바닥을 스친다
raccoon.degree_to(0, -10, -70, -10, 20)
raccoon.open_gripper()
input("고무줄로 감았으면 (이미 물렸으면 그대로) Enter > ")
raccoon.close_gripper()

for i in range(5):
    raccoon.degree_to(0, -10, -70, -10)      # 팔을 세워 집게를 다시 수평으로 — move_to 만 이어 쓰면 집게가 조금씩 숙여진다
    raccoon.move_to(출발[0], 출발[1], 10)    # 출발점을 거쳐
    raccoon.move_to(-8, 12, 10)              # C2 위로
    raccoon.move_to(-8, 12, z_펜, 20)        # 콕!
    raccoon.beep()
    raccoon.move_to(-8, 12, 10)

raccoon.degree_to(0, -10, -140, 60)
raccoon.dispose()
