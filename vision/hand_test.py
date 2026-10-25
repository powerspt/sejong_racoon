# -*- coding: utf-8 -*-
"""
주제 8 · 15차시 실습 1 — 손에 점 21개가 붙는다. 로봇은 쓰지 않는다.

무엇을 보는가
    · 손가락마다 점이 몇 번인지 (n 키로 번호 켜기)   0 손목 · 4 엄지 · 8 검지 · 12 중지 · 16 약지 · 20 새끼
    · 손 모양 이름과 확신도 — 모양을 바꾸면 숫자가 어떻게 흔들리는지
    · 손 크기(span) — 손을 앞뒤로 움직이면 커지고 작아진다
    · 아래 '명령' 칸 — 주먹을 1초 쥐고 있어도 집기는 한 번만 나간다 (gestures.py 의 규칙)

실행
    python hand_test.py                  # 카메라로
    python hand_test.py --index 1        # 다른 카메라로
    python hand_test.py --image 손.jpg   # 카메라 없이 사진 한 장으로 (결과를 png 로 저장)

키
    q 종료   n 점 번호   g 명령 칸 켜기/끄기   s 사진 저장   c 다음 카메라
"""
import sys as _sys
for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import argparse
import os
import time
from collections import deque

import cv2
import numpy as np

import config as cfg
import camera_test
from hand_tracker import (HandTracker, draw_hand, put_texts_ko, open_hand_camera,
                          read_hand_frame, GESTURE_KO, THUMB_TIP, INDEX_TIP)
from gestures import GestureIntent

WIN = "RaccoonBot 손 인식 확인"


def draw_panel(frame, sig, intent, log, fps, show_log=True):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 92), (28, 30, 36), -1)
    texts = []

    name = sig.gesture_ko if sig.found else "손 없음"
    texts.append((f"손 모양 : {name}", (14, 10), True, (255, 230, 150)))

    # 확신도 — 모양이 애매하면 숫자가 떨어진다
    cv2.rectangle(frame, (14, 50), (14 + 220, 66), (70, 70, 80), -1)
    if sig.found:
        cv2.rectangle(frame, (14, 50), (14 + int(220 * sig.score), 66), (120, 220, 120), -1)
    texts.append((f"확신 {sig.score:.2f}  (기준 {cfg.GESTURE_MIN_SCORE:.2f} 아래는 '모름')",
                  (244, 46), False, (210, 210, 210)))

    # 확정까지의 진행 — STABLE_FRAMES
    bx = max(300, w - 250)
    bw = max(80, w - bx - 30)
    cv2.rectangle(frame, (bx, 18), (bx + bw, 34), (70, 70, 80), -1)
    cv2.rectangle(frame, (bx, 18), (bx + int(bw * intent.stable_ratio), 34), (90, 180, 255), -1)
    texts.append((f"확정 {intent.pending_count}/{intent.stable}", (max(240, bx - 95), 16), False, (190, 215, 255)))

    if sig.found:
        texts.append((f"손 크기 span {sig.span:.3f}    엄지-검지 {sig.distance(THUMB_TIP, INDEX_TIP):.3f}",
                      (14, 68), False, (200, 200, 200)))

    if show_log:
        cv2.rectangle(frame, (0, h - 112), (300, h), (28, 30, 36), -1)
        texts.append(("발행된 명령", (14, h - 108), False, (255, 210, 120)))
        for i, line in enumerate(list(log)[-4:]):
            texts.append((line, (14, h - 84 + i * 22), False, (235, 235, 235)))

    texts.append((f"{fps:4.1f} fps   q 종료 · n 번호 · g 명령",
                  (max(310, w - 280), h - 28), False, (170, 170, 180)))
    put_texts_ko(frame, texts)
    return frame


def run_image(path):
    """카메라 없이 사진 한 장으로 확인하고 결과를 저장한다."""
    frame = cv2.imread(path)
    if frame is None:
        print("[실패] 사진을 열 수 없습니다:", path)
        return 1
    if frame.shape[1] < 640:                   # 작은 사진은 글자가 겹치지 않게 키운다
        k = 640 / frame.shape[1]
        frame = cv2.resize(frame, (640, int(frame.shape[0] * k)))
    tracker = HandTracker(video=False)
    intent = GestureIntent()
    sig = tracker.read(frame)
    log = deque(maxlen=8)
    for _ in range(intent.stable + intent.hold):   # 같은 사진을 계속 넣어 확정·길게누르기까지 본다
        for c in intent.update(sig):
            if c.kind != "JOG":
                log.append(f"{c.ko}  {c}")
    draw_hand(frame, sig, numbers=True)
    draw_panel(frame, sig, intent, log, 0.0)
    out = os.path.splitext(os.path.basename(path))[0] + "_hand.png"
    cv2.imwrite(out, frame)
    print(f"손={sig.found} 모양={sig.gesture}({sig.gesture_ko}) 확신={sig.score:.2f} "
          f"span={sig.span:.3f}")
    print("명령:", ", ".join(log) or "(없음)")
    print("저장:", os.path.abspath(out))
    tracker.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description="손 인식 확인 (로봇 없음)")
    ap.add_argument("--index", type=int, default=None, help="카메라 번호")
    ap.add_argument("--image", help="카메라 대신 사진 한 장으로 확인")
    args = ap.parse_args()

    if args.image:
        return run_image(args.image)

    cap = open_hand_camera(args.index)
    if cap is None:
        print("[카메라] 열 수 있는 카메라가 없습니다. --index 로 번호를 지정해 보세요.")
        return 1

    print("[준비] 모델을 확인합니다 (처음 한 번만 내려받습니다)")
    tracker = HandTracker()
    intent = GestureIntent()
    log = deque(maxlen=8)

    frame = read_hand_frame(cap)
    if frame is None:
        print("[카메라] 화면을 읽지 못했습니다.")
        return 1
    h, w = frame.shape[:2]
    camera_test.open_resizable_window(WIN, w, h)

    numbers, show_log = False, True
    fps, t_prev = 0.0, time.time()
    print("[시작] 손을 카메라에 보여 주세요.  q 로 종료합니다.")

    while True:
        frame = read_hand_frame(cap)
        if frame is None:
            break
        sig = tracker.read(frame)
        for c in intent.update(sig):
            if c.kind != "JOG":                    # JOG 는 매 프레임 나오므로 로그에 쌓지 않는다
                log.append(f"{c.ko}  {c}")
                print("[명령]", c.ko, c)

        draw_hand(frame, sig, numbers=numbers)
        now = time.time()
        fps = 0.9 * fps + 0.1 / max(1e-3, now - t_prev)
        t_prev = now
        draw_panel(frame, sig, intent, log, fps, show_log)

        cv2.imshow(WIN, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        elif key == ord("n"):
            numbers = not numbers
        elif key == ord("g"):
            show_log = not show_log
        elif key == ord("s"):
            name = f"hand_{int(time.time())}.jpg"
            cv2.imwrite(name, frame)
            print("[저장]", os.path.abspath(name))
        elif key == ord("c"):
            cap = camera_test.next_camera(cap)
            if cap is None:
                break
        if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    tracker.close()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
