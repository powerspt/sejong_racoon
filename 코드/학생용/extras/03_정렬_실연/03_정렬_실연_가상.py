# -*- coding: utf-8 -*-
"""정렬 실연 · 가상 — 로봇 없이 화면으로

    python 03_정렬_실연_가상.py

선택 정렬과 버블 정렬을 같은 배열로 연달아 돌리고 비교표를 보여 준다.
이 파일 하나만 있으면 돌아간다.

고칠 데는 바로 아래 [설정] 한 군데다.
"""
import sys

try:                                   # 콘솔이 못 찍는 글자(—)를 ? 로 흘려보낸다
    sys.stdout.reconfigure(errors="replace")      # (건드리지 않아도 된다)
except (AttributeError, ValueError):
    pass

# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
SLOTS = ["B4", "D4", "F4", "H4"]
#   블록 4개를 늘어놓을 칸. 왼쪽부터다. 칸을 늘리면 블록도 그만큼 늘어난다.
TEMP = "E3"
#   스왑할 때 한 블록을 잠깐 내려놓는 칸. 비어 있어야 한다.
START = [4, 3, 2, 1]
#   그냥 Enter 를 눌렀을 때 쓸 순서. 역순이면 두 정렬의 차이가 가장 크다.
집기초, 놓기초 = 2.6, 2.4
#   로봇이 한 번 집고 놓는 데 걸리는 시간(초). 주제 4에서 잰 값이다.
# ══════════════════════════════════════════════════════


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


class 정렬봇:
    def __init__(self, arm, arr):
        self.arm = arm
        self.arr = list(arr)
        self.cmp = 0           # 비교 횟수
        self.swaps = 0         # 스왑 횟수

    def less(self, i, j):
        self.cmp += 1
        return self.arr[i] < self.arr[j]

    def swap(self, i, j):
        """자리 두 개를 맞바꾼다 — 로봇은 집기 세 번이 든다."""
        self.swaps += 1
        a, b = SLOTS[i], SLOTS[j]
        print(f"  스왑 {self.arr[i]}({a}) <-> {self.arr[j]}({b})")
        self.arm.pick(a), self.arm.place(TEMP)
        self.arm.pick(b), self.arm.place(a)
        self.arm.pick(TEMP), self.arm.place(b)
        self.arr[i], self.arr[j] = self.arr[j], self.arr[i]

    def selection(self):
        n = len(self.arr)
        for k in range(n):
            m = k
            for i in range(k + 1, n):
                if self.less(i, m):
                    m = i
            if m != k:
                self.swap(k, m)

    def bubble(self):
        n = len(self.arr)
        for k in range(n - 1):
            for i in range(n - 1 - k):
                if self.less(i + 1, i):
                    self.swap(i, i + 1)


def main(arm=None, 되돌리기=""):
    """arm 을 주지 않으면 종이팔로 돈다. 실기기 파일이 진짜 팔을 넣어 준다."""
    arm = arm or 종이팔()
    start = 순서묻기()
    표 = []
    for 이름, 방법 in (("선택 정렬", "selection"), ("버블 정렬", "bubble")):
        print(f"\n=== {이름} === 시작 배열 {start}")
        print("예상부터 적는다 — 스왑이 몇 번 나올까? ___ 회")
        input(되돌리기 + "준비되면 Enter > ")
        t0 = getattr(arm, "초", 0.0)
        봇 = 정렬봇(arm, start)
        getattr(봇, 방법)()
        arm.home()
        print(f"정렬 결과 {봇.arr}")
        표.append((이름, 봇.cmp, 봇.swaps, getattr(arm, "초", 0.0) - t0))

    print("\n" + "=" * 46)
    for 이름, 비교, 스왑, 초 in 표:
        걸린 = f" · {초:.0f}초" if 초 else ""
        print(f"{이름}: 비교 {비교}회 (공짜) · 스왑 {스왑}회 (집기 3번씩){걸린}")
    print(arm.summary())
    print("\n[해보기] 블록 순서를 바꿔 다시 — 두 정렬의 스왑 수가 같아지는 배열이 있을까?")
    arm.close()



# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도 기준이다. B4 지도는 03_정렬_실연_실기기_B4.py 가 지도맞추기("B4") 로
# 아래 값으로 갈아 끼운다. 두 지도 모두 블록 4개다.
지도별 = {
    "A3": dict(SLOTS=["B4", "D4", "F4", "H4"], TEMP="E3", START=[4, 3, 2, 1]),
    "B4": dict(SLOTS=["A3", "C3", "E3", "G3"], TEMP="D2", START=[4, 3, 2, 1]),
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

    def pick(self, cell, level=0, next_cell=None, next_level=0):
        x, y = cell_to_xy(cell)
        gz = GRASP + BLOCK_H * level
        also = None
        if next_cell is not None:
            nx, ny = cell_to_xy(next_cell)
            also = (nx, ny, GRASP + BLOCK_H * next_level)
        hover = self._approach(x, y, gz, also)
        self.bot.open_gripper()
        if not self._goto(x, y, hover):
            return
        if not self._descend(x, y, hover, gz):
            return
        self.bot.close_gripper()
        self._wait(WAIT_GRIP_MS)
        self._descend(x, y, gz, hover)

    def place(self, cell, level=0):
        x, y = cell_to_xy(cell)
        gz = GRASP + BLOCK_H * level
        hover = self._approach(x, y, gz)
        if not self._goto(x, y, hover):
            return
        if not self._descend(x, y, hover, gz):
            return
        self.bot.open_gripper()
        self._wait(500)
        self._descend(x, y, gz, hover)

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
