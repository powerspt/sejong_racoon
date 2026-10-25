# -*- coding: utf-8 -*-
"""[콘텐츠 ⑤-실습] 하노이 탑 — 2장짜리를 보고 3장짜리를 직접 만든다

    python 05_하노이탑_실습_가상.py
    (실행하면 작업 지도와 가상/실기기를 묻는다 — 그냥 Enter = 가상)

기본본(05_하노이탑_기본_가상.py)에서는 7수를 사람이 적어 두었다. 4장이면 15수,
10장이면 1023수라 그 방법은 거기서 끝난다. 여기서는 **함수가 목록을 만든다.**

세 걸음으로 간다.

    1단계  두장()   블록 2장짜리. **이미 적혀 있다** — 읽고 그대로 돌려 본다
    2단계  세장()   [TODO 1] 두장() 을 불러서 3장짜리를 만든다
                    moves.append 는 **딱 한 번만** 쓴다 (가장 큰 판 한 장)
    3단계  hanoi()  [TODO 2] 두장() 과 세장() 이 똑같이 생겼다는 것을 보고
                    둘을 한 함수로 합친다 — 이것이 재귀다

**2단계만 끝내도 로봇은 움직인다.** 3단계까지 끝내면 블록수를 마음대로 바꿀 수 있다.

채우기 전에 실행해도 죽지 않는다. `확인()` 이 로봇을 쓰지 않고 먼저 채점하고,
틀리면 **몇 수째에서** 틀렸는지 말해 준다. 통과해야 팔이 움직인다.

다 해낸 뒤에 05_하노이탑_가상.py (완성본) 를 본다 — 같은 함수에 칸 점검·예행·
한수씩 모드가 붙어 있다.
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):   # 한글이 깨지지 않게
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ───────── 설정 — 여기만 바꿔 보세요 ─────────
# [레벨0] 1·2단계를 끝낸다 (블록수는 3 그대로)
# [레벨1] 3단계까지 끝내고 블록수 를 2, 4, 5 로 바꿔 본다
# [레벨2] 세장() 을 지우고 hanoi() 만으로 돌려 본다 — 무엇이 없어도 되는가
블록수 = 3          # 3단계(hanoi)를 안 채웠으면 3 으로 둔다

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

# 기본본에 적어 둔 3장짜리 정답. 확인() 이 대조용으로만 쓴다.
정답_3장 = [("A", "C"), ("A", "B"), ("C", "B"), ("A", "C"),
          ("B", "A"), ("B", "C"), ("A", "C")]

쓴횟수 = {"두장": 0}   # 세장() 이 두장() 을 정말 썼는지 세어 본다 (채점용)
# ─────────────────────────────────────────────


# ═══ 1단계 — 이미 적혀 있다. 읽기만 한다 ═══════════════════
def 두장(src, dst, via, moves):
    """블록 2장을 src 기둥에서 dst 기둥으로 옮기는 순서를 moves 에 적는다.

    팔을 움직이지 않는다. (출발, 도착) 쌍을 순서대로 적을 뿐이다.
        src = 출발 기둥 · dst = 도착 기둥 · via = 경유 기둥   ("A" / "B" / "C")

    큰 판을 옮기려면 그 위의 작은 판이 먼저 비켜 줘야 한다.
    비켜 줄 곳은 도착 기둥이 아니라 **경유 기둥**이다.
    """
    쓴횟수["두장"] += 1
    moves.append((src, via))      # ① 작은 판을 '경유'로 비켜 둔다
    moves.append((src, dst))      # ② 큰 판을 '도착'으로 옮긴다
    moves.append((via, dst))      # ③ 비켜 둔 작은 판을 그 위로


# ═══ 2단계 — [TODO 1] ═════════════════════════════════════
def 세장(src, dst, via, moves):
    """블록 3장을 src 기둥에서 dst 기둥으로. **두장() 을 써서** 채운다.

    2장짜리와 생각이 똑같다. 맨 아래 가장 큰 판을 옮기려면 그 위의 **2장**이
    먼저 비켜 줘야 하고, 비켜 줄 곳은 도착이 아니라 경유다.
    그 2장을 옮기는 방법은 이미 두장() 이 알고 있다.
    """
    # ── TODO 1 ─ 아래 ①과 ③ 두 줄을 채운다 ─────────────────
    #
    # ① 위의 2장을 '경유' 기둥으로 비켜 둔다
    #       그 작은 문제에서는 출발이 src, 도착이 via 다.
    #       남는 기둥 하나가 그 문제의 경유가 된다.
    #       두장(___, ___, ___, moves)
    #
    # ② 가장 큰 판 한 장을 출발에서 도착으로  (이 줄은 적어 두었다)
    moves.append((src, dst))
    #
    # ③ 비켜 둔 2장을 '경유'에서 '도착'으로 옮긴다
    #       그 작은 문제에서는 출발이 via, 도착이 dst 다.
    #       두장(___, ___, ___, moves)
    #
    # 함정: moves.append 를 더 쓰지 않는다. 7수를 손으로 적으면 두장() 을 안 쓴 것이고,
    #       3단계에서 합칠 것이 없어진다.


# ═══ 3단계 — [TODO 2] ═════════════════════════════════════
def hanoi(n, src, dst, via, moves):
    """n 장을 src 기둥에서 dst 기둥으로. 두장() 과 세장() 을 하나로 합친 것.

    두 함수를 나란히 놓고 보면 다른 것은 **장 수뿐**이다.
        두장 = (1장짜리) + 가운데 한 수 + (1장짜리)
        세장 = (2장짜리) + 가운데 한 수 + (2장짜리)
    그러면 n 장은 (n-1 장짜리) + 가운데 한 수 + (n-1 장짜리) 다.
    부를 함수의 이름이 자기 자신이 된다.
    """
    # ── TODO 2 ─ 아래 세 줄을 채운다 ───────────────────────
    #
    # 멈추는 조건 — 옮길 블록이 한 장도 없으면 할 일이 없다
    #       if ___ : return
    #
    # ① 위의 n-1 장을 '경유' 기둥으로
    #       hanoi(n - 1, ___, ___, ___, moves)
    #
    # ② 가장 큰 판 한 장  (이 줄은 적어 두었다)
    moves.append((src, dst))
    #
    # ③ 비켜 둔 n-1 장을 '경유'에서 '도착'으로
    #       hanoi(n - 1, ___, ___, ___, moves)
    #
    # 함정: 멈추는 조건이 없으면 함수가 자기를 끝없이 불러 프로그램이 멈춘다.
    # [레벨2] 세장() 의 두 줄을 그대로 옮겨 적고 이름과 숫자만 바꿔 본다.


# ═══ 채점 ═════════════════════════════════════════════════
def 확인(moves, n):
    """로봇을 쓰지 않고 먼저 채점한다. 통과하면 None, 아니면 틀린 이유 한 줄."""
    if not moves:
        return "목록이 비어 있다 — 아직 TODO 를 안 채웠다."
    if len(moves) < n:
        return (f"{len(moves)}수뿐이다 — 가장 큰 판 한 장만 옮기고 끝났다. "
                f"나머지 {n - 1}장을 비켜 두는 줄이 빠졌다.")
    tower = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    for i, (s, d) in enumerate(moves, 1):
        if s not in tower or d not in tower:
            return f"{i}수: 기둥 이름이 이상하다 ({s} → {d}). A · B · C 중 하나여야 한다."
        if s == d:
            return f"{i}수: {s}기둥에서 집어 {d}기둥에 놓는다 — 제자리다."
        if not tower[s]:
            return f"{i}수: {s}기둥이 비어 있는데 거기서 집으려 한다."
        블록 = tower[s][-1]
        if tower[d] and tower[d][-1] < 블록:
            return (f"{i}수: {블록}번 블록을 {tower[d][-1]}번 블록보다 먼 칸에 두려 한다 "
                    f"— 작은 판보다 먼 칸에 큰 판을 둘 수 없다.")
        tower[d].append(tower[s].pop())
    if len(tower["C"]) != n:
        return f"끝났는데 C기둥에 {len(tower['C'])}장뿐이다 — {n}장을 다 옮기지 못했다."
    if len(moves) != 2 ** n - 1:
        return (f"{len(moves)}회가 나왔다 — 최소 횟수는 {2 ** n - 1}회다. "
                f"쓸데없이 옮기는 수가 있다.")
    if n == 3 and moves != 정답_3장:
        다른수 = next(i for i, (a, b) in enumerate(zip(moves, 정답_3장), 1) if a != b)
        return (f"규칙은 지켰는데 기본본의 7수와 다르다 — {다른수}수째가 처음 갈린다 "
                f"(적어 둔 것은 {정답_3장[다른수 - 1][0]} → {정답_3장[다른수 - 1][1]}).")
    return None


def 세장_채점():
    """2단계 결과. (목록, 틀린 이유 또는 None)"""
    쓴횟수["두장"] = 0
    moves = []
    세장("A", "C", "B", moves)
    틀림 = 확인(moves, 3)
    if 틀림:
        return moves, 틀림
    if 쓴횟수["두장"] != 2:
        return moves, (f"7수는 맞는데 두장() 을 {쓴횟수['두장']}번 썼다 — 두 번이어야 한다. "
                       f"손으로 적지 말고 두장() 에게 시킨다.")
    return moves, None


def hanoi_채점(n):
    """3단계 결과. (목록, 상태) · 상태 = None 통과 / '미완성' / 틀린 이유"""
    moves = []
    try:
        hanoi(n, "A", "C", "B", moves)
    except RecursionError:
        return moves, "함수가 자기를 끝없이 불렀다 — 멈추는 조건이 없다."
    if len(moves) == 1 and n > 1:
        return moves, "미완성"
    return moves, 확인(moves, n)


# ═══ 로봇 ═════════════════════════════════════════════════
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


def 동선정하기():
    """어느 단계까지 됐는지 보고, 팔이 수행할 목록과 블록 수를 정한다."""
    moves, 틀림 = 세장_채점()
    if 틀림:
        print("\n  X  2단계(세장) — " + 틀림)
        print("\n  세장() 의 TODO 1 을 고치고 다시 실행하세요.")
        print("  바로 위 두장() 을 다시 읽어 보세요 — 생각이 똑같습니다.")
        return None, None
    print("  O  2단계(세장) 통과 — 7수, 규칙을 지켰고 두장() 을 두 번 썼습니다.")

    h_moves, 상태 = hanoi_채점(블록수)
    if 상태 == "미완성":
        print("  -  3단계(hanoi) 는 아직입니다 — 오늘은 세장() 으로 돌립니다.")
        print("     블록 3장만 됩니다. 3단계를 채우면 블록수를 바꿀 수 있습니다.")
        return moves, 3
    if 상태:
        print(f"\n  X  3단계(hanoi) — {상태}")
        print("\n  hanoi() 의 TODO 2 를 고치고 다시 실행하세요.")
        print("  (2단계는 이미 통과했습니다 — 세장() 의 두 줄을 옮겨 적는 것부터.)")
        return None, None
    print(f"  O  3단계(hanoi) 통과 — 블록 {블록수}장 {len(h_moves)}수 "
          f"(= 2^{블록수} - 1).")
    return h_moves, 블록수


def main(arm=None):
    print("채점부터 합니다 (로봇 없이).\n")
    moves, n = 동선정하기()
    if moves is None:
        return 1

    print()
    for i, (s, d) in enumerate(moves[:31], 1):
        print(f"   {i}수  {s} → {d}")
    if len(moves) > 31:
        print(f"   ... 모두 {len(moves)}수 (너무 많아 31수까지만 적었습니다)")
        # 블록수를 올려 본 학생은 여기서 지수 증가를 숫자가 아니라 결정으로 만난다
        print(f"\n한 수에 6초면 {len(moves)}수는 {len(moves) * 6 / 60:.0f}분입니다.")
        if input("그래도 수행할까요? [y / 그냥 Enter = 여기서 끝] > ").strip().lower() != "y":
            print("안 돌리기로 했습니다 — 그 결정 자체가 답입니다.")
            return 0

    paper = ask_paper()
    if n not in LAYOUTS[paper]:
        있는것 = ", ".join(f"{k}장" for k in sorted(LAYOUTS[paper]))
        print(f"{paper} 매트에 {n}장짜리 기둥 배치가 없습니다. 있는 것: {있는것}")
        print("   LAYOUTS 에 칸을 적어 주면 그 수로도 됩니다.")
        return 1
    pegs = LAYOUTS[paper][n]
    set_paper(paper)
    print(f"  기둥 A={pegs['A'][0]}..  B={pegs['B'][0]}..  C={pegs['C'][0]}.. "
          f"— 매트에 적힌 칸 이름과 같은지 보세요")

    tower = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    print(f"\n블록 {n}장은 1번이 가장 작고 {n}번이 가장 큽니다.")
    for cell, d in zip(pegs["A"][:n], tower["A"]):
        print(f"   {d}번 크기 블록을 {cell} 칸에 놓아 주세요.")
    print(f"   {pegs['A'][0]} 가 로봇에 가장 가까운 칸입니다.\n")
    picture(tower, pegs, n, legend=True)
    input("\n다 놓았으면 Enter 를 누르세요 (가상 모드면 그냥 Enter) > ")

    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    for i, (s, d) in enumerate(moves, 1):
        disk = tower[s][-1]
        from_cell = pegs[s][len(tower[s]) - 1]
        to_cell = pegs[d][len(tower[d])]
        print(f"- {i}/{len(moves)}  {disk}번 크기 블록  {s}({from_cell}) → {d}({to_cell})")
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
#  1. 네장() 을 세장() 처럼 손으로 써 본다. 다섯장() 은? — 어디까지 할 수 있는가
#  2. hanoi() 맨 위에 print(n, src, dst, via) 를 한 줄 넣고 3장으로 돌린다.
#     호출이 어떤 순서로 들어갔다 나오는지 눈으로 본다.
#  3. 블록수 를 20 으로 두면 몇 수인가? 한 수에 6초면 며칠인가?
#     (돌리지 말고 계산만 한다 — 왜 돌리면 안 되는지가 이 문제의 답이다)
#  4. ②의 moves.append 를 ① 앞으로 올리면 어떤 동선이 나오는가? 확인() 이 뭐라고 하는가?
