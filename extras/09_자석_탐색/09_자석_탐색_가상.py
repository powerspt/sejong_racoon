# -*- coding: utf-8 -*-
"""[콘텐츠 ⑨] 자석 탐색 · 가상 — 한 줄에 숨은 클립 하나를 몇 번 만에 찾나

    python 09_자석_탐색_가상.py          로봇 없이 — 코드가 클립을 숨기고 '붙었나' 를 답한다
    python 09_자석_탐색_실기기_A3.py     진짜 로봇 · A3 지도 (B4 는 _B4)

작업 지도의 **한 줄**(2행)에 짝이 클립 **하나**를 놓는다. 술래는 지도를 보지 않는다.
로봇이 칸을 하나씩 찍어 보고(자석을 내렸다 든다), 붙었는지를 사람이 y/n 으로 답한다.
**몇 번 만에 찾았나**가 점수다.

    찍는 순서를 고른다
      1 순차 탐색   왼쪽 끝부터 차례로
      2 랜덤 탐색   매번 남은 칸 가운데 아무 데나
      3 내가 정한 순서
      4 이진 탐색     가운데를 찍고, 짝이 "더 왼쪽 / 더 오른쪽" 을 알려 주면 반을 버린다

    여러 판을 돌려 **평균**을 낸다. 순차든 랜덤이든 평균은 (칸 수 + 1) / 2 로 같다 —
    그런데 왜 다르게 느껴질까? 최악은? 이동 시간은?
    이진 탐색은 "붙었나" 만으로는 안 된다 — 자석은 정답이 어느 쪽인지 모른다. 짝이
    왼쪽/오른쪽을 말해 줘야(= 자료가 정렬돼 있어야) 아홉 칸을 네 번 안에 끝낸다.

이 파일 하나로 돌아간다 — 로봇을 움직이는 부품은 파일 맨 아래에 있다.
"""
import random
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
줄 = ["A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2", "I2"]
#   클립을 놓는 한 줄 (A3 지도 2행). 집게를 세우지 않고(0°/45°) 닿는 줄이다 — 1행은 안 닿는다
자석높이 = 2.7        # ★ 자석을 내리는 집게 끝 높이 — 08_자석_확인 이 알려 준 권장값을 적는다
판수 = 3              # 몇 판 돌리나 (판마다 짝이 클립을 다시 놓는다). 실기기는 판 사이에 q 로 끝낼 수 있다
SEED = 7              # 가상 모드가 클립을 놓는 자리. 같은 숫자 = 같은 문제
방식 = None           # None 이면 실행할 때 고른다. "순차" / "랜덤" / "직접" 을 적으면 안 묻는다
내순서 = []           # 방식 "직접" 일 때 찍을 순서. 비면 실행할 때 입력받는다
시험판수 = 300        # 가상에서 방식별 평균을 낼 때 돌리는 판 수
이동속도 = 8.0        # cm/s — 가상 시계용. 멀리 뛰면 그만큼 오래 걸린다
# ─────────────────────────────────────────────────────
# [레벨0] 세 방식을 5판씩 돌려 평균 횟수를 견준다 — 누가 이기나? 정말 이긴 건가?
# [레벨1] 판수 를 1000 으로 두고(가상) 평균이 어디로 모이나 본다 — (칸 수+1)/2
# [레벨2] 이진_한판() 에서 가운데 대신 1/3 지점을 찍게 바꾸면 평균이 어떻게 되나

방식이름 = {"1": "순차", "2": "랜덤", "3": "직접", "4": "이진"}


def 순서_만들기(방식, rng):
    if 방식 == "이진":
        return None                       # 순서를 미리 정하지 않는다 — 답을 듣고 반을 고른다
    if 방식 == "순차":
        return list(줄)
    if 방식 == "랜덤":
        return rng.sample(줄, len(줄))
    순서 = [c.strip().upper() for c in 내순서 if c.strip()]
    모름 = [c for c in 순서 if c not in 줄]
    if 모름 or len(set(순서)) != len(줄):
        raise ValueError(f"내순서 에는 {줄} 를 한 번씩 전부 적는다 (잘못된 것: {모름 or '빠진 칸'})")
    return 순서


def 여행(arm, 여기, 저기):
    """가상 모드에서만 — 칸 사이 거리에 비례해 시간을 더한다."""
    if 여기 is not None and hasattr(arm, "t"):
        (x0, y0), (x1, y1) = cell_to_xy(여기), cell_to_xy(저기)
        d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        arm._log(f"MOVE  {여기}→{저기} {d:.0f}cm", d / 이동속도)


def 묻기_예아니오(글):
    while True:
        a = input(글 + " [y/n] > ").strip().lower()
        if a in ("y", "ㅇ", "yes"):
            return True
        if a in ("n", "ㄴ", "no"):
            return False


def 이진_한판(arm, 정답, 실기기):
    """가운데를 찍고 '더 왼쪽/더 오른쪽' 을 들어 반씩 버린다. (횟수, 찾은 칸)."""
    lo, hi, 지금, 횟수 = 0, len(줄) - 1, None, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        cell = 줄[mid]
        횟수 += 1
        여행(arm, 지금, cell)
        arm.pick_magnet(cell, 자석높이)
        지금 = cell
        if 실기기:
            while True:
                a = input(f"    {cell}: [y 붙었다 / l 정답은 더 왼쪽 / r 더 오른쪽] > ").strip().lower()
                a = {"ㅛ": "y", "ㅣ": "l", "ㄱ": "r"}.get(a, a)
                if a in ("y", "l", "r"):
                    break
            답 = a
        else:
            k = 줄.index(정답)
            답 = "y" if k == mid else ("l" if k < mid else "r")
        print(f"    {횟수:2d}번째 {cell} (남은 {줄[lo]}~{줄[hi]}) → "
              + {"y": "O 붙었다", "l": "X, 더 왼쪽", "r": "X, 더 오른쪽"}[답])
        if 답 == "y":
            if 실기기:
                input("    붙은 클립을 떼어 통에 넣고 Enter > ")
            return 횟수, cell
        if 답 == "l":
            hi = mid - 1
        else:
            lo = mid + 1
    return 횟수, None


def 한판(arm, 순서, 정답, 실기기):
    """순서대로 찍어 본다. (횟수, 찾은 칸) — 못 찾으면 (len(줄), None)."""
    지금 = None
    for 횟수, cell in enumerate(순서, 1):
        여행(arm, 지금, cell)
        arm.pick_magnet(cell, 자석높이)
        지금 = cell
        붙음 = 묻기_예아니오(f"    {cell}: 붙었나?") if 실기기 else (cell == 정답)
        print(f"    {횟수:2d}번째 {cell} → {'O 붙었다' if 붙음 else 'X'}")
        if 붙음:
            if 실기기:
                input("    붙은 클립을 떼어 통에 넣고 Enter > ")
            return 횟수, cell
    return len(순서), None


def 평균표(rng):
    """가상 — 방식별로 시험판수 만큼 돌려 평균·최악 횟수와 평균 이동 거리를 낸다."""
    print(f"\n  [참고] 방식별 {시험판수}판 (가상)")
    print("   방식    평균 횟수   최악   평균 이동(cm)")
    for 이름 in ("순차", "랜덤", "이진"):
        합, 최악, 거리합 = 0, 0, 0.0
        for _ in range(시험판수):
            정답 = rng.choice(줄)
            if 이름 == "이진":
                순서, lo, hi = [], 0, len(줄) - 1
                while True:
                    mid = (lo + hi) // 2
                    순서.append(줄[mid])
                    if 줄[mid] == 정답:
                        break
                    if 줄.index(정답) < mid:
                        hi = mid - 1
                    else:
                        lo = mid + 1
            else:
                순서 = 순서_만들기(이름, rng)
            n = 순서.index(정답) + 1
            합 += n
            최악 = max(최악, n)
            d = 0.0
            for a, b in zip(순서, 순서[1:n]):
                (x0, y0), (x1, y1) = cell_to_xy(a), cell_to_xy(b)
                d += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            거리합 += d
        print(f"   {이름:4s}   {합 / 시험판수:6.2f}      {최악:2d}      {거리합 / 시험판수:6.1f}")
    print(f"   (칸 {len(줄)}개 → 순차·랜덤 기대값 {(len(줄) + 1) / 2:.1f}번 · 이진은 최대 {len(줄).bit_length()}번."
          "  순차와 랜덤은 평균이 같고 **이동 거리**가 다르다. 이진은 **힌트**가 있어야 된다)")


def main(arm=None):
    global 내순서
    if arm is None:            # 그냥 돌리면 가상 — 실기기는 _실기기.py 가 진짜 팔을 넘긴다
        arm = DummyArm()
    실기기 = not hasattr(arm, "t")
    rng = random.Random(SEED)
    print(__doc__.split("\n\n")[1])
    print(f"\n  줄: {' '.join(줄)}  (클립 1개 · {판수}판)")

    고른 = 방식
    if 고른 not in ("순차", "랜덤", "직접", "이진"):
        while True:
            a = input("\n어떻게 찾을까요? [1 순차 / 2 랜덤 / 3 내가 정한 순서 / 4 이진(짝이 왼쪽·오른쪽 힌트)] > ").strip()
            if a in 방식이름:
                고른 = 방식이름[a]
                break
    if 고른 == "직접" and not 내순서:
        s = input(f"  찍을 순서를 띄어 적는다 ({len(줄)}칸 전부, 예: E2 D2 F2 C2 G2 …) > ")
        내순서 = s.replace(",", " ").split()
    if 고른 == "이진":
        print("  규칙 — 로봇이 찍은 칸에 클립이 없으면 짝이 '더 왼쪽' 인지 '더 오른쪽' 인지 말해 준다.")
    try:
        순서_만들기(고른, random.Random(0))
    except ValueError as e:
        print("  !", e)
        return

    기록 = []
    for 판 in range(1, 판수 + 1):
        print(f"\n[{판}판 · {고른} 탐색]")
        if 실기기:
            input(f"  술래는 지도를 보지 않는다. 짝이 {' '.join(줄)} 중 한 칸에 클립을 놓았으면 Enter > ")
            정답 = None
        else:
            정답 = rng.choice(줄)
        순서 = 순서_만들기(고른, rng)
        if 순서 is not None and 고른 != "순차":
            print(f"  순서: {' '.join(순서)}")
        t0 = 0.0 if 실기기 else arm.t
        횟수, 찾은 = (이진_한판(arm, 정답, 실기기) if 고른 == "이진"
                  else 한판(arm, 순서, 정답, 실기기))
        걸림 = 0.0 if 실기기 else arm.t - t0
        기록.append(횟수)
        print(f"  → {횟수}번 만에 " + (f"{찾은} 에서 찾았다" if 찾은 else "못 찾았다 — 클립이 줄 밖에 있나?")
              + ("" if 실기기 else f"  (가상 {걸림:.1f}초)"))
        if 실기기 and 판 < 판수 and input("  [Enter = 다음 판 / q = 여기서 끝] > ").strip().lower() == "q":
            break

    print("\n" + "=" * 46)
    print(f"{고른} 탐색 {len(기록)}판 — 횟수 {기록} · 평균 {sum(기록) / len(기록):.2f}번 · 최악 {max(기록)}번")
    print("=" * 46)
    if not 실기기:
        평균표(random.Random(SEED + 1))
    print("\n[생각] 순차와 랜덤은 평균이 같은데 랜덤이 더 느리게 느껴진다면 왜일까?")
    print("       이진은 왜 자석만으로는 안 되나 — 짝이 해 준 일은 무엇인가? 칸이 100개라면 몇 번?")
    arm.home()
    if hasattr(arm, "summary"):
        print(arm.summary())
    if hasattr(arm, "close"):
        arm.close()


# ── 작업 지도별 칸 ─────────────────────────────────────
# 위 설정은 A3 지도(2행 A~I) 기준이다. B4 지도는 _실기기_B4.py 가 지도맞추기("B4") 로 바꾼다.
지도별 = {
    "A3": dict(줄=["A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2", "I2"]),
    "B4": dict(줄=["A2", "B2", "C2", "D2", "E2", "F2", "G2"]),
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
