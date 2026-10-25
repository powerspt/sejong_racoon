# -*- coding: utf-8 -*-
"""[콘텐츠 ④] 공장 시뮬레이션 — 정확도 × 처리량, 전략이 점수가 된다 (카메라 불필요)

    python extras/04_공장_시뮬레이션_가상.py
    (실행하면 가상/실기기를 묻는다 — 그냥 Enter = 가상. 판정은 키보드 r/b/x)

규칙
  - 제품이 투입 칸 E3 에 하나씩 도착한다 (빨강/파랑, 가끔 불량).
  - 분류: 빨강 → A4, 파랑 → I4, 불량 → E4 (폐기함).
  - 색 판정은 "검사원"(= 키보드 입력 r/b/x) 이 한다. 카메라가 없으니 사람이 센서다.
    → 주제 6~7을 들은 반이라면 여기에 색 검출기/YOLO 를 꽂는 것이 자연스러운 확장.
  - 역할 2개: "출제자"는 화면을 보고 코드가 정한 색 블록을 E3 에 놓는다.
    "검사원"은 화면을 보지 않고 매트의 블록만 보고 판정한다 — 그래야 게임이 성립한다.
  - 점수 = 맞게 분류한 개수 × 10 − 잘못 분류 × 15, 그리고 총 소요 시간을 같이 기록.

핵심 포인트
  - 빨리 하면(속도↑) 오분류가 늘고, 신중하면 처리량이 준다 — 트레이드오프를 점수로.
  - 결과가 CSV 로 남는다: 이 폴더의 factory_log.csv (제품, 정답, 판정, 맞음, 누적시간)
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):   # 한글이 깨지지 않게
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import csv
import os
import random
import time


# ───────── 설정 — 여기만 바꿔 보세요 ─────────
# [레벨0] 점수 규칙 바꾸기 — 아래 main() 의  +10 / -15  숫자 (틀림을 -50 으로 하면?)
# [레벨1] BINS 의 목적지 칸 바꾸기 / 불량 확률 0.15 바꾸기 (make_products)
# [레벨2] 새 색(초록 G) 추가 — NAMES 와 BINS 에 한 줄씩
N_PRODUCTS = 8     # 판별할 블록 수의 기본값 — 실행하면 물어본다 (그냥 Enter = 이 값)
SEED = 42          # 같은 숫자 = 같은 제품 순서 — 반 전체가 공정하게 비교할 수 있다
AUTO_JUDGE = False  # (교사 시연용) True 면 판정을 자동으로 — 수업에서는 False
IN_CELL = "E3"
BINS = {"R": "A4", "B": "I4", "X": "E4"}
NAMES = {"R": "빨강", "B": "파랑", "X": "불량"}
# ─────────────────────────────────────────────


def make_products(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        out.append("X" if r < 0.15 else ("R" if r < 0.575 else "B"))
    return out


def main(arm=None):
    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    while True:
        s = input(f"판별할 블록 개수 [그냥 Enter = {N_PRODUCTS}] > ").strip()
        if not s:
            n = N_PRODUCTS
            break
        if s.isdigit() and int(s) > 0:
            n = int(s)
            break
        print("  1 이상의 숫자로 적으세요.")
    products = make_products(n, SEED)
    bin_count = {"R": 0, "B": 0, "X": 0}
    rows, score, correct = [], 0, 0
    t0 = time.time()

    print(f"\n제품 {n}개 · 빨강→A4 파랑→I4 불량→E4 · 판정 입력: r / b / x")
    print("역할 분담 — 출제자: 이 화면을 보고 그 색 블록을 E3 에 놓는다 · 검사원: 화면을 보지 않고 블록만 보고 판정\n")
    for i, truth in enumerate(products, 1):
        print(f"[{i}/{n}] (출제자만 보기) 이번 제품: {NAMES[truth]} — 블록을 E3 십자에 놓고 검사원에게 넘긴다")
        if AUTO_JUDGE:
            guess = truth
            print(f"  자동 판정: {NAMES[guess]}")
        else:
            g = input(f"  검사원 판정 (r/b/x, 정답은 비밀): ").strip().lower()
            guess = {"r": "R", "b": "B", "x": "X"}.get(g, "X")
        dest = BINS[guess]
        arm.pick(IN_CELL)
        arm.place(dest, level=bin_count[guess])
        bin_count[guess] += 1
        ok = guess == truth
        correct += ok
        score += 10 if ok else -15
        elapsed = getattr(arm, "t", time.time() - t0)
        rows.append([i, NAMES[truth], NAMES[guess], "O" if ok else "X", f"{elapsed:.1f}"])
        print(f"  정답은 {NAMES[truth]} — {'맞음 +10' if ok else '틀림 −15'} (누적 {score}점)\n")
    arm.home()

    elapsed = getattr(arm, "t", time.time() - t0)
    rate = correct / n * 100
    through = n / (elapsed / 60) if elapsed else 0
    print("=" * 46)
    print(f"정확도 {correct}/{n} ({rate:.0f}%) · 점수 {score} · 소요 {elapsed:.0f}초"
          f" · 처리량 {through:.1f}개/분")
    print(arm.summary())
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "factory_log.csv")
    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["번호", "정답", "판정", "맞음", "누적시간(s)"])
        w.writerows(rows)
    print(f"기록 저장: {log_path}")
    print("\n[해보기] 점수 규칙을 바꿔 보자 — 틀림을 −50 으로 하면 검사원의 행동이 어떻게 변하는가?")
    print("[확장]   판정을 사람 대신 vision 의 색 검출기로 — 주제 6 코드가 그대로 꽂힌다.")
    arm.close()



# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도 기준이다. B4 지도는 04_공장_시뮬레이션_실기기_B4.py 가 지도맞추기("B4") 로 바꾼다.
지도별 = {
    "A3": dict(IN_CELL="E3", BINS={"R": "A4", "B": "I4", "X": "E4"}),
    "B4": dict(IN_CELL="D2", BINS={"R": "A3", "B": "G3", "X": "D3"}),
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
    main()
