# -*- coding: utf-8 -*-
"""기본 동작 · 가상 — 로봇 없이 화면으로

로봇팔이 하는 일을 가장 작은 동작 네 개로 쪼개 놓았다.

    가기(칸, 높이=8, 기울기=-45)   집게 끝을 그 칸의 그 높이로 보낸다
    집게("열기")  ·  집게("닫기")   집게를 움직인다
    기다리기(0.7)                   그대로 멈춰 있는다 (초)
    홈()                            처음 자세로 돌아간다

집기 · 놓기 · 옮기기 · 자석 은 이 네 개를 이어 붙인 것이다. 아래 [조합 동작] 칸에
한 줄씩 풀어 적어 두었다. 줄을 빼 보고, 숫자를 바꿔 보고, 순서를 바꿔 본다.
    예) 집기() 에서 집게("닫기") 줄을 빼면?   ·  ⑥ 드는 줄을 빼고 놓기() 를 하면?
        접근높이 를 3 으로 낮추면?            ·  집는높이 를 3 으로 올리면?
가상에서는 화면에 찍히는 줄만 달라진다. 무슨 일이 생기는지는 실제 로봇에서 본다.

고칠 데는 [설정] · [해보기] · [조합 동작] 세 칸이다.
기울기는 0 이 수평, -45 가 비스듬히, -90 이 아래로다. 높이 z 는 집게 끝 기준이다 (책상 = 0).
세운 집게(-90)는 z 1.5, 눕힌 집게(0)는 z 0.6 쯤에서 바닥에 닿는다 — 1.5 아래로는 보내지 않는다.
안 되는 명령을 만나면 그 줄에서 멈추고, 멈춘 뒤에는 더 움직이지 않는다 (Home 으로도 돌아가지 않는다).
이 파일은 가상(로봇 없이)이다. 실제 로봇은 11_기본_동작_실기기_A3.py 를 연다.
"""
import sys


try:                                   # 콘솔이 못 찍는 글자(—)를 ? 로 흘려보낸다
    sys.stdout.reconfigure(errors="replace")      # (건드리지 않아도 된다)
except (AttributeError, ValueError):
    pass


# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
집는칸 = "E3"
놓는칸 = "E2"
#   블록을 집을 칸과 놓을 칸. 실제 로봇으로 돌릴 때는 집는칸 에 3cm 블록을 놓는다.
접근높이 = 8
#   칸 위에서 멈추는 높이(cm · z 는 집게 끝 기준, 책상 = 0). 블록(3cm) 위로 넘어 다닐 만큼 띄운다.
집는높이 = 1.5
#   블록을 쥐는 높이(cm). 주제 4에서 잰 값이다.
자석높이 = 2.7
#   자석을 내리는 높이(cm).
# ══════════════════════════════════════════════════════


# ════════ 해보기 — 돌려 볼 동작을 한 줄씩 적는다 ════════════
def 해보기():
    가기(집는칸, 높이=접근높이)        # 기본 동작만으로 — 칸 위에 갔다가
    가기(집는칸, 높이=집는높이)        # 내려갔다가
    가기(집는칸, 높이=접근높이)        # 올라온다
    홈()

    집기(집는칸)                       # 조합 동작 — 아래 칸에 풀어 적혀 있다
    놓기(놓는칸)
    홈()
# ══════════════════════════════════════════════════════


# ════════ 조합 동작 — 기본 동작을 이어 붙인 것. 뜯어 고쳐 본다 ════════
# 새 동작을 만들려면 def 한 덩어리를 복사해 이름을 바꾸고, 해보기() 에서 부른다.
# 여기서 만든 동작은 통째로 복사해 11_프로젝트_틀_가상.py 의 [조합 동작] 칸에 붙여 쓴다.
def 집기(칸):
    집게("열기")                                   # ① 벌린다
    가기(칸, 높이=접근높이, 기울기=맞는기울기(칸))  # ② 칸 위로 — 기울기는 여기서 잡는다
    가기(칸, 높이=집는높이)                        # ③ 곧게 내려간다
    집게("닫기")                                   # ④ 쥔다
    기다리기(0.7)                                  # ⑤ 집게가 다 닫힐 때까지
    가기(칸, 높이=접근높이)                        # ⑥ 든다


def 놓기(칸):
    가기(칸, 높이=접근높이)                        # ① 칸 위로 — 기울기는 쥘 때 그대로
    가기(칸, 높이=집는높이)                        # ② 내려간다
    집게("열기")                                   # ③ 놓는다
    기다리기(0.5)
    가기(칸, 높이=접근높이)                        # ④ 빈손으로 올라온다


def 옮기기(어디서, 어디로):
    집기(어디서)                                   # 조합 동작끼리도 이어 붙인다
    놓기(어디로)
    홈()


def 자석(칸):
    집게("닫기")                                   # 자석은 닫힌 집게 날 사이에 있다
    가기(칸, 높이=접근높이, 기울기=맞는기울기(칸))
    가기(칸, 높이=자석높이)                        # 붙을 만큼만 내려간다
    기다리기(0.3)
    가기(칸, 높이=접근높이)
# ══════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 여기부터 파일 끝까지는 고치지 않는다 — 실행 부분이다.
# 기본 동작 네 개(가기 · 집게 · 기다리기 · 홈)의 속은 이 파일 맨 아래에 있다.
# ══════════════════════════════════════════════════════════════════════


def main(arm=None):
    팔 = 팔잡기(arm or DummyArm())
    끝까지 = False
    try:
        해보기()
        끝까지 = True
    except 멈춤 as e:
        print(f"\n  ■ 멈춤 — {e}")
        print("    해보기() 에 이 줄이 없으면 [조합 동작] 안의 줄이다. 고친 뒤 다시 돌린다.")
    except ValueError as e:                       # 없는 칸 이름
        print(f"\n  ■ 멈춤 — {e}")
    except KeyboardInterrupt:
        print("\n  ■ 사람이 멈췄다 (Ctrl+C)")
    finally:
        print("\n" + "=" * 46)
        print(팔.summary())
        팔.close(home=끝까지)             # 멈췄으면 Home 으로 가지 않는다


# ── 작업 지도 ─────────────────────────────────────────
# 설정의 칸 이름은 A3 지도 기준이다. B4 지도는 11_기본_동작_실기기_B4.py 가 지도맞추기("B4") 로 바꾼다.
지도별 = {
    "B4": dict(집는칸="D2", 놓는칸="D1"),
}


def 지도맞추기(paper):
    """지도("A3"/"B4")를 정한다. 실제 로봇 파일이 부른다. B4 일 때만 칸 설정을 B4 용으로 바꾼다."""
    지도_바꾸기(paper, globals(), "집는칸 놓는칸")

# ══════════════════════════════════════════════════════════════════════
# 여기부터 끝까지는 로봇을 움직이는 부품이다 — 고치지 않는다.
# 바꿔 볼 것은 위의 '설정 — 여기만 바꿔 보세요' 칸에 있다.
# (robot_helpers.py 에서 이 활동이 쓰는 것만 옮겨 왔다)
# ══════════════════════════════════════════════════════════════════════
import math
import os
import sys
import time

class Stopped(Exception):
    pass
멈춤 = Stopped

def 지도_바꾸기(paper, 설정, 보일=''):
    set_paper(paper)
    if paper in 설정.get('지도별', {}):
        설정.update(설정['지도별'][paper])
        값 = ' '.join((f'{이름}={설정[이름]}' for 이름 in 보일.split()))
        print(f'[{paper} 지도] 칸 설정을 {paper} 용으로 바꿨다 — {값}')
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
TRAVEL = 9.0
PRECISION_MODE = False
L1, L2, L3 = (8.25, 10.0, 10.0)
JOINT_LIMITS = ((-120, 120), (-90, 30), (-150, 0), (-105, 105))
TOOL_REF = (8.0, -0.6)

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

    def go(self, where, z=HOVER, tilt=None):
        x, y = where if isinstance(where, (tuple, list)) else cell_to_xy(where)
        지금 = getattr(self, 'tilt_now', 0.0)
        후보 = [tilt] if tilt is not None else [지금, tilt_for((x * x + y * y) ** 0.5)[0]]
        for a in 후보:
            if not over_limit(ik_joints(x, y, z, a, TOOL_REF)):
                self.n_move += 1
                self.tilt_now = a
                self._log(f'GO    {where} ({x:g}, {y:g}) z={z:g} 기울기 {a:g}°', self.T_MOVE)
                return True
        bad = over_limit(ik_joints(x, y, z, 후보[0], TOOL_REF))
        why = ', '.join((f'J{i}={v:.0f}° (한계 {lo}~{hi})' for i, v, lo, hi in bad if v is not None)) or '팔 길이로 닿지 않는 거리'
        self._log(f'!!    {where} z={z:g} 기울기 {후보[0]:g}° 로는 설 수 없다 — {why}', 0)
        return False

    def grip(self, open_=True):
        self._log('GRIP  ' + ('열기' if open_ else '닫기'), 0.7)
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

    def go(self, where, z=HOVER, tilt=None):
        x, y = where if isinstance(where, (tuple, list)) else cell_to_xy(where)
        후보 = [tilt] if tilt is not None else [self.tilt_now, tilt_for((x * x + y * y) ** 0.5)[0]]
        고름 = next((a for a in 후보 if self._solve(x, y, z, a) is not None), None)
        if 고름 is None:
            print(f'  !! {where} z={z:g} 기울기 {후보[0]:g}° 로는 설 수 없다 — {self._why(x, y, z, 후보[0])}')
            return False
        self._set_tilt(고름)
        if abs(self.tilt_now - 고름) >= 1.0:
            return False
        try:
            cx, cy, cz = self.bot.xyz()[:3]
        except Exception:
            cx = None
        if cx is not None and ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5 < 0.5:
            return self._descend(x, y, cz, z)
        위 = z
        while 위 + 0.5 <= TRAVEL and self._solve(x, y, 위 + 0.5) is not None:
            위 += 0.5
        if 위 > z:
            return self._goto(x, y, 위) and self._descend(x, y, 위, z)
        return self._goto(x, y, z)

    def grip(self, open_=True):
        if open_:
            self.bot.open_gripper()
        else:
            self.bot.close_gripper()
        self._wait(WAIT_GRIP_MS)

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
최저높이 = 1.5
팔 = None

def 팔잡기(arm):
    global 팔
    팔 = arm
    return arm

def 가기(자리, 높이=10, 기울기=None):
    if 높이 < 최저높이:
        raise 멈춤(f'가기({자리!r}, 높이={높이}) — 높이는 {최저높이} 이상으로 적는다 (세운 집게는 {최저높이} 에서 바닥에 닿는다)')
    if 팔.go(자리, 높이, 기울기) is False:
        raise 멈춤(f'가기({자리!r}, 높이={높이}, 기울기={기울기}) — 높이를 올리거나 기울기를 바꿔 본다')

def 집게(무엇):
    if 무엇 not in ('열기', '닫기'):
        raise 멈춤(f'집게({무엇!r}) — "열기" 나 "닫기" 로 적는다')
    팔.grip(무엇 == '열기')

def 기다리기(초):
    if hasattr(팔, 't'):
        팔.t += 초
        print(f'  [가상 {팔.t:6.1f}s] WAIT  {초:g}초')
    else:
        time.sleep(초)

def 맞는기울기(자리):
    x, y = 자리 if isinstance(자리, (tuple, list)) else cell_to_xy(자리)
    return tilt_for((x * x + y * y) ** 0.5)[0]

def 홈():
    팔.home()
    if hasattr(팔, 't'):
        팔.tilt_now = 0.0


if __name__ == "__main__":
    main()
