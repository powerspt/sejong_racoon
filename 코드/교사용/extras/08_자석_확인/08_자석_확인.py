# -*- coding: utf-8 -*-
"""자석 낚시 — 적용 가능성 확인 (실제 로봇 전용, 30분)

    python 08_자석_확인_실기기_A3.py     A3 지도
    python 08_자석_확인_실기기_B4.py     B4 지도

활동을 만들기 전에 셋을 잰다. 셋이 되면 자석 활동은 코드 두 함수로 끝난다.

    1) 붙는 높이   z 를 3.0 → 1.5 로 내려 가며 몇 번 중 몇 번 붙나  → 09·10 의 자석높이
    2) 손목 돌림   붙인 채 홈으로 가도 안 떨어지나                   → 자력이 충분한가
    3) 겹침        한 칸에 클립 3개 — 한 번에 몇 개가 붙어 오나       → 경주 규칙

끝나면 권장 높이가 화면에 나온다 — 09·10 _가상.py 의 자석높이 에 그 숫자를 적는다.
붙은 클립은 **사람이 뗀다.** 턱으로 떼어내는 방식은 집게가 바닥을 긁어 뺐다(2026-10-25).

준비
    집게 날 **아래 면**(눕힌 채 바닥을 보는 면)에 네오디뮴 원형 자석(10~12mm)을 양면테이프로 붙이고 집게를 닫는다.
    집게는 세우지 않는다 — 블록 집을 때처럼 눕힌 채 반경에 맞춰 0°/45° 만 쓴다.
    시험 칸 E3(B4 는 D3)에 철 클립 하나.
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
시험칸 = "E3"
Z_목록 = (3.0, 2.5, 2.0, 1.5)      # 1) 붙는 높이 — 높은 데서 내려온다
회수 = 3                           # 높이마다 몇 번
# ─────────────────────────────────────────────────────


# 위 설정은 A3 지도 기준이다 — A3 에서는 설정을 그대로 쓴다.
# B4 지도는 08_자석_확인_실기기_B4.py 가 지도맞추기("B4") 로 아래 칸으로 갈아 끼운다.
지도별 = {
    "B4": dict(시험칸="D3"),
}


def 지도맞추기(paper):
    """실제 로봇 파일이 부른다. A3 는 설정 그대로, 다른 지도는 칸 이름만 그 지도 것으로 바꾼다."""
    set_paper(paper)
    if paper != "A3":
        globals().update(지도별[paper])
        print(f"[{paper} 지도] 칸 설정을 {paper} 용으로 바꿨다 — 시험칸={시험칸}")


def 예(글):
    return input(글 + " [y/n] > ").strip().lower() in ("y", "ㅇ", "yes")


def 비율(arm, z):
    붙음 = 0
    for i in range(회수):
        input(f"    {i + 1}/{회수} — 클립을 {시험칸} 가운데에 놓고 Enter > ")
        arm.pick_magnet(시험칸, z)
        if 예("    붙었나?"):
            붙음 += 1
            input("    클립을 떼고 Enter > ")
    return 붙음


@안전하게
def main(arm=None):
    if arm is None:            # 이 파일을 바로 실행했다 — 팔은 실제 로봇 파일이 넘겨 준다
        print("이 활동은 실제 로봇 전용이다 — 08_자석_확인_실기기_A3.py 를 연다 (B4 지도는 _B4).")
        return
    print(__doc__.split("준비")[0])
    결과 = {}

    print("\n[1] 붙는 높이")
    for z in Z_목록:
        print(f"  z = {z}")
        결과[z] = 비율(arm, z)
        print(f"  → {결과[z]}/{회수}")
        if 결과[z] == 회수 and z > Z_목록[-1]:
            if not 예("  다 붙었다. 더 낮은 높이도 재 볼까?"):
                break

    print("\n[2] 손목 돌림 — 붙인 채 홈으로 간다")
    input("  클립을 놓고 Enter > ")
    arm.pick_magnet(시험칸)
    arm.home()
    손목 = 예("  홈까지 갔다. 아직 붙어 있나?")
    if 손목:
        input("  클립을 떼고 Enter > ")

    print("\n[3] 겹침 — 한 칸에 클립 3개")
    겹침 = []
    for i in range(회수):
        input(f"    {i + 1}/{회수} — 클립 3개를 {시험칸} 에 겹쳐 놓고 Enter > ")
        arm.pick_magnet(시험칸)
        n = input("    몇 개 붙어 왔나? [숫자] > ").strip()
        겹침.append(int(n) if n.isdigit() else 0)
        input("    붙은 것을 떼고, 남은 클립을 치우고 Enter > ")

    arm.home()
    arm.close()

    print("\n" + "=" * 50)
    print("붙는 높이   " + "  ".join(f"z{z}:{결과.get(z, '-')}/{회수}" for z in Z_목록))
    print(f"손목 돌림   {'붙어 있음' if 손목 else '떨어짐 — 자석을 더 센 것으로'}")
    print(f"겹침        {겹침}  (한 번에 {max(겹침) if 겹침 else 0}개까지)")
    print("=" * 50)
    좋은z = [z for z, n in 결과.items() if n == 회수]
    if 좋은z:
        z권장 = round(max(좋은z) - 0.5, 2) if max(좋은z) - 0.5 >= min(Z_목록) else max(좋은z)
        print(f"권장 자석높이 = {z권장}   (다 붙은 높이 중 가장 높은 것 {max(좋은z)} 에서 0.5 더 가까이)")
        print(f"  → 09_자석_탐색_가상.py · 10_자석_경주_가상.py 의 자석높이 = {z권장} 로 적는다")
    else:
        print(f"자석높이 권장 못 함 — 어느 높이에서도 {회수}/{회수} 가 안 됐다. 자석이 약하거나 클립이 미끄러진다")
    print(f"판단: 붙기 {회수}/{회수} · 손목 붙어 있음 이면 활동을 그대로 쓴다. 아니면 그 줄부터 손본다.")

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
