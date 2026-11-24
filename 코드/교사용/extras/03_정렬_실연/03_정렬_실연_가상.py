# -*- coding: utf-8 -*-
"""정렬 실연 · 가상 — 로봇 없이 화면으로

    python 03_정렬_실연_가상.py

선택 정렬과 버블 정렬을 같은 배열로 연달아 돌리고 비교표를 보여 준다.
이 파일 하나만 있으면 돌아간다. 실제 로봇은 03_정렬_실연_실기기_A3.py 를 연다.

고칠 데는 바로 아래 [설정] 한 군데다. 읽을 데는 그 아래 교환 · 선택정렬 · 버블정렬 세 함수다.
"""
import sys

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

def 지도_바꾸기(paper, 설정, 보일=''):
    set_paper(paper)
    if paper in 설정.get('지도별', {}):
        설정.update(설정['지도별'][paper])
        값 = ' '.join((f'{이름}={설정[이름]}' for 이름 in 보일.split()))
        print(f'[{paper} 지도] 칸 설정을 {paper} 용으로 바꿨다 — {값}')
MAP_LAYOUT = {'A3': ([-16, -12, -8, -4, 0, 4, 8, 12, 16], [8, 12, 16, 20]), 'B4': ([-12, -8, -4, 0, 4, 8, 12], [8, 12, 16])}
PAPER = 'A3'
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

try:                                   # 콘솔이 못 찍는 글자(—)를 ? 로 흘려보낸다
    sys.stdout.reconfigure(errors="replace")      # (건드리지 않아도 된다)
except (AttributeError, ValueError):
    pass

# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
SLOTS = ["B4", "D4", "F4", "H4"]
#   블록 4개를 늘어놓을 칸. 왼쪽부터다. 칸을 늘리면 START 의 숫자도 그만큼 늘린다.
TEMP = "I2"
#   교환할 때 한 블록을 잠깐 내려놓는 칸. 비어 있어야 한다.
#   슬롯으로 들어가는 팔의 길 옆으로 뺀 자리다 — 슬롯 앞(E3 같은 칸)에 두면 집게가 지나가다 친다.
START = [4, 3, 2, 1]
#   그냥 Enter 를 눌렀을 때 쓸 순서. 역순이면 두 정렬의 차이가 가장 크다.
집기초, 놓기초 = 2.6, 2.4
#   로봇이 한 번 집고 놓는 데 걸리는 시간(초). 주제 4에서 잰 값이다.
# ══════════════════════════════════════════════════════


def 교환(arm, arr, i, j):
    """i번째와 j번째 블록의 자리를 맞바꾼다 — 로봇은 집기 세 번이 든다."""
    a = SLOTS[i]
    b = SLOTS[j]
    print(f"  교환 {arr[i]}({a}) <-> {arr[j]}({b})")
    arm.pick(a)             # 1) a 의 블록을 임시 칸으로
    arm.place(TEMP)
    arm.pick(b)             # 2) b 의 블록을 빈 a 로
    arm.place(a)
    arm.pick(TEMP)          # 3) 임시 칸의 블록을 빈 b 로
    arm.place(b)
    잠깐 = arr[i]           # 리스트 안의 숫자도 똑같이 맞바꾼다
    arr[i] = arr[j]
    arr[j] = 잠깐


def 선택정렬(arm, arr):
    """남은 것 가운데 가장 작은 것을 찾아 맨 앞과 바꾼다. (비교, 교환) 횟수를 돌려준다."""
    비교 = 0
    교환수 = 0
    n = len(arr)
    for k in range(n):                  # k번째 자리에 들어갈 블록을 정한다
        m = k                           # 지금까지 본 것 중 가장 작은 블록의 자리
        for i in range(k + 1, n):
            비교 += 1
            if arr[i] < arr[m]:
                m = i
        if m != k:                      # 이미 제자리면 로봇은 움직이지 않는다
            교환(arm, arr, k, m)
            교환수 += 1
    return 비교, 교환수


def 버블정렬(arm, arr):
    """이웃한 둘을 견주어 순서가 거꾸로면 바꾼다. (비교, 교환) 횟수를 돌려준다."""
    비교 = 0
    교환수 = 0
    n = len(arr)
    for k in range(n - 1):              # 한 바퀴 돌 때마다 가장 큰 것이 오른쪽 끝에 자리 잡는다
        for i in range(n - 1 - k):
            비교 += 1
            if arr[i + 1] < arr[i]:
                교환(arm, arr, i, i + 1)
                교환수 += 1
    return 비교, 교환수


@안전하게
def main(arm=None, 되돌리기=""):
    """arm 을 주지 않으면 종이팔로 돈다. 실제 로봇 파일이 진짜 팔을 넣어 준다."""
    if arm is None:
        arm = 종이팔()
    print(f"슬롯 {SLOTS} · 임시 칸 {TEMP}")
    if len(SLOTS) != len(START):
        print(f"  ! SLOTS 는 {len(SLOTS)}칸인데 START 는 {len(START)}개다 — 개수를 맞추고 다시 실행한다")
        arm.close()
        return
    start = 순서묻기()
    표 = []
    for 이름 in ["선택 정렬", "버블 정렬"]:
        print(f"\n=== {이름} === 시작 배열 {start}")
        print("예상부터 적는다 — 교환이 몇 번 나올까? ___ 회")
        input(되돌리기 + "준비되면 Enter > ")
        t0 = getattr(arm, "초", 0.0)        # 종이팔에만 초(가상 시계)가 있다
        arr = list(start)                   # 두 정렬이 같은 배열에서 시작하게 베껴 쓴다
        if 이름 == "선택 정렬":
            비교, 교환수 = 선택정렬(arm, arr)
        else:
            비교, 교환수 = 버블정렬(arm, arr)
        arm.home()
        print(f"정렬 결과 {arr}")
        표.append((이름, 비교, 교환수, getattr(arm, "초", 0.0) - t0))

    print("\n" + "=" * 46)
    for 이름, 비교, 교환수, 초 in 표:
        걸린 = f" · {초:.0f}초" if 초 else ""
        print(f"{이름}: 비교 {비교}회 (공짜) · 교환 {교환수}회 (집기 3번씩){걸린}")
    print(arm.summary())
    print("\n[해보기] 블록 순서를 바꿔 다시 — 두 정렬의 교환 수가 같아지는 배열이 있을까?")
    arm.close()


def 순서묻기():
    """로봇은 블록의 번호를 보지 못한다 — 놓인 순서를 사람이 알려 준다."""
    기본 = "".join(str(v) for v in START)
    while True:
        s = input(f"블록을 놓은 순서를 왼쪽({SLOTS[0]})부터 "
                  f"(예: {기본} / 그냥 Enter = {기본}) > ").strip()
        if not s:
            return list(START)
        s = s.replace(",", "").replace(" ", "")
        if len(s) == len(SLOTS) and s.isdigit() and sorted(s) == sorted(기본):
            return [int(c) for c in s]
        print(f"  ! {기본} 처럼 숫자를 한 번씩, 붙여서 {len(SLOTS)}자리로 쓰세요")


# ── 아래는 화면에 적기만 하는 가짜 팔 — 고치지 않는다 ──────────
class 종이팔:
    """로봇 대신 화면에 적는 팔. 진짜 팔과 이름이 같다 (pick · place · home)."""

    def __init__(self):
        self.집기 = 0
        self.초 = 0.0

    def pick(self, 칸):
        self.집기 += 1
        self.초 += 집기초
        print(f"    집기  {칸}")

    def place(self, 칸):
        self.초 += 놓기초
        print(f"    놓기  {칸}")

    def home(self):
        pass

    def summary(self):
        return f"집기 {self.집기}회 · 가상 소요 {self.초:.0f}초"

    def close(self):
        pass


# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도 기준이다 — A3 에서는 설정을 그대로 쓴다.
# B4 지도는 03_정렬_실연_실기기_B4.py 가 지도맞추기("B4") 로 아래 칸으로 갈아 끼운다.
지도별 = {
    "B4": dict(SLOTS=["A3", "C3", "E3", "G3"], TEMP="G1"),
}


def 지도맞추기(paper):
    """실제 로봇 파일이 부른다. A3 는 설정 그대로, 다른 지도는 칸 이름만 그 지도 것으로 바꾼다."""
    지도_바꾸기(paper, globals(), "SLOTS TEMP")

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
