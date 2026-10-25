# -*- coding: utf-8 -*-
"""04. 좌표 제어 — 작업 지도의 칸으로 움직인다

    python examples/04_xyz_move.py A3                 # 대화형 — 칸이나 좌표를 입력하면 바로 간다
    python examples/04_xyz_move.py A3 --go E3 A1 I4   # 그 칸들을 차례로 (명령줄에서 한 번에)
    python examples/04_xyz_move.py A3 --limits        # 갈 수 있는 범위를 재 본다 (안 움직임)

로봇이 없으면 표만 보여 주고 끝난다 (칸 -> 좌표 -> 관절각 계산은 로봇 없이도 된다).

대화형에서 입력할 수 있는 것
    E3              칸 이름. 기울기와 높이가 따라 정해진다
    10 15 8         좌표 (x y z, cm). 반경에 맞는 기울기를 자동으로 고른다
    10 15 8 -90     네 번째 값으로 기울기를 직접 지정
    ?               갈 수 있는 범위 표
    ls              칸 목록
    (그냥 Enter)     끝내기

좌표 기준
  원점 (0,0,0) : 베이스 회전축이 책상면과 만나는 점
  +x / +y / +z : 오른쪽 / 로봇 정면 앞쪽 / 위
  기준점        : 닫힌 집게의 두 날이 만나는 점 (end_effector("gripper") 기본값)

수업에서 설명할 내용은 docs/teaching_notes.md 의 '주제 3' 을 보세요.
"""
import argparse
import math
import os
import sys
import time

# 윈도우 한국어 터미널은 기본 코드페이지가 cp949 라서 한글 출력이 깨지거나 죽는다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision"))
import mat_fit as mf                                        # noqa: E402
from roboid import *                                        # noqa: E402,F401,F403

CONNECT_TIMEOUT_S = 10.0
ZONE_NAME = {0: "수평 0도", -45: "기울임 -45도", -90: "수직 -90도"}


def ask(prompt):
    try:
        return input(prompt)
    except EOFError:
        return None


def 계산기(alpha=0.0):
    """로봇 없이 roboid 의 기구학 계산만 쓴다. 기울기(alpha)마다 따로 만든다."""
    from roboid.raccoon import Raccoon as _R

    class 오프라인(_R):
        def __init__(s):
            s._pos_ref_dev = _R._REF_GRIPPER
            s._pos_ref_rel = s._pos_ref_abs = (0.0, 0.0, 0.0)
            s._roboid = s
            s._enc = {1: -10.0, 2: -140.0}
            s._enc[3] = alpha - 90.0 - s._enc[1] - s._enc[2]

        def _unit(s, value=None):
            return _R._CM           # 읽기도 쓰기도 cm 로 고정 (unit("cm") 이 쓰기로 부른다)

        def read(s, device_id, arg=None):
            if device_id == _R.ENCODER:
                return s._enc.get(arg, 0.0)
            if device_id == _R.SLOT_R2:
                return 3                               # 서보 그리퍼가 달린 것으로
            return 0

        def signal_strength(s):
            return 0

        def dispose(s):
            pass

    return 오프라인()


def wait_connected(bot, timeout_s=CONNECT_TIMEOUT_S):
    """roboid 공식 판정. Raccoon() 이 돌아와도 연결이 늦게 될 수 있어 폴링한다."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if bot.is_connected():
            return True
        wait(300)
    return False


def 칸_정보(paper, cell):
    """칸 이름 -> (x, y, 반경, 기울기, 높이). 기울기와 높이는 반경에서 따라 정해진다."""
    cells = mf.all_cells(paper)
    cell = cell.strip().upper()
    if cell not in cells:
        return None
    x, y = cells[cell]
    r = math.hypot(x, y)
    alpha, hover = mf.tilt_for(r)
    return x, y, r, alpha, hover


def 표로_보기(bot, paper, cells):
    """칸 -> 좌표 -> 관절각 표. 칸마다 그 구역의 기울기로 계산한다 (로봇 불필요)."""
    계산기들 = {a: 계산기(a) for a in (0, -45, -90)}
    print(f"\n[{paper}] 칸 -> 좌표 -> 그 구역 기울기로 푼 관절 각도")
    print(f"{'칸':<5}{'x':>6}{'y':>6}{'r':>7}{'기울기':>8}{'높이':>6}"
          f"{'관절 (j1, j2, j3, j4)':>34}")
    for c in cells:
        info = 칸_정보(paper, c)
        if info is None:
            print(f"{c:<5}  ★ {paper} 매트에 없는 칸")
            continue
        x, y, r, alpha, hover = info
        계산 = 계산기들[alpha]
        각도 = 계산.xyz_to_degree(x, y, hover)
        if 각도[0] is None:
            각도표시, 비고 = "해 없음", "★"
        else:
            각도표시 = str(tuple(round(float(v), 1) for v in 각도))
            비고 = "" if 계산.can_degree_to(*각도) else "★ 관절 한계 밖"
        print(f"{c:<5}{x:>6}{y:>6}{r:>7.1f}{alpha:>8}{hover:>6}{각도표시:>34}  {비고}")


def 준비_확인(bot, paper):
    """움직이기 전 확인. 집게를 닫는다 (좌표 기준점이 닫힌 두 날이 만나는 점이라서)."""
    print(f"\n준비:  {paper} 작업 지도 (100% 인쇄)  ·  집게 끝에 실+클립(다림추)  ·  팔 주변 30cm")
    답 = ask("준비됐으면 Enter,  취소하려면 q + Enter : ")
    if 답 is None:
        print("(키보드 입력이 안 되는 창이라 그대로 진행합니다)")
    elif 답.strip().lower() in ("q", "quit", "n"):
        print("취소했습니다.")
        return False

    bot.close_gripper()
    wait(800)
    print("집게 닫음.")
    return True


def 한_점으로(bot, 이름, x, y, z, alpha):
    """한 좌표로 보내고 명령값·실제값·관절을 찍는다. 칸이든 생좌표든 여기를 거친다."""
    print(f"\n[{이름}] ({x}, {y}, {z}) cm   r={math.hypot(x, y):.1f}   {ZONE_NAME.get(alpha, f'{alpha}도')}")
    if not mf.safe_tilt(bot, alpha):
        return False
    if not bot.can_move_to(x, y, z):
        print(f"  ! 도달 불가. 기울기 {alpha}도로는 이 점에 못 간다")
        return False

    bot.move_to(x, y, z, 50)
    wait(1000)
    실제 = tuple(round(float(v), 2) for v in bot.xyz())
    관절 = tuple(round(float(v), 2) for v in bot.encoder(-1))
    기울기 = round(관절[1] + 관절[2] + 관절[3] + 90, 1)
    오차 = math.dist((x, y, z), 실제) * 10
    print(f"  명령 ({x}, {y}, {z})  ->  실제 {실제}   차이 {오차:.1f} mm")
    print(f"  관절 {관절}   실제 기울기 {기울기}도")
    return True


def 이동(bot, paper, cells):
    for c in cells:
        info = 칸_정보(paper, c)
        if info is None:
            print(f"\n[{c}] {paper} 매트에 없는 칸입니다.")
            continue
        x, y, r, alpha, hover = info
        한_점으로(bot, c, x, y, hover, alpha)


def 대화형(bot, paper):
    """칸 이름이나 좌표를 입력받아 보낸다."""
    print("\n" + "─" * 64)
    print("갈 곳을 입력하세요.")
    print(f"  칸 이름   E3            ({paper} 매트의 칸)")
    print("  좌표      10 15 8       (x y z, cm)")
    print("  기울기 지정 10 15 8 -90   (네 번째 값 = 기울기)")
    print("  ?                       갈 수 있는 범위 표")
    print("  칸목록    ls")
    print("  끝내기    그냥 Enter")
    print("─" * 64)

    while True:
        줄 = ask("\n> ")
        if 줄 is None:
            print("\n(키보드 입력이 끊겼습니다)")
            return
        줄 = 줄.strip()
        if not 줄 or 줄.lower() in ("q", "quit", "exit"):
            return
        if 줄 == "?":
            한계_재보기(bot, paper)
            continue
        if 줄.lower() in ("ls", "목록", "칸목록"):
            print("  " + "  ".join(sorted(mf.all_cells(paper))))
            continue

        조각 = 줄.replace(",", " ").split()
        if len(조각) == 1:
            info = 칸_정보(paper, 조각[0])
            if info is None:
                print(f"  {paper} 매트에 없는 칸입니다: {조각[0]}   (ls 로 목록 확인)")
                continue
            x, y, _r, alpha, hover = info
            한_점으로(bot, 조각[0].upper(), x, y, hover, alpha)
            continue

        try:
            값 = [float(v) for v in 조각]
        except ValueError:
            print("  숫자로 읽을 수 없습니다. 예: 10 15 8   또는  E3")
            continue
        if len(값) == 3:
            x, y, z = 값
            alpha, _hover = mf.tilt_for(math.hypot(x, y))   # 반경에 맞는 기울기 자동
            print(f"  반경 {math.hypot(x, y):.1f}cm -> 기울기 {alpha}도")
        elif len(값) == 4:
            x, y, z, alpha = 값
        else:
            print("  값은 3개(x y z) 또는 4개(x y z 기울기) 로 주세요.")
            continue
        한_점으로(bot, f"({x:g}, {y:g})", x, y, z, alpha)


def 한계_재보기(bot, paper):
    """기울기·높이별로 갈 수 있는 반경의 경계를 can_move_to 로 훑는다."""
    print("\n정면(x=0) 으로 갈 수 있는 반경 (cm)")
    print(f"{'기울기':<14}{'높이':>6}{'가장 가까이':>12}{'가장 멀리':>10}{'폭':>8}")
    for alpha in (0, -45, -90):
        계산 = 계산기(alpha)
        for z in (3, 6, 10, 15):
            닿는곳 = [rr / 10 for rr in range(30, 300) if 계산.can_move_to(0, rr / 10, z)]
            if not 닿는곳:
                print(f"{ZONE_NAME[alpha]:<14}{z:>6}{'갈 수 있는 곳 없음':>22}")
                continue
            print(f"{ZONE_NAME[alpha]:<14}{z:>6}{min(닿는곳):>12.1f}{max(닿는곳):>10.1f}"
                  f"{max(닿는곳) - min(닿는곳):>8.1f}")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paper_pos", nargs="?", choices=list(mf.LAYOUT), default=None,
                    help="작업 지도 (--paper 없이 그냥 A3 / B4 로 줘도 된다)")
    ap.add_argument("--paper", choices=list(mf.LAYOUT), default=None)
    ap.add_argument("--go", nargs="*", metavar="칸", default=None,
                    help="그 칸들로 실제 이동한다 (예: --go E3 A1 I4)")
    ap.add_argument("--limits", action="store_true", help="갈 수 있는 범위를 재 본다")
    ap.add_argument("--port", default=None)
    args = ap.parse_args()
    paper = args.paper or args.paper_pos or mf.choose_paper(ask, "04_xyz_move.py")
    if paper is None:
        return

    # --go 로 칸을 지정한 경우에만 로봇이 필요하다. 그 외에는 표만 보여 준다.
    움직임 = bool(args.go)

    bot = Raccoon(0, args.port) if args.port else Raccoon()
    연결됨 = wait_connected(bot)
    if not 연결됨:
        bot.dispose()
        if 움직임:
            print(f"\n{CONNECT_TIMEOUT_S:.0f}초 안에 연결되지 않았습니다. 이동하려면 로봇이 필요합니다.")
            print("  진단: examples/01_connect_test.py   포트 지정: --port COM26")
            return
        print("\n로봇이 연결되지 않아 계산만 합니다 (표와 범위는 로봇 없이도 나온다).")
        bot = 계산기()
    try:
        bot.unit("cm")
        bot.end_effector("gripper")
        print((f"연결됨 (신호 {bot.signal_strength()}dBm)" if 연결됨 else "로봇 없이 계산만")
              + f"  ·  {paper} 매트")
        print("현재 집게 끝 좌표:", tuple(round(float(v), 2) for v in bot.xyz()))
        print("Home 자세의 좌표 :", tuple(round(float(v), 2) for v in bot.degree_to_xyz(0, -10, -140, 60)))

        if args.limits:
            한계_재보기(bot, paper)
            return

        if not 연결됨:                      # 로봇 없이 왔으면 표만 보여 주고 끝
            표로_보기(bot, paper, sorted(mf.all_cells(paper)))
            print(f"\n로봇을 연결하면 바로 보낼 수 있습니다:"
                  f"  python examples/04_xyz_move.py {paper}")
            print(f"범위를 재 보려면  :  python examples/04_xyz_move.py {paper} --limits")
            return

        대상 = args.go if args.go else None
        if args.go is not None and not args.go:     # --go 를 값 없이 준 경우
            대상 = (mf.ZONE_CELLS[paper][0][:1] + mf.ZONE_CELLS[paper][-45][:1]
                    + mf.ZONE_CELLS[paper][-90][:1])
            print(f"\n--go 에 칸을 안 줘서 구역별 대표 칸으로 갑니다: {', '.join(대상)}")

        if 대상:                             # 명령줄로 받은 칸들을 차례로
            표로_보기(bot, paper, 대상)
            if 준비_확인(bot, paper):
                이동(bot, paper, 대상)
        else:                                # 대화형 — 입력받아 바로 보낸다
            표로_보기(bot, paper, sorted(mf.all_cells(paper)))
            if not 준비_확인(bot, paper):
                return
            대화형(bot, paper)

        mf.safe_tilt(bot, 0)
        bot.unlock()
        bot.init_pose()
        wait(1200)
        print("\nHome 으로 돌아왔습니다.")
    finally:
        bot.dispose()


if __name__ == "__main__":
    main()
