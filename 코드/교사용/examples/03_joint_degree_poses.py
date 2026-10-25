# -*- coding: utf-8 -*-
"""03. 각도 제어: 기준 자세(Zero / Park / Home) 와 속도 옵션, 상대 이동"""
from roboid import *

ZERO = (0, 0, 0, 0)
PARK = (0, 25, -145, -60)
HOME = (0, -10, -140, 60)

raccoon = Raccoon()

raccoon.degree_to(*ZERO)            # 팔을 위로 쭉 편 기준 자세 (속도 기본 100)
wait(500)
raccoon.degree_to(*PARK, 50)        # 보관 자세, 속도 50
wait(500)
raccoon.degree_to(*HOME, 25)        # Home, 속도 25 (천천히)

# 관절 하나만: degree_to(관절번호, 각도, 속도)
raccoon.degree_to(1, 45, 80)
raccoon.degree_by(1, -90)           # 현재 각도에서 -90 만큼 (45 -> -45)
raccoon.degree_to(1, 0)

# 기다리지 않는 이동 + is_moving 으로 완료 감지
# 주의: 명령 직후 약 0.1초 동안은 is_moving() 이 아직 False 이므로 잠시 기다린 뒤 검사한다.
raccoon.degree_to(0, 0, -90, 0, 60, wait=False)
wait(200)
while raccoon.is_moving():
    print("이동 중...", tuple(round(v, 2) for v in raccoon.encoder(-1)))
    wait(200)
raccoon.stop()

raccoon.degree_to(*HOME)
raccoon.dispose()
