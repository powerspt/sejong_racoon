# -*- coding: utf-8 -*-
"""주제 3 — 작업 공간 (완성)

기본·실습본에 네 가지를 더했다.
  1. 세 기울기(수평 / 45도 / 수직) 를 **로봇을 움직이지 않고** 비교한다
  2. 경계를 이진 탐색으로 **0.1mm 까지** 좁힌다
  3. 경계에서 **어느 관절이 먼저 한계에 걸리는지** 찾아낸다
  4. 단면도를 글자로 그리고, matplotlib 가 있으면 그림 파일로도 저장한다

    python lessons/03_작업공간_완성.py
    (실행하면 로봇 연결 여부를 묻는다 — 그냥 Enter = 계산만.
     matplotlib 가 설치되어 있으면 단면도 그림은 자동으로 저장된다)
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from roboid.raccoon import Raccoon                          # noqa: E402

높이들 = [3, 8, 15]
기울기들 = [(0, "수평 0도"), (-45, "기울임 -45도"), (-90, "수직 -90도")]
한계 = (("j1", -120, 120), ("j2", -90, 30), ("j3", -150, 0), ("j4", -105, 105))


def 계산기(alpha):
    """연결 없이 roboid 의 역기구학만 쓴다.

    roboid 의 역기구학은 '지금 손목 각도를 유지하는 해' 를 찾으므로,
    기울기마다 객체를 따로 만들어야 그 기울기의 작업 공간이 나온다.
    """
    class 오프라인(Raccoon):
        def __init__(s):
            s._pos_ref_dev = Raccoon._REF_GRIPPER
            s._pos_ref_rel = s._pos_ref_abs = (0.0, 0.0, 0.0)
            s._roboid = s
            s._enc = {1: -10.0, 2: -140.0}
            s._enc[3] = alpha - 90.0 - s._enc[1] - s._enc[2]

        def _unit(s, value=None):
            return Raccoon._CM

        def read(s, device_id, arg=None):
            if device_id == Raccoon.ENCODER:
                return s._enc.get(arg, 0.0)
            if device_id == Raccoon.SLOT_R2:
                return 3
            return 0

    return 오프라인()


def 경계_좁히기(bot, z, 되는y, 안되는y, 정밀=0.01):
    """되는 점과 안 되는 점 사이를 반씩 좁혀 경계를 찾는다 (이진 탐색)."""
    while abs(되는y - 안되는y) > 정밀:
        가운데 = (되는y + 안되는y) / 2
        if bot.can_move_to(0, 가운데, z):
            되는y = 가운데
        else:
            안되는y = 가운데
    return 되는y


def 범위_찾기(bot, z):
    """높이 z 에서 정면으로 갈 수 있는 (가장 가까이, 가장 멀리). 없으면 None."""
    굵게 = [y / 10 for y in range(20, 300) if bot.can_move_to(0, y / 10, z)]
    if not 굵게:
        return None
    안쪽 = 경계_좁히기(bot, z, min(굵게), max(2.0, min(굵게) - 0.1))
    바깥 = 경계_좁히기(bot, z, max(굵게), max(굵게) + 0.1)
    return 안쪽, 바깥


def 막은_관절(bot, x, y, z):
    """그 점에 못 가는 이유 — 한계를 넘은 관절들을 돌려준다."""
    각도 = bot.xyz_to_degree(x, y, z)
    if 각도[0] is None:
        return [("해 없음", None, None, None)]
    return [(이름, round(float(v), 1), lo, hi)
            for v, (이름, lo, hi) in zip(각도, 한계) if not lo <= float(v) <= hi]


def 단면도(bot, z, 간격=1.5):
    print(f"\n── 높이 {z}cm ──")
    칸수 = 0
    y = 28.0
    while y >= 2.0:
        줄 = ""
        x = -24.0
        while x <= 24.0:
            되나 = bool(bot.can_move_to(x, y, z))
            줄 += "O" if 되나 else "."
            칸수 += 되나
            x += 간격
        print(f"{y:>5.0f} |{줄}")
        y -= 간격
    가운데 = int(round(24.0 / 간격))        # 줄에서 x=0 이 놓인 칸 번호
    print(" " * 7 + " " * 가운데 + "^ x=0 (로봇 원점)")
    print(f"      갈 수 있는 칸 {칸수}개")


def png_저장(계산기들):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager            # noqa: F401
        matplotlib.rcParams["font.family"] = "Malgun Gothic"
        matplotlib.rcParams["axes.unicode_minus"] = False
    except ImportError:
        print("\nmatplotlib 가 없어 그림은 건너뜁니다 (글자 단면도는 위에 있습니다).")
        return

    fig, axes = plt.subplots(len(기울기들), len(높이들),
                             figsize=(4 * len(높이들), 3.6 * len(기울기들)))
    for i, (alpha, 이름) in enumerate(기울기들):
        bot = 계산기들[alpha]
        for j, z in enumerate(높이들):
            ax = axes[i][j]
            점 = [(x / 2, y / 2) for x in range(-48, 49) for y in range(4, 57)
                  if bot.can_move_to(x / 2, y / 2, z)]
            if 점:
                ax.scatter([p[0] for p in 점], [p[1] for p in 점], s=4, marker="s")
            ax.plot(0, 0, "r+", markersize=12)
            ax.set_title(f"{이름}  z={z}cm", fontsize=10)
            ax.set_xlim(-26, 26)
            ax.set_ylim(0, 30)
            ax.set_aspect("equal")
            ax.grid(alpha=0.3)
    fig.suptitle("라쿤봇 작업 공간 단면도 (빨간 +가 로봇 원점)")
    fig.tight_layout()
    out = "작업공간_단면도.png"
    fig.savefig(out, dpi=110)
    print(f"\n그림 저장: {out}")


def main():
    ans = input("로봇을 연결했나요? [y = can_move_to 대조 / 그냥 Enter = 계산만]: ").strip().lower()
    로봇대조 = ans in ("y", "yes", "ㅛ")

    계산기들 = {alpha: 계산기(alpha) for alpha, _ in 기울기들}

    print("정면(x=0) 으로 갈 수 있는 반경 — 이진 탐색으로 0.1mm 까지")
    print(f"{'기울기':<14}{'높이':>6}{'가장 가까이':>12}{'가장 멀리':>11}{'폭':>8}")
    for alpha, 이름 in 기울기들:
        bot = 계산기들[alpha]
        for z in 높이들:
            r = 범위_찾기(bot, z)
            if r is None:
                print(f"{이름:<14}{z:>6}{'갈 수 있는 곳 없음':>23}")
                continue
            안쪽, 바깥 = r
            print(f"{이름:<14}{z:>6}{안쪽:>12.2f}{바깥:>11.2f}{바깥 - 안쪽:>8.2f}")
        print()

    print("경계 바로 바깥에서 어느 관절이 막는가 (수평, z=5)")
    bot = 계산기들[0]
    for y in (10.0, 12.0, 13.0, 27.0, 28.0, 29.0):
        막힘 = 막은_관절(bot, 0, y, 5)
        상태 = "갈 수 있음" if not 막힘 else ", ".join(
            f"{n} {v}도 (한계 {lo}~{hi})" if lo is not None else n for n, v, lo, hi in 막힘)
        print(f"  y={y:>5.1f} cm   {상태}")

    print("\n글자 단면도 (수평 기울기)")
    for z in 높이들:
        단면도(계산기들[0], z)

    if 로봇대조:
        from roboid import Raccoon as R, wait
        import time
        실물 = R()
        t0 = time.time()
        while time.time() - t0 < 10 and not 실물.is_connected():
            wait(300)
        if not 실물.is_connected():
            print("\n로봇이 연결되지 않아 대조를 건너뜁니다.")
        else:
            실물.unit("cm")
            실물.end_effector("gripper")
            실물.lock_horz()
            wait(500)
            어긋남 = [(x, y) for x in (-20, -10, 0, 10, 20) for y in (6, 12, 18, 24)
                      if bool(실물.can_move_to(x, y, 5)) != bool(계산기들[0].can_move_to(x, y, 5))]
            print(f"\n로봇 대조 (수평, z=5, 20점): "
                  + ("전부 일치" if not 어긋남 else f"★ 어긋남 {어긋남}"))
        실물.dispose()

    png_저장(계산기들)   # matplotlib 가 없으면 스스로 건너뛴다


if __name__ == "__main__":
    main()
