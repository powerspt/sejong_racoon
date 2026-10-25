# -*- coding: utf-8 -*-
"""
1단계: 카메라 연결 확인 + 검출기 튜닝 도구

사용법 (학생은 그냥 실행하면 된다)
  python camera_test.py            # 물음에 y = HSV 슬라이더 튜너 / 그냥 Enter = 검출 결과 미리보기

교사용 옵션 (물음 없이 바로 그 모드로)
  python camera_test.py --list     # 연결된 카메라 인덱스 목록 출력
  python camera_test.py --index 1  # 특정 인덱스로 열기
  python camera_test.py --hsv      # HSV 트랙바로 색 범위 튜닝 (color 모드)
  python camera_test.py --probe    # 카메라가 실제로 내주는 해상도 조사 (가로세로 비율 확인용)

키
  q : 종료         s : 현재 프레임을 snapshot_*.jpg 로 저장
  c : 다음 카메라로 전환 (노트북 웹캠이 보이면 팔 카메라가 나올 때까지 누름)
  m : (color 모드) 마스크 창 토글
"""

# 윈도우 한국어 터미널은 기본 코드페이지가 cp949 라서, 출력에 '—' 같은 글자가 있으면
# UnicodeEncodeError 로 죽는다. 출력 인코딩을 UTF-8 로 고정해 둔다.
import sys as _sys
for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import argparse
import sys
import time

import cv2
import numpy as np

import config as cfg
from detectors import make_detector, draw_detection, ColorDetector


def list_cameras(max_index=6):
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                found.append((i, frame.shape[1], frame.shape[0]))
        cap.release()
    return found


MAX_CAM_INDEX = 6
current_index = -1          # 지금 열려 있는 카메라 번호 (오버레이 표시용)


def try_open(index: int):
    """열리면 VideoCapture, 아니면 None"""
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, _ = cap.read()
    if not ok:
        cap.release()
        return None
    return cap


PROBE_MODES = [(320, 240), (640, 360), (640, 480), (800, 600), (1280, 720), (1280, 960), (1920, 1080)]


def probe_modes(index: int):
    """요청 해상도별로 카메라가 실제로 돌려주는 해상도를 출력"""
    print(f"카메라 {index} 해상도 조사 (요청 -> 실제)")
    seen = set()
    for w, h in PROBE_MODES:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("  열 수 없음 (다른 프로그램이 사용 중?)"); cap.release(); return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        ok, f = cap.read()
        cap.release()
        if ok and f is not None:
            got = (f.shape[1], f.shape[0])
            mark = "" if got in seen else "  <- 새 모드"
            seen.add(got)
            print(f"  {w}x{h:<5} -> {got[0]}x{got[1]}  (비율 {got[0] / got[1]:.2f}){mark}")
        else:
            print(f"  {w}x{h:<5} -> 프레임 없음")
    print("실제 모드:", sorted(seen))


def open_camera(index: int):
    global current_index
    cap = try_open(index)
    if cap is None:
        raise RuntimeError(f"카메라 {index} 를 열 수 없습니다. --list 로 인덱스를 확인하세요.")
    current_index = index
    return cap


def _snapshot(index, w=240, h=180, warm=4):
    """카메라 index 의 미리보기 한 장 (회전 적용). 못 열면 None"""
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return None
    frame = None
    for _ in range(warm):
        ok, f = cap.read()
        if ok and f is not None:
            frame = f
    cap.release()
    if frame is None:
        return None
    frame = read_frame_from(frame)
    fh, fw = frame.shape[:2]
    s = min(w / fw, h / fh)
    thumb = cv2.resize(frame, (int(fw * s), int(fh * s)))
    canvas = np.zeros((h, w, 3), np.uint8)
    y0, x0 = (h - thumb.shape[0]) // 2, (w - thumb.shape[1]) // 2
    canvas[y0:y0 + thumb.shape[0], x0:x0 + thumb.shape[1]] = thumb
    return canvas


def choose_camera(preferred: int = None, max_index: int = MAX_CAM_INDEX, title="카메라 선택"):
    """연결된 카메라를 미리보기와 함께 보여주고 클릭/숫자 키로 고르게 한다.
    preferred 가 바로 열리면 선택 화면 없이 그 카메라를 연다. 선택을 취소(Esc/창 닫기)하면 None."""
    global current_index
    if preferred is not None:
        cap = try_open(preferred)
        if cap is not None:
            current_index = preferred
            return cap
        print(f"[camera] {preferred} 번을 열 수 없어 선택 화면을 띄웁니다.")
    print("[camera] 연결된 카메라를 찾는 중...")
    thumbs = []
    for i in range(max_index + 1):
        t = _snapshot(i)
        if t is not None:
            thumbs.append((i, t))
    if not thumbs:
        print("[camera] 열 수 있는 카메라가 없습니다.")
        return None
    tw, th, pad, cols = 240, 180, 12, 3
    rows = (len(thumbs) + cols - 1) // cols
    W, H = cols * (tw + pad) + pad, 70 + rows * (th + 36 + pad) + pad
    rects = []
    chosen = [None]

    def draw():
        img = np.full((H, W, 3), (48, 50, 56), np.uint8)
        cv2.putText(img, "Select camera  (click / number key / Esc)", (pad, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 220, 120), 2)
        cv2.putText(img, "arm camera = HAMSTER_AI_UVC (usually the last one)", (pad, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        rects.clear()
        for k, (idx, t) in enumerate(thumbs):
            r, c = divmod(k, cols)
            x, y = pad + c * (tw + pad), 70 + r * (th + 36 + pad)
            img[y:y + th, x:x + tw] = t
            cv2.rectangle(img, (x, y), (x + tw, y + th + 32), (120, 124, 134), 1)
            cv2.rectangle(img, (x, y + th), (x + tw, y + th + 32), (70, 74, 84), -1)
            cv2.putText(img, f"[{idx}]  camera {idx}", (x + 8, y + th + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            rects.append((x, y, x + tw, y + th + 32, idx))
        return img

    def on_mouse(event, mx, my, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for x1, y1, x2, y2, idx in rects:
                if x1 <= mx <= x2 and y1 <= my <= y2:
                    chosen[0] = idx
    cv2.namedWindow(title)
    cv2.setMouseCallback(title, on_mouse)
    img = draw()
    while chosen[0] is None:
        cv2.imshow(title, img)
        k = cv2.waitKey(30) & 0xFF
        if k == 27 or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
            break
        if ord("0") <= k <= ord("9") and any(idx == k - ord("0") for idx, _ in thumbs):
            chosen[0] = k - ord("0")
    cv2.destroyWindow(title)
    if chosen[0] is None:
        return None
    cap = try_open(chosen[0])
    if cap is None:
        print(f"[camera] {chosen[0]} 번을 열지 못했습니다.")
        return None
    current_index = chosen[0]
    print(f"[camera] {chosen[0]} 번 선택")
    return cap


def next_camera(cap):
    """현재 카메라를 닫고 다음 번호의 열리는 카메라로 바꿉니다 (c 키). 실행 중 소스 교체용."""
    global current_index
    if cap is not None:
        cap.release()
    for k in range(1, MAX_CAM_INDEX + 2):
        idx = (current_index + k) % (MAX_CAM_INDEX + 1)
        c = try_open(idx)
        if c is not None:
            current_index = idx
            print(f"[camera] {idx} 번으로 전환")
            return c
    print("[camera] 열 수 있는 카메라가 없습니다")
    current_index = -1
    return None


def read_frame(cap):
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return read_frame_from(frame)


def read_frame_from(frame):
    """원본 프레임에 config 의 플립/회전 적용"""
    if cfg.FLIP_HORIZONTAL:
        frame = cv2.flip(frame, 1)
    if cfg.FLIP_VERTICAL:
        frame = cv2.flip(frame, 0)
    rot = getattr(cfg, "ROTATE", None)
    if rot == "cw":
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rot == "ccw":
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rot == "180":
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    return frame



def open_resizable_window(name, width, height):
    """크기 조절 가능한 창을 만들고, 화면에 다 들어가도록 초기 크기를 맞춘다 (마우스 좌표는 OpenCV 가 원본 크기로 환산)."""
    cv2.namedWindow(name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    try:
        import ctypes
        sw, sh = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
        scale = min(1.0, (sh - 140) / height, (sw - 80) / width)
    except Exception:
        scale = 1.0
    cv2.resizeWindow(name, int(width * scale), int(height * scale))


def _nothing(_):
    pass


def hsv_tuner(cap):
    """트랙바로 HSV 범위를 찾는 도구. 찾은 값을 config.COLOR_HSV_RANGES 에 적으세요."""
    win = "HSV tuner"
    cv2.namedWindow(win)
    for name, val, mx in [("H_lo", 0, 180), ("H_hi", 10, 180), ("S_lo", 120, 255),
                          ("S_hi", 255, 255), ("V_lo", 70, 255), ("V_hi", 255, 255)]:
        cv2.createTrackbar(name, win, val, mx, _nothing)
    while True:
        frame = read_frame(cap)
        if frame is None:
            continue
        lo = tuple(cv2.getTrackbarPos(n, win) for n in ("H_lo", "S_lo", "V_lo"))
        hi = tuple(cv2.getTrackbarPos(n, win) for n in ("H_hi", "S_hi", "V_hi"))
        det = ColorDetector([(lo, hi)], cfg.COLOR_MIN_AREA)
        d = det.detect(frame)
        draw_detection(frame, d)
        cv2.putText(frame, f"lo={lo} hi={hi}", (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow(win, frame)
        cv2.imshow("mask", det.last_mask)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print(f"COLOR_HSV_RANGES = [({lo}, {hi})]")
            break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--index", type=int, default=cfg.CAMERA_INDEX)
    ap.add_argument("--hsv", action="store_true")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    if args.probe:
        probe_modes(args.index)
        return

    if args.list:
        cams = list_cameras()
        print("연결된 카메라:", cams if cams else "없음")
        return

    if not args.hsv:
        # 학생은 인자 없이 실행한다 — 모드는 물어서 정한다 (y = HSV 슬라이더 튜너)
        try:
            ans = input("HSV 슬라이더 튜너를 열까요? [y = 슬라이더 / 그냥 Enter = 검출 미리보기] ").strip().lower()
        except EOFError:
            ans = ""
        if ans in ("y", "yes", "ㅛ"):
            args.hsv = True

    cap = choose_camera(args.index)
    if cap is None:
        print("카메라를 선택하지 않아 종료합니다.")
        return
    try:
        if args.hsv:
            hsv_tuner(cap)
            return
        det = make_detector(cfg)
        show_mask = False
        t0, n = time.time(), 0
        while True:
            frame = read_frame(cap)
            if frame is None:
                continue
            d = det.detect(frame)
            draw_detection(frame, d)
            n += 1
            fps = n / max(1e-6, time.time() - t0)
            cv2.putText(frame, f"cam {current_index} | {cfg.DETECTOR} {fps:.1f} fps | c:switch", (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imshow(cfg.WINDOW_NAME, frame)
            if show_mask and isinstance(det, ColorDetector) and det.last_mask is not None:
                cv2.imshow("mask", det.last_mask)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            elif k == ord("s"):
                name = f"snapshot_{int(time.time())}.jpg"
                cv2.imwrite(name, frame)
                print("저장:", name)
            elif k == ord("c"):
                cap = next_camera(cap)
                if cap is None:
                    break
            elif k == ord("m"):
                show_mask = not show_mask
                if not show_mask:
                    cv2.destroyWindow("mask")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    sys.exit(main())
