# -*- coding: utf-8 -*-
"""작업 지도(매트) 공통 모듈 — 칸 이름/좌표, 기울기 구역, 정렬 보정 계산

  examples/07_fk_measure.py   (영역별 오차 측정) 와
  examples/08_map_calibrate.py (정렬 보정) 가 같은 정의를 쓰도록 여기 모아 둔다.

칸 이름 규칙은 make_work_mat.py 가 매트에 인쇄하는 것과 같다.
  열 = A, B, C ... (왼쪽부터)      행 = 1, 2, 3 ... (로봇에서 가까운 쪽부터)
"""

import math

try:
    from . import config as cfg
except ImportError:                     # 스크립트로 직접 실행할 때
    import config as cfg

# 매트 격자 (cm). make_work_mat.py 와 같은 값을 쓴다 (config 가 원본).
LAYOUT = cfg.MAP_LAYOUT

MEASURE_Z = 6.0     # 오차를 잴 때 쓰는 공통 높이(cm).
# 구역마다 hover 높이가 다르지만(TILT_RULES: 10/8/6), 잴 때는 하나로 고정한다.
# 다림추 실 길이가 하나뿐이라 높이가 다르면 실이 늘어져 추가 집게 바로 아래에 있지 않게 된다.
# 전 칸이 자기 기울기로 z=4~10cm 어디서든 닿는 것을 확인했으므로 6cm 로 통일해도 잃는 게 없다.


def choose_paper(ask, script):
    """매트 종류를 정한다. 인자로 안 왔으면 물어본다.

    argparse 의 required=True 로 두면 IDE 실행 버튼처럼 인자 없이 돌릴 때
    SystemExit(2) 가 나서 디버거가 예외로 잡는다. 그래서 직접 묻는다.
    기본값을 두지 않는 이유는 따로 있다 - B4 를 깔아 놓고 A3 좌표로 보내면
    매트 밖으로 간다. 실제로 겪었다.
    """
    print("\n어느 작업 지도를 깔았습니까?")
    for name in LAYOUT:
        xs, ys = LAYOUT[name]
        print(f"  {name}: {len(xs)} x {len(ys)} = {len(xs)*len(ys)}칸"
              f"   (열 {chr(64+1)}~{chr(64+len(xs))}, 행 1~{len(ys)})")
    v = ask("  A3 또는 B4 를 입력하세요: ")
    if v is None:
        print("\n이 창은 키보드 입력을 받을 수 없습니다. 매트 종류를 인자로 주세요:")
        for name in LAYOUT:
            print(f"    python examples/{script} --paper {name}")
        return None
    v = v.strip().upper()
    if v in LAYOUT:
        return v
    print(f"  A3 또는 B4 중에서 입력하세요 (받은 값: {v!r})")
    return None


def all_cells(paper):
    """매트의 모든 칸 이름 -> (x, y) cm"""
    xs, ys = LAYOUT[paper]
    return {f"{chr(ord('A') + ci)}{ri + 1}": (x, y)
            for ci, x in enumerate(xs) for ri, y in enumerate(ys)}


def tilt_for(r_cm):
    """반경 r 에 맞는 (기울기 alpha°, hover 높이 cm). config.TILT_RULES 참조.
    alpha 는 0 = 수평, -90 = 수직 아래. roboid 내부의 alpha 와 같은 정의다."""
    for r_min, alpha, hover in cfg.TILT_RULES:
        if r_cm >= r_min:
            return alpha, hover
    return cfg.TILT_RULES[-1][1], cfg.TILT_RULES[-1][2]


def zone_of(x, y):
    """그 칸이 속한 기울기 구역(alpha°)"""
    return tilt_for(math.hypot(x, y))[0]


# 영역별 오차 측정에 쓰는 칸. 구역마다 좌 / 중 / 우 로 넓게 잡았다.
# 전부 '제 기울기' 로 z = MEASURE_Z 에서 도달 가능한 것을 확인했다.
ZONE_CELLS = {
    "A3": {0: ["A1", "E4", "I1"], -45: ["B1", "E2", "H1"], -90: ["D1", "E1", "F1"]},
    "B4": {0: ["A3", "D3", "G3"], -45: ["A1", "D2", "G1"], -90: ["C1", "D1", "E1"]},
}

# 정렬 보정(08)에 쓰는 칸. 전부 '수평' 으로 도달 가능해야 한다 — 기울기를 하나로 고정해야
# 그리퍼 오프셋 오차가 모든 점에 똑같이 실려 평행이동으로 흡수되기 때문이다.
# (주의: TILT_RULES 의 r>=15.5 '0도 구역' 은 *집기* 좋은 조건이지 *도달* 조건이 아니다.
#  수평으로는 r 이 13cm 쯤부터 닿는다. 실측: B4 A1(r14.4) 닿음 / D2(r12.0) 안 닿음)
CALIB_CELLS = {
    "A3": ["A1", "I1", "A4", "I4", "E3"],
    "B4": ["A1", "G1", "A2", "G2", "A3", "G3"],
}

# 거친 정렬에 쓰는 두 칸. 첫 칸으로 위치를, 둘째 칸으로 회전을 잡는다.
ALIGN_CELLS = {"A3": ("E3", "I3"), "B4": ("D3", "G3")}


# 기울기를 바꾸기 전에 거쳐 가는 '세운' 자세의 어깨/팔꿈치 각도.
# J2 + J3 = -90 이므로 J4 = alpha 가 되어 계산이 깔끔하다.
J2_SAFE, J3_SAFE = -30.0, -60.0
TIP_MIN_Z = 4.0         # 손목을 돌리는 동안 집게 끝이 이보다 낮아지면 먼저 팔을 세운다


def offline_calc(alpha=0.0):
    """로봇 없이 roboid 의 기구학만 쓰는 객체.

    roboid 의 역기구학은 '지금 손목 각도를 유지하는 해' 를 찾으므로,
    기울기마다 따로 만들어야 그 기울기의 도달 범위가 나온다.
    팔을 움직이지 않고 여러 기울기를 비교할 때 쓴다.
    """
    from roboid.raccoon import Raccoon

    class _Offline(Raccoon):
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
                return 3            # 서보 그리퍼가 달린 것으로
            return 0

        def signal_strength(s):
            return 0

        def dispose(s):
            pass

    return _Offline()


def reaches(alpha, x, y, zs):
    """기울기 alpha 로 (x, y) 를 zs 의 모든 높이에서 닿는가."""
    c = offline_calc(alpha)
    return all(c.can_move_to(x, y, z) for z in zs)


def common_tilt(paper, cells_wanted, zs, prefer=(-45, 0, -90)):
    """주어진 칸들을 **하나의 기울기**로 전부 닿을 수 있는가. 없으면 None.

    집은 채로 손목을 돌리면 물체가 눕거나 굴러 떨어진다 (실측 확인).
    그래서 집어 옮길 때는 기울기를 하나로 고정하는 편이 낫다.
    -45도가 가장 넓게 닿으므로 먼저 본다.
    """
    pts = [all_cells(paper)[c] for c in cells_wanted]
    for alpha in prefer:
        if all(reaches(alpha, x, y, zs) for x, y in pts):
            return alpha
    return None


def safe_tilt(bot, alpha, say=print):
    """그리퍼 기울기를 **안전하게** 바꾼다. roboid 의 Raccoon 객체를 그대로 받는다.

    ⚠️ 낮은 곳에서 손목만 돌리면 집게가 바닥을 긁는다.
       집게 끝은 손목에서 8cm 떨어져 있어서, 손목을 제자리에 두고 기울기만 바꾸면
       끝이 원을 그리며 내려온다. 0도 -> -90도 면 7.4cm 내려간다.
       측정 높이 6cm 에서 돌리면 6 - 7.4 = -1.4cm, 즉 매트를 뚫는다.

       roboid 는 막아 주지 않는다. can_degree_to 는 '관절 범위 안인가' 만 보지
       '안전한가' 를 보지 않고, 책상이라는 개념 자체가 없다 (can_move_to(0,20,0) 도 True).
       그래서 **돌리면 끝이 어디로 갈지 degree_to_xyz 로 미리 물어보고**,
       너무 낮으면 팔을 세운 뒤에 돌린다. 값 자체는 roboid 가 정확히 알려 준다.

    move_to 는 현재 손목 방향을 유지하므로, 한 번 잡아 두면 이후 좌표 이동 내내 유지된다.
    """
    j1, j2, j3, j4 = (float(v) for v in bot.encoder(-1))
    cur = j2 + j3 + j4 + 90
    if abs(cur - alpha) < 1.0:              # 이미 그 기울기면 할 일 없다
        return True

    z_after = bot.degree_to_xyz(j1, j2, j3, alpha - 90 - j2 - j3)[2]
    if z_after < TIP_MIN_Z:
        if not (bot.can_degree_to(j1, J2_SAFE, J3_SAFE, cur)
                and bot.can_degree_to(j1, J2_SAFE, J3_SAFE, alpha)):
            say(f"  ! 기울기 {alpha}도로 안전하게 바꿀 자세가 없습니다 (끝이 {z_after:.1f}cm 로 내려감)")
            return False
        say(f"  팔을 먼저 세웁니다 (그대로 돌리면 집게 끝 {z_after:.1f}cm — 바닥에 닿음)")
        bot.unlock()
        bot.degree_to(j1, J2_SAFE, J3_SAFE, cur)        # 기울기는 유지한 채 올리기만
        _, j2, j3, _ = (float(v) for v in bot.encoder(-1))

    if alpha == 0:
        bot.lock_horz()
        return True
    if alpha == -90:
        bot.lock_vert()
        return True
    bot.unlock()
    j4 = alpha - 90 - j2 - j3
    if not bot.can_degree_to(4, j4):
        say(f"  ! 기울기 {alpha}도 불가 (관절4 {j4:.1f}도가 범위 밖)")
        return False
    bot.degree_to(4, j4)
    return True


def fit_similarity(nominal, measured):
    """nominal -> measured 를 가장 잘 맞추는 (배율 s, 회전 deg, 평행이동 tx, ty).

    nominal  = 매트에 인쇄된 칸 중심 좌표 (mm)
    measured = 로봇이 실제로 가리킨 곳을 매트 좌표로 읽은 값 = nominal + Δ (mm)
    """
    n = len(nominal)
    px = sum(p[0] for p in nominal) / n
    py = sum(p[1] for p in nominal) / n
    mx = sum(m[0] for m in measured) / n
    my = sum(m[1] for m in measured) / n

    sxx = syy = sxy = syx = spp = 0.0
    for (a, b), (c, d) in zip(nominal, measured):
        a -= px; b -= py; c -= mx; d -= my
        sxx += a * c; syy += b * d
        sxy += a * d; syx += b * c
        spp += a * a + b * b

    th = math.atan2(sxy - syx, sxx + syy)
    s = (((sxx + syy) * math.cos(th) + (sxy - syx) * math.sin(th)) / spp) if spp else 1.0
    tx = mx - s * (math.cos(th) * px - math.sin(th) * py)
    ty = my - s * (math.sin(th) * px + math.cos(th) * py)
    return s, math.degrees(th), tx, ty


def residuals(nominal, measured, s, th_deg, tx, ty):
    """맞춘 변환으로 설명되지 않고 남는 양 (mm). 각 점마다 (거리, dx, dy)."""
    th = math.radians(th_deg)
    out = []
    for (a, b), (c, d) in zip(nominal, measured):
        ex = s * (math.cos(th) * a - math.sin(th) * b) + tx
        ey = s * (math.sin(th) * a + math.cos(th) * b) + ty
        out.append((math.hypot(c - ex, d - ey), c - ex, d - ey))
    return out
