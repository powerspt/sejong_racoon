# -*- coding: utf-8 -*-
"""
주제 8 · 3층 [동작] — 손 모양으로 라쿤봇을 움직인다.

    [웹캠] → hand_tracker(인식) → gestures(의도) → 여기(동작) → 라쿤봇

손 모양과 명령 (config.py 의 GESTURE_MAP 에서 바꿀 수 있다)
    ✋ 손바닥   정지 + 조종 해제        ✊ 주먹   집기
    ✌ 브이      놓기                    ☝ 검지   조종 — 손을 움직이면 팔이 따라온다
    👍 엄지 위  홈 복귀 (1.5초 유지)    👎 엄지 아래  관측 자세 (1.5초 유지)

안전
    · 손이 3프레임 안 보이면 바로 정지한다 — 인식 실패의 기본값은 정지
    · 조종은 꺼진 채로 시작한다. 검지를 세워야 켜진다
    · 스페이스 = 즉시 정지, q = 종료 (화면에 포커스가 있어야 한다)
    · 목표 좌표는 can_move_to 와 반경 제한을 모두 통과해야 보낸다

실행
    이 파일을 열고 F5. 아래 '설정' 의 로봇없이 = True 면 로봇 없이 화면으로만 돈다 (먼저 이걸로).
    로봇을 붙일 때 False 로 바꾼다.
    (명령 프롬프트에서는 --dry-run · --port COM26 도 그대로 쓸 수 있다)
"""
import sys as _sys
for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import argparse
import math
import threading
import time
from collections import deque

import cv2

import config as cfg
import camera_test
from hand_tracker import (HandTracker, draw_hand, put_texts_ko,
                          open_hand_camera, read_hand_frame)
from gestures import GestureIntent, Command
from arm_helper import make_arm, xy_to_polar

# ════════ 설정 — 여기만 바꿔 보세요 ════════════════════
로봇없이 = True       # True = 로봇 없이 화면으로만 (먼저 이걸로) · False = 로봇을 붙여 실기
# ─────────────────────────────────────────────────────

WIN = "RaccoonBot 손동작 제어"


# ───────────────────────── 팔 워커 ─────────────────────────
class ArmWorker(threading.Thread):
    """팔 동작은 시간이 걸린다. 메인 루프에서 직접 부르면 화면이 얼어붙는다.

    그래서 별도 스레드로 돌리고, 대기열은 '한 칸' 만 둔다.
    새 명령이 오면 기다리던 명령을 버린다 — 밀린 조종 명령은 쓸모가 없고 위험하다.
    단, 정지·집게 명령은 버리지 않는다.
    """

    def __init__(self, arm, log):
        super().__init__(daemon=True)
        self.arm = arm
        self.log = log
        self.lock = threading.Lock()
        self.slot = None                 # 대기 중인 명령 (한 칸)
        self.urgent = deque()            # 버리면 안 되는 명령
        self.alive = True
        self.busy = False
        self.anchor_xy = None            # 조종 시작 때의 팔 위치
        self.target = None               # 마지막으로 보낸 좌표 (화면 표시용)

    def send(self, cmd: Command):
        with self.lock:
            if cmd.urgent:
                self.urgent.append(cmd)
                self.slot = None         # 정지가 왔으면 대기 중인 이동은 버린다
            else:
                self.slot = cmd

    def _take(self):
        with self.lock:
            if self.urgent:
                return self.urgent.popleft()
            cmd, self.slot = self.slot, None
            return cmd

    def run(self):
        while self.alive:
            cmd = self._take()
            if cmd is None:
                time.sleep(0.01)
                continue
            self.busy = True
            try:
                self._do(cmd)
            except Exception as e:
                self.log(f"[오류] {cmd.kind}: {e}")
            self.busy = False

    def _do(self, cmd: Command):
        arm = self.arm
        if cmd.kind == "STOP":
            arm.stop()
            self.anchor_xy = None
            self.log("정지")
        elif cmd.kind == "GRIP_CLOSE":
            arm.close()
            self.log("집었다")
        elif cmd.kind == "GRIP_OPEN":
            arm.open()
            self.log("놓았다")
        elif cmd.kind == "HOME":
            arm.home()
            self.anchor_xy = None
            self.log("홈 복귀")
        elif cmd.kind == "OBSERVE":
            arm.scan_pose()
            self.anchor_xy = None
            self.log("관측 자세")
        elif cmd.kind == "TRACK_ON":
            x, y, _z = arm.xyz()
            self.anchor_xy = (float(x), float(y))
            self.log(f"조종 시작 (기준 {x:.1f}, {y:.1f})")
        elif cmd.kind == "TRACK_OFF":
            self.anchor_xy = None
            self.log("조종 해제")
        elif cmd.kind == "JOG":
            self._jog(cmd)

    def _jog(self, cmd: Command):
        if self.anchor_xy is None:
            return
        ax, ay = self.anchor_xy
        tx, ty = ax + cmd.dx, ay + cmd.dy

        # (1) 한 번에 너무 멀리 가지 않게 — 현재 위치에서의 걸음 제한
        cx, cy, _cz = self.arm.xyz()
        vx, vy = tx - float(cx), ty - float(cy)
        dist = math.hypot(vx, vy)
        if dist < 0.3:                                   # 거의 제자리면 보내지 않는다
            return
        if dist > cfg.TRACK_MAX_STEP_CM:
            k = cfg.TRACK_MAX_STEP_CM / dist
            tx, ty = float(cx) + vx * k, float(cy) + vy * k

        # (2) 팔이 닿는 반경 안인지 — 바깥이면 경계까지만
        r, yaw = xy_to_polar(tx, ty)
        r = max(cfg.R_MIN_CM, min(cfg.R_MAX_CM, r))
        tx, ty = -r * math.sin(math.radians(yaw)), r * math.cos(math.radians(yaw))

        # (3) can_move_to 가 거부하면 보내지 않는다
        if not self.arm.move_xyz(tx, ty, cfg.TRACK_Z, cfg.TRACK_SPEED):
            return
        self.target = (tx, ty)

    def shutdown(self):
        self.alive = False


# ───────────────────────── 화면 ─────────────────────────
def draw_panel(frame, sig, intent, worker, log, fps, dry_run):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 60), (28, 30, 36), -1)
    cv2.rectangle(frame, (0, h - 120), (w, h), (28, 30, 36), -1)
    texts = []

    name = sig.gesture_ko if sig.found else "손 없음"
    texts.append((f"손 모양 : {name}", (14, 14), True, (255, 230, 150)))

    mode = "조종 중" if worker.anchor_xy else "대기"
    color = (120, 255, 170) if worker.anchor_xy else (180, 180, 180)
    texts.append((f"[{mode}]", (max(230, w - 380), 16), True, color))
    texts.append(("가상 로봇" if dry_run else "실기", (max(360, w - 150), 20), False,
                  (160, 200, 255) if dry_run else (120, 255, 170)))

    # 길게 누르기 진행
    if intent.hold_ratio > 0:
        cv2.rectangle(frame, (w // 2 - 80, 64), (w // 2 + 80, 80), (70, 70, 80), -1)
        cv2.rectangle(frame, (w // 2 - 80, 64),
                      (w // 2 - 80 + int(160 * intent.hold_ratio), 80), (255, 200, 90), -1)
        texts.append(("유지 중...", (w // 2 - 36, 84), False, (255, 200, 90)))

    for i, line in enumerate(list(log)[-4:]):
        texts.append((line, (14, h - 112 + i * 22), False, (235, 235, 235)))

    if worker.target:
        texts.append((f"목표 ({worker.target[0]:+.1f}, {worker.target[1]:+.1f}) cm",
                      (max(300, w - 300), h - 112), False, (190, 215, 255)))
    texts.append((f"{fps:4.1f} fps   q 종료 · 스페이스 정지 · +/- 민감도 {cfg.TRACK_GAIN_X:.0f}",
                  (max(280, w - 360), h - 28), False, (170, 170, 180)))

    put_texts_ko(frame, texts)
    return frame


# ───────────────────────── 메인 ─────────────────────────
def main():
    ap = argparse.ArgumentParser(description="손동작으로 라쿤봇 조종")
    ap.add_argument("--dry-run", action="store_true", help="로봇 없이 콘솔로만 확인")
    ap.add_argument("--port", help="COM 포트 직접 지정 (예: COM26)")
    ap.add_argument("--index", type=int, default=None, help="카메라 번호")
    args = ap.parse_args()
    args.dry_run = args.dry_run or 로봇없이

    cap = open_hand_camera(args.index)
    if cap is None:
        print("[카메라] 열 수 있는 카메라가 없습니다.")
        return 1

    print("[준비] 모델을 확인합니다...")
    tracker = HandTracker()
    intent = GestureIntent()

    print("[준비] 팔을 연결합니다..." if not args.dry_run else "[준비] 가상 로봇으로 실행합니다")
    try:
        arm = make_arm(args.dry_run, port=args.port)
    except Exception as e:
        print("[실패]", e)
        return 1

    log = deque(maxlen=8)

    def say(msg):
        log.append(msg)
        print("[팔]", msg)

    worker = ArmWorker(arm, say)
    worker.start()

    frame = read_hand_frame(cap)
    if frame is None:
        print("[카메라] 화면을 읽지 못했습니다.")
        return 1
    h, w = frame.shape[:2]
    camera_test.open_resizable_window(WIN, w, h)

    fps, t_prev = 0.0, time.time()
    print("[시작] 팔 주변 30cm 를 비우세요.  손바닥 = 정지,  q = 종료")
    try:
        while True:
            frame = read_hand_frame(cap)
            if frame is None:
                break
            sig = tracker.read(frame)
            for cmd in intent.update(sig):
                worker.send(cmd)

            draw_hand(frame, sig)
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(1e-3, now - t_prev)
            t_prev = now
            draw_panel(frame, sig, intent, worker, log, fps, args.dry_run)

            cv2.imshow(WIN, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            elif key == ord(" "):                     # 키보드 백업 — 즉시 정지
                worker.send(Command("STOP"))
                intent.reset()
            elif key in (ord("+"), ord("=")):
                intent.gain_x += 2.0
                intent.gain_y += 1.5
                say(f"민감도 {intent.gain_x:.0f}/{intent.gain_y:.0f}")
            elif key in (ord("-"), ord("_")):
                intent.gain_x = max(4.0, intent.gain_x - 2.0)
                intent.gain_y = max(3.0, intent.gain_y - 1.5)
                say(f"민감도 {intent.gain_x:.0f}/{intent.gain_y:.0f}")
            if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        worker.send(Command("STOP"))
        time.sleep(0.2)
        worker.shutdown()
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()
        arm.close_connection()
    print("[끝]")
    return 0


# ───────────────────────── 카메라·로봇 없이 확인 ─────────────────────────
def _selftest():
    """손 모양 대본을 흘려보내 가상 팔이 어떻게 움직이는지 본다."""
    from hand_tracker import HandSignal

    print("가상 로봇으로 흐름 확인 (카메라 없음)\n")
    arm = make_arm(True)
    log = deque(maxlen=20)
    worker = ArmWorker(arm, lambda m: (log.append(m), print("   [팔]", m)))
    worker.start()
    intent = GestureIntent()

    def feed(label, n, x=0.5, y=0.5):
        for _ in range(n):
            for cmd in intent.update(HandSignal(True, label, 0.9, "Right", x, y, 0.3, None)):
                worker.send(cmd)
            time.sleep(0.01)

    print("1) 주먹 10프레임 — 집기 한 번")
    feed("Closed_Fist", 10)
    time.sleep(0.5)
    print("2) 브이 10프레임 — 놓기 한 번")
    feed("Victory", 10)
    time.sleep(0.5)
    print("3) 검지를 세우고 손을 오른쪽 위로 — 조종")
    feed("Pointing_Up", 6, 0.50, 0.50)
    feed("Pointing_Up", 6, 0.62, 0.38)
    time.sleep(0.6)
    print("4) 손바닥 — 조종 해제 + 정지")
    feed("Open_Palm", 10)
    time.sleep(0.5)

    worker.shutdown()
    arm.close_connection()
    kinds = [m.split()[0] for m in log]
    ok = "집었다" in log and "놓았다" in log and any("조종 시작" in m for m in log) and "정지" in log
    print("\n결과:", "흐름 정상" if ok else "⚠️ 확인 필요")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in _sys.argv:
        raise SystemExit(_selftest())
    raise SystemExit(main())
