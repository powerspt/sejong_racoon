# -*- coding: utf-8 -*-
"""
주제 8 · 1층 [인식] — 웹캠 프레임 하나를 손 정보 하나(HandSignal)로 바꾼다.

이 파일이 하는 일은 딱 하나다.
    프레임(사진) → HandSignal(손이 보이는가 / 어떤 모양인가 / 어디 있는가)
로봇도, 게임도 여기서는 모른다. 그래서 이 파일만 갈아끼우면 인식 방법을 통째로 바꿀 수 있다.

쓰는 법
    from hand_tracker import HandTracker, draw_hand
    tracker = HandTracker()
    sig = tracker.read(frame)          # frame 은 OpenCV BGR 이미지
    if sig.found:
        print(sig.gesture, sig.score, sig.palm_x, sig.palm_y)

혼자 확인해 보기 (카메라 없이)
    python hand_tracker.py                 # 모델 받아 두기 + 빈 화면으로 동작 확인
    python hand_tracker.py --image 손.jpg  # 사진 한 장으로 확인

⚠️ mediapipe 1.0 부터 mp.solutions 가 없어졌다. 인터넷 예제 대부분이 동작하지 않는다.
   여기서는 Tasks API (mediapipe.tasks.python.vision) 만 쓴다.
"""
import sys as _sys
for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import math
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

import config as cfg

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "models")


# ───────────────────────── 손 번호 (MediaPipe 21점) ─────────────────────────
# 0 손목 | 4 엄지 끝 | 8 검지 끝 | 12 중지 끝 | 16 약지 끝 | 20 새끼 끝
WRIST, THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 0, 4, 8, 12, 16, 20
FINGER_TIPS = (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)

# 화면에 한글로 보여 줄 이름표
GESTURE_KO = {
    "Open_Palm": "손바닥",
    "Closed_Fist": "주먹",
    "Victory": "브이",
    "Pointing_Up": "검지",
    "Thumb_Up": "엄지 위",
    "Thumb_Down": "엄지 아래",
    "ILoveYou": "사랑해",
    "None": "모름",
}


@dataclass
class HandSignal:
    """한 프레임에서 읽어낸 손. 인식층이 아래층에 넘기는 유일한 값이다."""
    found: bool = False              # 손이 보이는가
    gesture: str = "None"            # "Open_Palm" | "Closed_Fist" | ... | "None"
    score: float = 0.0               # 0~1 확신도
    handedness: str = ""             # "Left" | "Right"
    palm_x: float = 0.0              # 0~1 정규화. 화면 왼쪽=0, 오른쪽=1
    palm_y: float = 0.0              # 0~1 정규화. 화면 위=0, 아래=1
    span: float = 0.0                # 손목~중지끝 거리(화면 높이 대비). 카메라와의 거리 대용
    landmarks: Optional[List[Tuple[float, float, float]]] = None   # 21점 (x, y, z) 정규화

    @property
    def gesture_ko(self) -> str:
        return GESTURE_KO.get(self.gesture, self.gesture)

    def point(self, idx: int, w: int, h: int) -> Optional[Tuple[int, int]]:
        """21점 중 idx 번 점의 화면 픽셀 좌표. 손이 없으면 None"""
        if not self.landmarks:
            return None
        x, y, _ = self.landmarks[idx]
        return int(x * w), int(y * h)

    def distance(self, a: int, b: int, aspect: float = 1.0) -> float:
        """두 점 사이 거리(정규화). aspect = 가로/세로 비를 주면 화면 비율을 보정한다."""
        if not self.landmarks:
            return 0.0
        ax, ay, _ = self.landmarks[a]
        bx, by, _ = self.landmarks[b]
        return math.hypot((ax - bx) * aspect, ay - by)


# ───────────────────────── 모델 파일 ─────────────────────────
def ensure_model(path: str = None, url: str = None, quiet: bool = False) -> str:
    """.task 모델이 없으면 내려받는다. 이미 있으면 그대로 쓴다.

    교실에서 16대가 동시에 받으면 와이파이가 죽는다.
    교사 PC 에서 한 번 받아 vision/models/ 폴더째 USB 로 복사해 두는 것이 안전하다.
    """
    path = path or os.path.join(MODEL_DIR, cfg.GESTURE_MODEL)
    url = url or cfg.GESTURE_MODEL_URL
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not quiet:
        print(f"[model] {os.path.basename(path)} 를 내려받습니다 (약 8MB, 처음 한 번만)")
    tmp = path + ".part"
    try:
        with urllib.request.urlopen(url, timeout=30) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            got = 0
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if not quiet and total:
                    print(f"\r        {got * 100 // total}%", end="")
        os.replace(tmp, path)
        if not quiet:
            print("\r        받았습니다      ")
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError(
            f"모델을 받지 못했습니다: {e}\n"
            f"  인터넷이 막혀 있으면 다른 PC 에서 아래 주소의 파일을 받아\n"
            f"  {path}\n  위치에 복사해 주세요.\n  {url}"
        ) from e
    return path


# ───────────────────────── 인식기 ─────────────────────────
class HandTracker:
    """MediaPipe Tasks 의 GestureRecognizer 를 감싼 것. 프레임 → HandSignal"""

    def __init__(self, model_path: str = None, max_hands: int = None,
                 min_score: float = None, video: bool = True, quiet: bool = False):
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python import vision as mp_vision

        self.min_score = cfg.GESTURE_MIN_SCORE if min_score is None else min_score
        self.video = video
        self._mp_vision = mp_vision
        model = ensure_model(model_path, quiet=quiet)
        options = mp_vision.GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=model),
            running_mode=(mp_vision.RunningMode.VIDEO if video else mp_vision.RunningMode.IMAGE),
            num_hands=cfg.HAND_MAX_NUM if max_hands is None else max_hands,
        )
        self.recognizer = mp_vision.GestureRecognizer.create_from_options(options)
        self._t0 = time.time()
        self._last_ms = -1

    def read(self, frame_bgr: np.ndarray, timestamp_ms: int = None) -> HandSignal:
        """OpenCV 프레임(BGR) 한 장 → HandSignal"""
        import mediapipe as mp

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        if self.video:
            if timestamp_ms is None:
                timestamp_ms = int((time.time() - self._t0) * 1000)
            # 영상 모드는 시각이 반드시 커져야 한다
            if timestamp_ms <= self._last_ms:
                timestamp_ms = self._last_ms + 1
            self._last_ms = timestamp_ms
            result = self.recognizer.recognize_for_video(image, timestamp_ms)
        else:
            result = self.recognizer.recognize(image)
        return self._to_signal(result, frame_bgr.shape[1], frame_bgr.shape[0])

    def _to_signal(self, result, w: int, h: int) -> HandSignal:
        if not result.hand_landmarks:
            return HandSignal(found=False)

        lm = [(p.x, p.y, p.z) for p in result.hand_landmarks[0]]

        gesture, score = "None", 0.0
        if result.gestures and result.gestures[0]:
            top = result.gestures[0][0]
            gesture, score = top.category_name, float(top.score)
        if score < self.min_score:          # 확신이 약하면 모른다고 한다
            gesture = "None"
        handed = ""
        if result.handedness and result.handedness[0]:
            handed = result.handedness[0][0].category_name

        # 손바닥 중심 = 손목·검지뿌리·새끼뿌리의 평균 (손가락을 접어도 잘 흔들리지 않는다)
        px = (lm[0][0] + lm[5][0] + lm[17][0]) / 3.0
        py = (lm[0][1] + lm[5][1] + lm[17][1]) / 3.0
        aspect = w / float(h) if h else 1.0
        span = math.hypot((lm[WRIST][0] - lm[MIDDLE_TIP][0]) * aspect,
                          lm[WRIST][1] - lm[MIDDLE_TIP][1])
        return HandSignal(True, gesture, score, handed, px, py, span, lm)

    def close(self):
        try:
            self.recognizer.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


# ───────────────────────── 그리기 도우미 ─────────────────────────
def _connections():
    from mediapipe.tasks.python.vision import HandLandmarksConnections
    return [(c.start, c.end) for c in HandLandmarksConnections.HAND_CONNECTIONS]


_CONN = None
TIP_COLORS = [(80, 80, 255), (80, 200, 255), (80, 255, 160), (255, 200, 80), (255, 120, 220)]


def draw_hand(frame, sig: HandSignal, numbers: bool = False, color=(90, 230, 120)):
    """21점과 뼈대를 그린다. numbers=True 면 점 번호도 같이."""
    global _CONN
    if not sig.found or not sig.landmarks:
        return frame
    h, w = frame.shape[:2]
    if _CONN is None:
        _CONN = _connections()
    pts = [(int(x * w), int(y * h)) for x, y, _ in sig.landmarks]
    for a, b in _CONN:
        cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for i, p in enumerate(pts):
        if i in FINGER_TIPS:
            cv2.circle(frame, p, 8, TIP_COLORS[FINGER_TIPS.index(i)], -1, cv2.LINE_AA)
        else:
            cv2.circle(frame, p, 4, (240, 240, 240), -1, cv2.LINE_AA)
        if numbers:
            cv2.putText(frame, str(i), (p[0] + 6, p[1] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1, cv2.LINE_AA)
    return frame


# cv2 는 한글을 못 그린다. 윈도우 기본 글꼴을 빌려 쓴다 (없으면 영문만).
try:
    from PIL import Image, ImageDraw, ImageFont
    _FONT = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 18)
    _FONT_B = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 24)
except Exception:                                    # pillow 가 없거나 글꼴이 없을 때
    Image = ImageDraw = ImageFont = None
    _FONT = _FONT_B = None


def put_texts_ko(frame, items):
    """한글 글자 여러 개를 '한 번에' 쓴다.  items = [(글자, (x, y), 큰글씨?, 색BGR), ...]

    프레임↔PIL 변환이 느려서, 한 프레임에 여러 줄을 쓸 때는 반드시 이 함수를 쓴다.
    """
    if not items:
        return frame
    if _FONT is None:                                 # pillow·글꼴이 없으면 영문만
        for text, org, big, color in items:
            cv2.putText(frame, text.encode("ascii", "ignore").decode(), org,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8 if big else 0.5, color, 2, cv2.LINE_AA)
        return frame
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    for text, org, big, color in items:
        draw.text(org, text, font=(_FONT_B if big else _FONT),
                  fill=(color[2], color[1], color[0]))
    frame[:, :] = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return frame


def put_text_ko(frame, text, org, big=False, color=(255, 255, 255)):
    """한글이 섞인 글자 한 줄. (색은 OpenCV 와 같은 BGR)"""
    return put_texts_ko(frame, [(text, org, big, color)])


def open_hand_camera(index=None):
    """사람 쪽 웹캠을 연다. 못 열면 선택 화면을 띄운다. (camera_test.py 재사용)"""
    import camera_test
    idx = cfg.HAND_CAMERA_INDEX if index is None else index
    cap = camera_test.try_open(idx) if idx is not None else None
    if cap is None:
        cap = camera_test.choose_camera(None, title="손을 비출 카메라 선택")
    if cap is None:
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.HAND_FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.HAND_FRAME_HEIGHT)
    return cap


def read_hand_frame(cap):
    """손 카메라용 읽기. 거울 보기(좌우 반전)는 여기서만 적용한다."""
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    if cfg.HAND_FLIP_HORIZONTAL:
        frame = cv2.flip(frame, 1)
    return frame


# ───────────────────────── 혼자 확인하기 ─────────────────────────
def _selftest(image_path=None):
    print("[1] 모델 확인")
    path = ensure_model()
    print("    ", path, f"{os.path.getsize(path) / 1e6:.1f}MB")

    print("[2] 인식기 생성")
    tracker = HandTracker(video=False)
    print("     준비됨")

    if image_path:
        frame = cv2.imread(image_path)
        if frame is None:
            print("    [실패] 사진을 열 수 없습니다:", image_path)
            return 1
        print(f"[3] 사진으로 인식 — {os.path.basename(image_path)} {frame.shape[1]}x{frame.shape[0]}")
    else:
        frame = np.full((480, 640, 3), 40, np.uint8)
        print("[3] 빈 화면으로 인식 (손이 없으니 found=False 가 정상)")

    t0 = time.time()
    sig = tracker.read(frame)
    dt = (time.time() - t0) * 1000
    print(f"     found={sig.found} gesture={sig.gesture}({sig.gesture_ko}) "
          f"score={sig.score:.2f} palm=({sig.palm_x:.2f},{sig.palm_y:.2f}) "
          f"span={sig.span:.3f}  {dt:.0f}ms")
    if sig.found:
        print(f"     엄지-검지 거리 = {sig.distance(THUMB_TIP, INDEX_TIP):.3f}")
    tracker.close()
    print("[4] 끝 — 오류 없이 여기까지 왔으면 인식층은 정상입니다")
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="인식층 단독 점검 (카메라 없이)")
    ap.add_argument("--image", help="손이 찍힌 사진으로 확인")
    args = ap.parse_args()
    raise SystemExit(_selftest(args.image))
