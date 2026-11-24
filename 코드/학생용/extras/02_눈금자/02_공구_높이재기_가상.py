# -*- coding: utf-8 -*-
"""[콘텐츠 ②-0] 공구 높이 재기 — 집게에 무엇을 달았든, 그 장치가 일하는 z 를 재서 적는다

    python 02_공구_높이재기_가상.py           로봇 없이 — 재는 순서만 본다
    python 02_공구_높이재기_실기기_A3.py      진짜 로봇으로 잰다 (B4 지도는 _B4)

로봇이 말하는 z 는 **펜 끝 높이가 아니다.** 자로 잰 펜 길이를 z 로 적으면 안 된다.
집게를 아래로 향해 닫으면 손가락 끝이 z 보다 1.5cm 쯤 낮고, 펜 끝은 거기서 더 내려와 있다.
자석을 붙이면 자력이 닿는 거리가 따로 있다. 그래서 장치마다 '일하는 z' 가 다르고,
**계산으로는 모른다 — 찍어 보고 재는 수밖에 없다.** 이 파일이 그 재는 과정이다.

    1) 무엇을 달았나 고른다       펜 · 자석 · 다른 것
    2) 높은 데서 내려오며 묻는다   "점이 찍혔나?" / "클립이 붙었나?" — 사람이 본다
       (펜은 손가락 맨 끝에서 펜 끝까지를 먼저 묻는다 — 그보다 3.5cm 높은 데서 시작하려는 것이다)
    3) 처음 된 높이에 여유를 둔다   펜은 0.1 낮게, 자석은 0.5 낮게(더 가까이)
    4) 화면에 나온 z 를 활동 파일에 적는다   펜 → 02_눈금자_가상.py 의 Z_DRAW
                                            자석 → 09·10 _가상.py 의 자석높이

왜 두 자리인가(펜만) — 종이 면이 로봇의 z 평면과 나란하다는 보장이 없다. 가까운
쪽과 먼 쪽을 따로 재서 두 값이 다르면 종이가 기울어 있다는 뜻이다.

이 파일 하나로 돌아간다 — 로봇을 움직이는 부품은 파일 맨 아래에 있다.
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ── 로봇 부품 값 (아래 코드가 바로 쓴다) — 고치지 않는다 ──
class Stopped(Exception):
    pass

def 안전하게(main):
    import functools

    @functools.wraps(main)
    def 감싼(*a, **k):
        try:
            return main(*a, **k)
        except Stopped as e:
            print(f'\n  ■ 멈춤 — {e}')
        except KeyboardInterrupt:
            print('\n  ■ 사람이 멈췄다 (Ctrl+C)')
        finally:
            팔 = RealArm.live
            if 팔 is not None and (not 팔.closed):
                팔.close(home=False)
    return 감싼
MAP_LAYOUT = {'A3': ([-16, -12, -8, -4, 0, 4, 8, 12, 16], [8, 12, 16, 20]), 'B4': ([-12, -8, -4, 0, 4, 8, 12], [8, 12, 16])}
PAPER = 'A3'
HOVER = 10.0
WAIT_GRIP_MS = 700
SPEED_DOWN = 40
SPEED_MOVE = 60
HOME_POSE = (0, -10, -140, 60)
TILT_RULES = [(15.5, 0, 10.0), (11.0, -45, 8.0), (0.0, -90, 6.0)]
TILT = None
J2_SAFE, J3_SAFE = (-30.0, -60.0)
DOWN_STEPS = 3
PEN_LIFT = 1.0
PEN_STEPS = (0.4, 0.2, 0.1, 0.05)
PEN_SEG = 0.15
PEN_TILT = -90
PEN_POSE = (0.0, 16.0, 10.0)
PEN_OUT = 2.5
MAGNET_TILT = None
MAGNET_Z = 2.7
MAGNET_HOVER = None
PEN_Y_EPS = 0.02
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
PATH_Z_MIN = 3.0

def tip_z(sol, ref):
    t2 = math.radians(sol[1])
    t3 = t2 + math.radians(sol[2])
    al = math.radians(sol[1] + sol[2] + sol[3] + 90)
    return L1 + L2 * math.cos(t2) + L3 * math.cos(t3) + ref[0] * math.sin(al) + ref[1] * math.cos(al)

def path_low(a, b, ref):
    d = [b[i] - a[i] for i in range(4)]
    m = max((abs(x) for x in d))
    if m < 1e-06:
        return tip_z(b, ref)
    low = 1000000000.0
    for k in range(41):
        간 = m * k / 40
        j = [a[i] + math.copysign(min(abs(d[i]), 간), d[i]) for i in range(4)]
        low = min(low, tip_z(j, ref))
    return low

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
        raise ValueError(f'{paper or PAPER} 작업 지도에 없는 칸: {cell!r} (A1~{last_cell(paper)})')
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

    def pen_mount(self, out=PEN_OUT):
        self._log('PEN   물리기 (가상 — 집게를 아래로 끼우고 고무줄, 끼운 자리에 선을 긋는다)', self.T_MOVE)
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

    def close(self, home=None):
        pass

class RealArm:
    live = None

    def __init__(self, tilt=TILT):
        from roboid import Raccoon, wait, wait_until
        self._wait = wait
        self._wait_until = wait_until
        self.tilt_fixed = tilt
        self.tilt_now = 0.0
        self.failed = False
        self.closed = False
        self.last = None
        self.bot = Raccoon()
        t0 = time.time()
        while not self.bot.is_connected():
            wait(100)
            if time.time() - t0 > 10:
                self.bot.dispose()
                raise RuntimeError('로봇 연결 실패 — 전원·BLE 확인')
        RealArm.live = self
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
        self.last = (j1, J2_SAFE, J3_SAFE, alpha)

    def _raise_if_low(self, sol):
        if self.last is None:
            return
        low = path_low(self.last, sol, self.ref)
        if low >= PATH_Z_MIN or low >= min(tip_z(self.last, self.ref), tip_z(sol, self.ref)) - 0.5:
            return
        for j1 in (self.last[0], sol[0]):
            if self.bot.can_degree_to(j1, J2_SAFE, J3_SAFE, self.tilt_now):
                self.bot.degree_to(j1, J2_SAFE, J3_SAFE, self.tilt_now, SPEED_MOVE)
                self.last = (j1, J2_SAFE, J3_SAFE, self.tilt_now)

    def _descend(self, x, y, z_from, z_to, steps=None, ask=True):
        n = DOWN_STEPS if steps is None else max(1, int(steps))
        for i in range(1, n + 1):
            z = z_from + (z_to - z_from) * i / n
            if not self._goto(x, y, z, SPEED_DOWN, ask):
                return False
        return True

    def _why(self, x, y, z, tilt):
        bad = over_limit(ik_joints(x, y, z, tilt, self.ref))
        return ', '.join((f'J{i}={v:.0f}° (한계 {lo}~{hi})' for i, v, lo, hi in bad if v is not None)) or '팔 길이로 닿지 않는 거리'

    def _reach(self, 칸, x, y, 위, 아래):
        if not (self._goto(x, y, 위, ask=False) and self._descend(x, y, 위, 아래, ask=False)):
            raise Stopped(f'{칸} 칸에 높이 {아래:g} 로는 갈 수 없다 — 칸이나 높이를 바꾼다')

    def _lift(self, 칸, x, y, 아래, 위):
        if not self._descend(x, y, 아래, 위, ask=False):
            raise Stopped(f'{칸} 칸에서 높이 {위:g} 로 올라오지 못했다')

    def _goto(self, x, y, z, speed=SPEED_MOVE, ask=True) -> bool:
        sol = self._solve(x, y, z)
        if sol is None:
            print(f'  !! ({x:.1f}, {y:.1f}, {z:.1f}) 에 기울기 {self.tilt_now:g}° 로는 설 수 없다 — {self._why(x, y, z, self.tilt_now)}')
            self.failed = True
            if ask:
                print('     사람이 처리해 주세요 (Enter)')
                input()
            return False
        self._raise_if_low(sol)
        self.bot.degree_to(sol[0], sol[1], sol[2], sol[3], speed)
        self.last = tuple(sol)
        return True

    def _goto_hold(self, x, y, z, speed=SPEED_DOWN) -> bool:
        sol = self._solve(x, y, z)
        if sol is None:
            return self._goto(x, y, z, speed)
        self.bot.degree_to(sol[0], sol[1], sol[2], sol[3], speed, wait=False)
        self._wait_until(self.bot._evaluate_joint_state)
        self.last = tuple(sol)
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
        print('  1) 벌어진 턱 사이로 펜을 **위에서 아래로** 내려 끼운다.')
        print('     블록을 쥘 때와 같은 방향이다 — 펜이 턱을 따라 들어간다.')
        print('     손가락 맨 끝에서 펜 끝까지 **2~3cm** 나오게 한다 (2.5cm 면 z 4.0 쯤에서 닿는다).')
        print('     펜에 지난번에 그은 선이 있으면 **그 선을 집게 끝에 맞춘다.**')
        print('  2) 고무줄로 집게와 펜을 함께 두세 번 감는다.')
        print('     집게 **바로 아래** 펜 몸통에도 여러 번 감아 턱을 만든다')
        print('     — 그래야 종이에 눌릴 때 펜이 위로 밀려 올라가지 않는다.')
        input('  감았으면 Enter > ')
        self.bot.close_gripper()
        self._wait(WAIT_GRIP_MS)
        print('  집게를 닫았다. 펜을 눌러 보고 밀려 올라가면 고무줄을 더 감는다.')
        input('  단단하면 Enter > ')
        print('  3) 선이 없는 펜이면 **지금 집게 끝이 닿는 자리에** 색연필로 선을 하나 긋는다.')
        print('     다음에 이 선을 집게 끝에 맞춰 끼우면 이번에 잰 높이를 그대로 쓴다.')
        print('  물렸다. 쓰는 높이는 02_공구_높이재기 로 잰다 — 새로 끼웠으면 다시 잰다.')
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

    def pick_magnet(self, cell, z=None):
        z = MAGNET_Z if z is None else float(z)
        x, y = cell_to_xy(cell)
        alpha, hover = self._magnet_pose(x, y)
        self._set_tilt(alpha)
        self.bot.close_gripper()
        self._reach(cell, x, y, hover, z)
        self._wait(300)
        self._lift(cell, x, y, z, hover)
        return True

    def _magnet_pose(self, x, y):
        if MAGNET_TILT is not None:
            return (MAGNET_TILT, MAGNET_HOVER if MAGNET_HOVER is not None else HOVER)
        alpha, hover = tilt_for((x * x + y * y) ** 0.5)
        return (alpha, MAGNET_HOVER if MAGNET_HOVER is not None else hover)

    def pen_park(self, xy=None):
        x, y = xy if xy else (0.0, 14.0)
        for z in (PEN_PARK_Z, PEN_PARK_Z - 1.0, PEN_PARK_Z - 2.0):
            if self._solve(x, y, z) is not None:
                self._goto(x, y, z)
                break
        self._set_tilt(0)
        self.home()

    def home(self):
        if self.last is not None and abs(self.tilt_now) >= 1.0:
            self._set_tilt(0)
        self.bot.unlock()
        self.bot.degree_to(*HOME_POSE)
        self.tilt_now = 0.0
        self.last = HOME_POSE

    def close(self, home=None):
        if self.closed:
            return
        self.closed = True
        if home is None:
            home = not self.failed and sys.exc_info()[0] is None
        try:
            if home:
                self.home()
            else:
                self.bot.stop()
                print('  (중단 — 팔을 그 자리에 세웠다. Home 으로 돌아가지 않는다)')
        finally:
            self.bot.dispose()
팔 = None

# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
가까운칸 = "E2"          # (0, 12) — 재는 자리. 종이·클립을 여기 둔다
먼칸 = "E3"             # (0, 16) — 펜은 먼 자리도 잰다 (종이가 기울었는지)
START_Z = 5.0           # 처음 시험할 높이의 아래 한계. 펜은 나온 길이를 물어 이보다 높은 데서 시작한다
시작여유 = 3.5          # 펜 — 적은 '나온 길이' 보다 이만큼 높은 데서 내려오기 시작한다 (cm)
최고 = 9.5              # 이보다 높은 데서는 시작하지 않는다 (팔이 서는 한계 근처)
굵은걸음, 잔걸음 = 0.5, 0.1   # 먼저 0.5 씩 내려가 찾고, 0.1 씩 되짚어 경계를 잡는다
공구 = {                # 번호: (이름, 물음, 여유, 적을 곳)
    #                     여유 = 셋째 값(0.1 · 0.5). 처음 된 높이에서 얼마나 더 내려 쓸지(cm)
    "1": ("펜", "점이 찍혔나?", 0.1, "02_눈금자_가상.py 의 Z_DRAW"),
    "2": ("자석", "클립이 붙었나?", 0.5, "09_자석_탐색_가상.py · 10_자석_경주_가상.py 의 자석높이"),
}
# ─────────────────────────────────────────────────────
# [레벨0] 굵은걸음 을 1.0 으로 — 몇 번 덜 묻는 대신 경계를 놓칠 수 있나?
# [레벨1] 공구 의 셋째 값(여유 — 펜 0.1 · 자석 0.5)을 0 으로 두고 활동을 돌려 보면 무슨 일이 나나 (펜: 흐린 선, 자석: 가끔 안 붙음)


def 예(글):
    while True:
        a = input(글 + " [y/n] > ").strip().lower()
        if a in ("y", "ㅇ", "yes"):
            return True
        if a in ("n", "ㄴ", "no"):
            return False


def 시험_만들기(arm, 이름):
    """공구마다 '한 번 해 보는' 동작. z 를 받아 로봇을 움직인다."""
    if 이름 == "자석":
        def 시험(cell, z):
            arm.pick_magnet(cell, z)
    else:                                             # 펜 · 다른 것 — 내렸다 들기
        def 시험(cell, z):
            x, y = cell_to_xy(cell)
            arm.draw([(x, y)], z, z + 1.0)
    return 시험


def 경계찾기(arm, 이름, 물음, cell, z0=START_Z, floor=PEN_Z_FLOOR):
    """z0 에서 내려오며 처음 '된' 높이를 찾는다. 못 찾으면 None."""
    시험 = 시험_만들기(arm, 이름)
    z = z0
    print(f"  {cell} 에서 {z0} 부터 {굵은걸음} 씩 내려온다 ({floor} 아래로는 안 간다)")
    while z >= floor - 1e-9:
        시험(cell, round(z, 2))
        if 예(f"    z={z:.1f} — {물음}"):
            break
        z -= 굵은걸음
    else:
        return None
    if z >= z0 - 1e-9:                                # 첫 시험에서 바로 됐다 — 더 위에서도 될지 모른다
        print("    처음부터 됐다. START_Z 를 올려 다시 재면 경계를 알 수 있다.")
        return z
    위 = z + 굵은걸음                                  # 안 됐던 마지막 높이
    print(f"    {위:.1f} 은 안 되고 {z:.1f} 은 된다 — 사이를 {잔걸음} 씩 되짚는다")
    for k in range(1, int(round(굵은걸음 / 잔걸음))):
        zz = round(위 - 잔걸음 * k, 2)
        시험(cell, zz)
        if 예(f"    z={zz:.2f} — {물음}"):
            return zz
    return z


def 펜_시작높이():
    """손가락 맨 끝에서 펜 끝까지를 물어, 그보다 넉넉히 높은 데서 내려오기 시작한다.

    수직으로 닫은 손가락 끝은 z 보다 1.5cm 쯤 낮다 (2026-11-24 실제 로봇) — 2.5cm 나온 펜은 z = 4.0 에서 닿았다.

    적은 길이는 **시작 높이를 정하는 데만** 쓴다 — 쓰는 높이는 내려오며 찍어 본 값으로 정한다.
    """
    print("  재는 곳 — **집게 손가락 맨 끝**에서 펜 끝까지. 집게 몸통이나 손목부터 재지 않는다.")
    print("  예시 — 손가락 끝에서 2.5cm 나온 펜은 z = 4.0 에서 처음 찍혔다 (2026-11-24 실제 로봇).")
    print("         적는 길이와 z 는 다르다 — 이 길이는 어디서 내려오기 시작할지 정하는 데만 쓴다.")
    while True:
        s = input("집게 손가락 끝에서 펜 끝까지 대략 몇 cm 나왔나? (예: 2.5 · 모르면 Enter — 가장 높은 데서 시작) > ").strip()
        if not s:
            return 최고
        try:
            return min(최고, max(START_Z, round(float(s) + 시작여유, 1)))
        except ValueError:
            print("  ! 숫자로 적는다. 예: 2.5")


@안전하게
def main(arm=None):
    if arm is None:            # 그냥 돌리면 가상 — 실제 로봇은 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    실기기 = not hasattr(arm, "t")      # 가상 팔에만 t(가상 시계)가 있다
    print(__doc__.split("\n\n")[2])     # 독스트링의 활동 설명 문단
    고름 = input("\n무엇을 달았나요? [1 펜 / 2 자석 / 이름을 직접 쓰면 그 이름으로] > ").strip()
    if 고름 in 공구:
        이름, 물음, 여유, 적을곳 = 공구[고름]
    elif 고름:
        이름, 물음, 여유, 적을곳 = 고름, "작동했나?", 0.1, "그 활동 파일의 높이 설정"
    else:
        return

    if not 실기기:
        print(f"\n[가상] 로봇이 없어 잴 수는 없다. 실제 로봇 파일로 재면 마지막에 z 가 나온다.")
        print(f"  그 숫자를 {적을곳} 에 적는다.")
        return

    시작z = START_Z
    if 이름 == "펜":
        if arm.pen_mount(PEN_OUT) is None:
            print("펜을 물리지 못했다 — 여기서 멈춘다.")
            arm.close()
            return
        input("종이를 작업 지도 2~3행에 붙이고 테이프로 고정했으면 Enter > ")
        시작z = 펜_시작높이()
    elif 이름 == "자석":
        input(f"집게 날 아래 면에 자석을 붙이고 닫았나? 클립을 {가까운칸} 에 놓고 Enter > ")
    else:
        input(f"장치를 달고 {가까운칸} 에 시험할 것을 두었으면 Enter > ")

    근 = 경계찾기(arm, 이름, 물음, 가까운칸, z0=시작z)
    if 근 is None:
        print(f"\n{PEN_Z_FLOOR} 까지 내려가도 안 됐다 — 장치가 덜 나왔거나 자력이 모자란다.")
        arm.home()
        arm.close()
        return
    결과 = {"근": 근}
    if 이름 == "펜" and 예(f"\n가까운 쪽 {근:.2f}. 먼 자리({먼칸})도 잴까?"):
        원 = 경계찾기(arm, 이름, 물음, 먼칸, z0=근 + 1.0)
        if 원 is not None:
            결과["원"] = 원
            print(f"  먼 쪽 {원:.2f} — 차이 {원 - 근:+.2f}cm" + ("  (종이가 기울어 있다)" if abs(원 - 근) >= 0.1 else ""))
    z = round(max(PEN_Z_FLOOR, 근 - 여유), 2)
    if hasattr(arm, "pen_park") and 이름 == "펜":
        arm.pen_park(cell_to_xy(가까운칸))
    else:
        arm.home()
    arm.close()

    print("\n" + "=" * 46)
    print(f"{이름}: 처음 된 높이 {근:.2f} → 여유 {여유} 를 두어  z = {z}")
    if "원" in 결과:
        print(f"  (먼 쪽 {결과['원']:.2f})")
    print(f"  → {적을곳} 에 {z} 를 적는다")
    print("=" * 46)
    print("장치를 다시 달면 다시 잰다.")



# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도 기준이다 — A3 에서는 설정을 그대로 쓴다.
# B4 지도는 02_공구_높이재기_실기기_B4.py 가 지도맞추기("B4") 로 아래 칸으로 갈아 끼운다.
지도별 = {
    "B4": dict(가까운칸="D2", 먼칸="D3"),
}


def 지도맞추기(paper):
    """실제 로봇 파일이 부른다. A3 는 설정 그대로, 다른 지도는 칸 이름만 그 지도 것으로 바꾼다."""
    set_paper(paper)
    if paper != "A3":
        globals().update(지도별[paper])
        print(f"[{paper} 지도] 칸 설정을 {paper} 용으로 바꿨다 — 가까운칸={가까운칸} 먼칸={먼칸}")

# ══════════════════════════════════════════════════════════════════════
# 여기부터 끝까지는 로봇을 움직이는 부품이다 — 고치지 않는다.
# 바꿔 볼 것은 위의 '설정 — 여기만 바꿔 보세요' 칸에 있다.
# (robot_helpers.py 에서 이 활동이 쓰는 것만 옮겨 왔다)
# ══════════════════════════════════════════════════════════════════════
import math
import os
import sys
import time


if __name__ == "__main__":
    main()
