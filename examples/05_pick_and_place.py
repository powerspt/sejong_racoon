# -*- coding: utf-8 -*-
"""05. 카메라 보면서 로봇 조종하기 + Pick & Place

카메라 화면 오른쪽에 버튼 패널과 사용법이 표시됩니다.
버튼을 마우스로 클릭하거나 괄호 안의 키를 눌러 그리퍼를 조금씩 움직이고,
물체 위치에서 [집기 위치 저장], 놓을 자리에서 [놓기 위치 저장] 을 누른 뒤 [실행] 하면
집기 -> 들기 -> 옮기기 -> 놓기 -> Home 을 자동으로 수행합니다.

    python 05_pick_and_place.py                # 카메라 0번
    python 05_pick_and_place.py --camera 1     # 다른 카메라
    python 05_pick_and_place.py --no-camera    # 카메라 없이 패널만

로봇 명령은 별도 스레드에서 실행되므로 이동 중에도 카메라 화면은 계속 갱신됩니다.
"""
import argparse
import os
import queue
import threading
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from roboid import *

# ───────────── 설정 ─────────────
HOME = (0, -10, -140, 60)
CAM_W, CAM_H = 640, 480     # 화면에 표시할 카메라 영역 크기 (원본은 비율 유지해 맞춤)
ROTATE = None               # 카메라 회전: "cw" / "ccw" / "180" / None (그리퍼 위 장착 기준 None)
PANEL_W = 380
STATUS_H = 170
HOVER_UP = 7.0          # 집기/놓기 위치 위로 이 만큼 올라가서 접근 (cm)
LIFT_UP = 7.0           # 집은 뒤 들어올리는 높이 (cm). 멀리(24cm 이상) 있는 물체는 높이 들면 못 닿으므로 낮게
TILTS = [(0, "수평"), (-45, "45°"), (-90, "수직")]   # 그리퍼 기울기 (관절 2+3+4 합 = alpha-90)
# 수평 그리퍼는 앞 14~27cm 만 내려갈 수 있고, 45° 는 10~24cm, 수직은 4~19cm 까지 닿습니다 (z=3cm 기준).
# 가까운 물체를 못 집으면 V 로 기울기를 바꾸세요.
JOG_SPEED = 40
MOVE_SPEED = 60
# 기울기를 바꿀 때 거쳐 가는 '세운' 자세. J2 + J3 = -90 이라 J4 = 기울기 가 되어 계산이 깔끔하다
J2_SAFE, J3_SAFE = -30.0, -60.0
TIP_MIN_Z = 4.0         # 손목을 돌리는 동안 집게 끝이 이보다 낮아지면 먼저 팔을 세운다 (블록 3cm + 여유)
STEPS = [0.5, 1.0, 2.0, 5.0]
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

try:
    FONT = ImageFont.truetype(FONT_PATH, 16)
    FONT_S = ImageFont.truetype(FONT_PATH, 13)
    FONT_B = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 17)
except OSError:
    FONT = FONT_S = FONT_B = ImageFont.load_default()


# ───────────── 상태 ─────────────
class State:
    step_idx = 1
    tilt_idx = 0
    gripper_closed = False
    pick = None             # (x, y, z)
    place = None
    busy = False
    msg = "준비 완료. 버튼 또는 키로 조종하세요."
    quit = False
    xyz = (0.0, 0.0, 0.0)
    joints = (0.0, 0.0, 0.0, 0.0)
    cam_index = -1
    cam_switch = False

    @classmethod
    def step(cls):
        return STEPS[cls.step_idx]

    @classmethod
    def tilt(cls):
        return TILTS[cls.tilt_idx]


actions = queue.Queue()


# ───────────── 로봇 작업 (워커 스레드) ─────────────
def robot_worker(bot):
    while not State.quit:
        try:
            act = actions.get(timeout=0.05)
        except queue.Empty:
            continue
        State.busy = True
        try:
            run_action(bot, act)
        except Exception as e:                       # 로봇 예외로 프로그램이 죽지 않도록
            State.msg = f"오류: {e}"
        State.busy = False


def safe_move(bot, x, y, z, speed=MOVE_SPEED):
    if not bot.can_move_to(x, y, z):
        State.msg = f"도달 불가: ({x:.1f}, {y:.1f}, {z:.1f})"
        return False
    bot.move_to(x, y, z, speed)
    return True


def apply_tilt(bot, alpha):
    """그리퍼 기울기 적용: 0 수평(lock_horz), -90 수직(lock_vert), 그 외 관절 4 직접 설정

    ⚠️ 낮은 곳에서 손목만 돌리면 집게가 바닥을 긁는다.
       집게 끝은 손목에서 8cm 떨어져 있어서, 손목을 제자리에 두고 기울기만 바꾸면
       끝이 원을 그리며 내려온다. 0° -> -90° 면 7.4cm 내려간다.
       Home(끝 높이 8.8cm)에서 수직으로 바꾸면 끝이 1.4cm 까지 내려와 책상을 긁는다.

       roboid 는 이걸 막아 주지 않는다. can_degree_to 는 '관절 범위 안인가' 만 보지
       '안전한가' 를 보지 않고, 책상이라는 개념 자체가 없다 (can_move_to(0,20,0) 도 True).
       그래서 **돌리면 끝이 어디로 갈지 degree_to_xyz 로 미리 물어보고**,
       너무 낮으면 팔을 세운 뒤에 돌린다. 값 자체는 roboid 가 정확히 알려 준다.
    """
    j1, j2, j3, j4 = (float(v) for v in bot.encoder(-1))
    cur = j2 + j3 + j4 + 90
    if abs(cur - alpha) < 1.0:              # 이미 그 기울기면 할 일 없다
        return True

    # 지금 자리에서 손목만 돌리면 집게 끝이 z 얼마로 가는가
    z_after = bot.degree_to_xyz(j1, j2, j3, alpha - 90 - j2 - j3)[2]
    if z_after < TIP_MIN_Z:
        if not (bot.can_degree_to(j1, J2_SAFE, J3_SAFE, cur)
                and bot.can_degree_to(j1, J2_SAFE, J3_SAFE, alpha)):
            State.msg = f"기울기 {alpha}° 로 안전하게 바꿀 자세가 없습니다 (끝 {z_after:.1f}cm)"
            return False
        State.msg = f"팔을 세웁니다 (그대로 돌리면 집게 끝 {z_after:.1f}cm — 바닥에 닿음)"
        bot.unlock()
        # J2+J3 = -90 이므로 J4 = 지금 기울기. 기울기는 유지한 채 올리기만 한다
        bot.degree_to(j1, J2_SAFE, J3_SAFE, cur, MOVE_SPEED)
        _, j2, j3, _ = (float(v) for v in bot.encoder(-1))   # 세운 뒤 값으로 다시 계산

    if alpha == 0:
        bot.lock_horz(); return True
    if alpha == -90:
        bot.lock_vert(); return True
    bot.unlock()
    j4 = alpha - 90 - j2 - j3
    if not bot.can_degree_to(4, j4):
        State.msg = f"기울기 {alpha}° 불가 (관절4 {j4:.0f}° 범위 밖)"
        return False
    bot.degree_to(4, j4, MOVE_SPEED)
    return True


def run_action(bot, act):
    s = State.step()
    if act == "home":
        State.msg = "Home 으로 이동"
        bot.unlock(); bot.degree_to(*HOME, MOVE_SPEED); State.tilt_idx = 0; bot.lock_horz()
    elif act in ("x+", "x-", "y+", "y-", "z+", "z-"):
        d = {"x+": (s, 0, 0), "x-": (-s, 0, 0), "y+": (0, s, 0),
             "y-": (0, -s, 0), "z+": (0, 0, s), "z-": (0, 0, -s)}[act]
        if bot.can_move_by(*d):
            bot.move_by(*d, JOG_SPEED)
            State.msg = f"이동 {act} {s}cm"
        else:
            State.msg = f"이동 불가 ({act}, 작업 영역 밖)"
    elif act in ("j1+", "j1-"):
        deg = 5 if act == "j1+" else -5
        if bot.can_degree_by(1, deg):
            bot.degree_by(1, deg, JOG_SPEED)
            State.msg = f"관절1 {deg:+d}°"
        else:
            State.msg = "관절1 한계"
    elif act == "grip":
        if State.gripper_closed:
            bot.open_gripper(); State.gripper_closed = False; State.msg = "그리퍼 열림"
        else:
            bot.close_gripper(); State.gripper_closed = True; State.msg = "그리퍼 닫힘"
    elif act == "set_pick":
        State.pick = tuple(round(v, 1) for v in bot.xyz())
        bot.sound("BEEP"); State.msg = f"집기 위치 저장 {State.pick}"
    elif act == "set_place":
        State.place = tuple(round(v, 1) for v in bot.xyz())
        bot.sound("BEEP"); State.msg = f"놓기 위치 저장 {State.place}"
    elif act == "goto_pick" and State.pick:
        x, y, z = State.pick; State.msg = "집기 위치로 이동"
        safe_move(bot, x, y, z + HOVER_UP) and safe_move(bot, x, y, z, 30)
    elif act == "goto_place" and State.place:
        x, y, z = State.place; State.msg = "놓기 위치로 이동"
        safe_move(bot, x, y, z + HOVER_UP) and safe_move(bot, x, y, z, 30)
    elif act == "run":
        if not (State.pick and State.place):
            State.msg = "집기/놓기 위치를 먼저 저장하세요"; return
        px, py, pz = State.pick
        qx, qy, qz = State.place
        State.msg = "Pick & Place 실행 중..."
        apply_tilt(bot, State.tilt()[0])
        bot.open_gripper(); State.gripper_closed = False
        if not safe_move(bot, px, py, pz + HOVER_UP): return
        if not safe_move(bot, px, py, pz, 30): return
        bot.close_gripper(); State.gripper_closed = True
        if not safe_move(bot, px, py, pz + LIFT_UP): return
        if not safe_move(bot, qx, qy, qz + LIFT_UP): return
        if not safe_move(bot, qx, qy, qz, 30): return
        bot.open_gripper(); State.gripper_closed = False
        safe_move(bot, qx, qy, qz + HOVER_UP)
        bot.unlock(); bot.degree_to(*HOME, MOVE_SPEED); State.tilt_idx = 0; bot.lock_horz()
        bot.sound("GOOD JOB"); State.msg = "Pick & Place 완료"
    elif act == "step":
        State.step_idx = (State.step_idx + 1) % len(STEPS)
        State.msg = f"이동 단위 {State.step()}cm"
    elif act == "tilt":
        State.tilt_idx = (State.tilt_idx + 1) % len(TILTS)
        alpha, name = State.tilt()
        if apply_tilt(bot, alpha):
            State.msg = f"그리퍼 기울기: {name}"
    elif act == "stop":
        bot.stop(); State.msg = "정지"


# ───────────── UI ─────────────
# (라벨, 키표시, 액션, 열, 행, 폭)  열 0~1, 폭 1=반, 2=전체
BUTTONS = [
    ("↑ 앞으로  Y+", "W", "y+", 0, 0, 2),
    ("← 왼쪽 X-", "A", "x-", 0, 1, 1), ("오른쪽 X+ →", "D", "x+", 1, 1, 1),
    ("↓ 뒤로  Y-", "S", "y-", 0, 2, 2),
    ("올리기 Z+", "R", "z+", 0, 3, 1), ("내리기 Z-", "F", "z-", 1, 3, 1),
    ("회전 ← J1+", "[", "j1+", 0, 4, 1), ("회전 → J1-", "]", "j1-", 1, 4, 1),
    ("이동 단위 변경", "T", "step", 0, 5, 1), ("그리퍼 개폐", "G", "grip", 1, 5, 1),
    ("그리퍼 기울기 전환", "V", "tilt", 0, 11, 2),
    ("집기 위치 저장", "P", "set_pick", 0, 6, 1), ("놓기 위치 저장", "L", "set_place", 1, 6, 1),
    ("집기 위치로", "K", "goto_pick", 0, 7, 1), ("놓기 위치로", "O", "goto_place", 1, 7, 1),
    ("▶ Pick & Place 실행", "Enter", "run", 0, 8, 2),
    ("Home", "H", "home", 0, 9, 1), ("정지", "Space", "stop", 1, 9, 1),
    ("카메라 전환", "C", "cam", 0, 10, 1), ("종료", "Q / Esc", "quit", 1, 10, 1),
]
KEYMAP = {ord("w"): "y+", ord("a"): "x-", ord("d"): "x+", ord("s"): "y-",
          ord("r"): "z+", ord("f"): "z-", ord("["): "j1+", ord("]"): "j1-",
          ord("t"): "step", ord("g"): "grip", ord("p"): "set_pick", ord("l"): "set_place",
          ord("k"): "goto_pick", ord("o"): "goto_place", 13: "run", ord(" "): "stop",
          ord("h"): "home", ord("c"): "cam", ord("v"): "tilt", ord("q"): "quit", 27: "quit"}
HELP = [
    "사용법",
    "1. W/A/S/D 앞뒤좌우, R/F 위아래로 그리퍼 이동.",
    "2. 물체를 잡을 위치에 그리퍼를 두고 [집기 위치 저장].",
    "3. 놓을 자리로 옮긴 뒤 [놓기 위치 저장].",
    "4. [실행] 을 누르면 집기→들기→옮기기→놓기→Home.",
    "· T 로 이동 단위(0.5/1/2/5cm) 변경, G 로 그리퍼 테스트.",
    "· 이동 중(빨간 BUSY)에는 새 명령이 무시됩니다.",
    "· 좌표는 그리퍼 끝 기준, +y 정면 / +x 오른쪽 / +z 위.",
    "· 엉뚱한 카메라가 보이면 C 로 다음 카메라로 전환.",
    "· 못 가면 V 로 기울기 변경: 수평 14~27 / 45° 10~24 / 수직 4~19cm",
]

BTN_X0, BTN_Y0, BTN_H, BTN_GAP = 12, 10, 32, 5
BTN_W1 = (PANEL_W - BTN_X0 * 2 - BTN_GAP) // 2
_rects = []     # (x1, y1, x2, y2, action)


def draw_panel(canvas_w, canvas_h):
    global _rects
    panel = Image.new("RGB", (PANEL_W, canvas_h), (40, 42, 48))
    d = ImageDraw.Draw(panel)
    _rects = []
    for label, key, act, col, row, span in BUTTONS:
        x1 = BTN_X0 + col * (BTN_W1 + BTN_GAP)
        w = BTN_W1 if span == 1 else BTN_W1 * 2 + BTN_GAP
        y1 = BTN_Y0 + row * (BTN_H + BTN_GAP)
        x2, y2 = x1 + w, y1 + BTN_H
        if act == "run":
            fill = (60, 130, 80)
        elif act == "quit":
            fill = (120, 60, 60)
        elif act == "grip":
            fill = (150, 110, 40) if State.gripper_closed else (70, 90, 130)
        else:
            fill = (70, 74, 84)
        if State.busy and act not in ("quit", "stop"):
            fill = tuple(int(c * 0.5) for c in fill)
        d.rounded_rectangle((x1, y1, x2, y2), radius=6, fill=fill, outline=(110, 114, 124))
        d.text((x1 + 8, y1 + 6), label, font=FONT, fill=(240, 240, 240))
        kw = d.textlength(f"[{key}]", font=FONT_S)
        d.text((x2 - kw - 8, y1 + 9), f"[{key}]", font=FONT_S, fill=(200, 200, 120))
        _rects.append((x1, y1, x2, y2, act))
    y = BTN_Y0 + len(set(b[4] for b in BUTTONS)) * (BTN_H + BTN_GAP) + 6
    for i, line in enumerate(HELP):
        d.text((BTN_X0, y + i * 18), line, font=FONT_B if i == 0 else FONT_S,
               fill=(255, 220, 120) if i == 0 else (210, 210, 210))
    return np.array(panel)[:, :, ::-1]


def draw_status(width):
    img = Image.new("RGB", (width, STATUS_H), (28, 30, 34))
    d = ImageDraw.Draw(img)
    x, y, z = State.xyz
    j = State.joints
    d.text((10, 8), f"그리퍼 끝  x={x:6.1f}  y={y:6.1f}  z={z:6.1f} cm", font=FONT_B, fill=(120, 220, 255))
    d.text((10, 32), f"관절  1={j[0]:6.1f}  2={j[1]:6.1f}  3={j[2]:6.1f}  4={j[3]:6.1f} °", font=FONT, fill=(200, 200, 200))
    cam = f"카메라 {State.cam_index}" if State.cam_index >= 0 else "카메라 없음"
    d.text((10, 54), f"이동 단위 {State.step()} cm    그리퍼 {'닫힘' if State.gripper_closed else '열림'}    기울기 {State.tilt()[1]}    {cam}", font=FONT, fill=(200, 200, 200))
    d.text((10, 76), f"집기 위치 {State.pick or '-'}     놓기 위치 {State.place or '-'}", font=FONT, fill=(255, 200, 120))
    d.text((10, 100), State.msg, font=FONT, fill=(255, 255, 255))
    if State.busy:
        d.rounded_rectangle((width - 90, 8, width - 10, 34), radius=6, fill=(180, 50, 50))
        d.text((width - 74, 12), "BUSY", font=FONT_B, fill=(255, 255, 255))
    return np.array(img)[:, :, ::-1]


def on_mouse(event, mx, my, flags, param):
    if event != cv2.EVENT_LBUTTONDOWN or mx < CAM_W:
        return
    px = mx - CAM_W
    for x1, y1, x2, y2, act in _rects:
        if x1 <= px <= x2 and y1 <= my <= y2:
            submit(act)
            return


def submit(act):
    if act == "quit":
        State.quit = True
    elif act == "cam":
        State.cam_switch = True
    elif act == "stop":
        actions.put(act)
    elif State.busy:
        State.msg = "이동 중입니다. 잠시 기다리세요."
    else:
        actions.put(act)


# ───────────── 카메라 ─────────────
MAX_CAM_INDEX = 6


def fit_frame(frame):
    """회전 적용 후 CAM_W x CAM_H 안에 비율을 유지해 넣고 남는 부분은 검게 채운다."""
    if ROTATE == "cw":
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif ROTATE == "ccw":
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif ROTATE == "180":
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    h, w = frame.shape[:2]
    scale = min(CAM_W / w, CAM_H / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (nw, nh))
    canvas = np.zeros((CAM_H, CAM_W, 3), np.uint8)
    x0, y0 = (CAM_W - nw) // 2, (CAM_H - nh) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = resized
    return canvas


def open_camera(index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, _ = cap.read()
    if not ok:
        cap.release()
        return None
    return cap


def next_camera(cap, current):
    """현재 다음 번호부터 순환하며 열리는 카메라를 찾는다."""
    if cap is not None:
        cap.release()
    for k in range(1, MAX_CAM_INDEX + 1):
        idx = (current + k) % (MAX_CAM_INDEX + 1)
        c = open_camera(idx)
        if c is not None:
            State.cam_index = idx
            State.msg = f"카메라 {idx} 번으로 전환"
            return c
    State.cam_index = -1
    State.msg = "열 수 있는 카메라가 없습니다"
    return None


# ───────────── 메인 ─────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=2, help="카메라 번호 (팔 카메라 HAMSTER_AI_UVC, 현재 2)")
    ap.add_argument("--no-camera", action="store_true")
    args = ap.parse_args()

    cap = None
    if not args.no_camera:
        cap = open_camera(args.camera)
        if cap is None:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision"))
            try:
                from camera_test import choose_camera
                import camera_test as _ct
                cap = choose_camera(None)
                if cap is not None:
                    State.cam_index = _ct.current_index
            except Exception as e:
                print("카메라 선택 화면 실패:", e)
            if cap is None:
                print(f"카메라 {args.camera} 를 열 수 없어 패널만 표시합니다. C 키로 다른 카메라를 찾을 수 있습니다.")
        else:
            State.cam_index = args.camera

    bot = Raccoon()
    bot.lock_horz()
    worker = threading.Thread(target=robot_worker, args=(bot,), daemon=True)
    worker.start()

    win = "RaccoonBot 조종 (카메라)"
    canvas_h = CAM_H + STATUS_H
    cv2.namedWindow(win, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    try:
        import ctypes
        _sw, _sh = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
        _sc = min(1.0, (_sh - 140) / canvas_h, (_sw - 80) / (CAM_W + PANEL_W))
    except Exception:
        _sc = 1.0
    cv2.resizeWindow(win, int((CAM_W + PANEL_W) * _sc), int(canvas_h * _sc))
    cv2.setMouseCallback(win, on_mouse)

    try:
        while not State.quit:
            if State.cam_switch:
                State.cam_switch = False
                cap = next_camera(cap, State.cam_index)
            if cap is not None:
                ok, frame = cap.read()
                if not ok or frame is None:
                    frame = np.zeros((CAM_H, CAM_W, 3), np.uint8)
                else:
                    frame = fit_frame(frame)
            else:
                frame = np.zeros((CAM_H, CAM_W, 3), np.uint8)
                cv2.putText(frame, "NO CAMERA", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (80, 80, 80), 2)
            cv2.line(frame, (CAM_W // 2, 0), (CAM_W // 2, CAM_H), (255, 255, 0), 1)
            cv2.line(frame, (0, CAM_H // 2), (CAM_W, CAM_H // 2), (255, 255, 0), 1)

            State.xyz = bot.xyz()
            State.joints = bot.encoder(-1)

            left = np.vstack([frame, draw_status(CAM_W)])
            canvas = np.hstack([left, draw_panel(CAM_W + PANEL_W, canvas_h)])
            cv2.imshow(win, canvas)

            k = cv2.waitKey(30) & 0xFF
            if k in KEYMAP:
                submit(KEYMAP[k])
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                State.quit = True
    finally:
        State.quit = True
        print("종료: 정지 후 Home 으로 이동합니다.")
        try:
            bot.stop()
            worker.join(timeout=5)
            bot.unlock()
            bot.degree_to(*HOME, MOVE_SPEED)
        except Exception:
            pass
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        bot.dispose()


if __name__ == "__main__":
    main()
