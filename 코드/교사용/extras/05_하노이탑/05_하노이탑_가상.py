# -*- coding: utf-8 -*-
"""[콘텐츠 ⑤] 하노이 탑 — 재귀가 짠 이동 목록을 팔이 수행한다

교사 시연용 완성본이다 — 학생은 05_하노이탑_기본 → 05_하노이탑_실습 순서로 한다.
이 파일은 가상(로봇 없이)이다. 실제 로봇은 05_하노이탑_실기기_A3.py 를 연다.

    이 파일을 편집기로 열고 F5 를 눌러 실행한다. 명령 프롬프트는 쓰지 않는다.
    (작업 지도를 묻는다)

바꿀 것은 아래 '설정' 의 다섯 줄뿐이다.
    PAPER    쓰는 작업 지도. "" 면 실행할 때 물어본다 ("A3" / "B4" 로 못박아도 된다)
    블록수   블록 몇 장으로 할지. 0 이면 작업 지도 기본 (A3 3장 / B4 3장)
    예행     블록 없이 칸만 짚어 본다 — 실제 로봇에서 처음 돌릴 때 True 로
    한수씩   한 수마다 멈춘다 (Enter 로 진행, q 로 중단)
    느리게   천천히 움직인다

탑을 쌓지 않는다. **로봇에서 멀어지는 쪽으로 눕혀서** 한 열에 늘어놓는다.
    기둥 하나 = 작업 지도 한 열(세로)의 연속 칸
    가까운 칸이 바닥, 멀어질수록 위           [3][2][1]  ← 1번이 맨 위
    로봇은 늘 바닥 높이(level 0)에서만 집고 놓는다
    **"작은 판 위에 큰 판을 못 올린다"가 "작은 판보다 먼 칸에 큰 판을 못 둔다"가 된다.**

배치: 집게 기울기는 칸마다 자동으로 고르되 **블록을 쥐고 있는 동안에는 안 바꾼다**
      (robot_helpers). 돌릴 일이 있으면 집기 전, 빈손일 때 끝낸다.
      A3 는 C·E·G 열의 2~4행으로 3장, B4 는 B·D·F 열의 1~3행으로 3장까지 된다.
      A3 의 아홉 칸은 모두 45° 로 돈다. B4 의 1행(반경 8cm)은 로봇에 바싹 붙어
      **수직으로만** 닿아서, 그 칸이 낀 수만 수직으로 돌고 나머지는 45° 다.

핵심 포인트
  - 재귀 함수 7줄이 이동 목록 전부를 만든다. 로봇은 목록을 수행할 뿐.
  - 이동 횟수 = 2^n − 1. 실행 전에 n=5 의 예상 소요 시간을 계산해 보면
    "오늘 수업 안에 못 끝난다"가 계산으로 나온다 — 지수 증가의 체감.
  - 쌓기를 눕히기로 바꿔도 문제는 그대로다 — 표현을 바꾼 것이지 문제를 바꾼 것이 아니다.
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):   # 한글이 깨지지 않게
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import sys

rh = sys.modules[__name__]   # 부품은 이 파일 안에 있다

# ───────── 설정 — 여기만 바꿔 보세요 ─────────
# [레벨0] 블록수 를 1씩 올리며 걸린 시간을 적는다 — 3장 7번, 4장 15번, 5장 31번
#         (가상에서 4장부터는 그림과 팔 동작 없이 횟수와 시간만 센다)
# [레벨1] 아래 LAYOUTS 의 칸을 다른 칸으로 바꿔 본다 — 점검이 알아서 걸러 준다
# [레벨2] hanoi() 안의 ①과 ③ 줄을 서로 바꾸면? — 예상하고 실행
PAPER = ""          # 쓰는 작업 지도. "" 면 실행할 때 물어본다 ("A3" / "B4" 로 못박아도 된다)
블록수 = 0          # 블록 몇 장으로 할지. 0 이면 작업 지도 기본 (A3 3장 / B4 3장)
예행 = False        # True 면 블록 없이 칸만 짚어 본다 (실제 로봇에서 처음 돌릴 때)
한수씩 = False      # True 면 한 수마다 멈춘다 (Enter 로 진행, q 로 중단)
느리게 = False      # True 면 천천히 움직인다

REHEARSE, STEP, SLOW = 예행, 한수씩, 느리게   # 아래 코드가 쓰는 이름
# ─────────────────────────────────────────────

# ── 아래는 고치지 않는다 (LAYOUTS 는 [레벨1] 에서만) ──
# 작업 지도마다 "블록 수 -> 기둥 배치". 기둥은 **가까운 칸이 바닥**이다 (로봇 쪽이 아래).
# B4 로 3장을 하려면 1행까지 써야 한다 — 1행은 로봇에 바싹 붙어 있어서
# 집게가 수직으로 내려와 집는다. 45° 로 들어가는 2장짜리와 동작이 꽤 다르다.
LAYOUTS = {
    "A3": {
        2: {"A": ["C3", "C4"],       "B": ["E3", "E4"],       "C": ["G3", "G4"]},
        3: {"A": ["C2", "C3", "C4"], "B": ["E2", "E3", "E4"], "C": ["G2", "G3", "G4"]},
    },
    "B4": {
        2: {"A": ["B2", "B3"],       "B": ["D2", "D3"],       "C": ["F2", "F3"]},
        3: {"A": ["B1", "B2", "B3"], "B": ["D1", "D2", "D3"], "C": ["F1", "F2", "F3"]},
    },
}
기본블록수 = {"A3": 3, "B4": 3}
N, PEGS = None, None                     # 블록 수 · 기둥 배치 — main() 에서 정한다
PEG_GAP = 7.9                            # 기둥끼리 최소 간격 (날이 벌어져도 안 닿는 거리)
집게오프셋 = (8.0, -0.6)                 # 닿는지 미리 계산할 때 쓴다 (서보 집게)


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
_rh_PAPER = 'A3'
HOVER = 10.0
GRASP = 1.5
BLOCK_H = 3.0
WAIT_GRIP_MS = 700
SPEED_DOWN = 40
SPEED_MOVE = 60
HOME_POSE = (0, -10, -140, 60)
TILT_RULES = [(15.5, 0, 10.0), (11.0, -45, 8.0), (0.0, -90, 6.0)]
TILT = None
J2_SAFE, J3_SAFE = (-30.0, -60.0)
DOWN_STEPS = 3
LIFT_CLEAR = 2.0
TRAVEL = 9.0
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
    global _rh_PAPER
    paper = paper.strip().upper()
    if paper not in MAP_LAYOUT:
        raise ValueError(f"모르는 용지: {paper!r} ({' / '.join(MAP_LAYOUT)})")
    _rh_PAPER = paper
    xs, ys = MAP_LAYOUT[paper]
    print(f"[작업 지도 {paper}] 가로 A~{chr(ord('A') + len(xs) - 1)} · 세로 1~{len(ys)}")

def last_cell(paper=None):
    xs, ys = MAP_LAYOUT[paper or _rh_PAPER]
    return f"{chr(ord('A') + len(xs) - 1)}{len(ys)}"

def cell_to_xy(cell: str, paper=None):
    xs, ys = MAP_LAYOUT[paper or _rh_PAPER]
    cell = cell.strip().upper()
    col = ord(cell[0]) - ord('A') if len(cell) == 2 else -1
    row = int(cell[1]) - 1 if len(cell) == 2 and cell[1].isdigit() else -1
    if not (0 <= col < len(xs) and 0 <= row < len(ys)):
        raise ValueError(f'{paper or _rh_PAPER} 작업 지도에 없는 칸: {cell!r} (A1~{last_cell(paper)})')
    return (xs[col], ys[row])

def radius(cell: str, paper=None) -> float:
    x, y = cell_to_xy(cell, paper)
    return (x * x + y * y) ** 0.5

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

    def pick(self, cell, level=0, next_cell=None, next_level=0):
        self.n_pick += 1
        self._log(f'PICK  {cell} {level}층', self.T_PICK)
        return True

    def place(self, cell, level=0):
        self.n_place += 1
        self._log(f'PLACE {cell} {level}층', self.T_PLACE)
        return True
    T_MAGNET = 1.5

    def home(self):
        self._log('HOME', self.T_MOVE)

    def close(self, home=None):
        pass

    def summary(self):
        센것 = [f'{이름} {n}회' for 이름, n in (('집기', self.n_pick), ('놓기', self.n_place), ('이동', self.n_move)) if n]
        return (' · '.join(센것) or '한 동작도 안 함') + f' · 가상 소요 {self.t:.0f}초 (약 {self.t / 60:.1f}분)'

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

    def _hover_for(self, x, y, gz, tilt):
        if self._solve(x, y, gz, tilt) is None:
            return None
        base = dict(((a, h) for _, a, h in TILT_RULES)).get(tilt, HOVER)
        hover = max(base, gz + BLOCK_H + LIFT_CLEAR)
        while hover > gz + BLOCK_H and self._solve(x, y, hover, tilt) is None:
            hover -= 0.5
        if self._solve(x, y, hover, tilt) is None:
            return None
        while hover + 0.5 <= TRAVEL and self._solve(x, y, hover + 0.5, tilt) is not None:
            hover += 0.5
        return hover

    def _usable(self, spot, tilt):
        x, y, gz = spot
        return self._solve(x, y, gz, tilt) is not None and self._solve(x, y, gz + BLOCK_H, tilt) is not None

    def _approach(self, x, y, gz, also=None):
        want, _ = tilt_for((x * x + y * y) ** 0.5)
        if self.tilt_fixed is not None:
            want = self.tilt_fixed
            cands = [want]
        elif also is None:
            cands = [self.tilt_now, want]
        else:
            cands = [want, tilt_for((also[0] ** 2 + also[1] ** 2) ** 0.5)[0], self.tilt_now]
        seen, order = (set(), [])
        for a in cands:
            if a not in seen:
                seen.add(a)
                order.append(a)
        for alpha in order:
            hover = self._hover_for(x, y, gz, alpha)
            if hover is None:
                continue
            if also is not None and (not self._usable(also, alpha)):
                continue
            self._set_tilt(alpha)
            return hover
        self._set_tilt(want)
        return self._hover_for(x, y, gz, want) or gz + BLOCK_H

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

    def pick(self, cell, level=0, next_cell=None, next_level=0):
        x, y = cell_to_xy(cell)
        gz = GRASP + BLOCK_H * level
        also = None
        if next_cell is not None:
            nx, ny = cell_to_xy(next_cell)
            also = (nx, ny, GRASP + BLOCK_H * next_level)
        hover = self._approach(x, y, gz, also)
        self.bot.open_gripper()
        self._reach(cell, x, y, hover, gz)
        self.bot.close_gripper()
        self._wait(WAIT_GRIP_MS)
        self._lift(cell, x, y, gz, hover)
        return True

    def place(self, cell, level=0):
        x, y = cell_to_xy(cell)
        gz = GRASP + BLOCK_H * level
        hover = self._approach(x, y, gz)
        self._reach(cell, x, y, hover, gz)
        self.bot.open_gripper()
        self._wait(500)
        self._lift(cell, x, y, gz, hover)
        return True

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

    def summary(self):
        return '실제 로봇 실행 완료'
팔 = None


def reach_tilt(cell):
    """그 칸을 어떤 기울기로 쓸 수 있는가. 못 쓰면 None.

    로봇 없이 역기구학으로 따져 본다 — robot_helpers 가 실제로 고르는
    순서(TILT_RULES)와 같은 순서로 본다.
    """
    x, y = cell_to_xy(cell)
    for _, tilt, hover in TILT_RULES:
        if (not over_limit(ik_joints(x, y, GRASP, tilt, 집게오프셋))
                and not over_limit(ik_joints(x, y, hover, tilt, 집게오프셋))):
            return tilt
    return None


def ask_paper():
    """어떤 작업 지도를 쓰는지 묻는다.

    편집기에서 F5 로 실행하면 명령줄 인자를 줄 수 없다. 기본값을 두면
    B4 작업 지도를 깔아 놓고 A3 격자로 도는 사고가 난다 — 두 격자는 칸 간격이
    같아서 **팔은 멀쩡히 움직이고 칸 이름만 한 칸씩 밀린다.**
    """
    while True:
        ans = input(f"어떤 작업 지도를 쓰나요? [{' / '.join(LAYOUTS)}] > ").strip().upper()
        if ans in LAYOUTS:
            return ans
        print(f"  {' 또는 '.join(LAYOUTS)} 중에서 적어 주세요.")


def 지도맞추기(paper):
    """지도("A3"/"B4")를 정해 둔다 — 실행할 때 묻지 않는다. 실제 로봇 파일이 부른다."""
    global PAPER
    PAPER = paper


def hanoi(n, src, dst, via, moves):
    if n == 0:
        return
    hanoi(n - 1, src, via, dst, moves)   # ① n-1 장을 비켜 둔다
    moves.append((src, dst))             # ② 가장 큰 판을 옮긴다
    hanoi(n - 1, via, dst, src, moves)   # ③ 비켜 둔 것을 그 위로


def 규칙검사(moves, n):
    """이동 목록을 팔 없이 처음부터 따라가 본다. 규칙을 지켰으면 None, 아니면 틀린 이유 한 줄."""
    tower = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    for i, (s, d) in enumerate(moves, 1):
        if not tower[s]:
            return f"{i}수: {s}기둥이 비어 있는데 거기서 집으려 한다."
        블록 = tower[s][-1]
        if tower[d] and tower[d][-1] < 블록:
            return (f"{i}수: {블록}번 블록을 {tower[d][-1]}번 블록보다 먼 칸에 두려 한다 "
                    f"— 작은 판보다 먼 칸에 큰 판을 둘 수 없다.")
        tower[d].append(tower[s].pop())
    return None


def 횟수만(n):
    """기둥 배치가 없는 장수 — 팔 없이 이동 횟수와 가상 소요 시간만 센다."""
    if n <= 20:
        moves = []
        hanoi(n, "A", "C", "B", moves)
        틀림 = 규칙검사(moves, n)
        if 틀림:
            print(f"\n  !! {틀림}")
            print("  이동 목록이 규칙을 어겼다 — 여기서 끝낸다.")
            return 1
        횟수 = len(moves)
    else:
        횟수 = 2 ** n - 1                 # 목록이 너무 길다 — 만들지 않고 계산한다
    가장큰 = max(k for 배치 in LAYOUTS.values() for k in 배치)
    print(f"\n블록 {n}장을 A기둥에서 C기둥으로 옮깁니다. "
          f"옮기는 횟수는 {횟수}회입니다 (= 2^{n} - 1).")
    print(f"그림과 팔 동작은 {가장큰}장까지 — 횟수와 시간만 센다.")
    # 가상 팔과 같은 셈 — 한 수 = 집기 + 놓기, 끝에 Home 한 번
    초 = 횟수 * (DummyArm.T_PICK + DummyArm.T_PLACE) + DummyArm.T_MOVE
    print(f"\n집기 {횟수}회 · 놓기 {횟수}회 · 가상 소요 {초:.0f}초 (약 {초 / 60:.1f}분)")
    return 0


def check_pegs():
    """칸이 모자라지 않는지, 닿는 자리인지, 기둥끼리 충분히 떨어졌는지 본다."""
    ok = True
    for name, slots in PEGS.items():
        if len(slots) < N:
            print(f"  !! {name}기둥의 칸이 {len(slots)}개뿐이다 — 블록 {N}장을 두려면 {N}개가 필요하다")
            ok = False
        for cell in slots[:N]:
            try:
                r = radius(cell)
            except ValueError as e:
                print(f"     {name}기둥 {cell}  !! {e}")
                ok = False
                continue
            tilt = reach_tilt(cell)
            if tilt is None:
                print(f"     {name}기둥 {cell}  반경 {r:4.1f}cm   <-- 어떤 각도로도 안 닿는다")
                ok = False
                continue
            # TILT_RULES 는 평평한 각도부터 본다 — 아래 값이 '가장 눕혀 쓸 수 있는 각도'다
            쓸것 = {0: "수평으로 닿음",
                   -45: "45° 아래로 닿음 (수평으로는 안 됨)",
                   -90: "수직으로만 닿음 — 로봇에 바싹 붙은 칸"}.get(tilt, f"{tilt}° 로 닿음")
            print(f"     {name}기둥 {cell}  반경 {r:4.1f}cm  {쓸것}")
    if not ok:
        return False

    # 기둥끼리 너무 가까우면 집게를 열 때 옆 기둥의 블록을 친다
    flat = [(p, c) for p, slots in PEGS.items() for c in slots[:N]]
    for i, (p1, c1) in enumerate(flat):
        for p2, c2 in flat[i + 1:]:
            if p1 == p2:
                continue
            (x1, y1), (x2, y2) = cell_to_xy(c1), cell_to_xy(c2)
            d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if d < PEG_GAP:
                print(f"  !! {c1} 과 {c2} 가 {d:.1f}cm 뿐이다 — "
                      f"집게를 열 때 옆 블록을 친다 ({PEG_GAP}cm 이상 띄울 것)")
                ok = False
    return ok


def rehearse(arm):
    """블록 없이 칸을 차례로 짚어 본다 — 실제 로봇 첫 점검용.

    집기·놓기 동작을 그대로 하되 잡을 것이 없다. 볼 것 세 가지
      1) 내려가는 길에 집게가 작업 지도를 긁지 않는가
      2) 집게 끝이 칸 네모 **안**에 들어오는가 (빗나가면 작업 지도를 옮겨 맞춘다)
      3) 기울기가 바뀌는 칸에서 팔을 먼저 세웠다 돌리는가
    """
    print("\n[예행] 블록을 모두 치우고 Enter — 빈손으로 칸을 짚는다.")
    input("> ")
    for name in ("A", "B", "C"):
        for cell in PEGS[name][:N]:
            r = radius(cell)
            print(f"- {name}기둥 {cell}  반경 {r:4.1f}cm", end="", flush=True)
            arm.pick(cell)                     # 빈손으로 내려갔다 올라온다
            arm.place(cell)
            # 실제로 쓴 각도를 적는다 (규칙값이 아니라 — 앞 칸 각도를 물려받기도 한다)
            print(f"  기울기 {getattr(arm, 'tilt_now', tilt_for(r)[0]):g}°")
            if STEP and input("    Enter = 다음 칸 / q = 중단 > ").strip().lower() == "q":
                arm.home()
                arm.close()
                return 1
    arm.home()
    print("\n칸을 모두 짚었다. 긁거나 빗나간 칸이 있으면 그 칸 이름을 적어 둘 것.")
    arm.close()
    return 0


def picture(tower, legend=False):
    """탑을 눕힌 그림. 왼쪽이 바닥(= 로봇에서 가까운 칸)이다."""
    if legend:
        print("     (왼쪽이 로봇에 가까운 칸 · 숫자 = 블록 크기 번호)")
    for name in ("A", "B", "C"):
        disks = "".join(f"[{d}]" for d in tower[name])
        empty = "[ ]" * (N - len(tower[name]))
        print(f"     {name}  {disks}{empty}   {' '.join(PEGS[name][:N])}")


@안전하게
def main(arm=None):
    global N, PEGS
    가상 = arm is None
    if 가상 and 블록수 and not any(블록수 in 배치 for 배치 in LAYOUTS.values()):
        return 횟수만(블록수)              # 어느 지도에도 배치가 없다 — 지도를 묻지 않는다
    paper = PAPER or ask_paper()
    n = 블록수 or 기본블록수[paper]
    if n not in LAYOUTS[paper]:
        if 가상:
            return 횟수만(n)
        있는것 = ", ".join(f"{k}장" for k in sorted(LAYOUTS[paper]))
        print(f"{paper} 작업 지도에 {n}장짜리 기둥 배치가 없습니다. 있는 것: {있는것}")
        print("   LAYOUTS 에 칸을 적어 주면 그 수로도 됩니다.")
        return 1
    N, PEGS = n, LAYOUTS[paper][n]
    set_paper(paper)
    print(f"  기둥 A={PEGS['A'][0]}..  B={PEGS['B'][0]}..  C={PEGS['C'][0]}.. "
          f"— 작업 지도에 적힌 칸 이름과 같은지 보세요")
    if SLOW:
        rh.SPEED_MOVE, rh.SPEED_DOWN = 25, 15
        print("[느리게] 이동 25 · 하강 15 — 처음 돌려 볼 때만 쓴다")
    moves = []
    hanoi(N, "A", "C", "B", moves)
    틀림 = 규칙검사(moves, N)            # 팔을 움직이기 전에 목록부터 본다
    if 틀림:
        print(f"\n  !! {틀림}")
        print("  이동 목록이 규칙을 어겼다 — 팔을 움직이지 않고 끝낸다.")
        return 1
    print(f"\n블록 {N}장을 A기둥에서 C기둥으로 옮깁니다. "
          f"옮기는 횟수는 {len(moves)}회입니다 (= 2^{N} - 1).")
    print("   먼저 예상해 보세요 — 한 번 옮기는 데 6초면 전체는 몇 분일까요? ___ 분\n")

    print("기둥으로 쓸 칸을 점검합니다 — 팔이 닿는지, 기둥끼리 충분히 떨어졌는지")
    if not check_pegs():
        print("\n  PEGS 를 고치고 다시 실행한다.")
        return 1
    print()

    if arm is None:            # 그냥 돌리면 가상 — 실제 로봇은 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    if REHEARSE:
        return rehearse(arm)

    tower = {"A": list(range(N, 0, -1)), "B": [], "C": []}   # 왼쪽이 바닥 = 큰 번호
    print()
    print(f"블록 {N}장은 1번이 가장 작고 {N}번이 가장 큽니다.")
    for cell, d in zip(PEGS["A"][:N], tower["A"]):
        print(f"   {d}번 크기 블록을 {cell} 칸에 놓아 주세요.")
    print(f"   {PEGS['A'][0]} 가 로봇에 가장 가까운 칸입니다.\n")
    picture(tower, legend=True)
    input("\n다 놓았으면 Enter 를 누르세요 (가상 모드면 그냥 Enter) > ")

    for i, (s, d) in enumerate(moves, 1):
        disk = tower[s][-1]                       # 맨 위 = 줄의 오른쪽 끝
        from_cell = PEGS[s][len(tower[s]) - 1]
        to_cell = PEGS[d][len(tower[d])]
        print(f"- {i}/{len(moves)}  {disk}번 크기 블록  {s}({from_cell}) → {d}({to_cell})")
        if STEP and input("    Enter = 이 수 실행 / q = 중단 > ").strip().lower() == "q":
            print("  중단했다 — 블록은 그대로 두고 어디서 틀어졌는지 본다.")
            break
        # 놓을 칸을 같이 넘긴다 — 집게 각도를 집기 **전에** 두 칸 모두에 맞춘다.
        arm.pick(from_cell, next_cell=to_cell)    # 늘 1층이다 — level 을 쓰지 않는다
        arm.place(to_cell)
        tower[d].append(tower[s].pop())
        picture(tower)
    arm.home()
    print(f"\n{arm.summary()}")
    print(f"[해보기] 맨 위의 블록수 를 1씩 올리며 소요 시간을 적기 — 10장이면? (계산: {2**10 - 1}회)")
    print("[해보기] 눕힌 그림과 쌓은 그림이 같은 문제인지 한 줄로 쓰기")
    arm.close()
    return 0

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
    sys.exit(main())
