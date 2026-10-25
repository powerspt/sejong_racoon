# -*- coding: utf-8 -*-
"""08. 작업 지도 정렬 보정 — 매트를 로봇에 맞춘다

    python examples/08_map_calibrate.py --paper B4 --align   # 1단계: 거친 정렬 (먼저)
    python examples/08_map_calibrate.py --paper B4           # 2단계: 정밀 보정
    python examples/08_map_calibrate.py --paper B4 --check    # 도달 확인만

이 스크립트가 보는 것 / 보지 않는 것
  **매트가 어디에 놓였는지**만 본다. 로봇이 맞는지는 07_fk_measure.py 가 본다.
  07 을 먼저 통과시켜야 여기서 나오는 "매트를 5mm 옮기세요" 를 믿을 수 있다.

두 단계로 나뉘는 이유
  정밀 보정은 **mm 단위**를 다룬다. 다림추가 그 칸 안에 있어야 "이 칸 십자에서 얼마나
  벗어났나" 를 읽을 수 있다.

  실제로 겪었다 - 매트를 그냥 깔고 A1 로 보냈더니 집게가 두 칸 옆에 섰다.
  그 상태에서는 무엇을 기준으로 읽어야 할지조차 알 수 없다.

    --align  거친 정렬. 로봇이 가리키는 곳에 **매트를 맞춘다.** cm 단위 어긋남을 없앤다
    (기본)   정밀 보정. 남은 mm 단위 어긋남을 평행이동/회전/배율로 분해한다

  ⚠️ 매트 종류가 맞아야 한다. B4 를 깔아 놓고 A3 좌표로 보내면 매트 밖으로 간다. 실제로 겪었다.
     --paper 를 안 주면 물어본다. `08_map_calibrate.py B4` 처럼 이름 없이 줘도 된다.

보정점을 어떻게 골랐는가 (vision/mat_fit.py CALIB_CELLS)
  1) 기울기를 하나로 고정 - 전 구간 **수평(lock_horz)**.
     그래야 그리퍼 오프셋 오차가 모든 점에 똑같이 실려 평행이동으로 흡수된다.
     (주의: TILT_RULES 의 r>=15.5 '0도 구역' 은 *집기* 좋은 조건이지 *도달* 조건이 아니다.
      수평으로는 r 이 13cm 쯤부터 닿는다. 실측: B4 A1(r14.4) 닿음 / D2(r12.0) 안 닿음)
  2) 넓게 퍼뜨린다. 좁으면 회전·배율이 안 잡힌다.
  읽기 오차 1mm 기준 분해 불확실도: A3 5점 -> 회전 0.17도 배율 0.29% / B4 6점 -> 0.19도 0.33%

읽는 법 (부호)
  Δx : 다림추가 칸 중심 십자보다 **오른쪽**이면 +
  Δy : 다림추가 칸 중심 십자보다 **앞쪽(로봇에서 먼 쪽)**이면 +
  단위는 mm
"""
import argparse
import math
import os
import sys
import time

# 출력이 파이프로 넘어가면 윈도우 기본 코드페이지(cp949)로 나가 한글이 깨진다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision"))
import mat_fit as mf                                        # noqa: E402
from roboid import *                                        # noqa: E402,F401,F403

CELL_CM = 4.0               # 칸 한 변. Δ 가 이 절반을 넘으면 옆 칸을 보고 있다는 뜻이다
CONNECT_TIMEOUT_S = 10.0
HOME = (0, -10, -140, 60)   # 매뉴얼상 xyz = (0, 14.7, 8.8)
HOME_Y_CM = 14.74           # 그리퍼가 인식됐을 때의 값
HOME_Y_NO_GRIPPER = 6.74    # 인식 안 됐을 때 (오프셋 8cm 가 빠진다)

# 합격 기준. 보정점 5~6개, 읽기 오차 1mm 일 때의 분해 한계보다 크게 잡았다.
TOL_SHIFT_MM = 1.0
TOL_ROT_DEG = 0.3
TOL_SCALE = 0.005
TOL_RESID_MM = 3.0


def ask(prompt):
    """키보드 입력을 받는다. 받을 수 없는 창이면 None.

    isatty() 는 믿을 수 없다 - 터미널로 보이면서 읽으면 바로 EOF 인 환경이 있다.
    """
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
    """그리퍼가 인식됐는지 본다.

    move_to / can_move_to 도 속으로 그리퍼 종류를 읽어 집게 끝 8cm 오프셋을 더한다.
    인식이 안 되면 그 오프셋이 '조용히' 빠진 채 계산되고, 예외도 경고도 없다.
    그 상태로 재면 매트가 8cm 어긋난 것처럼 보인다.
    """
    y = r.degree_to_xyz(*HOME)[1]
    if abs(y - HOME_Y_CM) < 0.3:
        return True
    print("\n★ 그리퍼가 인식되지 않았습니다.")
    print(f"  Home 자세의 계산값 y = {round(y, 2)} cm  (정상 {HOME_Y_CM} / 미인식 {HOME_Y_NO_GRIPPER})")
    print("  집게 끝 8cm 오프셋이 빠진 채로 계산됩니다. 보정값이 전부 틀립니다.")
    print("  확인: 그리퍼가 물리적으로 꽂혀 있는가 / end_effector('gripper') 를 불렀는가")
    return False


def calib_points(paper):
    """[(칸이름, x, y)] — 정렬 보정에 쓰는 칸"""
    cells = mf.all_cells(paper)
    return [(n, cells[n][0], cells[n][1]) for n in mf.CALIB_CELLS[paper]]


def report(names, nominal, measured):
    """모은 Δ 로 보정값을 계산하고 할 일을 문장으로 알려 준다. 로봇이 필요 없다."""
    print("\n" + "=" * 66)
    if len(nominal) < 3:
        print("점이 3개 미만이라 보정을 계산할 수 없습니다.")
        return

    s, th, tx, ty = mf.fit_similarity(nominal, measured)
    res = mf.residuals(nominal, measured, s, th, tx, ty)
    worst = max(e for e, _ex, _ey in res)

    print(f"{'칸':<6}{'Δx':>8}{'Δy':>8}{'거리':>8}{'잔차':>8}")
    for nm, (a, b), (c, d), (e, _ex, _ey) in zip(names, nominal, measured, res):
        print(f"{nm:<6}{c-a:>8.1f}{d-b:>8.1f}{math.hypot(c-a, d-b):>8.1f}{e:>8.1f}")
    print("-" * 66)

    print("\n[보정값]")
    print(f"  평행이동   x {tx:+.1f} mm,  y {ty:+.1f} mm")
    print(f"  회전       {th:+.2f}도  (+ = 반시계)")
    print(f"  배율       {s:.4f}  ({(s-1)*100:+.2f} %)")
    print(f"  잔차(최대) {worst:.1f} mm   <- 이 값은 매트를 고쳐도 남는다")

    print("\n[조치]")
    done = True
    if math.hypot(tx, ty) >= TOL_SHIFT_MM:
        done = False
        xw = "오른쪽" if tx > 0 else "왼쪽"
        yw = "앞쪽" if ty > 0 else "뒤쪽"
        print(f"  - 매트를 {xw}으로 {abs(tx):.1f} mm, {yw}으로 {abs(ty):.1f} mm 옮기세요")
    if abs(th) >= TOL_ROT_DEG:
        done = False
        print(f"  - 매트를 {'반시계' if th > 0 else '시계'} 방향으로 {abs(th):.2f}도 돌리세요")
    if abs(s - 1) >= TOL_SCALE:
        done = False
        print(f"  - 인쇄 배율이 {(s-1)*100:+.2f}% 어긋났습니다 -> 100% 로 다시 인쇄하세요")
        print("    (매트의 10cm 자를 실제 자로 재서 확인. 딱 100mm 면 인쇄는 맞는 것이고,")
        print("     그때 이 배율은 로봇이 반지름 방향으로 더/덜 가는 것입니다 -> 07 로 확인)")
    if worst >= TOL_RESID_MM:
        print(f"  - 잔차 {worst:.1f} mm 는 평행이동/회전/배율로 설명되지 않습니다.")
        print("    07_fk_measure.py 를 통과했다면 매트가 휘었거나 읽기 오차입니다.")
        print("    07 을 아직 안 했다면 그것부터 하세요 - 로봇 쪽 문제일 수 있습니다.")
    if done:
        print(f"  - 조치할 것 없음. 정렬이 충분합니다"
              f" (이동 {TOL_SHIFT_MM}mm 미만, 회전 {TOL_ROT_DEG}도 미만)")
    else:
        print("\n  옮긴 뒤 처음부터 다시 재서 확인하세요.")


def parse_deltas(text, paper):
    """--fit 인자를 푼다.  "A1:1.5,-2  I1:0,3"  ->  names, nominal, measured"""
    cells = mf.all_cells(paper)
    names, nominal, measured = [], [], []
    for chunk in text.replace(";", " ").split():
        if ":" not in chunk:
            continue
        nm, _, rest = chunk.partition(":")
        nm = nm.strip().upper()
        if nm not in cells:
            print(f"  ! {paper} 매트에 없는 칸: {nm}")
            continue
        try:
            dx, dy = (float(v) for v in rest.split(","))
        except ValueError:
            print(f"  ! {nm} 의 값을 읽지 못했습니다: {rest!r}  (형식: {nm}:1.5,-2.0)")
            continue
        x, y = cells[nm]
        names.append(nm)
        nominal.append((x * 10.0, y * 10.0))
        measured.append((x * 10.0 + dx, y * 10.0 + dy))
    return names, nominal, measured


def connect(port, paper):
    r = Raccoon(0, port) if port else Raccoon()
    if not wait_connected(r):
        print("연결되지 않았습니다. examples/01_connect_test.py 로 진단하세요.")
        r.dispose()
        return None
    r.unit("cm")
    r.end_effector("gripper")
    # precision_mode 는 쓰지 않는다 (결정 2026-10-06).
    # 켜면 도착 후 같은 목표를 한 번 더 보내 산포가 줄지만 이동 시간이 약 2배가 된다.
    # 수업에서 기본으로 쓰지 않을 설정이면, 검증도 그 조건에서 해야 의미가 있다.
    print(f"연결됨 (신호 {r.signal_strength()}dBm)  ·  {paper} 매트  ·  정밀 모드 끔")
    if not check_gripper(r):
        r.dispose()
        return None
    return r


def check_reach(r, pts):
    """재기 전에 전부 닿는지 먼저 본다. 중간에 '도달 불가' 가 튀어나오면
    보정점 수가 줄어 정밀도가 떨어지므로, 시작 전에 알아야 한다."""
    r.lock_horz()
    bad = [n for n, x, y in pts if not r.can_move_to(x, y, mf.MEASURE_Z)]
    if bad:
        print(f"\n★ 수평 자세로 닿지 않는 보정점: {', '.join(bad)}")
        print("  매트 종류(--paper)가 맞는지, 그리퍼가 장착되어 있는지 확인하세요.")
        return len(pts) - len(bad) >= 4
    print(f"보정점 {len(pts)}개 전부 수평으로 도달 가능")
    return True


def goto(r, paper, cell, quiet=False):
    """한 칸으로만 가서 멈춘다. 보정점뿐 아니라 매트의 아무 칸이나 갈 수 있다."""
    cell = cell.strip().upper()
    if cell == "REST":
        r.unlock()
        r.init_pose()           # 공식 API. Home 자세로 돌아간다
        wait(1200)
        r.open_gripper()
        print("Home 자세로 돌아왔습니다. 집게를 열었습니다.")
        return False
    cells = mf.all_cells(paper)
    if cell not in cells:
        print(f"모르는 칸: {cell}   ({paper} 매트는 {', '.join(sorted(cells))}, 그리고 REST)")
        return False
    x, y = cells[cell]
    # 기준점은 '닫힌 집게의 두 날이 만나는 점'. 매번 닫아 두어야 재는 기준이 흔들리지 않는다.
    r.close_gripper()
    wait(800)
    r.lock_horz()
    if not r.can_move_to(x, y, mf.MEASURE_Z):
        print(f"[{cell}] ({x}, {y}) cm 는 수평 자세로 닿지 않습니다 "
              f"(원점에서 {math.hypot(x, y):.1f}cm - 너무 가깝습니다).")
        return False
    r.move_to(x, y, mf.MEASURE_Z, 40)
    wait(1200)
    enc = tuple(round(v, 2) for v in r.encoder(-1))
    cx, cy, cz = (round(v, 2) for v in r.xyz())
    print(f"\n[{cell}] 도착.  명령 ({x}, {y}, {mf.MEASURE_Z}) cm   "
          f"로봇이 보고한 위치 ({cx}, {cy}, {cz}) cm")
    print(f"  관절 {enc}")
    if not quiet:
        print(f"  다림추가 [{cell}] 칸 중심 십자에서 얼마나 벗어났는지 mm 로 재세요.")
        print("    Δx: 오른쪽이 +     Δy: 앞쪽(로봇에서 먼 쪽)이 +")
        print("  로봇은 이 자세로 멈춰 있습니다. 다음 칸은 --goto 로 다시 부르세요.")
    return True


def align(r, paper, step=None):
    """거친 정렬 - 매트를 로봇에 맞춘다 (반대가 아니다)."""
    c1, c2 = mf.ALIGN_CELLS[paper]
    if step in (None, 1):
        if not goto(r, paper, c1, quiet=True):
            return
        print("\n[거친 정렬 1/2 - 위치]")
        print(f"  테이프를 떼고 **매트를 움직여서**, [{c1}] 칸의 중심 십자가")
        print("  다림추 바로 아래에 오게 하세요. 매트를 돌리지는 마세요.")
        if step == 1:
            print(f"\n  다 맞추면:  python examples/08_map_calibrate.py --paper {paper} --align 2")
            return
        if ask("  맞추고 나서 Enter ") is None:
            print("\n  키보드가 안 되는 창입니다. 다 맞춘 뒤 이렇게 이어서 하세요:")
            print(f"    python examples/08_map_calibrate.py --paper {paper} --align 2")
            return
    if step in (None, 2):
        if not goto(r, paper, c2, quiet=True):
            return
        arm = math.hypot(*mf.all_cells(paper)[c2]) * 10.0
        print("\n[거친 정렬 2/2 - 회전]")
        print(f"  이번에는 **매트를 [{c1}] 점을 축으로 돌려서**, [{c2}] 칸의 중심 십자가")
        print("  다림추 바로 아래에 오게 하세요. 밀지 말고 돌리기만 하세요.")
        print(f"\n  이 거리에서 1mm 어긋나면 각도로는 {math.degrees(math.atan2(1.0, arm)):.2f}도 입니다.")
        print("  눈으로 맞출 수 있는 한계가 이 정도이고, 나머지는 정밀 보정이 잡습니다.")
        print("\n  다 맞추면 테이프로 고정하고, 정밀 보정으로 넘어가세요:")
        print(f"    python examples/08_map_calibrate.py --paper {paper}")
        print("  (돌리다 위치가 틀어졌다 싶으면 --align 1 부터 다시)")


def usage_noninteractive(paper, pts):
    cells = [n for n, _x, _y in pts]
    print("\n이 창은 키보드 입력을 받을 수 없습니다 (stdin 없음).")
    print("한 칸씩 따로 실행하는 방법으로 진행하세요.\n")
    print("  1) 집게에 실+클립(다림추)을 매답니다")
    for i, c in enumerate(cells, 1):
        print(f"  2-{i}) python examples/08_map_calibrate.py --paper {paper} --goto {c}")
        print(f"        -> 멈추면 [{c}] 칸 중심 십자에서 벗어난 Δx, Δy 를 mm 로 적어 둡니다")
    print(f"  3) python examples/08_map_calibrate.py --paper {paper} --rest")
    print("  4) 모은 값으로 계산 (로봇 없이 됩니다):")
    ex = " ".join(f"{c}:0,0" for c in cells)
    print(f"        python examples/08_map_calibrate.py --paper {paper} --fit \"{ex}\"")
    print("\n키보드가 되는 터미널이라면 --paper 만 주고 실행하면 한 번에 끝납니다.")


def interactive(r, paper, pts):
    # 로봇을 움직이기 전에 키보드가 되는지 먼저 본다.
    if ask("집게를 닫습니다. 팔 주변을 비우고 Enter ") is None:
        usage_noninteractive(paper, pts)
        return
    r.close_gripper()
    wait(1000)
    ask("집게 끝에 실+클립(다림추)을 매달고 Enter ")
    if not check_reach(r, pts):
        print("  남는 점이 너무 적어 중단합니다.")
        return

    nominal, measured, names = [], [], []
    half = CELL_CM * 10 / 2
    for name, x, y in pts:
        if ask(f"\n[{name}] ({x}, {y}) cm 로 이동합니다. 팔 주변을 비우고 Enter ") is None:
            break
        if not goto(r, paper, name, quiet=True):
            continue
        print(f"  추가 [{name}] 칸 중심 십자에서 얼마나 벗어났습니까?"
              "  (Δx 오른쪽 + / Δy 앞쪽 +, mm)")
        try:
            dx = float(ask("    Δx (mm): "))
            dy = float(ask("    Δy (mm): "))
        except (ValueError, TypeError):
            print("  숫자가 아니어서 건너뜁니다.")
            continue
        if max(abs(dx), abs(dy)) > half:
            print(f"  ! Δ 가 칸 절반({half:.0f}mm)을 넘습니다. 옆 칸을 보고 계신 건 아닌가요?")
            print(f"    크게 어긋났다면 --align 으로 먼저 맞추는 편이 빠릅니다.")
        nominal.append((x * 10.0, y * 10.0))
        measured.append((x * 10.0 + dx, y * 10.0 + dy))
        names.append(name)
        print(f"    기록: Δ = ({dx:+.1f}, {dy:+.1f}) mm   거리 {math.hypot(dx, dy):.1f} mm")

    goto(r, paper, "REST")
    report(names, nominal, measured)


def main():
    ap = argparse.ArgumentParser()
    # 기본값을 두지 않는다. B4 를 깔아 놓고 A3 좌표로 보내면 매트 밖으로 간다.
    # required=True 로 두면 인자 없이 돌릴 때 argparse 가 SystemExit(2) 를 내서
    # IDE 디버거가 예외로 잡는다. 대신 아래에서 직접 물어본다.
    ap.add_argument("paper_pos", nargs="?", choices=list(mf.LAYOUT), default=None,
                    help="작업 지도 (--paper 없이 그냥 A3 / B4 로 줘도 된다)")
    ap.add_argument("--paper", choices=list(mf.LAYOUT), default=None,
                    help="깔아 놓은 작업 지도 (A3 또는 B4)")
    ap.add_argument("--port", default=None)
    ap.add_argument("--align", nargs="?", type=int, const=0, choices=[0, 1, 2], default=None,
                    help="거친 정렬. 1 = 위치만, 2 = 회전만, 생략하면 둘 다")
    ap.add_argument("--goto", metavar="칸", default=None,
                    help="그 칸으로만 이동하고 멈춘다 (예: A1). REST 면 Home")
    ap.add_argument("--rest", action="store_true", help="--goto REST 와 같다")
    ap.add_argument("--fit", metavar="\"A1:dx,dy ...\"", default=None,
                    help="모은 Δ 로 보정값만 계산한다. 로봇이 필요 없다")
    ap.add_argument("--check", action="store_true", help="도달 가능성만 확인하고 끝낸다")
    args = ap.parse_args()
    paper = args.paper or args.paper_pos or mf.choose_paper(ask, "08_map_calibrate.py")
    if paper is None:
        return
    args.paper = paper
    pts = calib_points(args.paper)

    # 계산만 하는 모드는 로봇을 켜지 않는다
    if args.fit:
        report(*parse_deltas(args.fit, args.paper))
        return

    r = connect(args.port, args.paper)
    if r is None:
        return
    try:
        if args.check:
            check_reach(r, pts)
        elif args.align is not None:
            align(r, args.paper, args.align or None)
        elif args.rest or args.goto:
            goto(r, args.paper, "REST" if args.rest else args.goto)
        else:
            interactive(r, args.paper, pts)
    finally:
        r.dispose()


if __name__ == "__main__":
    main()
