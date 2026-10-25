# -*- coding: utf-8 -*-
"""09. 칸 집기 시험 — 작업 지도의 칸 이름으로 집고 든다 (field_test.md G·I-4 단계)

    python examples/09_grasp_test.py --paper A3 --cell E3
    python examples/09_grasp_test.py --paper A3 --zones      # 구역마다 한 칸씩
    python examples/09_grasp_test.py --paper A3 --cell E3 --step approach   # 한 걸음씩
    python examples/09_grasp_test.py --paper A3 --check      # 계산만, 팔 안 움직임

왜 좌표가 아니라 칸 이름인가
  (0, 16) 이라고 쓰면 그 자리가 어느 구역인지, 기울기를 얼마로 둬야 하는지,
  hover 를 몇 cm 로 잡아야 하는지를 사람이 매번 따로 챙겨야 한다. 빠뜨리기 쉽다.
  칸 이름을 주면 **반경에서 구역이 정해지고, 기울기와 hover 가 따라 정해진다**
  (config.TILT_RULES). 매트에 인쇄된 이름 그대로라 눈으로 대조하기도 쉽다.

  ⚠️ --paper 를 안 주면 물어본다. `09_grasp_test.py A3` 처럼 이름 없이 줘도 된다.

한 칸에서 하는 일 (걸음 이름)
  approach  그리퍼 열고, 그 칸 구역의 기울기를 잡고, hover 높이로 이동
  grasp     GRASP_Z 까지 내려가 집는다
  lift      hover 로 들어올린다  <- 여기서 미끄러지면 속도나 대기 시간 문제
  place     다시 내려놓고 집게를 연다
  rest      hover 로 올라와 Home

기울기를 바꿀 때
  집게 끝은 손목에서 8cm 떨어져 있다. 낮은 곳에서 손목만 돌리면 끝이 원을 그리며
  내려와 바닥을 긁는다 (0도 -> -90도 면 7.4cm 하강).
  그래서 **팔을 세운 뒤에** 돌린다. 세운 자세에서는 -90도라도 끝이 8.9cm 높이에 있다.
"""
import argparse
import math
import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision"))
import config as cfg                                        # noqa: E402
import mat_fit as mf                                        # noqa: E402
from roboid import *                                        # noqa: E402,F401,F403

CONNECT_TIMEOUT_S = 10.0
HOME = (0, -10, -140, 60)
HOME_Y_CM = 14.74
HOME_Y_NO_GRIPPER = 6.74
ZONE_NAME = {0: "수평 0도", -45: "기울임 -45도", -90: "수직 -90도"}
STEPS = ["approach", "grasp", "lift", "move", "place", "rest"]


def ask(prompt):
    """키보드 입력을 받는다. 받을 수 없는 창이면 None."""
    try:
        return input(prompt)
    except EOFError:
        return None


def wait_connected(bot, timeout_s=CONNECT_TIMEOUT_S):
    """roboid 공식 판정. Raccoon() 이 돌아와도 연결이 늦게 될 수 있어 폴링한다."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if bot.is_connected():
            return True
        wait(300)
    return False


def check_gripper(r):
    """그리퍼가 인식됐는지 본다. 인식이 안 되면 8cm 오프셋이 조용히 빠진다."""
    y = r.degree_to_xyz(*HOME)[1]
    if abs(y - HOME_Y_CM) < 0.3:
        return True
    print("\n★ 그리퍼가 인식되지 않았습니다.")
    print(f"  Home 자세의 계산값 y = {round(y, 2)} cm  (정상 {HOME_Y_CM} / 미인식 {HOME_Y_NO_GRIPPER})")
    print("  집게 끝 8cm 오프셋이 빠진 채로 계산됩니다. 엉뚱한 곳으로 갑니다.")
    return False


# 옮기기에서 기울기를 하나로 고정할 때 쓴다 (None 이면 칸마다 반경으로 정함)
고정_기울기 = None


def cell_spec(paper, cell):
    """칸 이름 -> (x, y, r, 기울기, hover). 구역은 반경에서 자동으로 정해진다."""
    cells = mf.all_cells(paper)
    cell = cell.strip().upper()
    if cell not in cells:
        return None
    x, y = cells[cell]
    r_cm = math.hypot(x, y)
    alpha, hover = mf.tilt_for(r_cm)
    if 고정_기울기 is not None:
        alpha = 고정_기울기
        hover = {0: 10.0, -45: 8.0, -90: 6.0}.get(alpha, hover)
    return x, y, r_cm, alpha, hover


def run_step(r, paper, cell, step, pause=True, to=None):
    """한 걸음만 실행한다. to 를 주면 그 칸으로 옮겨 놓는다."""
    spec = cell_spec(paper, cell)
    if spec is None:
        print(f"모르는 칸: {cell}   ({paper} 매트는 {', '.join(sorted(mf.all_cells(paper)))})")
        return False
    x, y, r_cm, alpha, hover = spec

    if step == "approach":
        print(f"\n[{cell}] ({x}, {y}) cm   r = {r_cm:.1f}cm   {ZONE_NAME[alpha]} 구역"
              f"   hover {hover}cm   집는 높이 {cfg.GRASP_Z}cm")
        r.open_gripper()
        wait(700)
        if not mf.safe_tilt(r, alpha):
            return False
        if not r.can_move_to(x, y, hover):
            print(f"  ! hover {hover}cm 로 닿지 않습니다.")
            return False
        r.move_to(x, y, hover, cfg.APPROACH_SPEED)
        wait(600)
        enc = tuple(round(v, 2) for v in r.encoder(-1))
        print(f"  관절 {enc}   실제 기울기 {round(enc[1]+enc[2]+enc[3]+90, 1)}도 (목표 {alpha}도)")
        print(f"  집게가 [{cell}] 칸 점선 사각형 바로 위에 열린 채로 있습니까?")

    elif step == "grasp":
        if not r.can_move_to(x, y, cfg.GRASP_Z):
            print(f"  ! 집는 높이 {cfg.GRASP_Z}cm 로 닿지 않습니다.")
            return False
        r.move_to(x, y, cfg.GRASP_Z, 30)
        wait(500)
        print(f"  집는 높이({cfg.GRASP_Z}cm)까지 내려왔습니다."
              " 집게가 블록을 감쌀 위치입니까?")

    elif step == "lift":
        r.close_gripper()
        wait(cfg.GRIPPER_SETTLE_MS)
        r.move_to(x, y, hover, cfg.LIFT_SPEED)
        wait(800)
        print(f"  {hover}cm 로 들어올렸습니다. 블록이 딸려 올라왔습니까?")
        print("  미끄러졌다면: 집게 대기 시간을 늘리거나 LIFT_SPEED 를 낮춥니다")

    elif step == "move":
        if to is None or to == cell:
            return True                     # 옮길 곳이 없으면 건너뛴다
        tx, ty, t_r, t_alpha, t_hover = cell_spec(paper, to)
        print(f"\n  [{cell}] -> [{to}] ({tx}, {ty}) cm   r = {t_r:.1f}cm   "
              f"{ZONE_NAME[t_alpha]} 구역   hover {t_hover}cm")
        if t_alpha != alpha:
            print(f"  기울기 {alpha}도 -> {t_alpha}도 (블록을 쥔 채로 바꾼다)")
        if not mf.safe_tilt(r, t_alpha):
            return False
        if not r.can_move_to(tx, ty, t_hover):
            print(f"  ! hover {t_hover}cm 로 닿지 않습니다.")
            return False
        r.move_to(tx, ty, t_hover, cfg.APPROACH_SPEED)
        wait(800)
        enc = tuple(round(v, 2) for v in r.encoder(-1))
        print(f"  관절 {enc}   실제 기울기 {round(enc[1]+enc[2]+enc[3]+90, 1)}도 (목표 {t_alpha}도)")
        print("  옮기는 동안 블록을 놓치지 않았습니까?")

    elif step == "place":
        px, py, _pr, _pa, _ph = cell_spec(paper, to) if to else (x, y, 0, alpha, hover)
        r.move_to(px, py, cfg.GRASP_Z, 30)
        wait(500)
        r.open_gripper()
        wait(700)
        print(f"  [{to or cell}] 칸에 내려놓았습니다. 점선 사각형 안에 들어갔습니까?")

    elif step == "rest":
        rx, ry, _r2, _a2, rh = cell_spec(paper, to) if to else (x, y, 0, alpha, hover)
        r.move_to(rx, ry, rh, cfg.LIFT_SPEED)
        wait(600)
        r.unlock()
        r.init_pose()
        wait(1200)
        print("  Home 자세로 돌아왔습니다.")

    if pause and step != "rest":
        ask("  확인 후 Enter ")
    return True


def 집는높이_찾기(r, paper, cell, 시작=4.0, 간격=0.5):
    """집게를 열고 0.5cm 씩 내려가며 '블록을 감싸는 높이' 를 눈으로 찾는다.

    기준점은 닫힌 두 날이 만나는 점이다. 3cm 블록에 z=3 이면 날 끝이 블록 윗면 높이라
    감싸지 못한다. 실제로 얼마나 내려가야 하는지는 집게 모양에 달렸으므로 재 본다.
    """
    spec = cell_spec(paper, cell)
    if spec is None:
        print(f"모르는 칸: {cell}")
        return None
    x, y, r_cm, alpha, hover = spec

    print(f"\n[{cell}] ({x}, {y}) cm   {ZONE_NAME[alpha]} 구역")
    print(f"집게를 연 채로 {시작}cm 부터 {간격}cm 씩 내려갑니다.")
    print("  Enter = 더 내려간다   y = 여기서 집어 본다   q = 중단")

    r.open_gripper()
    wait(700)
    if not set_tilt_or_fail(r, alpha):
        return None

    z = 시작
    while z >= 0.0:
        if not r.can_move_to(x, y, z):
            print(f"  z={z:.1f} 도달 불가. 여기까지입니다.")
            break
        r.move_to(x, y, z, 30)
        wait(500)
        실제 = round(float(r.xyz()[2]), 2)
        답 = ask(f"  z = {z:>4.1f} cm  (로봇 보고 {실제})  > ")
        if 답 is None:
            print("\n  키보드 입력이 안 되는 창입니다.")
            print(f"  값을 정했으면:  --cell {cell} --grasp-z <값>  으로 시험하세요.")
            return None
        답 = 답.strip().lower()
        if 답 == "q":
            return None
        if 답 == "y":
            break
        z -= 간격

    if z < 0:
        print("  바닥까지 내려왔습니다. 블록 높이나 집게 상태를 확인하세요.")
        return None

    print(f"\n  z = {z:.1f} cm 에서 집어 봅니다.")
    r.close_gripper()
    wait(cfg.GRIPPER_SETTLE_MS)
    r.move_to(x, y, hover, cfg.LIFT_SPEED)
    wait(900)
    답 = ask("  들어올렸습니다. 블록이 딸려 왔습니까? (y / n) > ")
    r.move_to(x, y, cfg.GRASP_Z if cfg.GRASP_Z <= hover else z, 30)
    wait(400)
    r.open_gripper()
    wait(600)

    if 답 is not None and 답.strip().lower().startswith("n"):
        print("  놓쳤습니다. 더 내려가거나 집게 대기 시간을 늘려 다시 해 보세요.")
        return None
    print(f"\n  ■ 집는 높이 = {z:.1f} cm")
    print(f"    vision/config.py 의 GRASP_Z 를 {z:.1f} 로 바꾸세요 (지금 {cfg.GRASP_Z}).")
    print(f"    다른 구역에서도 같은 값이 되는지 확인하세요:")
    for a in (0, -45, -90):
        if a != alpha:
            print(f"      python examples/09_grasp_test.py {paper} "
                  f"--cell {mf.ZONE_CELLS[paper][a][1]} --find-z")
    return z


def set_tilt_or_fail(r, alpha):
    return mf.safe_tilt(r, alpha)


def 옮기기_준비(paper, 집, 놓):
    """집은 채로 손목을 돌리지 않아도 되는지 먼저 본다.

    실측: 집게가 수평->수직으로 90도 돌면 물체가 옆으로 누워 굴러 떨어진다.
    두 칸을 모두 닿는 기울기가 하나라도 있으면 그걸로 고정해 회전을 없앤다.
    """
    global 고정_기울기
    고정_기울기 = None
    if not 놓 or 놓 == 집:
        return True

    공통 = mf.common_tilt(paper, [집, 놓], [cfg.GRASP_Z])
    if 공통 is not None:
        고정_기울기 = 공통
        print(f"\n[{집}] -> [{놓}]  기울기 {공통}도 하나로 전 구간을 갑니다 (손목 회전 없음).")
        return True

    각각 = {c: cell_spec(paper, c)[3] for c in (집, 놓)}
    print(f"\n★ [{집}]({각각[집]}도 구역) 과 [{놓}]({각각[놓]}도 구역) 을 **동시에 닿는 기울기가 없습니다.**")
    print("  옮기려면 블록을 쥔 채 손목을 돌려야 하는데, 그러면 블록이 눕거나 굴러 떨어집니다.")
    답 = ask("  그래도 해 보시겠습니까? (y = 진행 / 그 외 = 중단) > ")
    return 답 is not None and 답.strip().lower() == "y"


def run_cell(r, paper, cell, pause=True, to=None):
    if not 옮기기_준비(paper, cell, to):
        return False
    for step in STEPS:
        if not run_step(r, paper, cell, step, pause, to):
            print(f"  [{cell}] 여기서 멈춥니다.")
            run_step(r, paper, cell, "rest", False, to)
            return False
    return True


def zone_cells(paper):
    """구역마다 한 칸씩 — 기울기가 다른 곳을 반드시 섞어서 본다."""
    return [mf.ZONE_CELLS[paper][a][1] for a in (0, -45, -90)]


def show_plan(paper, cells):
    print(f"\n[{paper}] 칸별 설정 — 반경에서 구역·기울기·hover 가 자동으로 정해진다")
    print(f"{'칸':<5}{'x':>6}{'y':>6}{'r(cm)':>8}   {'구역':<14}{'기울기':>7}{'hover':>7}{'집는높이':>9}")
    for c in cells:
        spec = cell_spec(paper, c)
        if spec is None:
            print(f"{c:<5}  ★ {paper} 매트에 없는 칸")
            continue
        x, y, r_cm, alpha, hover = spec
        print(f"{c:<5}{x:>6}{y:>6}{r_cm:>8.1f}   {ZONE_NAME[alpha]:<14}"
              f"{alpha:>7}{hover:>7}{cfg.GRASP_Z:>9}")
    print(f"\nconfig.TILT_RULES = {cfg.TILT_RULES}   GRASP_Z = {cfg.GRASP_Z}cm")


def usage_noninteractive(paper, cells):
    print("\n이 창은 키보드 입력을 받을 수 없습니다 (stdin 없음).")
    print("한 걸음씩 따로 실행하세요.\n")
    c = cells[0]
    for step in STEPS:
        print(f"  python examples/09_grasp_test.py --paper {paper} --cell {c} --step {step}")
    print("\n키보드가 되는 터미널이라면 --step 없이 실행하면 한 번에 끝납니다.")


def main():
    ap = argparse.ArgumentParser()
    # required=True 로 두면 인자 없이 돌릴 때 argparse 가 SystemExit(2) 를 내서
    # IDE 디버거가 예외로 잡는다. 대신 아래에서 직접 물어본다.
    ap.add_argument("paper_pos", nargs="?", choices=list(mf.LAYOUT), default=None,
                    help="작업 지도 (--paper 없이 그냥 A3 / B4 로 줘도 된다)")
    ap.add_argument("--paper", choices=list(mf.LAYOUT), default=None,
                    help="깔아 놓은 작업 지도 (A3 또는 B4)")
    ap.add_argument("--cell", default=None, help="칸 이름 (예: E3)")
    ap.add_argument("--zones", action="store_true", help="구역마다 한 칸씩 차례로")
    ap.add_argument("--find-z", action="store_true",
                    help="집게를 열고 내려가며 집는 높이를 찾는다")
    ap.add_argument("--grasp-z", type=float, default=None,
                    help="이번 실행에만 집는 높이를 바꿔서 시험한다 (cm)")
    ap.add_argument("--to", metavar="칸", default=None,
                    help="집은 블록을 이 칸으로 옮겨 놓는다 (예: --cell E1 --to E4)")
    ap.add_argument("--step", choices=STEPS, default=None, help="이 걸음만 실행하고 끝")
    ap.add_argument("--port", default=None)
    ap.add_argument("--check", action="store_true", help="설정만 보고 끝낸다")
    args = ap.parse_args()
    paper = args.paper or args.paper_pos or mf.choose_paper(ask, "09_grasp_test.py")
    if paper is None:
        return
    args.paper = paper

    cells = zone_cells(args.paper) if args.zones else ([args.cell] if args.cell else None)
    if not cells:
        print("--cell 또는 --zones 중 하나를 주세요.")
        show_plan(args.paper, zone_cells(args.paper))
        return
    if args.check:
        if args.grasp_z is not None:
            print(f"\n집는 높이를 {args.grasp_z}cm 로 시험합니다"
                  f" (config.GRASP_Z = {cfg.GRASP_Z}).")
            cfg.GRASP_Z = args.grasp_z
        show_plan(args.paper, cells)
        return

    r = Raccoon(0, args.port) if args.port else Raccoon()
    if not wait_connected(r):
        print(f"\n{CONNECT_TIMEOUT_S:.0f}초 안에 연결되지 않았습니다.")
        print("  진단: examples/01_connect_test.py   포트 지정: --port COM26")
        r.dispose()
        return
    try:
        r.unit("cm")
        r.end_effector("gripper")
        # precision_mode 는 쓰지 않는다 (결정 2026-10-06).
        # 켜면 도착 후 같은 목표를 한 번 더 보내 산포가 줄지만 이동 시간이 약 2배가 된다.
        # 수업에서 기본으로 쓰지 않을 설정이면, 검증도 그 조건에서 해야 의미가 있다.
        print(f"연결됨 (신호 {r.signal_strength()}dBm, 배터리 {r.battery_state()})"
              f"  ·  {args.paper} 매트  ·  정밀 모드 끔")
        if not check_gripper(r):
            return
        show_plan(args.paper, cells)

        if args.find_z:
            for c in cells:
                집는높이_찾기(r, args.paper, c)
            return
        if args.step:
            run_step(r, args.paper, cells[0], args.step, pause=False, to=args.to)
            return
        if ask("\n블록을 각 칸의 점선 사각형에 맞춰 놓고 Enter ") is None:
            usage_noninteractive(args.paper, cells)
            return
        for c in cells:
            run_cell(r, args.paper, c, to=args.to)
    finally:
        r.dispose()


if __name__ == "__main__":
    main()
