# -*- coding: utf-8 -*-
"""
카메라 기반 사물 집기 프로토타입 - 설정 파일
모든 튜닝 값은 이 파일 하나에서 바꿉니다.

좌표계(라쿤봇 베이스 좌표계, 단위 cm):
  원점 = 베이스 회전축이 작업 테이블과 만나는 점
  +y   = 로봇 정면(전방)      +x = 로봇이 바라볼 때 오른쪽      +z = 위
  관절 1 각도(θ1)와 반경 r 로 표현하면  x = -r·sin(θ1),  y = r·cos(θ1)
  (θ1 > 0 이면 위에서 봤을 때 반시계 = 왼쪽으로 회전)
"""

# ───────────────────────── 카메라 ─────────────────────────
# 장착 방식:
#   "fixed" = 테이블/거치대에 고정 (권장, 실습용). 보정은 한 번, 팔이 움직여도 시야 불변, 관절1 회전 보정 불필요
#   "arm"   = 팔(그리퍼 앞)에 장착. 관측 자세(SCAN_POSE)에서만 보정이 유효, 집기 전 관절1 회전 보정 필요
CAMERA_MOUNT = "fixed"        # 현재(2026-09-11 사진 확인): 카메라가 어깨 관절 옆 베이스 기둥에 장착.
                              # 관절 1 과는 같이 돌지만 관절 2/3/4 로는 움직이지 않음 -> 관절 1 = 0° 에서 관측하는 고정 카메라로 취급
# fixed 모드에서 물체를 볼 때 팔이 카메라 시야를 가리지 않도록 치우는 자세. 관절 1 은 반드시 0.
# 카메라가 어깨 옆에서 앞을 보므로 팔을 위로 세운 Zero(0,0,0,0) 가 시야 밖. find_scan_pose.py 로 화면 보며 확인/저장.
OBSERVE_POSE = (0, 7, 0, 0)
CAMERA_INDEX = 2            # HAMSTER_AI_UVC (팔 카메라). 번호가 바뀌면 실행 중 c 키로 전환 가능
FRAME_WIDTH = 640           # HAMSTER_AI_UVC 기본 해상도 640x360
FRAME_HEIGHT = 360
FLIP_HORIZONTAL = False     # 화면이 좌우 반전돼 보이면 True
FLIP_VERTICAL = False       # 카메라를 거꾸로 달았으면 True
ROTATE = None               # 카메라가 옆으로 달려 있으면 "cw" / "ccw", 거꾸로면 "180", 정상이면 None
                            # 어깨 옆 장착(2026-09-11): 회전 없음이 "로봇 앞 = 화면 위" (화면 아래쪽에 팔/집게가 보임)
                            # 화면에서 앞이 왼쪽이면 "cw", 오른쪽이면 "ccw", 아래면 "180" 으로 바꿀 것

# ───────────────────────── 검출기 ─────────────────────────
DETECTOR = "color"          # "color" (HSV 색상 기반, 학습 불필요) 또는 "yolo" (ultralytics)

# color 검출기: 목표 물체 색. COLOR_NAME 으로 고르고, 보정 도구/조종 도구에서는 버튼으로 실행 중 바꿀 수 있음
COLOR_PRESETS = {
    "blue":   [((100, 80, 50), (125, 255, 255))],                              # 파란 원통 블록 실측 H 108~115
    "green":  [((40, 80, 60), (85, 255, 255))],
    "yellow": [((20, 100, 100), (35, 255, 255))],
    "red":    [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (180, 255, 255))],   # H 가 0 근처에서 감겨 두 구간
}
COLOR_LABELS = {"blue": "파랑", "green": "초록", "yellow": "노랑", "red": "빨강"}
COLOR_NAME = "green"
COLOR_HSV_RANGES = COLOR_PRESETS[COLOR_NAME]
COLOR_MIN_AREA = 400        # 이보다 작은 덩어리는 노이즈로 무시 (픽셀 수)

# yolo 검출기
YOLO_MODEL = "yolo11n.pt"   # 처음 실행 시 자동 다운로드(인터넷 필요)
YOLO_CONF = 0.4
YOLO_TARGET_CLASSES = ["cup", "bottle", "apple", "orange", "sports ball", "banana"]
# None 으로 두면 모든 클래스 중 가장 확신도가 높은 것을 목표로 삼음

# ───────────────────────── 로봇 자세 ─────────────────────────
HOME_POSE = (0, -10, -140, 60)     # 라쿤봇 Home (전원 켤 때 자동 이동하는 자세)
# 카메라로 테이블을 내려다보는 "관측 자세". 관절 1 은 탐색 중 바뀌므로 0 으로 둡니다.
# 카메라 장착 위치에 따라 관절 2, 3 을 조정해 물체가 화면 안에 들어오게 하세요.
SCAN_POSE = (0, -24, -147, 60)
SCAN_SPEED = 60

# ───────────────────────── 관절 1 시각 서보 ─────────────────────────
# 카메라가 팔과 함께 회전하므로, 물체가 화면 중앙에 오도록 관절 1 만 돌리면 됩니다.
YAW_SIGN = -1               # 물체가 화면 오른쪽에 있을 때 관절 1 을 - 방향으로 돌려야 하면 -1, 반대면 +1
YAW_KP = 0.07               # 픽셀 오차 1px 당 회전 각도(°). 60° 화각/640px ≈ 0.09 °/px 이므로 살짝 작게
YAW_MAX_STEP = 15.0         # 한 번에 최대 회전 각도(°)
YAW_MIN_STEP = 0.5          # 이보다 작은 명령은 보내지 않음
YAW_LIMIT = 115.0           # 관절 1 안전 한계(사양 ±120°)
CENTER_TOL_PX = 10          # 이 픽셀 이내면 "중앙에 정렬됨"
MAX_SERVO_ITER = 25
SERVO_SPEED = 40            # 서보 중 관절 이동 속도

# 탐색(물체가 안 보일 때) : 관절 1 을 좌우로 훑음
SEARCH_STEP_DEG = 15
SEARCH_RANGE_DEG = 90

# ───────────────────────── 카메라 보정 / 거리 추정 ─────────────────────────
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
CAMERA_CALIB_FILE = _os.path.join(_HERE, "camera_calib.json")   # calibrate_camera.py 가 만드는 파일 (실행 위치와 무관하게 vision/ 에 저장)
# 보정점 (u 좌우 cm, v 앞 cm, 종류). 인쇄 매트(make_calib_mat.py)와 보정 도구(calibrate_camera.py)가 함께 사용
#   main  = 필수 보정점 (파란 원)     check = 저장 후 정확도 확인용 (회색 원)
CALIB_POINTS = [
    (0, 9, "main"), (0, 18, "main"),
    (6, 12, "main"), (-6, 12, "main"),
    (6, 17, "main"), (-6, 17, "main"),
    (0, 13.5, "check"), (3, 15, "check"), (-3, 10.5, "check"),
]
CALIB_BLOCK_DIAMETER_MM = 30              # 매트에 그리는 원 지름(블록 크기)
OBJECT_RADIUS_CM = 1.5                    # 집을 물체(원통 블록)의 반지름. 마우스 클릭 보정일 때 아래 변 -> 바닥 중심 보정에 사용
# 기울기별 집기 보정 (calibrate_camera 의 [오프셋 측정] 이 저장): {alpha: {"du","dv","grasp_z"}}
# 집게가 블록을 문 상태에서 잰 로봇 좌표 기준이므로 좌우/앞뒤 오프셋과 '집는 높이' 가 함께 보정됨.
PICK_CALIB_FILE = _os.path.join(_HERE, "pick_calib.json")
# 기울기별 보정이 없을 때 쓰는 고정 오프셋 (팔 기준 u 좌우, v 앞, cm). [오프셋 측정] 이 마지막 값을 여기에도 기록.
PICK_OFFSET_UV = (-2.89, -2.16)
DIST_CALIB_FILE = _os.path.join(_HERE, "distance_calib.json")   # calibrate_distance.py 가 만드는 파일 (구식: 화면 y -> 거리, 카메라 보정이 없을 때만 사용)
FIXED_REACH_CM = 16.0       # 보정 파일이 없을 때 쓰는 고정 반경(cm). 수평 그리퍼는 14.1cm 미만이면 못 내려감
DIST_SAMPLES = 8            # 거리 추정 시 중앙값을 낼 프레임 수
R_MIN_CM = 6.0              # 이 범위를 벗어난 반경은 집기 시도하지 않음 (6 미만은 베이스와 충돌 위험)
R_MAX_CM = 26.0             # 수평 그리퍼 z=3cm 최대 도달 26.8cm (역기구학+관절한계 계산값)

# ───────────────────────── 집기 동작 ─────────────────────────
# 그리퍼 기울기(alpha, 0=수평, -90=수직 아래)는 거리에 따라 자동 선택합니다.
# 역기구학 + 관절 한계로 계산한, hover 높이에서 z=3cm 까지 수직 하강이 가능한 반경 범위:
#   alpha   0 (수평, lock_horz) : 14.1 ~ 26.8 cm
#   alpha -45 (45° 기울임)      : 10.4 ~ 24.3 cm  (hover 8)
#   alpha -90 (수직, lock_vert) :  4.0 ~ 18.5 cm  (hover 6)
# (r 하한, alpha, hover 높이) - r 이 큰 규칙부터 검사
# 작업 지도(매트) 격자 — 열 중심 x(cm), 행 중심 y(cm). make_work_mat.py 가 이걸로 인쇄한다
MAP_LAYOUT = {
    "A3": ([-16, -12, -8, -4, 0, 4, 8, 12, 16], [8, 12, 16, 20]),
    "B4": ([-12, -8, -4, 0, 4, 8, 12], [8, 12, 16]),
}

TILT_RULES = [
    (15.5, 0, 10.0),
    (11.0, -45, 8.0),
    (0.0, -90, 6.0),
]
# 그리퍼를 닫는 높이(cm). 좌표 기준점이 '닫힌 두 날이 만나는 점' 이라, 3cm 블록에 3.0 을 주면
# 날 끝이 블록 윗면 높이에 있어 감싸지 못한다. 3cm 블록에서 실측: 1.0 도 1.5 도 잡힌다.
# 1.5 를 쓰는 이유 — 집는 높이를 낮추면 먼 쪽 도달 거리가 줄어든다.
#   1.0 -> 수평 정면 14.95~25.46cm, A3 먼 모서리 A4·I4(r=25.6) 가 어느 기울기로도 안 닿음 (34/36칸)
#   1.5 -> 수평 정면 14.78~25.88cm, A3 36칸 전부 도달
# 블록 높이나 집게를 바꾸면 다시 재야 한다:
#   python examples/09_grasp_test.py A3 --cell E4 --find-z
GRASP_Z = 1.5
DROP_XYZ = (-10.0, 10.0, 3.0)   # 내려놓을 위치 (r=14.1 -> 45° 기울임 규칙이 적용됨)
APPROACH_SPEED = 50
LIFT_SPEED = 60
GRIPPER_SETTLE_MS = 700     # 그리퍼 개폐 후 대기

# ───────────────────────── 시각 서보 (물체 위에서 카메라로 보며 미세 조정) ─────────────────────────
SERVO_ENABLE = True                                   # False 면 관측 자세 1회 측정만으로 내려감
SERVO_CALIB_FILE = _os.path.join(_HERE, "servo_calib.json")   # 기울기별 기준 픽셀 + 자코비언 (pick_by_camera 의 [기준점 저장])
SERVO_TOL_PX = 8            # 이 픽셀 이내면 정렬 완료
SERVO_MAX_ITER = 8
SERVO_GAIN = 0.8            # 한 번에 오차의 몇 배를 보정할지 (1 보다 작게 두면 진동 방지)
SERVO_MAX_STEP_CM = 2.5     # 한 번 이동 상한
SERVO_PROBE_CM = 1.5        # 자코비언 추정용 시험 이동 거리
SERVO_SPEED = 30
JOG_STEP_CM = 0.5           # 기준점 잡을 때 수동 미세 이동 단위

# ───────────────────────── 기타 ─────────────────────────
WINDOW_NAME = "RaccoonBot Vision Pick"
FLUSH_FRAMES = 4            # 로봇 이동 직후 버퍼에 남은 오래된 프레임 버리기

# ───────────────────── 손동작 인식 (주제 8) ─────────────────────
# 사람 쪽을 보는 웹캠. 팔 카메라(CAMERA_INDEX)와 다른 장치다.
HAND_CAMERA_INDEX = 0        # None 이면 실행할 때 카메라 선택 화면이 뜬다
HAND_FLIP_HORIZONTAL = True  # 거울처럼 보여야 손을 움직이기 쉽다
HAND_FRAME_WIDTH = 640
HAND_FRAME_HEIGHT = 480

# MediaPipe Tasks 모델 파일(.task). vision/models/ 에 받아 두고 다시 받지 않는다.
# ⚠️ mediapipe 1.0 부터 mp.solutions 가 없다. 인터넷 예제 대부분이 동작하지 않는다.
GESTURE_MODEL = "gesture_recognizer.task"
GESTURE_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
                     "gesture_recognizer/float16/1/gesture_recognizer.task")
GESTURE_MIN_SCORE = 0.55     # 확신도가 이보다 낮으면 "None"(모름) 으로 본다
HAND_MAX_NUM = 1             # 손 하나만 본다. 둘이면 어느 손의 명령인지 모호해진다

# 제스처는 '상태' 가 아니라 '사건' 이다 — 주먹을 1초 쥐면 30프레임이 들어온다
STABLE_FRAMES = 5            # 같은 라벨이 N프레임 연속일 때만 확정
HOLD_FRAMES = 45             # 홈 복귀처럼 큰 동작은 N프레임(약 1.5초) 유지해야 발행
LOST_FRAMES = 3              # N프레임 미검출 -> 즉시 STOP (인식 실패의 기본값은 정지)

# 제스처 -> (명령, 종류).  종류: edge(바뀌는 순간 한 번) / level(유지하는 동안) / hold(길게 눌러야)
GESTURE_MAP = {
    "Open_Palm":   ("STOP",       "edge"),
    "Closed_Fist": ("GRIP_CLOSE", "edge"),
    "Victory":     ("GRIP_OPEN",  "edge"),
    "Pointing_Up": ("TRACK_ON",   "level"),
    "Thumb_Up":    ("HOME",       "hold"),
    "Thumb_Down":  ("OBSERVE",    "hold"),
}

# 조종 모드(TRACK): 손의 '움직인 양' 만 팔에 전달한다 — 카메라 보정이 필요 없다
TRACK_GAIN_X = 24.0          # 손이 화면 폭을 가로지르면 팔이 좌우로 24cm 움직인다
TRACK_GAIN_Y = 18.0          # 화면 높이만큼 움직이면 팔이 앞뒤로 18cm
TRACK_MAX_STEP_CM = 2.0      # 한 프레임에 움직일 수 있는 최대 거리
TRACK_DEADZONE = 0.02        # 손 떨림 무시 (정규화 좌표)
TRACK_Z = 8.0                # 조종 중 유지할 집게 높이(cm)
TRACK_SPEED = 45
