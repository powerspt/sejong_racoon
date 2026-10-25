# -*- coding: utf-8 -*-
"""[콘텐츠 ②-2] 로봇이 만든 눈금자 — 자로 재서 로봇을 검증한다

    python extras/02_눈금자_가상.py

로봇에게 **2cm 간격으로 점을 찍으라**고 시킨다. 그러고 그 점들을 **진짜 자로**
재 본다. 2.00cm 가 나오는가? 왜 안 나오는가?

    1회차   y 한 줄에 점을 N 개 찍는다
    2회차   한 줄 아래에 **똑같은 명령**으로 다시 찍는다
    보기    두 줄의 점이 세로로 나란한가? 자로 재어 간격을 적는다
    견주기  명령값 2.00 과 얼마나 다른가(정확도) ·
            1회차와 2회차가 얼마나 다른가(반복정밀도)

이 둘은 다른 것이다. 늘 2.05 가 나오면 **치우침**이라 보정할 수 있고,
1.95~2.05 로 흩어지면 **산포**라 보정으로 못 없앤다. 인공지능이 어느 쪽을
어떻게 다루는지는 docs/오차와_AI.md 에 적어 두었다.

펜을 내린 채로는 x 로만 움직인다 — 점 찍기와 가로선뿐이라 로봇이 잘하는
동작만 쓴다. 먼저 02_공구_높이재기_실기기_A3.py 로 Z_DRAW 를 재어 아래에 적는다.
이 파일 하나로 돌아간다 — 로봇을 움직이는 부품은 파일 맨 아래에 있다.
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):   # 한글이 깨지지 않게
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
Z_DRAW = 4.0           # ★ 펜 쓰는 높이 — 02_공구_높이재기 가 알려 준 z 를 적는다
Z_EASE = 0.0           # 선이 질질 끌리면 0.05 씩 올린다
Z_LIFT = 1.0           # 점 사이에 펜을 드는 높이  — 높이 들수록 손목이 많이 돌아 쓸린다
간격 = 2.0             # 눈금 간격(cm) — 명령값. 이 숫자가 자로 재는 기준이다
눈금수 = 7             # 점 몇 개. 7개면 간격이 6칸 나온다
시작 = (4.0, 12.0)     # 첫 점의 (x, y). 왼쪽(-x)으로 찍어 나간다
줄간격 = -1.2          # 2회차를 찍을 줄의 y 차이 (펜은 들고 움직인다)
회차 = 2               # 몇 번 반복할까. 3 으로 늘리면 산포가 더 잘 보인다
# ─────────────────────────────────────────────────────
# [레벨0] 간격을 1.0 으로 줄여 본다 — 오차 비율이 커지는가?
# [레벨1] 시작 y 를 16 으로 (반경이 커진다) 다시 재서 견준다
# [레벨2] 눈금수를 늘려 줄 끝까지 — 멀어질수록 어긋남이 쌓이는가?


def 한줄_찍기(arm, y, z):
    """y 한 줄에 눈금수 개의 점을 간격 cm 로 찍는다. 명령한 x 들을 돌려준다."""
    xs = [시작[0] - 간격 * i for i in range(눈금수)]
    for i, x in enumerate(xs):
        arm.draw([(x, y)], z, z + Z_LIFT)      # 점 하나 — 내렸다 들기
        print(f"    {i}번 점  x={x:6.2f}")
    return xs


def 기록표(회차수):
    """학생이 자로 재어 적을 표를 화면에 찍는다."""
    print("\n[기록 양식] 자로 재어 적는다 — 점 중심에서 점 중심까지 mm 로")
    머리 = "  칸    " + "".join(f"{i+1}회차   " for i in range(회차수)) + "명령값"
    print(머리)
    print("  " + "-" * (len(머리) - 2))
    for k in range(눈금수 - 1):
        print(f"  {k}-{k+1}   " + "______  " * 회차수 + f" {간격*10:.0f}mm")
    print("  평균  " + "______  " * 회차수 + f" {간격*10:.0f}mm")
    print("  최대-최소(산포)  ______mm")


def 왜_안맞나():
    print("\n[왜 2.00 이 안 나오나] 짐작되는 것부터 하나씩 지워 간다")
    print("  1) 인쇄 배율      작업 지도를 100% 로 안 뽑으면 자부터 틀렸다")
    print("  2) 관절 각도 분해능  모터가 낼 수 있는 각도가 띄엄띄엄하다")
    print("  3) 기어 백래시    방향을 바꿀 때 톱니 틈만큼 늦게 따라온다")
    print("  4) 팔의 처짐      멀리 뻗으면 중력에 휜다 (반경이 클수록 크다)")
    print("  5) 반경 증폭      같은 각도 오차가 팔 끝에서는 r배로 커진다")
    print("                    호의 길이 = r x 각도 — 먼 칸이 더 흩어지는 이유")
    print("  6) 종이·펜        종이가 들뜨거나 펜 끝이 굵으면 점 중심이 흐려진다")
    print("\n  이 가운데 1·6 은 사람이 없앨 수 있고, 2~5 는 로봇의 몫이다.")
    print("  2~5 를 '보정' 과 '산포' 로 갈라 보는 것이 오늘의 핵심이다.")


def main(arm=None):
    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    실기기 = not hasattr(arm, "t")
    저장 = Z_DRAW
    z = 저장 + Z_EASE

    if 실기기:
        if arm.pen_mount(PEN_OUT) is None:
            print("펜을 물리지 못했다 — 여기서 멈춘다.")
            arm.close()
            return
        잰값 = ask_pen_z(저장)          # 펜 길이를 물어 쓰는 높이를 정한다 (기본 = 적어 둔 값)
        if 잰값 is None:
            print("쓰는 높이를 정하지 못했다 — 여기서 멈춘다.")
            arm.close()
            return
        z = 잰값 + Z_EASE
        input("종이를 매트 2~3행에 붙이고 테이프로 고정했으면 Enter > ")

    print(f"\n점 {눈금수}개 · 간격 {간격}cm · {회차}회 반복")
    print(f"한 줄 길이 {간격 * (눈금수 - 1):.1f}cm")
    y = 시작[1]
    for n in range(회차):
        print(f"\n[{n + 1}회차] y={y:.1f}")
        if 실기기 and n:
            input("  앞 줄을 건드리지 않았는지 보고 Enter > ")
        한줄_찍기(arm, y, z)
        y += 줄간격
    arm.pen_park((시작[0] - 간격 * (눈금수 - 1), y - 줄간격))

    print("\n" + "=" * 52)
    print("먼저 **눈으로** 본다 — 두 줄의 점이 세로로 나란한가?")
    print("  나란하지 않다면 같은 명령인데 자리가 다르게 나온 것이다 (산포).")
    기록표(회차)
    왜_안맞나()
    print("\n[다음] 적은 숫자를 들고 docs/오차와_AI.md 를 읽는다 —")
    print("       사람이 자로 잰 이 표가 인공지능이 배우는 '데이터' 와 같은 것이다.")
    print(arm.summary())
    arm.close()



# ── 작업 지도 ────────────────────────────────────────
# 눈금자는 칸 이름이 아니라 cm 좌표로 찍어서 지도가 달라도 같은 자리다.
# 지도맞추기() 는 작업 지도 그림(어느 칸에 놓나)을 맞추려고만 있다.
지도별 = {"A3": {}, "B4": {}}


def 지도맞추기(paper):
    """지도("A3"/"B4")에 맞는 칸 이름으로 설정을 갈아 끼운다. 실기기 파일이 부른다."""
    set_paper(paper)
    globals().update(지도별[paper])

# ══════════════════════════════════════════════════════════════════════
# 여기부터 끝까지는 로봇을 움직이는 부품이다 — 고치지 않는다.
# 바꿔 볼 것은 위의 '설정 — 여기만 바꿔 보세요' 칸에 있다.
# (robot_helpers.py 에서 이 활동이 쓰는 것만 옮겨 왔다)
# ══════════════════════════════════════════════════════════════════════
import math
import os
import sys
import time
MAP_LAYOUT = {'A3': ([-16, -12, -8, -4, 0, 4, 8, 12, 16], [8, 12, 16, 20]), 'B4': ([-12, -8, -4, 0, 4, 8, 12], [8, 12, 16])}
PAPER = 'A3'
WAIT_GRIP_MS = 700
SPEED_DOWN = 40
SPEED_MOVE = 60
HOME_POSE = (0, -10, -140, 60)
TILT = None
J2_SAFE, J3_SAFE = (-30.0, -60.0)
PEN_LIFT = 1.0
PEN_STEPS = (0.4, 0.2, 0.1, 0.05)
PEN_SEG = 0.15
PEN_TILT = -90
PEN_POSE = (0.0, 16.0, 10.0)
PEN_OUT = 4.1
PEN_Y_EPS = 0.02
PEN_Z_GAP = 0.1
PEN_Z_CEIL = 8.8
PEN_PARK_Z = 9.0
PEN_Z_FLOOR = 1.6
PRECISION_MODE = False
L1, L2, L3 = (8.25, 10.0, 10.0)
JOINT_LIMITS = ((-120, 120), (-90, 30), (-150, 0), (-105, 105))

def ik_joints(x, y, z, tilt, ref):
    x, y = (y, -x)
    rx, ry = (ref[0], ref[1])
    alpha = math.radians(tilt)
    beta = math.atan2(ry, rx)
    L = math.sqrt(rx * rx + ry * ry)
    Lx = L * math.cos(alpha + beta)
    Ly = L * math.sin(alpha + beta)
    th1 = math.atan2(y, x)
    x -= Lx * math.cos(th1)
    y -= Lx * math.sin(th1)
    z -= Ly
    c1, s1 = (math.cos(th1), math.sin(th1))
    zL1 = z - L1
    c3 = (x * x + y * y + zL1 * zL1 - L2 * L2 - L3 * L3) / (2 * L2 * L3)
    if c3 * c3 > 1 + 1e-09:
        return None
    s3 = -math.sqrt(max(0.0, 1 - min(c3 * c3, 1.0)))
    th3 = math.atan2(s3, c3)
    M1 = c3 * L3 + L2
    M2 = z - L1
    M3 = s3 * L3
    M4 = c1 * x + s1 * y
    th2 = math.atan2(-M2 * M3 - M1 * M4, M1 * M2 - M3 * M4)
    th1, th2, th3 = (math.degrees(th1), math.degrees(th2), math.degrees(th3))
    return (th1, th2, th3, math.degrees(alpha) - 90 - th2 - th3)

def over_limit(sol):
    if sol is None:
        return [(0, None, None, None)]
    return [(i + 1, v, lo, hi) for i, (v, (lo, hi)) in enumerate(zip(sol, JOINT_LIMITS)) if not lo <= v <= hi]

def set_paper(paper: str):
    global PAPER
    paper = paper.strip().upper()
    if paper not in MAP_LAYOUT:
        raise ValueError(f"모르는 용지: {paper!r} ({' / '.join(MAP_LAYOUT)})")
    PAPER = paper
    xs, ys = MAP_LAYOUT[paper]
    print(f"[작업 지도 {paper}] 가로 A~{chr(ord('A') + len(xs) - 1)} · 세로 1~{len(ys)}")

class DummyArm:
    T_MOVE, T_PICK, T_PLACE = (1.2, 2.6, 2.4)

    def __init__(self, verbose=True):
        self.t = 0.0
        self.n_move = self.n_pick = self.n_place = 0
        self.verbose = verbose

    def _log(self, msg, dt):
        self.t += dt
        if self.verbose:
            print(f'  [가상 {self.t:6.1f}s] {msg}')
    T_MAGNET = 1.5

    def pen_mount(self, out=PEN_OUT):
        self._log(f'PEN   물리기 (가상 — 집게를 아래로, 표시선 {out}cm 에 맞춰 고무줄)', self.T_MOVE)
        return out

    def draw(self, points_xy, z_draw=0.3, z_up=3.0):
        zs = list(z_draw) if isinstance(z_draw, (list, tuple)) else [z_draw] * len(points_xy)
        앞y = None
        for i, ((x, y), z) in enumerate(zip(points_xy, zs)):
            뭐 = '내리기' if i == 0 or abs(y - 앞y) > PEN_Y_EPS else '긋기'
            if 뭐 == '내리기' and i:
                self._log('PEN   들기 (y 가 바뀐다)', 0.3)
            self._log(f'PEN   ({x:5.1f},{y:5.1f}) z={z:4.2f} {뭐}', 0.6)
            앞y = y
        self._log('PEN   들기', 0.3)

    def pen_park(self, xy=None):
        self._log(f'PEN   빠져나오기 (제자리에서 z={PEN_PARK_Z} 까지 올린 뒤 홈)', self.T_MOVE)
        self.home()

    def home(self):
        self._log('HOME', self.T_MOVE)

    def close(self):
        pass

    def summary(self):
        센것 = [f'{이름} {n}회' for 이름, n in (('집기', self.n_pick), ('놓기', self.n_place), ('이동', self.n_move)) if n]
        return (' · '.join(센것) or '한 동작도 안 함') + f' · 가상 소요 {self.t:.0f}초 (약 {self.t / 60:.1f}분)'

class RealArm:

    def __init__(self, tilt=TILT):
        from roboid import Raccoon, wait, wait_until
        self._wait = wait
        self._wait_until = wait_until
        self.tilt_fixed = tilt
        self.tilt_now = 0.0
        self.bot = Raccoon()
        t0 = time.time()
        while not self.bot.is_connected():
            wait(100)
            if time.time() - t0 > 10:
                raise RuntimeError('로봇 연결 실패 — 전원·BLE 확인')
        self.ref = self._tool_offset()
        if PRECISION_MODE and hasattr(self.bot, 'precision_mode'):
            self.bot.precision_mode(True)
        self.bot.open_gripper()
        self.home()

    def _tool_offset(self):
        _, y, z = self.bot.degree_to_xyz(0, 0, 0, 0)
        ref = (z - (L1 + L2 + L3), -y)
        print(f'[공구 오프셋] 앞으로 {ref[0]:.1f}cm · 아래로 {-ref[1]:.1f}cm')
        return ref

    def _solve(self, x, y, z, tilt=None):
        sol = ik_joints(x, y, z, self.tilt_now if tilt is None else tilt, self.ref)
        if over_limit(sol):
            return None
        return sol if self.bot.can_degree_to(*sol) else None

    def _set_tilt(self, alpha):
        if abs(self.tilt_now - alpha) < 1.0:
            return
        j1 = float(self.bot.encoder(1))
        self.bot.unlock()
        if not self.bot.can_degree_to(j1, J2_SAFE, J3_SAFE, alpha):
            print(f'  !! 기울기 {alpha}° 를 잡지 못했다 — 수평 그대로 간다')
            return
        self.bot.degree_to(j1, J2_SAFE, J3_SAFE, alpha, SPEED_MOVE)
        self.tilt_now = alpha

    def _goto(self, x, y, z, speed=SPEED_MOVE) -> bool:
        sol = self._solve(x, y, z)
        if sol is None:
            bad = over_limit(ik_joints(x, y, z, self.tilt_now, self.ref))
            why = ', '.join((f'J{i}={v:.0f}° (한계 {lo}~{hi})' for i, v, lo, hi in bad if v is not None)) or '팔 길이로 닿지 않는 거리'
            print(f'  !! ({x:.1f}, {y:.1f}, {z:.1f}) 에 기울기 {self.tilt_now:g}° 로는 설 수 없다 — {why}')
            print('     사람이 처리해 주세요 (Enter)')
            input()
            return False
        self.bot.degree_to(sol[0], sol[1], sol[2], sol[3], speed)
        return True

    def _goto_hold(self, x, y, z, speed=SPEED_DOWN) -> bool:
        sol = self._solve(x, y, z)
        if sol is None:
            return self._goto(x, y, z, speed)
        self.bot.degree_to(sol[0], sol[1], sol[2], sol[3], speed, wait=False)
        self._wait_until(self.bot._evaluate_joint_state)
        return True

    def _pen_down(self, x, y, z, z_up):
        for 위 in PEN_STEPS:
            if z + 위 < z_up:
                self._goto_hold(x, y, z + 위)
        self._goto_hold(x, y, z)

    def _pen_line(self, x0, y0, z0, x1, y1, z1):
        거리 = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        n = max(1, int(거리 / PEN_SEG + 0.999))
        for k in range(1, n + 1):
            t = k / n
            self._goto_hold(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t, 25)

    def _pen_up(self, x, y, z, z_up):
        for 위 in reversed(PEN_STEPS):
            if z + 위 < z_up:
                self._goto_hold(x, y, z + 위)
        self._goto(x, y, z_up)

    def pen_mount(self, out=PEN_OUT):
        out = max(float(out), PEN_Z_FLOOR)
        self._set_tilt(self.tilt_fixed if self.tilt_fixed is not None else PEN_TILT)
        if not self._goto(*PEN_POSE):
            return None
        self.bot.open_gripper()
        self._wait(WAIT_GRIP_MS)
        print('\n[펜 물리기] 집게가 아래를 향한 채 벌어져 있다. 두 손으로 작업한다.')
        print(f'  0) 펜 끝에서 **{out:.1f}cm** 위에 색연필로 선을 하나 긋는다.')
        print('     (펜 한 자루에 한 번만 해 두면 다음 시간에도 그대로 쓴다)')
        print('  1) 벌어진 턱 사이로 펜을 **위에서 아래로** 내려 끼운다.')
        print('     블록을 쥘 때와 같은 방향이다 — 펜이 턱을 따라 들어간다.')
        print('  2) **표시선이 집게 끝에 오도록** 높이를 맞춘다.')
        print('  3) 고무줄로 집게와 펜을 함께 두세 번 감는다.')
        print('     집게 **바로 아래** 펜 몸통에도 여러 번 감아 턱을 만든다')
        print('     — 그래야 종이에 눌릴 때 펜이 위로 밀려 올라가지 않는다.')
        input('  감았으면 Enter > ')
        self.bot.close_gripper()
        self._wait(WAIT_GRIP_MS)
        print('  집게를 닫았다. 펜을 눌러 보고 밀려 올라가면 고무줄을 더 감는다.')
        input('  단단하면 Enter > ')
        print(f'  물렸다. 기준대로 끼웠으면 닿는 높이는 z={out:g} 안팎이다')
        print('  — 정확한 값은 찍어 보고 정한다.')
        return out

    def draw(self, points_xy, z_draw=0.3, z_up=3.0):
        zs = list(z_draw) if isinstance(z_draw, (list, tuple)) else [z_draw] * len(points_xy)
        if min(zs) < PEN_Z_FLOOR:
            print(f'  !! 쓰는 높이 {min(zs)} 는 집게가 바닥에 닿는 높이다 — {PEN_Z_FLOOR} 로 올려서 간다. 펜을 물렸는지 확인하세요.')
            zs = [max(z, PEN_Z_FLOOR) for z in zs]
        z_up = max(min(z_up, max(zs) + PEN_LIFT), max(zs) + PEN_LIFT)
        x0, y0 = points_xy[0]
        self._set_tilt(self.tilt_fixed if self.tilt_fixed is not None else PEN_TILT)
        self._goto(x0, y0, z_up)
        self._pen_down(x0, y0, zs[0], z_up)
        앞x, 앞y, 앞z = (x0, y0, zs[0])
        for (x, y), z in zip(points_xy[1:], zs[1:]):
            if abs(y - 앞y) > PEN_Y_EPS:
                print(f'  (y 가 {앞y:.1f}→{y:.1f} 로 바뀐다 — 펜을 들고 옮긴다)')
                self._pen_up(앞x, 앞y, z, z_up)
                self._goto(x, y, z_up)
                self._pen_down(x, y, z, z_up)
            else:
                self._pen_line(앞x, 앞y, 앞z, x, y, z)
            앞x, 앞y, 앞z = (x, y, z)
        x1, y1 = points_xy[-1]
        self._pen_up(x1, y1, zs[-1], z_up)

    def pen_park(self, xy=None):
        x, y = xy if xy else (0.0, 14.0)
        for z in (PEN_PARK_Z, PEN_PARK_Z - 1.0, PEN_PARK_Z - 2.0):
            if self._solve(x, y, z) is not None:
                self._goto(x, y, z)
                break
        self._set_tilt(0)
        self.home()

    def home(self):
        self.bot.unlock()
        self.bot.degree_to(*HOME_POSE)
        self.tilt_now = 0.0

    def close(self):
        self.home()
        self.bot.dispose()

    def summary(self):
        return '실기기 실행 완료'

def ask_pen_z(기본=None, 최대=None):
    천장 = PEN_Z_CEIL if 최대 is None else float(최대)
    print('\n[펜 길이] 집게 끝에서 펜 끝까지 몇 cm 인가요?')
    print('          자로 재서 적는다 — 펜마다 다르고 물릴 때마다 달라진다.')
    while True:
        안내 = f'그냥 Enter = 지난번 값 z={float(기본):g}' if 기본 is not None else '그냥 Enter = 그만두기'
        s = input(f'  펜 길이 cm ({안내}) > ').strip()
        if not s:
            if 기본 is None:
                return None
            z = float(기본)
            print(f'  지난번 값 그대로 z = {z:g} 로 쓴다.')
            break
        try:
            길이 = float(s)
        except ValueError:
            print('    ! 숫자로 적으세요. 예: 4.6')
            continue
        z = round(길이 - PEN_Z_GAP, 2)
        print(f'  잰 길이 {길이:g} → 쓰는 높이 z = {z:g}  (닿기만 하는 높이보다 {PEN_Z_GAP:g} 낮춰 잡는다)')
        break
    if z < PEN_Z_FLOOR:
        print(f'  !! z = {z:g} 까지 내려가면 집게가 책상을 긁는다 — {PEN_Z_FLOOR:g} 로 올린다.')
        print('     펜이 덜 나왔다는 뜻이니 고무줄을 풀고 더 내밀어 물리세요.')
        z = PEN_Z_FLOOR
    elif z > 천장:
        print(f'  !! z = {z:g} 에서는 팔이 종이에 못 닿는다 — {천장:g} 로 내린다.')
        print(f'     펜이 집게 아래로 {천장:g}cm 넘게 나왔다는 뜻이다. 덜 내밀어 물리세요.')
        z = 천장
    s = input(f'  z = {z:g} 로 쓸까요? [Enter = 예 / 숫자 = 직접 지정] > ').strip()
    if s:
        try:
            z = max(PEN_Z_FLOOR, min(천장, float(s)))
            print(f'  z = {z:g} 로 한다.')
        except ValueError:
            print(f'    ! 숫자가 아니라 z = {z:g} 를 그대로 쓴다.')
    print('  선이 안 나오면 0.1 내리고, 질질 끌리면 0.1 올린다.')
    return z


if __name__ == "__main__":
    main()
