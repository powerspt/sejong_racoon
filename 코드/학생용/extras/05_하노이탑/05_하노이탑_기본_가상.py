# -*- coding: utf-8 -*-
"""[콘텐츠 ⑤-기본] 하노이 탑 — 손으로 적은 동선을 팔이 수행한다

    python 05_하노이탑_기본_가상.py
    (실행하면 작업 지도와 가상/실기기를 묻는다 — 그냥 Enter = 가상)

블록 3장을 A기둥에서 C기둥으로 옮기는 순서를 **사람이 미리 적어 둔** 파일이다.
로봇은 그 목록을 위에서부터 차례로 수행할 뿐, 규칙도 전략도 모른다.

    동선 = (출발 기둥, 도착 기둥) 쌍의 **리스트**

탑을 쌓지 않는다. 로봇에서 멀어지는 쪽으로 눕혀 한 열에 늘어놓는다.
    기둥 하나 = 작업 지도 한 열(세로)의 연속 칸
    가까운 칸이 바닥, 멀어질수록 위           [3][2][1]  ← 1번이 맨 위
    "작은 판 위에 큰 판을 못 올린다" 가 "작은 판보다 먼 칸에 큰 판을 못 둔다" 가 된다

핵심 포인트
  - 로봇이 하는 일은 '목록 수행'이다. 생각은 목록을 **만드는** 쪽에 있다.
  - 3장은 7수다. 4장은 15수, 5장은 31수 — 손으로 적을 수 있을까?
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):   # 한글이 깨지지 않게
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ───────── 설정 — 여기만 바꿔 보세요 ─────────
# [레벨0] 이동목록의 순서를 하나 바꿔 보고, 어디서 규칙이 깨지는지 본다
# [레벨1] 블록 2장짜리 이동목록(3수)을 직접 적어 블록수 = 2 로 돌려 본다
블록수 = 3

# 블록 3장을 A기둥 -> C기둥으로. 사람이 종이에 적어 옮겨 온 순서다.
이동목록 = [
    ("A", "C"),      # 1수
    ("A", "B"),      # 2수
    ("C", "B"),      # 3수
    ("A", "C"),      # 4수  ← 가장 큰 블록이 움직이는 순간
    ("B", "A"),      # 5수
    ("B", "C"),      # 6수
    ("A", "C"),      # 7수
]

# 매트마다 기둥으로 쓸 칸. 기둥은 **가까운 칸이 바닥**이다 (로봇 쪽이 아래).
# 이 표는 05_하노이탑_가상.py 의 LAYOUTS 와 같아야 한다.
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
# ─────────────────────────────────────────────


def ask_paper():
    """어떤 작업 지도를 쓰는지 묻는다.

    기본값을 두면 B4 매트를 깔아 놓고 A3 격자로 도는 사고가 난다 — 두 격자는
    칸 간격이 같아서 팔은 멀쩡히 움직이고 칸 이름만 한 칸씩 밀린다.
    """
    while True:
        ans = input(f"어떤 작업 지도를 쓰나요? [{' / '.join(LAYOUTS)}] > ").strip().upper()
        if ans in LAYOUTS:
            return ans
        print(f"  {' 또는 '.join(LAYOUTS)} 중에서 적어 주세요.")


def picture(tower, pegs, n, legend=False):
    """탑을 눕힌 그림. 왼쪽이 바닥(= 로봇에서 가까운 칸)이다."""
    if legend:
        print("     (왼쪽이 로봇에 가까운 칸 · 숫자 = 블록 크기 번호)")
    for name in ("A", "B", "C"):
        disks = "".join(f"[{d}]" for d in tower[name])
        print(f"     {name}  {disks}{'[ ]' * (n - len(tower[name]))}   "
              f"{' '.join(pegs[name][:n])}")


def main(arm=None):
    paper = ask_paper()
    n = 블록수
    if n not in LAYOUTS[paper]:
        있는것 = ", ".join(f"{k}장" for k in sorted(LAYOUTS[paper]))
        print(f"{paper} 매트에 {n}장짜리 기둥 배치가 없습니다. 있는 것: {있는것}")
        return 1
    pegs = LAYOUTS[paper][n]
    set_paper(paper)
    print(f"  기둥 A={pegs['A'][0]}..  B={pegs['B'][0]}..  C={pegs['C'][0]}.. "
          f"— 매트에 적힌 칸 이름과 같은지 보세요")

    print(f"\n적어 둔 동선은 {len(이동목록)}수입니다.")
    for i, (s, d) in enumerate(이동목록, 1):
        print(f"   {i}수  {s} → {d}")

    tower = {"A": list(range(n, 0, -1)), "B": [], "C": []}   # 왼쪽이 바닥 = 큰 번호
    print(f"\n블록 {n}장은 1번이 가장 작고 {n}번이 가장 큽니다.")
    for cell, d in zip(pegs["A"][:n], tower["A"]):
        print(f"   {d}번 크기 블록을 {cell} 칸에 놓아 주세요.")
    print(f"   {pegs['A'][0]} 가 로봇에 가장 가까운 칸입니다.\n")
    picture(tower, pegs, n, legend=True)
    input("\n다 놓았으면 Enter 를 누르세요 (가상 모드면 그냥 Enter) > ")

    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    for i, (s, d) in enumerate(이동목록, 1):
        if not tower[s]:
            print(f"- {i}수  {s}기둥이 비어 있습니다 — 목록이 규칙을 어겼습니다.")
            break
        disk = tower[s][-1]                       # 맨 위 = 줄의 오른쪽 끝
        from_cell = pegs[s][len(tower[s]) - 1]
        to_cell = pegs[d][len(tower[d])]
        print(f"- {i}/{len(이동목록)}  {disk}번 크기 블록  {s}({from_cell}) → {d}({to_cell})")
        # 놓을 칸을 같이 넘긴다 — 집게 각도를 집기 **전에** 두 칸 모두에 맞춘다
        arm.pick(from_cell, next_cell=to_cell)
        arm.place(to_cell)
        tower[d].append(tower[s].pop())
        picture(tower, pegs, n)
    arm.home()
    print(f"\n{arm.summary()}")
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

    def place(self, cell, level=0):
        self.n_place += 1
        self._log(f'PLACE {cell} {level}층', self.T_PLACE)
    T_MAGNET = 1.5

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
    import sys
    sys.exit(main())


# 여기서 더 해볼 것
#  1. 이동목록에서 두 수의 자리를 바꿔 실행한다. 몇 수째에서 규칙이 깨지는가?
#  2. 블록 2장(3수)짜리 목록을 종이에 적고 블록수 = 2 로 돌려 본다.
#  3. 블록 4장이면 15수다. 종이에 적어 본다 — 몇 분 걸렸는가?
#     5장은 31수, 10장은 1023수다. 손으로 적는 방법은 여기서 끝난다.
#  4. 그래서 다음 파일은 **목록을 사람이 아니라 함수가 만든다**:
#     05_하노이탑_실습_가상.py
