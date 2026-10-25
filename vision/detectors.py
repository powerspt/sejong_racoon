# -*- coding: utf-8 -*-
"""
사물 검출기 모듈
- ColorDetector : HSV 색상 범위로 가장 큰 덩어리를 찾음 (학습 불필요, 수업용으로 가장 단순)
- YoloDetector  : ultralytics YOLO 로 일반 사물 검출 (pip install ultralytics)

두 검출기 모두 detect(frame) -> Detection | None 인터페이스를 가집니다.
Detection 은 화면 좌표(픽셀)의 중심점과 상자를 담습니다.
"""
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np


@dataclass
class Detection:
    cx: float           # 중심 x (픽셀)
    cy: float           # 중심 y (픽셀)
    x1: int
    y1: int
    x2: int
    y2: int
    label: str = "object"
    conf: float = 1.0

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def bottom_y(self) -> int:
        """물체가 테이블에 닿는 지점(상자 아래 변). 거리 추정에 중심보다 안정적."""
        return self.y2


def draw_detection(frame, det: Optional[Detection], color=(0, 255, 0)):
    """검출 결과와 화면 중앙선을 그려 넣습니다."""
    h, w = frame.shape[:2]
    cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 255, 0), 1)
    cv2.line(frame, (0, h // 2), (w, h // 2), (255, 255, 0), 1)
    if det is None:
        cv2.putText(frame, "no target", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return frame
    cv2.rectangle(frame, (det.x1, det.y1), (det.x2, det.y2), color, 2)
    cv2.circle(frame, (int(det.cx), int(det.cy)), 5, (0, 0, 255), -1)
    cv2.putText(frame, f"{det.label} {det.conf:.2f}", (det.x1, max(20, det.y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    err_x = det.cx - w / 2
    cv2.putText(frame, f"err_x={err_x:+.0f}px  cy={det.cy:.0f}  bottom={det.bottom_y}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame


class ColorDetector:
    """HSV 색 범위에 들어오는 픽셀 중 가장 큰 연결 영역을 물체로 봅니다."""

    def __init__(self, hsv_ranges: Sequence[Tuple[Tuple[int, int, int], Tuple[int, int, int]]],
                 min_area: int = 400, label: str = "color"):
        self.hsv_ranges = [(np.array(lo, dtype=np.uint8), np.array(hi, dtype=np.uint8))
                           for lo, hi in hsv_ranges]
        self.min_area = min_area
        self.label = label
        self.last_mask = None

    def set_ranges(self, hsv_ranges, label=None):
        """실행 중 목표 색을 바꿉니다."""
        self.hsv_ranges = [(np.array(lo, dtype=np.uint8), np.array(hi, dtype=np.uint8))
                           for lo, hi in hsv_ranges]
        if label:
            self.label = label

    def mask(self, frame) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        m = None
        for lo, hi in self.hsv_ranges:
            part = cv2.inRange(hsv, lo, hi)
            m = part if m is None else cv2.bitwise_or(m, part)
        kernel = np.ones((5, 5), np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
        self.last_mask = m
        return m

    def detect(self, frame) -> Optional[Detection]:
        m = self.mask(frame)
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < self.min_area:
            return None
        x, y, w, h = cv2.boundingRect(c)
        M = cv2.moments(c)
        cx = M["m10"] / M["m00"] if M["m00"] else x + w / 2
        cy = M["m01"] / M["m00"] if M["m00"] else y + h / 2
        return Detection(cx, cy, x, y, x + w, y + h, self.label, 1.0)


class YoloDetector:
    """ultralytics YOLO 검출기. target_classes 에 든 클래스 중 확신도가 가장 높은 것을 고릅니다."""

    def __init__(self, model_path: str = "yolo11n.pt", conf: float = 0.4,
                 target_classes: Optional[Sequence[str]] = None):
        from ultralytics import YOLO  # 지연 임포트: color 모드에서는 필요 없음
        self.model = YOLO(model_path)
        self.conf = conf
        self.target_classes = set(target_classes) if target_classes else None
        self.names = self.model.names

    def detect(self, frame) -> Optional[Detection]:
        results = self.model.predict(frame, conf=self.conf, verbose=False)
        best = None
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.names.get(cls_id, str(cls_id)) if isinstance(self.names, dict) else self.names[cls_id]
                if self.target_classes and label not in self.target_classes:
                    continue
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                det = Detection((x1 + x2) / 2, (y1 + y2) / 2, x1, y1, x2, y2, label, conf)
                if best is None or det.conf > best.conf:
                    best = det
        return best


def make_detector(cfg):
    """config 모듈을 받아 설정된 검출기를 만듭니다."""
    if cfg.DETECTOR == "yolo":
        return YoloDetector(cfg.YOLO_MODEL, cfg.YOLO_CONF, cfg.YOLO_TARGET_CLASSES)
    return ColorDetector(cfg.COLOR_HSV_RANGES, cfg.COLOR_MIN_AREA, getattr(cfg, "COLOR_NAME", "color"))
