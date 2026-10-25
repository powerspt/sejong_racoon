# -*- coding: utf-8 -*-
"""02. 속도 제어: 관절을 속도로 돌리고 멈추기 + 부드러운 가감속"""
from roboid import *

raccoon = Raccoon()
raccoon.degree_to(0, -10, -140, 60)     # Home 에서 시작

# 관절 1 을 +50 (반시계) 으로 1초, 정지
raccoon.velocity(1, 50)
wait(1000)
raccoon.velocity(1, 0)

# 관절 1 을 -50 (시계) 으로 1초, 정지
raccoon.velocity(1, -50)
wait(1000)
raccoon.stop()                          # stop() = 모든 관절 속도 0

# 가감속: 관절 3 을 0 -> 100 -> 0 으로 0.2초마다 10씩
speed = 0
for _ in range(10):
    speed += 10
    raccoon.velocity(3, speed)
    wait(200)
for _ in range(10):
    speed -= 10
    raccoon.velocity(3, speed)
    wait(200)

raccoon.degree_to(0, -10, -140, 60)     # Home 으로 복귀
raccoon.dispose()
