# -*- coding: utf-8 -*-
"""주제 2 — 순기구학 (완성)

기본본에 세 가지를 더했다.
  1. 집게의 **아래 방향 오프셋 0.6cm** 까지 반영 — 기본본의 6mm 차이가 여기서 사라진다
  2. **관절 한계 확인** — 계산은 되지만 로봇은 못 가는 자세를 걸러낸다
  3. **오차 대조표** — 내 계산 vs roboid 공식값을 10자세로 비교하고 원인까지 짚어 준다

    python lessons/02_순기구학_완성.py
    (실행하면 로봇 연결 여부를 묻는다 — 그냥 Enter = 로봇 없이 공식 계산과만 대조)
"""
import math
import sys

# 윈도우 한국어 터미널은 기본 코드페이지가 cp949 라서 출력이 깨지거나 죽는다
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ── 로봇의 치수 (cm). 매뉴얼 1장 ──
L1, L2, L3 = 8.25, 10.0, 10.0
GRIP_FWD = 8.0          # 손목축 -> 집게 끝, 앞으로
GRIP_DOWN = 0.6         # 손목축 -> 집게 끝, 아래로   <- 기본본이 빠뜨린 것

# ── 관절 한계 (매뉴얼 12장). roboid 가 범위를 넘으면 '조용히' 무시한다 ──
LIMITS = ((-120, 120), (-90, 30), (-150, 0), (-105, 105))


def 관절_한계_확인(각도):
    """범위를 벗어난 관절 번호와 값을 돌려준다. 전부 정상이면 빈 목록."""
    return [(i + 1, v, lo, hi)
            for i, (v, (lo, hi)) in enumerate(zip(각도, LIMITS)) if not lo <= v <= hi]


def 순기구학(j1, j2, j3, j4):
    """관절 각도 4개 -> 집게 끝 (x, y, z) cm

    옆에서 본 그림에서 막대 세 개를 잇는다.
      어깨에서 j2, 팔꿈치에서 j2+j3, 손목에서 j2+j3+j4 만큼 기울어진다.
      roboid 는 각도의 +를 '뒤로 젖히는 쪽' 으로 잡으므로 앞으로 간 거리는 부호를 뒤집는다.

    집게는 손목에서 **앞으로 8cm, 아래로 0.6cm** 떨어져 있다.
    손목이 기울면 이 0.6cm 도 같이 돌아가므로, 손목 각도로 회전시켜서 더해야 한다.
    """
    a2 = math.radians(j2)
    a3 = math.radians(j2 + j3)
    a4 = math.radians(j2 + j3 + j4)

    # 팔 세 마디 (손목축까지)
    r = -(L2 * math.sin(a2) + L3 * math.sin(a3))
    z = L1 + L2 * math.cos(a2) + L3 * math.cos(a3)

    # 집게 오프셋을 손목 기울기 a4 만큼 돌려서 더한다.
    # 앞으로 8cm 는 r 에 (부호 뒤집어서), 아래로 0.6cm 는 손목이 누운 만큼 r 과 z 에 나눠 들어간다.
    # 부호를 틀리면 오차가 지워지기는커녕 두 배가 된다 — 실제로 한 번 틀렸다.
    r += -GRIP_FWD * math.sin(a4) + GRIP_DOWN * math.cos(a4)
    z += GRIP_FWD * math.cos(a4) + GRIP_DOWN * math.sin(a4)

    a1 = math.radians(j1)
    return -r * math.sin(a1), r * math.cos(a1), z


# 오차 대조표용 10자세. 가까운 곳 / 먼 곳 / 좌우 / 기울기를 골고루 섞었다
자세들 = [
    ("Home", (0, -10, -140, 60)),
    ("팔 펴기", (0, -45, -90, 45)),
    ("왼쪽 가까이", (30, -20, -120, 40)),
    ("오른쪽 가까이", (-30, -20, -120, 40)),
    ("왼쪽 멀리", (45, -57, -70, 37)),
    ("오른쪽 멀리", (-45, -57, -70, 37)),
    ("정면 멀리", (0, -57, -70, 37)),
    ("정면 가까이", (0, -23, -145, 79)),
    ("수직 집기", (0, -30, -120, 60)),
    ("뒤로 젖힘", (0, 20, -120, 40)),
]


def 로봇_공식값(사용_로봇):
    """roboid 의 degree_to_xyz 를 쓴다. 로봇이 없으면 연결 없이 계산만 한다."""
    from roboid.raccoon import Raccoon
    if 사용_로봇:
        from roboid import Raccoon as R, wait
        import time
        bot = R()
        t0 = time.time()
        while time.time() - t0 < 10 and not bot.is_connected():
            wait(300)
        if not bot.is_connected():
            print("로봇이 연결되지 않았습니다. 연결 없이 계산만 비교합니다.")
            print("  진단: examples/01_connect_test.py")
        else:
            bot.unit("cm")
            bot.end_effector("gripper")
            print(f"로봇 연결됨 (신호 {bot.signal_strength()}dBm)")
            return bot, bot.dispose

    class 오프라인(Raccoon):
        """연결 없이 roboid 의 계산만 빌려 쓴다."""
        def __init__(s):
            s._pos_ref_dev = Raccoon._REF_GRIPPER
            s._pos_ref_rel = s._pos_ref_abs = (0.0, 0.0, 0.0)
            s._roboid = s

        def _unit(s):
            return Raccoon._CM

        def read(s, device_id, arg=None):
            return 3 if device_id == Raccoon.SLOT_R2 else 0    # 서보 그리퍼가 달린 것으로

    return 오프라인(), lambda: None


def main():
    ans = input("로봇을 연결했나요? [y = 로봇과 대조 / 그냥 Enter = 계산만]: ").strip().lower()
    bot, 정리 = 로봇_공식값(ans in ("y", "yes", "ㅛ"))

    print(f"\n{'자세':<14}{'내 계산 (x, y, z)':>26}{'roboid':>26}{'차이(mm)':>10}")
    오차들 = []
    try:
        for 이름, 각도 in 자세들:
            넘음 = 관절_한계_확인(각도)
            내값 = 순기구학(*각도)
            공식 = tuple(bot.degree_to_xyz(*각도))
            차이 = math.dist(내값, 공식) * 10
            오차들.append(차이)
            표시 = f"{이름:<14}{str(tuple(round(v, 2) for v in 내값)):>26}" \
                   f"{str(tuple(round(v, 2) for v in 공식)):>26}{차이:>10.2f}"
            if 넘음:
                표시 += "   ★ 관절 " + ", ".join(
                    f"{i}={v}°(한계 {lo}~{hi})" for i, v, lo, hi in 넘음)
            print(표시)
    finally:
        정리()

    최대 = max(오차들)
    print("-" * 76)
    print(f"최대 차이 {최대:.2f} mm   평균 {sum(오차들)/len(오차들):.2f} mm")

    print("\n[해석]")
    퍼짐 = 최대 - min(오차들)
    if 최대 < 0.1:
        print("  · 내 계산이 roboid 와 같다. 순기구학을 제대로 세운 것이다.")
    elif 퍼짐 < 0.5:
        print(f"  · 차이가 모든 자세에서 거의 같다 ({최대:.1f}mm). -> **상수 오프셋**을 빠뜨렸다.")
        print("    집게 기준점(앞 8cm, 아래 0.6cm) 중 하나를 안 넣지 않았는가?")
    else:
        print("  · 차이가 자세마다 다르다. -> 각도 기준선이나 부호 규약이 다르다.")
        print("    한 관절씩 0으로 고정하고 비교하면 어느 관절인지 좁힐 수 있다.")

    # ── 관절 한계: 계산되는 것과 갈 수 있는 것은 다르다 ──
    print(f"\n{'─' * 76}")
    print("[계산은 되지만 로봇이 못 가는 자세]")
    for 이름, 각도 in [("한계 안 (최대 범위)", (120, -90, -150, 105)),
                      ("j2 가 +35 (한계 +30)", (0, 35, -140, 60)),
                      ("j3 가 +10 (한계 0)", (0, -10, 10, 60))]:
        넘음 = 관절_한계_확인(각도)
        x, y, z = 순기구학(*각도)
        상태 = "갈 수 있음" if not 넘음 else "★ " + ", ".join(
            f"관절{i}={v}° (한계 {lo}~{hi})" for i, v, lo, hi in 넘음)
        print(f"  {이름:<22}{str(각도):<24} -> ({x:6.1f},{y:6.1f},{z:6.1f})   {상태}")
    print("  순기구학은 어떤 각도를 넣어도 답을 내놓는다. 그 자세가 **가능한지는 따로 봐야 한다.**")
    print("  roboid 는 범위를 넘는 명령을 경고 없이 무시하므로(매뉴얼 13장),")
    print("  보내기 전에 can_degree_to() 로 확인하는 습관을 들여야 한다.")


if __name__ == "__main__":
    main()
