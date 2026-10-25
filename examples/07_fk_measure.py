# -*- coding: utf-8 -*-
"""07. 영역별 오차 측정 — 작업 지도를 모눈종이로 쓴다 (field_test.md E 단계)

    python examples/07_fk_measure.py --paper B4
    python examples/07_fk_measure.py --paper B4 --goto A1      # 한 칸씩 (키보드 없는 창)
    python examples/07_fk_measure.py --paper B4 --check        # 계산만, 팔 안 움직임

왜 매트를 쓰는가
  매트에는 칸마다 중심 십자가 이미 인쇄되어 있다. 연필로 표점을 찍고 자로 거리를 재는 것보다
  **로봇을 칸으로 보내고 십자에서 얼마나 벗어났는지만 읽는 쪽이 훨씬 빠르다.**

  ⚠️ 매트 종류가 맞아야 한다. B4 를 깔아 놓고 A3 좌표로 보내면 매트 밖으로 간다. 실제로 겪었다.
     --paper 를 안 주면 물어본다 (기본값을 두지 않는 이유가 이것이다).
     `07_fk_measure.py B4` 처럼 이름 없이 줘도 된다.

세 구역을 모두 본다
  매트는 반경에 따라 그리퍼 기울기가 달라진다 (config.TILT_RULES).
      r >= 15.5cm  수평 0도      11.0 ~ 15.5cm  기울임 -45도      r < 11.0cm  수직 -90도
  구역마다 팔 모양이 완전히 달라지므로 **오차도 구역마다 다를 수 있다.**
  그래서 구역별로 좌/중/우 세 칸씩, 모두 9칸을 잰다.

  재는 높이는 **전 구역 z = 6cm 로 통일**한다. hover 높이(10/8/6)를 그대로 쓰면 높이가 달라져
  다림추 실이 늘어지고, 그러면 추가 집게 바로 아래에 있지 않게 된다.
  전 칸이 자기 기울기로 z = 4~10cm 어디서든 닿으므로 6cm 로 통일해도 잃는 것이 없다.

무엇이 나오는가
  잰 Δ 를 두 성분으로 가른다.
    매트가 놓인 상태 (평행이동 / 회전 / 배율)  -> 08_map_calibrate.py 가 고칠 몫
    그러고도 남는 것 (잔차)                  -> **로봇 자체의 오차.** 이게 07 이 보려던 값이다
  잔차를 구역별로도 나눠 보여 주므로, "먼 곳이 더 나쁜가" "수직 구역만 나쁜가" 를 바로 알 수 있다.

준비물
  · 작업 지도 100% 인쇄 (docs/work_map_B4.pdf 또는 work_map_A3.pdf)
  · 집게 끝에 실 + 클립(다림추). 실 길이 6cm 남짓
  · 매트는 대충 깔아도 된다. 크게 어긋나 있으면 08 --align 으로 먼저 맞춘다

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

TOL_MM = 5.0                # 잔차 합격 기준 (로봇 자체 오차)
CELL_CM = 4.0               # 칸 한 변. Δ 가 이 절반을 넘으면 옆 칸을 보고 있다는 뜻이다
CONNECT_TIMEOUT_S = 10.0
HOME = (0, -10, -140, 60)   # 매뉴얼상 xyz = (0, 14.7, 8.8)
HOME_Y_CM = 14.74           # 그리퍼가 인식됐을 때의 값
HOME_Y_NO_GRIPPER = 6.74    # 인식 안 됐을 때 (오프셋 8cm 가 빠진다)
ZONE_NAME = {0: "수평 0도", -45: "기울임 -45도", -90: "수직 -90도"}


def ask(prompt):
    """키보드 입력을 받는다. 받을 수 없는 창이면 None.

    isatty() 는 믿을 수 없다 - 터미널로 보이면서 읽으면 바로 EOF 인 환경이 있다.
    그래서 실제로 읽어 보고 판단한다.
    """
    try:
        return input(prompt)
    except EOFError:
        return None


def wait_connected(bot, timeout_s=CONNECT_TIMEOUT_S):
    """연결될 때까지 기다린다.

    roboid 는 Raccoon() 이 돌아와도 아직 연결되지 않았을 수 있고,
    BLE 특성상 중간에 끊겼다 붙기도 한다. 한 번만 확인하면 오탐이 난다.
    bot.is_connected() 가 roboid 가 제공하는 공식 판정이다.
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if bot.is_connected():
            return True
        wait(300)
    return False


def check_gripper(r):
    """그리퍼가 인식됐는지 본다.

    move_to 는 속으로 그리퍼 종류를 읽어 집게 끝 8cm 오프셋을 더한다.
    인식이 안 되면 그 오프셋이 '조용히' 빠진 채 계산되고, 예외도 경고도 없다.
    그 상태로 재면 매트가 8cm 어긋난 것처럼 보인다.
    """
    y = r.degree_to_xyz(*HOME)[1]
    if abs(y - HOME_Y_CM) < 0.3:
        return True
    print("\n★ 그리퍼가 인식되지 않았습니다.")
    print(f"  Home 자세의 계산값 y = {round(y, 2)} cm  (정상 {HOME_Y_CM} / 미인식 {HOME_Y_NO_GRIPPER})")
    print("  집게 끝 8cm 오프셋이 빠진 채로 계산됩니다. 재 봐야 전부 틀립니다.")
    print("  확인: 그리퍼가 물리적으로 꽂혀 있는가 / end_effector('gripper') 를 불렀는가")
    return False


def plan(paper):
    """잴 칸 목록. [(칸이름, x, y, r, 기울기)] 를 구역 순서대로."""
    cells = mf.all_cells(paper)
    out = []
    for alpha in (0, -45, -90):
        for name in mf.ZONE_CELLS[paper][alpha]:
            x, y = cells[name]
            out.append((name, x, y, math.hypot(x, y), alpha))
    return out


def goto(r, paper, cell, quiet=False):
    """한 칸으로 가서 멈춘다."""
    cell = cell.strip().upper()
    if cell == "REST":
        r.unlock()
        r.init_pose()           # 공식 API. Home 자세로 돌아간다
        wait(1200)
        r.open_gripper()
        print("Home 자세로 돌아왔습니다. 집게를 열었습니다.")
        return None
    cells = mf.all_cells(paper)
    if cell not in cells:
        print(f"모르는 칸: {cell}   ({paper} 매트는 {', '.join(sorted(cells))}, 그리고 REST)")
        return None
    x, y = cells[cell]
    alpha = mf.zone_of(x, y)

    r.close_gripper()           # 기준점 = 닫힌 두 날이 만나는 점
    wait(800)
    if not mf.safe_tilt(r, alpha):
        return None
    if not r.can_move_to(x, y, mf.MEASURE_Z):
        print(f"[{cell}] ({x}, {y}) 는 기울기 {alpha}도, 높이 {mf.MEASURE_Z}cm 로 닿지 않습니다.")
        return None
    r.move_to(x, y, mf.MEASURE_Z, 40)
    wait(1200)

    enc = tuple(round(v, 2) for v in r.encoder(-1))
    real_alpha = round(enc[1] + enc[2] + enc[3] + 90, 1)
    print(f"\n[{cell}] ({x}, {y}) cm   r = {math.hypot(x, y):.1f}cm   "
          f"{ZONE_NAME[alpha]} 구역")
    print(f"  관절 {enc}   실제 기울기 {real_alpha}도 (목표 {alpha}도)")
    if abs(real_alpha - alpha) > 3:
        print("  ★ 기울기가 목표와 다릅니다. 이 칸의 값은 믿기 어렵습니다.")
    if not quiet:
        print(f"  다림추가 [{cell}] 칸 중심 십자에서 얼마나 벗어났는지 mm 로 재세요.")
        print("    Δx: 오른쪽이 +     Δy: 앞쪽(로봇에서 먼 쪽)이 +")
        print("  로봇은 이 자세로 멈춰 있습니다. 다음 칸은 --goto 로 다시 부르세요.")
    return (x, y, alpha)


def report(paper, rows):
    """rows = [(칸, x, y, alpha, dx, dy)] (mm 단위 Δ)"""
    print("\n" + "=" * 74)
    if len(rows) < 4:
        print(f"잰 칸이 {len(rows)}개뿐이라 매트 성분을 분리할 수 없습니다 (4칸 이상 필요).")
        for name, _x, _y, alpha, dx, dy in rows:
            print(f"  {name}  {ZONE_NAME[alpha]:<12} Δ=({dx:+.1f}, {dy:+.1f}) mm")
        return

    nominal = [(x * 10.0, y * 10.0) for _n, x, y, _a, _dx, _dy in rows]
    measured = [(x * 10.0 + dx, y * 10.0 + dy) for _n, x, y, _a, dx, dy in rows]
    s, th, tx, ty = mf.fit_similarity(nominal, measured)
    res = mf.residuals(nominal, measured, s, th, tx, ty)

    print(f"{'칸':<5}{'구역':<14}{'r(cm)':>7}{'Δx':>7}{'Δy':>7}{'|Δ|':>7}"
          f"{'잔차':>8}{'잔차 방향':>20}")
    for (name, x, y, alpha, dx, dy), (e, ex, ey) in zip(rows, res):
        rr = math.hypot(x, y)
        # 잔차가 반지름 방향인지 옆 방향인지 — 반지름 방향이면 길이/오프셋 문제
        ux, uy = (x / rr, y / rr) if rr else (0.0, 1.0)
        radial = ex * ux + ey * uy
        lateral = -ex * uy + ey * ux
        print(f"{name:<5}{ZONE_NAME[alpha]:<14}{rr:>7.1f}{dx:>7.1f}{dy:>7.1f}"
              f"{math.hypot(dx, dy):>7.1f}{e:>8.1f}"
              f"{f'반지름{radial:+.1f} 옆{lateral:+.1f}':>20}")
    print("-" * 74)

    print("\n[매트가 놓인 상태]  <- 08_map_calibrate.py 가 고칠 몫")
    print(f"  평행이동 x {tx:+.1f} mm, y {ty:+.1f} mm   회전 {th:+.2f}도   배율 {(s-1)*100:+.2f} %")

    worst = max(e for e, _ex, _ey in res)
    print(f"\n[로봇 자체 오차]  = 위 성분을 빼고 남은 잔차")
    print(f"  최대 {worst:.1f} mm   평균 {sum(e for e, _a, _b in res)/len(res):.1f} mm"
          f"   ->  {'합격' if worst <= TOL_MM else f'★ 기준({TOL_MM:.0f}mm) 초과'}")

    # 구역별로 나눠 본다 — 이게 이 측정의 핵심이다
    print(f"\n{'구역':<14}{'칸수':>5}{'평균 잔차':>11}{'최대 잔차':>11}")
    byzone = {}
    for (_n, _x, _y, alpha, _dx, _dy), (e, _ex, _ey) in zip(rows, res):
        byzone.setdefault(alpha, []).append(e)
    for alpha in (0, -45, -90):
        v = byzone.get(alpha)
        if v:
            print(f"{ZONE_NAME[alpha]:<14}{len(v):>5}{sum(v)/len(v):>11.1f}{max(v):>11.1f}")

    notes = []
    if worst > TOL_MM:
        notes.append((f"잔차 최대 {worst:.1f} mm 가 기준({TOL_MM:.0f}mm)을 넘습니다.", None))

    means = {a: sum(v) / len(v) for a, v in byzone.items()}
    if len(means) > 1 and max(means.values()) - min(means.values()) > TOL_MM / 2:
        bad = max(means, key=means.get)
        notes.append((f"구역별로 차이가 납니다. **{ZONE_NAME[bad]}** 구역이 가장 나쁩니다"
                      f" (평균 {means[bad]:.1f} mm, 가장 좋은 구역의"
                      f" {means[bad] / max(min(means.values()), 0.1):.1f}배).",
                      "그 구역에서 쓰는 손목 각도나 그리퍼 기준점이 실제와 다를 수 있습니다."))

    rad, lat = [], []
    for (_n, x, y, _a, _dx, _dy), (_e, ex, ey) in zip(rows, res):
        rr = math.hypot(x, y)
        if not rr:
            continue
        rad.append(abs(ex * x / rr + ey * y / rr))
        lat.append(abs(-ex * y / rr + ey * x / rr))
    if rad and sum(rad) > 2 * sum(lat) and max(rad) > TOL_MM:
        notes.append(("잔차가 **반지름 방향**에 몰려 있습니다.",
                      "마디 길이 또는 집게 끝 오프셋(8cm) 문제입니다."))
    elif lat and sum(lat) > 2 * sum(rad) and max(lat) > TOL_MM:
        notes.append(("잔차가 **옆 방향**에 몰려 있습니다.",
                      "1번 관절(회전) 영점 문제입니다."))

    # 배율은 인쇄 배율과 '로봇이 반지름 방향으로 일정하게 더/덜 가는 것' 을 구별하지 못한다.
    # r 이 좁은 범위(8~20cm)에 모여 있으면 두 가지가 거의 같은 모양이라 잔차로는 안 잡힌다.
    if abs(s - 1) >= 0.003:
        r_mean = sum(math.hypot(a, b) for a, b in nominal) / len(nominal)
        equiv = (s - 1) * r_mean
        notes.append((f"배율이 {(s-1)*100:+.2f}% 나왔습니다. 이것만으로는 원인을 가를 수 없습니다.",
                      f"(a) 인쇄 배율이 틀렸거나, (b) 로봇이 반지름 방향으로 평균"
                      f" {equiv:+.1f} mm 더 갑니다.\n"
                      "    매트의 10cm 자를 실제 자로 재세요. 딱 100mm 면 (b) - 로봇 쪽입니다."))

    half = CELL_CM * 10 / 2
    if max(max(abs(dx), abs(dy)) for *_r, dx, dy in rows) > half:
        notes.append((f"Δ 가 칸 절반({half:.0f}mm)을 넘는 것이 있습니다."
                      " **옆 칸을 보고 읽었을 수 있습니다.**",
                      "매트가 크게 어긋났다면 08_map_calibrate.py --align 으로 먼저 맞추세요."))

    print("\n[해석]")
    if not notes:
        print("  · 구역에 상관없이 로봇이 명령한 칸에 잘 갑니다.")
        print("  · 이제 08_map_calibrate.py 로 매트 정렬만 맞추면 됩니다.")
    for head, detail in notes:
        print(f"  · {head}")
        if detail:
            print(f"    {detail}")


def parse_deltas(text, paper):
    """--fit 인자를 푼다.  "A1:1.5,-2  D3:0,3" """
    cells = mf.all_cells(paper)
    rows = []
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
        rows.append((nm, x, y, mf.zone_of(x, y), dx, dy))
    return rows


def show_plan(paper):
    print(f"\n[{paper}] 잴 칸 — 구역마다 좌/중/우 세 칸, 측정 높이 z = {mf.MEASURE_Z}cm 통일")
    print(f"{'구역':<14}{'칸':<6}{'x':>6}{'y':>6}{'r(cm)':>8}")
    for name, x, y, rr, alpha in plan(paper):
        print(f"{ZONE_NAME[alpha]:<14}{name:<6}{x:>6}{y:>6}{rr:>8.1f}")
    print(f"\n인쇄물: docs/work_map_{paper}.pdf  (100% 배율로 인쇄했는지 10cm 자로 먼저 확인)")


def usage_noninteractive(paper):
    cells = [c[0] for c in plan(paper)]
    print("\n이 창은 키보드 입력을 받을 수 없습니다 (stdin 없음).")
    print("한 칸씩 따로 실행하는 방법으로 진행하세요.\n")
    print("  1) 집게에 실+클립(다림추)을 매답니다")
    for i, c in enumerate(cells, 1):
        print(f"  2-{i}) python examples/07_fk_measure.py --paper {paper} --goto {c}")
        print(f"        -> 멈추면 [{c}] 칸 중심 십자에서 벗어난 Δx, Δy 를 mm 로 적어 둡니다")
    print(f"  3) python examples/07_fk_measure.py --paper {paper} --rest")
    print("  4) 모은 값으로 계산 (로봇 없이 됩니다):")
    ex = " ".join(f"{c}:0,0" for c in cells)
    print(f"        python examples/07_fk_measure.py --paper {paper} --fit \"{ex}\"")
    print("\n키보드가 되는 터미널이라면 --paper 만 주고 실행하면 한 번에 끝납니다.")


def interactive(r, paper):
    if ask("집게를 닫습니다. 팔 주변 30cm 를 비우고 Enter ") is None:
        usage_noninteractive(paper)
        return
    r.close_gripper()
    wait(1000)
    ask(f"집게 끝에 실+클립(다림추)을 매달고, {paper} 작업 지도를 깐 뒤 Enter ")

    rows = []
    for name, x, y, _rr, alpha in plan(paper):
        if ask(f"\n[{name}] {ZONE_NAME[alpha]} 구역으로 이동합니다. Enter ") is None:
            break
        if not r.is_connected():
            print("  연결이 끊겼습니다. 다시 붙을 때까지 기다립니다...")
            if not wait_connected(r):
                print("  재연결 실패. 여기서 멈춥니다.")
                break
            print("  재연결됨")
        if goto(r, paper, name, quiet=True) is None:
            continue
        print(f"  추가 [{name}] 칸 중심 십자에서 얼마나 벗어났습니까?  (Δx 오른쪽 + / Δy 앞쪽 +, mm)")
        try:
            dx = float(ask("    Δx (mm): "))
            dy = float(ask("    Δy (mm): "))
        except (ValueError, TypeError):
            print("  숫자가 아니어서 건너뜁니다.")
            continue
        if max(abs(dx), abs(dy)) > CELL_CM * 10 / 2:
            print(f"  ! Δ 가 칸 절반({CELL_CM * 10 / 2:.0f}mm)을 넘습니다. 옆 칸을 보고 계신 건 아닌가요?")
        rows.append((name, x, y, alpha, dx, dy))
        print(f"    기록: Δ = ({dx:+.1f}, {dy:+.1f}) mm   거리 {math.hypot(dx, dy):.1f} mm")

    goto(r, paper, "REST")
    report(paper, rows)


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
    ap.add_argument("--goto", metavar="칸", default=None,
                    help="그 칸으로만 이동하고 멈춘다 (예: A1). REST 면 Home")
    ap.add_argument("--rest", action="store_true", help="--goto REST 와 같다")
    ap.add_argument("--fit", metavar="\"A1:dx,dy ...\"", default=None,
                    help="모은 Δ 로 판정만 한다. 로봇이 필요 없다")
    ap.add_argument("--check", action="store_true", help="잴 칸만 보고 끝낸다")
    args = ap.parse_args()
    paper = args.paper or args.paper_pos or mf.choose_paper(ask, "07_fk_measure.py")
    if paper is None:
        return
    args.paper = paper

    # 로봇이 필요 없는 모드
    if args.fit:
        report(args.paper, parse_deltas(args.fit, args.paper))
        return
    if args.check:
        show_plan(args.paper)
        return

    r = Raccoon(0, args.port) if args.port else Raccoon()
    if not wait_connected(r):
        print(f"\n{CONNECT_TIMEOUT_S:.0f}초 안에 연결되지 않았습니다.")
        print("  1. USB to BLE 동글이 꽂혀 있는가 (노트북 내장 블루투스로는 안 된다)")
        print("  2. 로봇 전원과 배터리")
        print("  3. 다른 파이썬 창이 포트를 잡고 있지 않은가")
        print("  4. 포트 직접 지정: --port COM26")
        print("  자세한 진단은 examples/01_connect_test.py")
        r.dispose()
        return

    try:
        r.unit("cm")
        r.end_effector("gripper")
        # precision_mode 는 쓰지 않는다 (결정 2026-10-06).
        # 켜면 도착 후 같은 목표를 한 번 더 보내 산포가 줄지만 이동 시간이 약 2배가 된다.
        # 수업에서 기본으로 쓰지 않을 설정이면, 검증도 그 조건에서 해야 의미가 있다.
        print(f"연결됨 (신호 {r.signal_strength()}dBm, 배터리 {r.battery_state()})"
              f"  ·  {args.paper} 매트  ·  정밀 모드 끔(수업과 같은 조건)")
        if not check_gripper(r):
            return
        cell = "REST" if args.rest else args.goto
        if cell:
            goto(r, args.paper, cell)
        else:
            show_plan(args.paper)
            interactive(r, args.paper)
    finally:
        r.dispose()


if __name__ == "__main__":
    main()
