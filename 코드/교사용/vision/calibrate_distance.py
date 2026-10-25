# -*- coding: utf-8 -*-
"""
2단계: 화면 y좌표 -> 실제 거리(cm) 보정

카메라가 팔에 고정돼 있고 관측 자세(SCAN_POSE)가 항상 같으므로,
"물체 상자의 아래 변이 화면에서 얼마나 아래에 있는가"는 "베이스 축에서 물체까지의 반경 r" 과 1:1 로 대응합니다.
이 도구는 그 대응표를 만들어 distance_calib.json 에 저장합니다.

준비물: 자(줄자), 목표 물체
절차
  1. 로봇을 켜고  python calibrate_distance.py  실행 (로봇이 관측 자세로 이동)
     로봇 없이 카메라만 시험하려면 --dry-run
  2. 물체를 로봇 정면(관절 1 = 0°) 선 위, 베이스 회전축 중심에서 r cm 떨어진 곳에 놓습니다.
  3. 화면에서 물체가 검출되면  r  키를 누르고 콘솔에 거리를 cm 로 입력합니다.
  4. 거리를 바꿔가며 (예: 9, 12, 15, 18, 21 cm) 최소 3~5 점을 기록합니다.
  5. q 로 종료하면 파일이 저장됩니다.

키
  r : 현재 검출 위치 기록      d : 마지막 기록 삭제      q : 저장하고 종료
  c : 다음 카메라로 전환
"""

# 윈도우 한국어 터미널은 기본 코드페이지가 cp949 라서, 출력에 '—' 같은 글자가 있으면
# UnicodeEncodeError 로 죽는다. 출력 인코딩을 UTF-8 로 고정해 둔다.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import argparse
import json
import os
import statistics

import cv2

import config as cfg
from camera_test import open_camera, choose_camera, read_frame, next_camera
from detectors import make_detector, draw_detection
from arm_helper import make_arm


def collect_bottom_y(cap, det, n=8):
    ys = []
    while len(ys) < n:
        frame = read_frame(cap)
        if frame is None:
            continue
        d = det.detect(frame)
        if d is not None:
            ys.append(d.bottom_y)
    return statistics.median(ys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="로봇 없이 카메라만")
    ap.add_argument("--port", default=None)
    ap.add_argument("--out", default=cfg.DIST_CALIB_FILE)
    args = ap.parse_args()

    arm = make_arm(args.dry_run, args.port)
    arm.scan_pose(keep_yaw=False)

    cap = choose_camera(cfg.CAMERA_INDEX)
    if cap is None:
        print("카메라를 선택하지 않아 종료합니다."); arm.close_connection(); return
    det = make_detector(cfg)
    samples = []
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            samples = json.load(f).get("samples", [])
        print(f"기존 보정점 {len(samples)}개를 불러왔습니다.")

    print(__doc__)
    try:
        while True:
            frame = read_frame(cap)
            if frame is None:
                continue
            d = det.detect(frame)
            draw_detection(frame, d)
            for s in samples:
                y = int(s["bottom_y"])
                cv2.line(frame, (0, y), (frame.shape[1], y), (0, 200, 255), 1)
                cv2.putText(frame, f"{s['r_cm']}cm", (5, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            cv2.putText(frame, f"samples={len(samples)}  [r]record [d]delete [c]camera [q]save&quit",
                        (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.imshow("distance calibration", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            elif k == ord("c"):
                cap = next_camera(cap)
                if cap is None:
                    break
            elif k == ord("d") and samples:
                print("삭제:", samples.pop())
            elif k == ord("r"):
                if d is None:
                    print("물체가 검출되지 않았습니다.")
                    continue
                by = collect_bottom_y(cap, det)
                try:
                    r = float(input(f"  bottom_y={by:.1f}px 인 물체의 실제 반경 r (cm) 입력: "))
                except ValueError:
                    print("숫자를 입력하세요."); continue
                samples.append({"bottom_y": by, "r_cm": r, "box_h": d.height})
                print(f"  기록됨: y={by:.1f}px -> r={r}cm")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        arm.close_connection()

    samples.sort(key=lambda s: s["bottom_y"])
    data = {"scan_pose": list(cfg.SCAN_POSE), "frame": [cfg.FRAME_WIDTH, cfg.FRAME_HEIGHT], "samples": samples}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"저장 완료: {args.out} ({len(samples)}점)")
    if len(samples) < 2:
        print("경고: 보정점이 2개 미만이면 pick_by_camera.py 는 FIXED_REACH_CM 을 사용합니다.")


if __name__ == "__main__":
    main()
