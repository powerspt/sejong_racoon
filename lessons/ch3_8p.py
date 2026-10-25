# -*- coding: utf-8 -*-
"""주제 3 · 8페이지 — 관절은 어디까지 움직일까? (숫자만 바꿔 실행)

    python lessons/ch3_8p.py

j 와 각도 두 숫자만 바꿔 가며 True / False 경계를 찾는다.
can_degree_to 는 로봇을 움직이지 않고 물어보기만 한다 — 빠르고 안전하다.
팁: 0 은 어느 관절이든 항상 되고, ±180 은 어느 관절도 안 된다.
    되는 값과 안 되는 값 사이를 반씩 좁히면 금방 찾는다.
"""
from roboid import *

raccoon = Raccoon()

j = 2          # ← 조사할 관절 번호 (1~4)
각도 = 30      # ← 이 숫자만 바꾼다

print(j, "번 관절", 각도, "도 →", raccoon.can_degree_to(j, 각도))
raccoon.dispose()
