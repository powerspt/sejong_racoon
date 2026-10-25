# -*- coding: utf-8 -*-
"""주제 3 · 13페이지 — 경계 찾아보기 (숫자만 바꿔 실행)

    python lessons/ch3_13p.py

y 숫자만 바꿔 가며 O(True)/X(False) 경계를 찾는다.
팁: 되는 값과 안 되는 값을 하나씩 들고, 그 사이를 반으로 접는다 (이진 탐색).
높이별 측정(heights)은 z 를 3 / 8 / 15 로 바꿔 같은 일을 반복하면 된다.
"""
from roboid import *

raccoon = Raccoon()

y = 20        # ← 이 숫자만 바꾼다
z = 10        # 높이 (heights 활동에서는 3 / 8 / 15)

print(y, "→", raccoon.can_move_to(0, y, z))
raccoon.dispose()
