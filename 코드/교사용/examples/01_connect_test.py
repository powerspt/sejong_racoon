# -*- coding: utf-8 -*-
"""01. 연결 확인: 동글 포트 목록, 연결, 배터리/관절 값 읽기, 삐 소리

⚠️ 중요 — roboid 는 연결에 실패해도 예외를 내지 않는다.
   동글이 없으면 "No available USB to BLE bridge" 를 한 줄 찍고 계속 진행하며,
   이후 모든 읽기가 '기본값'을 돌려준다. 그 기본값이 그럴듯해서 더 위험하다.

       battery_state()  -> 2     ("중간"으로 보이지만 그냥 초기값)
       signal_strength()-> 0
       encoder(-1)      -> (0,0,0,0)        (Home 이 아니라 Zero)
       xyz()            -> (0, 0, 28.25)    (= L1+L2+L3, 그리퍼 오프셋도 미적용)

   그래서 이 예제는 값을 찍기 전에 '정말 붙었는지' 를 먼저 확인한다.
"""
import time

from roboid import *


def wait_connected(bot, timeout_s=10.0):
    """연결될 때까지 기다린다.

    Raccoon() 이 돌아와도 아직 연결되지 않았을 수 있고, BLE 특성상
    중간에 끊겼다 붙기도 한다. 한 번만 확인하면 오탐이 난다.
    bot.is_connected() 가 roboid 가 제공하는 공식 판정이다.
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if bot.is_connected():
            return True
        wait(300)
    return False


scan()                      # 시리얼 포트 목록 출력 (동글이 꽂혀 있으면 COMx 가 보인다)

raccoon = Raccoon()         # 연결 + Home 자세로 이동 (자동)

if not wait_connected(raccoon):
    print()
    print("=" * 60)
    print("연결되지 않았습니다. 아래 값을 읽어도 전부 '기본값'입니다.")
    print("=" * 60)
    print("확인 순서:")
    print("  1. USB to BLE 동글이 노트북에 꽂혀 있는가")
    print("     (노트북 내장 블루투스로는 안 된다. 동글은 COM 포트로 보인다)")
    print("  2. 위 'Serial ports:' 목록에 COMx 가 보이는가")
    print("     안 보이면 -> 다른 USB 포트에 직접 꽂기 (허브 말고)")
    print("  3. 로봇 전원이 켜져 있고 배터리가 남아 있는가")
    print("  4. 다른 파이썬 창이 포트를 잡고 있지 않은가 (전부 종료 후 재시도)")
    print("  5. 포트를 직접 지정: Raccoon(0, 'COM26')   <- 인자 두 개다")
else:
    print("\n연결됨")
    print("배터리 상태 (3 정상 / 2 중간 / 1 부족 / 0 없음):", raccoon.battery_state())
    print("충전 중?:", raccoon.charge_state())
    print("신호 세기 [dBm]:", raccoon.signal_strength())
    print("관절 각도 (1,2,3,4):", tuple(round(v, 2) for v in raccoon.encoder(-1)))
    print("그리퍼 끝 좌표 (x,y,z cm):", tuple(round(v, 2) for v in raccoon.xyz()))
    print("  -> Home 자세라면 (0, 14.7, 8.8) 근처여야 한다")
    raccoon.beep()

raccoon.dispose()
