# -*- coding: utf-8 -*-
"""[콘텐츠 ⑩] 자석 경주 · 가상 — 클립이 어디 있는지 모른 채, 어느 칸을 들를지 정한다

    python 10_자석_경주_가상.py          로봇 없이 — 코드가 클립을 아무 데나 흩어 놓는다
    python 10_자석_경주_실기기_A3.py     진짜 로봇 · A3 지도 (B4 는 _B4)

짝이 클립을 칸들에 **아무렇게나** 흩어 놓는다(술래는 안 본다). 술래는 **들를 칸의 순서**만
정하고, 로봇은 그 순서대로 칸마다 자석을 내렸다 들며 붙인 채로 다음 칸으로 간다.
제한 시간이 끝나면 **자석에 붙어 있는 클립을 센다** — 그게 점수다.

    클립이 어디 있는지 모르니, 정할 수 있는 것은 "어디를, 몇 칸, 어떤 순서로" 뿐이다.
    많이 들르면 더 건지지만 시간이 든다. 먼 칸을 오가면 이동만으로 시간이 샌다.

이 파일 하나로 돌아간다 — 로봇을 움직이는 부품은 파일 맨 아래에 있다.
"""
import random
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
칸 = ["C2", "E2", "G2",
     "C3", "E3", "G3",
     "C4", "E4", "G4"]       # 클립을 흩어 놓는 칸 (A3 지도 2~4행 — 집게를 세우지 않고 닿는 칸)
자석높이 = 2.7               # ★ 자석을 내리는 집게 끝 높이 — 08_자석_확인 이 알려 준 권장값을 적는다
클립개수 = 6                 # 흩어 놓는 클립 수
제한시간 = 12.0              # 초 — 아홉 칸을 다 돌려면 20초쯤 든다. 절반쯤만 들를 수 있게 둔다. (가상은 가상 시계, 실기기는 벽시계)
방문순서 = []                # ★ 들를 칸 순서. 비면 실행할 때 입력받는다. 예) ["C2", "E2", "G2", "G3"]
SEED = 7                     # 가상 모드가 클립을 흩어 놓는 자리. 같은 숫자 = 같은 판
시험판수 = 300               # 가상 — 내 순서를 '클립 자리가 매번 다른' 판에 돌려 평균을 낸다
이동속도 = 8.0               # cm/s — 가상 시계용. 실기기는 팔이 직접 가니 안 쓴다
# ─────────────────────────────────────────────────────
# [레벨0] 방문순서 를 바꿔 평균 점수를 올린다 — 많이 들를까, 가깝게 돌까?
# [레벨1] 제한시간 을 15 로 줄이면 어떤 순서가 유리한가
# [레벨2] 이동속도 를 절반으로(먼 칸이 두 배로 비싸진다) — 좋은 순서가 어떻게 바뀌나
# 가상에서는 한 칸을 들르면 그 칸의 클립이 다 붙는다고 친다.


def 거리(a, b):
    (x0, y0), (x1, y1) = cell_to_xy(a), cell_to_xy(b)
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


def 여행(arm, 여기, 저기):
    """가상 모드에서만 — 칸 사이 거리에 비례해 시간을 더한다."""
    if 여기 is not None and hasattr(arm, "t"):
        d = 거리(여기, 저기)
        arm._log(f"MOVE  {여기}→{저기} {d:.0f}cm", d / 이동속도)


def 흩기(rng):
    """클립을 칸들에 아무렇게나 놓는다 — 칸별 개수."""
    자리 = {c: 0 for c in 칸}
    for _ in range(클립개수):
        자리[rng.choice(칸)] += 1
    return 자리


def 순서받기():
    if 방문순서:
        순서 = [c.strip().upper() for c in 방문순서]
    else:
        s = input(f"\n  들를 칸을 순서대로 띄어 적는다 ({' '.join(칸)} 중, 같은 칸 반복 가능) > ")
        순서 = s.replace(",", " ").upper().split()
    모름 = [c for c in 순서 if c not in 칸]
    if 모름 or not 순서:
        raise ValueError(f"칸 {칸} 가운데서 적는다 (잘못된 것: {모름 or '비었다'})")
    return 순서


def 돌리기(arm, 순서, 시간재기):
    """순서대로 들른다. 제한 시간이 넘으면 멈춘다. 실제로 들른 칸 목록을 돌려준다."""
    들른, 지금 = [], None
    for cell in 순서:
        if 시간재기() >= 제한시간:
            print("  시간이 다 됐다.")
            break
        여행(arm, 지금, cell)
        arm.pick_magnet(cell, 자석높이)
        지금 = cell
        들른.append(cell)
        print(f"    {len(들른):2d}번째 {cell}  ({시간재기():5.1f}초)")
    return 들른


def 평균(순서):
    """가상 — 클립 자리가 매번 다른 시험판수 판에 같은 순서를 돌려 평균 점수를 낸다."""
    rng, 합 = random.Random(SEED + 1), 0
    for _ in range(시험판수):
        자리, a2, 지금, 남은 = 흩기(rng), DummyArm(verbose=False), None, None
        남은 = dict(자리)
        점수 = 0
        for cell in 순서:
            if a2.t >= 제한시간:
                break
            여행(a2, 지금, cell)
            a2.pick_magnet(cell, 자석높이)
            지금 = cell
            점수 += 남은[cell]
            남은[cell] = 0
        합 += 점수
    return 합 / 시험판수


def main(arm=None):
    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    실기기 = not hasattr(arm, "t")
    print(__doc__.split("\n\n")[1])
    print(f"\n[경주] 클립 {클립개수}개가 {' '.join(칸)} 어딘가에 흩어져 있다. 제한 시간 {제한시간:g}초.")
    try:
        순서 = 순서받기()
    except ValueError as e:
        print("  !", e)
        return
    print(f"  내 순서: {' '.join(순서)}")

    if 실기기:
        input(f"  술래는 지도를 보지 않는다. 짝이 클립 {클립개수}개를 칸들에 아무렇게나 놓았으면 Enter > ")
        시작 = time.time()
        들른 = 돌리기(arm, 순서, lambda: time.time() - 시작)
        걸림 = time.time() - 시작
        while True:
            n = input("\n  자석에 붙어 있는 클립을 세어 넣으세요 [숫자] > ").strip()
            if n.isdigit():
                점수 = int(n)
                break
    else:
        자리 = 흩기(random.Random(SEED))
        시작 = arm.t
        들른 = 돌리기(arm, 순서, lambda: arm.t - 시작)
        걸림 = arm.t - 시작
        점수 = sum(자리[c] for c in set(들른))
        print("\n  클립이 있던 자리:", "  ".join(f"{c}:{n}" for c, n in 자리.items() if n))

    print("\n" + "=" * 46)
    print(f"들른 칸 {len(들른)}곳 · {걸림:.1f}초 · 자석에 붙은 클립 {점수}개 / {클립개수}개")
    print("=" * 46)
    if not 실기기:
        print(f"  [참고] 같은 순서를 클립 자리가 다른 {시험판수}판에 돌리면 평균 {평균(순서):.2f}개")
    print("\n[생각] 한 판은 운이다. 평균을 올리려면 칸을 더 들를까, 이동을 줄일까?")
    arm.home()
    if hasattr(arm, "summary"):
        print(arm.summary())
    if hasattr(arm, "close"):
        arm.close()


# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도 기준이다. B4 지도는 _실기기_B4.py 가 지도맞추기("B4") 로 바꾼다.
# 집게를 세우지 않으므로 1행(y=8)은 못 닿는다. B4 는 2~3행에 다섯 칸.
지도별 = {
    "A3": dict(칸=["C2", "E2", "G2", "C3", "E3", "G3", "C4", "E4", "G4"]),
    "B4": dict(칸=["B2", "D2", "F2", "B3", "D3"]),
}


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
HOVER = 10.0
SPEED_DOWN = 40
SPEED_MOVE = 60
HOME_POSE = (0, -10, -140, 60)
TILT_RULES = [(15.5, 0, 10.0), (11.0, -45, 8.0), (0.0, -90, 6.0)]
TILT = None
J2_SAFE, J3_SAFE = (-30.0, -60.0)
DOWN_STEPS = 3
MAGNET_TILT = None
MAGNET_Z = 2.7
MAGNET_HOVER = None
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

def last_cell(paper=None):
    xs, ys = MAP_LAYOUT[paper or PAPER]
    return f"{chr(ord('A') + len(xs) - 1)}{len(ys)}"

def cell_to_xy(cell: str, paper=None):
    xs, ys = MAP_LAYOUT[paper or PAPER]
    cell = cell.strip().upper()
    col = ord(cell[0]) - ord('A') if len(cell) == 2 else -1
    row = int(cell[1]) - 1 if len(cell) == 2 and cell[1].isdigit() else -1
    if not (0 <= col < len(xs) and 0 <= row < len(ys)):
        raise ValueError(f'{paper or PAPER} 매트에 없는 칸: {cell!r} (A1~{last_cell(paper)})')
    return (xs[col], ys[row])

def tilt_for(r_cm: float):
    for r_min, alpha, hover in TILT_RULES:
        if r_cm >= r_min:
            return (alpha, hover)
    return (TILT_RULES[-1][1], TILT_RULES[-1][2])

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

    def pick_magnet(self, cell, z=None):
        self.n_pick += 1
        self._log(f'MAG   {cell} 내렸다 들기 (z={(MAGNET_Z if z is None else z)})', self.T_MAGNET)
        return True

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

    def _descend(self, x, y, z_from, z_to, steps=None):
        n = DOWN_STEPS if steps is None else max(1, int(steps))
        for i in range(1, n + 1):
            z = z_from + (z_to - z_from) * i / n
            if not self._goto(x, y, z, SPEED_DOWN):
                return False
        return True

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

    def pick_magnet(self, cell, z=None):
        z = MAGNET_Z if z is None else float(z)
        x, y = cell_to_xy(cell)
        alpha, hover = self._magnet_pose(x, y)
        self._set_tilt(alpha)
        self.bot.close_gripper()
        if not self._goto(x, y, hover):
            return False
        if not self._descend(x, y, hover, z):
            return False
        self._wait(300)
        self._descend(x, y, z, hover)
        return True

    def _magnet_pose(self, x, y):
        if MAGNET_TILT is not None:
            return (MAGNET_TILT, MAGNET_HOVER if MAGNET_HOVER is not None else HOVER)
        alpha, hover = tilt_for((x * x + y * y) ** 0.5)
        return (alpha, MAGNET_HOVER if MAGNET_HOVER is not None else hover)

    def home(self):
        self.bot.unlock()
        self.bot.degree_to(*HOME_POSE)
        self.tilt_now = 0.0

    def close(self):
        self.home()
        self.bot.dispose()

    def summary(self):
        return '실기기 실행 완료'


if __name__ == "__main__":
    main()
