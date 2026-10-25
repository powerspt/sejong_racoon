# 라쿤봇(RaccoonBot) 파이썬 구동 매뉴얼

> 로보메이션 라쿤봇을 파이썬으로 구동하기 위한 자체 매뉴얼.
> 공식 위키(roboid 1.7.3 기준 문서)를 읽고, **실제 설치된 roboid 1.7.11 패키지 소스로 검증**해 정리했다.
> 위키와 설치 버전이 다른 부분은 [12장](#12-위키와-설치-버전roboid-1711의-차이)에 모아 두었다.
>
> 참고 원문: https://github.com/roboid-python/RaccoonBot_API_KR/wiki

---

## 목차

1. [한눈에 보는 사양](#1-한눈에-보는-사양)
2. [개발 환경 준비](#2-개발-환경-준비)
3. [로봇 연결과 첫 프로그램](#3-로봇-연결과-첫-프로그램)
4. [프로그램 골격과 안전 습관](#4-프로그램-골격과-안전-습관)
5. [관절 제어](#5-관절-제어)
6. [기준 자세](#6-기준-자세)
7. [좌표 제어와 기구학](#7-좌표-제어와-기구학)
8. [말단 장치(그리퍼)](#8-말단-장치그리퍼)
9. [센서와 버튼](#9-센서와-버튼)
10. [소리](#10-소리)
11. [전역 함수와 동시 실행](#11-전역-함수와-동시-실행)
12. [위키와 설치 버전(roboid 1.7.11)의 차이](#12-위키와-설치-버전roboid-1711의-차이)
13. [문제 해결](#13-문제-해결)
14. [카메라 피지컬 AI 프로토타입](#14-카메라-피지컬-ai-프로토타입)
15. [API 치트시트](#15-api-치트시트)

---

## 1. 한눈에 보는 사양

### 기기 사양

| 항목 | 내용 |
| --- | --- |
| 형태 | 4축(4자유도) 초소형 교육용 로봇팔 |
| 크기 / 무게 | 93 × 118 × 180 mm / 825 g (그리퍼 제외). 실측: 좌우 폭 93, 앞뒤 길이 118 |
| 작업 영역 | 회전 240°, 거리 295 mm (그리퍼 포함) |
| 배터리 | 리튬이온 3.7 V, 3500 mAh |
| 구동 | 마이크로스텝 스테퍼 모터 + 감속기 |
| 통신 | Bluetooth 5.0, PC 쪽은 **USB to BLE 동글**(시리얼 포트로 보임) |
| 말단 장치 | 집게 그리퍼 (진공/서보 그리퍼 교체 가능) |
| 버튼 | TEACH, PLAY, DELETE (POWER 는 감지 불가) |
| 확장 | 컨베이어 등 주변장치 연결 |
| 소리 | 88건반 음정 + 내장 멜로디 |

### 관절 가동 범위와 방향

| 관절 | 범위 | 속도 + 방향 | 속도 - 방향 |
| --- | --- | --- | --- |
| Joint 1 (베이스 회전) | -120° ~ +120° | 반시계(위에서 볼 때) | 시계 |
| Joint 2 (어깨) | -90° ~ +30° | 위 | 아래 |
| Joint 3 (팔꿈치) | -150° ~ 0° | 위 | 아래 |
| Joint 4 (손목) | -105° ~ +105° | 위 | 아래 |

### 마디 길이 (roboid 1.7.11 내부 상수)

| 상수 | 값 | 의미 |
| --- | --- | --- |
| L1 | 8.25 cm | 테이블면 → 관절 2 축 높이 |
| L2 | 10 cm | 상완 |
| L3 | 10 cm | 하완 |
| 그리퍼 오프셋 | 전방 8 cm, 아래 0.6 cm | 손목 축 → 서보/DC 그리퍼 끝 |
| 진공 그리퍼 오프셋 | 전방 7.5 cm | 손목 축 → 진공 패드 |

### 베이스 좌표계 (단위 cm)

- 원점: 베이스 회전축이 작업 테이블과 만나는 점
- **+y = 로봇 정면**, **+x = 로봇이 바라볼 때 오른쪽**, **+z = 위**
- 관절 1 각도 θ1 과 반경 r 의 관계: `x = -r·sin(θ1)`, `y = r·cos(θ1)` (θ1 > 0 이면 왼쪽)
- `move_to()` 권장 입력 범위: x -20~20, y -10~20, z 0~28.25
- Home 자세에서 그리퍼 끝 좌표 = (0, 14.7, 8.8)

---

## 2. 개발 환경 준비

### 파이썬

- 공식 권장: **Python 3.9.13** (roboidai, mediapipe, tensorflow 와의 호환 때문)
- 이 PC 현황(2026-09-08): Python 3.14.3 에 roboid 1.7.11(1.7.10 에서 업그레이드, 공개 API 동일), roboidai 1.1.23, opencv 4.13, ultralytics 8.4, mediapipe 1.0 이 설치되어 있고 import 는 모두 정상. 로봇 구동은 하드웨어 연결 후 확인 필요.
- 설치 시 **Add Python to PATH** 체크, 설치 후 **Disable path length limit** 클릭.

### 패키지 설치

```bash
pip install -U roboid                 # 필수
pip install -U opencv-python numpy    # 카메라 프로토타입
pip install -U ultralytics            # YOLO 검출기를 쓸 때만
pip install -U roboidai               # 로보메이션 AI 패키지(선택, tensorflow 포함)
```

버전 확인:

```bash
python -c "import roboid; print(roboid.__version__)"
```

### 편집기

VS Code + Python 확장 + Python Debugger 확장. 터미널에서 한글이 깨지면 `chcp 65001` 실행.

---

## 3. 로봇 연결과 첫 프로그램

### 물리 연결 순서

1. USB to BLE 동글을 PC 에 꽂는다. 파란불이 **천천히 깜빡**이면 정상.
2. 라쿤봇 전원을 켜고 동글 가까이 둔다.
3. 삐 소리가 나고 동글/로봇 불이 **계속 켜지거나 빠르게 깜빡**이면 페어링 완료.
4. 소리가 안 나면 배터리를 확인한다. 불이 파랗지 않으면 동글을 살짝 눌러 접촉을 확인하거나 다른 USB 포트를 쓴다.

### 포트 확인

```python
from roboid import *
scan()          # 시리얼 포트 목록 출력. 동글이 없으면 "No available serial port"
```

### 첫 프로그램

```python
from roboid import *

raccoon = Raccoon()        # 동글 자동 탐색 + 연결 + Home 자세로 이동
wait(1000)
print(raccoon.encoder(-1)) # (j1, j2, j3, j4)
raccoon.beep()
raccoon.dispose()          # 연결 해제
```

### 생성자 형태

| 호출 | 의미 |
| --- | --- |
| `Raccoon()` | 첫 번째 로봇, 포트 자동 |
| `Raccoon(1)` | 두 번째 로봇(동글 2개) |
| `Raccoon(0, 'COM5')` | 포트 지정 |
| `Raccoon('COM5')` | **1.7.11 에서는 포트가 무시되는 버그** 있음. 위 형태를 쓸 것 |

`Raccoon()` 은 생성 즉시 `init_pose()` 를 호출하므로 **그리퍼가 열리고 Home(0, -10, -140, 60) 으로 움직인다.** 로봇 주변을 비워 두고 실행한다.

---

## 4. 프로그램 골격과 안전 습관

```python
from roboid import *

HOME = (0, -10, -140, 60)
raccoon = Raccoon()

try:
    raccoon.lock_horz()             # 그리퍼 수평 유지 (물건 다룰 때 권장)
    # ... 동작 ...
finally:
    raccoon.stop()                  # 모든 관절 정지
    raccoon.unlock()
    raccoon.degree_to(*HOME)        # 항상 Home 으로 정리
    raccoon.dispose()
```

- **Ctrl+C** 를 누르면 roboid 가 등록한 SIGINT 핸들러가 모든 로봇을 `dispose()` 하고 프로그램을 끝낸다. 따라서 `except KeyboardInterrupt` 로는 잡히지 않고 `SystemExit` 로 끝난다. 정리 코드는 `finally` 에 둔다.
- 각도 이동 함수(`degree_to`, `move_to`)는 **도착할 때까지 블로킹**된다. 기다리지 않으려면 `wait=False`.
- 범위를 벗어난 각도/좌표를 주면 **에러음이 나고 이동하지 않는다** (위키의 "0도로 설정" 설명과 다름, 1.7.11 소스 기준).
- 손으로 팔을 움직일 때는 멈추는 지점까지만 부드럽게. 모터 힘을 빼려면 `raccoon.turn_off()`.
- 그리퍼는 무거운 물체를 못 잡고 미끄러질 수 있다.
- 자동 수평/수직 유지는 보정 응답이 느린 보조 기능이다.

---

## 5. 관절 제어

두 가지 모드가 있고 동시에 쓸 수 없다. 각도 함수를 부르면 자동으로 각도 모드, 속도 함수를 부르면 속도 모드로 바뀐다.

### 5.1 속도 제어 (계속 회전, 명시적으로 멈춰야 함)

```python
raccoon.velocity(1, 50)          # 관절 1 을 속도 50 으로 (-100 ~ 100)
raccoon.velocity(-1, 30)         # 모든 관절 30
raccoon.velocity(50, -30, 20, 0) # 관절 1~4 각각
raccoon.velocity(1, 0)           # 관절 1 정지
raccoon.stop()                   # 전체 정지 (stop(2) 처럼 한 관절만도 가능)
raccoon.turn_off()               # 모터 힘 빼기 (손으로 자세 잡을 때)
```

부드러운 가감속은 반복문으로 속도를 단계적으로 바꾼다.

```python
speed = 0
for _ in range(10):
    speed += 10
    raccoon.velocity(3, speed)
    wait(200)
```

### 5.2 각도 제어 (목표 각도까지 자동 이동 후 대기)

```python
raccoon.degree_to(1, 45)                 # 관절 1 을 45° 로, 속도 기본 100
raccoon.degree_to(1, 45, 50)             # 속도 50
raccoon.degree_to(-1, 0)                 # 모든 관절 0°
raccoon.degree_to(0, -10, -140, 60)      # 관절 1~4 동시에
raccoon.degree_to(0, -10, -140, 60, 25)  # 5번째 인자 = 속도

raccoon.degree_by(1, -60)                # 현재 각도 기준 상대 이동
raccoon.degree_by(30, -30, 60, 0, 50)    # 4관절 상대 이동, 속도 50

raccoon.degree_to(0, 0, -90, 0, 60, wait=False)   # 기다리지 않음
wait(200)                                          # 플래그 갱신 대기 (아래 참고)
while raccoon.is_moving():
    wait(50)
```

- 속도 인자는 "허용 최대 속도(0~100)" 이고 실제 프로파일은 내부에서 계산된다.
- `is_moving()` 은 명령을 보낸 뒤 **약 0.1초가 지나야 True** 가 된다(실기 측정). `wait=False` 직후 바로 검사하면 False 라서 루프를 건너뛴다. 0.2초 정도 기다린 뒤 검사한다.
- 사전 검사: `raccoon.can_degree_to(j1, j2, j3, j4)`, `raccoon.can_degree_by(...)` → True/False.
- `precision_mode(True)` 를 켜면 도착 후 한 번 더 보정 이동을 한다.
- 위키의 `set_degree()` 는 **1.7.11 에 없다.** `degree_to(..., wait=False)` 를 쓴다.

---

## 6. 기준 자세

| 이름 | 각도 (j1, j2, j3, j4) | 용도 |
| --- | --- | --- |
| Zero | (0, 0, 0, 0) | 팔을 위로 쭉 편 기준점. 그리퍼 끝 높이 약 36 cm |
| Park | (0, 25, -145, -60) | 보관(가장 작게 접힘) |
| Home | (0, -10, -140, 60) | 전원 켤 때/`Raccoon()` 생성 시 자동 이동. 모든 동작의 출발점 |

```python
raccoon.init_pose()      # unlock + 그리퍼 열기 + Home 이동 (1.7.11 제공)
```

---

## 7. 좌표 제어와 기구학

### 7.1 기준점

1.7.11 의 기본 기준점은 **그리퍼 끝**이다 (`end_effector("gripper")`). 위키(손목 기준)와 다르다.

```python
raccoon.end_effector("gripper")   # 기본값: 그리퍼 끝 (서보 그리퍼면 손목에서 전방 8cm, 아래 0.6cm)
raccoon.end_effector("wrist")     # 손목(관절 4 축) 기준
raccoon.end_effector_to(y, z)     # 손목 기준 임의 오프셋 지정 (사용자 정의 말단 장치)
raccoon.unit("cm")                # "inch" 도 가능
```

### 7.2 이동

```python
raccoon.lock_horz()                    # 좌표 이동 전 수평 고정 권장
raccoon.can_move_to(10, 10, 5)         # 도달 가능? True/False
raccoon.move_to(10, 10, 5)             # 속도 기본 100
raccoon.move_to(10, 10, 5, 50)         # 속도 50
raccoon.move_to(10, 10, 5, 50, wait=False)
raccoon.can_move_by(0, 0, 5)
raccoon.move_by(0, 0, 5)               # 현재 위치에서 위로 5cm
```

권장 범위: x -20~20, y -10~20, z 0~28.25. 실제 판정은 역기구학 결과가 관절 범위 안인지로 한다.

#### 실제 도달 범위 (역기구학 + 관절 한계로 계산, 그리퍼 끝 기준, 정면 방향)

`move_to` 는 현재 손목 방향(관절 2+3+4 의 합)을 유지한 채 움직이므로, **그리퍼 기울기에 따라 닿는 거리가 크게 달라진다.** 아래는 hover 높이에서 z=3 cm 까지 수직으로 내려갈 수 있는 반경 범위다.

| 그리퍼 기울기 | 설정 방법 | 도달 반경 (z=3cm 기준) |
| --- | --- | --- |
| 수평 (alpha 0) | `lock_horz()` | 14.1 ~ 26.8 cm |
| 45° 아래 | `unlock()` 후 관절 4 = -45 -90 -j2 -j3 | 10.4 ~ 24.3 cm |
| 수직 아래 (alpha -90) | `lock_vert()` | 4.0 ~ 18.5 cm |

- 수평 그리퍼로 14 cm 안쪽의 낮은 물체를 잡으려 하면 관절 4 가 105° 한계에 걸려 에러음만 나고 움직이지 않는다. 가까운 물체는 수직으로 내려 잡는다.
- 관절 2 하한(-90°)이 먼 쪽 한계를 정한다. 어떤 기울기로도 27 cm 를 넘지 못한다.
- 높이 3 cm 에서 수평 그리퍼로 y=14 는 관절 4 가 105.5° 라 불가, y=18 은 (0, -58, -113, 82), y=26 은 (0, -83, -43, 36).
- `vision/arm_helper.py` 의 `tilt_for(r)` 가 이 표대로 기울기를 자동 선택한다 (15.5 cm 이상 수평, 11~15.5 는 45°, 그 미만 수직).

### 7.3 순기구학(각도 → 좌표) / 역기구학(좌표 → 각도)

```python
raccoon.xyz()                                   # 현재 (x, y, z)
raccoon.degree_to_xyz(0, -10, -140, 60)         # 각도 4개 -> (x, y, z)
raccoon.xyz_to_degree(10, 10, 5)                # (x, y, z) -> (th1, th2, th3, th4)
```

- 역기구학은 현재 손목 방향(관절 2+3+4 합)을 유지하도록 th4 를 정한다. 그래서 `lock_horz()` 와 잘 맞는다.
- 위키 4DoF 문서의 수식은 L1=0, L4=6 으로 단순화한 교육용 모델이다. 실제 라이브러리는 L1=8.25, 그리퍼 오프셋(8, -0.6) 을 쓴다.

교육용 수식(그리퍼 수평 고정, 3자유도 근사):

```
Z = L1 + L2·sin(θ2) + L3·sin(θ2+θ3)
P = L2·cos(θ2) + L3·cos(θ2+θ3) + L4
X = P·cos(θ1),  Y = P·sin(θ1)

θ1 = atan2(Y, X)
W = √(X²+Y²),  H' = Z - L4
D = √(W² + (H'-L1)²)
cos θ3 = (L2² + L3² - D²) / (2·L2·L3)
θ2 = atan2(H'-L1, W) - atan2(sin α, cos α),  cos α = (D² + L2² - L3²) / (2·L2·D)
```

---

## 8. 말단 장치(그리퍼)

```python
raccoon.open_gripper()       # 열기 (0.5초 대기 포함)
raccoon.close_gripper()      # 닫기
raccoon.open_gripper(wait=False)
raccoon.gripper_state()      # 그리퍼 상태 바이트 (0~255)

raccoon.lock_horz()          # 그리퍼를 지면과 수평으로 자동 유지 (관절 4 명령 무시됨)
raccoon.lock_vert()          # 수직 유지
raccoon.unlock()             # 해제
```

- 열기는 닫힌 상태에서만, 닫기는 열린 상태에서만 동작한다.
- `pick_gripper()` / `place_gripper()` 는 각각 close / open 의 별칭이다.
- 수평/수직 고정 중에는 `degree_to(j1, j2, j3, j4)` 의 4번째 값이 무시된다.

Pick & Place 골격:

```python
def pick(bot, x, y, hover=12, grasp=3, lift=15):
    bot.open_gripper()
    bot.move_to(x, y, hover, 60)
    bot.move_to(x, y, grasp, 30)
    bot.close_gripper()
    bot.move_to(x, y, lift, 60)
```

`examples/05_pick_and_place.py` 는 카메라 화면 옆에 버튼 패널을 띄워 그리퍼를 조금씩 움직이고(W/A/S/D, R/F), 물체 위치에서 집기 위치를, 놓을 자리에서 놓기 위치를 저장한 뒤 Enter 로 위 시퀀스를 실행하는 조종 도구다. 로봇 명령은 별도 스레드에서 돌아 이동 중에도 화면이 갱신된다.

---

## 9. 센서와 버튼

```python
raccoon.encoder(1)          # 관절 1 각도(°), encoder(-1) 은 4개 튜플
raccoon.battery_state()     # 3 정상 / 2 중간 / 1 부족 / 0 없음
raccoon.charge_state()      # 1 충전 중 / 0 아님
raccoon.signal_strength()   # -128 ~ 0 dBm (클수록 강함)
raccoon.is_moving()         # 관절 이동 중 True
```

버튼 (1.7.11 이름 기준):

> **이 버튼들은 로봇 본체에 붙어 있는 물리 버튼이다.** 화면 버튼도, 키보드 키도 아니다.
> 파이썬은 손가락으로 누른 것을 **읽기만** 한다. POWER 버튼만은 읽을 수 없다.
>
> - **클릭** = 짧게 눌렀다 떼기 → `*_clicked()` 가 **한 번만** True
> - **길게 누름** = 누른 채로 잠시 있기 → `*_long_pressed()`
> - **눌림 상태** = 누르고 있는 동안 계속 1 → `*_button()`
>
> 반복문에서 `*_button()` 을 쓰면 누르고 있는 동안 매 바퀴 반응해서 같은 일이 수십 번 일어난다.
> "한 번 눌렀을 때 한 번" 을 원하면 `*_clicked()` 를 쓴다.

| 버튼 | 눌림 상태(0/1) | 클릭(True 1회) | 길게 누름 |
| --- | --- | --- | --- |
| TEACH | `teach_button()` | `teach_clicked()` | `teach_long_pressed()` |
| PLAY | `play_button()` | `play_clicked()` | `play_long_pressed()` |
| DELETE | `delete_button()` | `delete_clicked()` | `delete_long_pressed()` |

위키의 `playback_button()`, `playback_clicked()`, `playback_long_pressed()` 는 1.7.11 에 없다.

```python
while True:
    if raccoon.teach_clicked():
        pose = raccoon.encoder(-1)
    elif raccoon.play_clicked():
        raccoon.degree_to(*pose)
    wait(20)
```

---

### 정밀 모드 `precision_mode()` — 반복정밀도에 직접 영향

```python
raccoon.precision_mode(True)    # 기본값 False
```

> **우리 교육 프로그램에서는 쓰지 않는다** (결정 2026-10-06).
> 산포는 줄지만 **이동 시간이 약 2배**가 되어 100분 블록 수업에 부담이 크다.
> 검증(07·08·09, field_test J)도 전부 끈 조건에서 한다 — 수업과 같은 조건이어야 숫자가 의미 있다.

켜면 `degree_to` / `move_to` 가 **이동이 끝난 뒤 같은 목표를 한 번 더 보내고 다시 기다린다.**
스테퍼가 목표에 살짝 못 미쳤을 때 2차 보정이 들어가므로 **같은 좌표로 반복 이동할 때 산포가 줄어든다.**
대신 한 번의 이동에 시간이 약 두 배 든다.

| | 끄면 (기본) | 켜면 |
| --- | --- | --- |
| 이동 명령 | 1회 | 1회 + 보정 1회 |
| 소요 시간 | 짧다 | 약 2배 |
| 반복정밀도 | 기준 | **개선** (실측으로 확인할 것) |

> 정밀 작업(집기·팔레타이징)에는 켜고, 속도가 중요한 시연에는 끈다.
> 수업에서는 **끈 상태와 켠 상태의 산포를 각각 재서 비교**하는 실험이 좋다.

### 그 밖의 공식 API — 직접 만들지 말 것

| 함수 | 하는 일 | 대신 쓰면 안 되는 것 |
| --- | --- | --- |
| `is_connected()` | **연결 여부 공식 판정** | 신호/엔코더로 추측하는 자작 검사 |
| `init_pose()` | `unlock()` + `open_gripper()` + Home 이동 | 손으로 조합 (단, 물체를 쥔 채 부르면 놓친다) |
| `is_moving()` | 이동 중인지 | 고정 `wait()` 로 어림잡기 |
| `gripper_state()` | 그리퍼 상태 | 눈으로 확인 |
| `can_degree_to()` / `can_move_to()` | 사전 도달 검사 | 보내 보고 되는지 확인 |
| `reset()` | 설정 전체 초기화 + `init_pose()` | — |

## 10. 소리

```python
raccoon.tempo(120)                  # BPM (기본 60)
raccoon.note("C4")                  # 계속 울림, note("OFF") 로 끔
raccoon.note("C#5", 0.5)            # 0.5박자 후 자동 종료
raccoon.sound("BEEP")               # 비동기 재생
raccoon.sound("ENGINE", -1)         # 무한 반복, sound("OFF") 로 끔
raccoon.sound_until_done("GOOD JOB")
raccoon.beep()                      # 삐 + 끝날 때까지 대기
```

음 이름: `C4`, `C#4`/`Db4`, `D4`, ... `B4`, 옥타브 0~8 (A0~C8).
사운드 ID (대소문자 구분 없음, `Raccoon._SOUNDS` 실측 — 2026-09-22 검증):
`OFF` `BEEP` `RANDOM BEEP` `SIREN` `ENGINE` `ROBOT` `DIBIDIBIDIP` `GOOD JOB` `NOISE` `CHOP` `RANDOM MELODY` `WAKE UP` `START` `BYE`
(공백 대신 밑줄도 됨: `RANDOM_BEEP`, `GOOD_JOB`, `WAKE_UP`, `RANDOM_MELODY`)

> ⚠️ **`HAPPY` `ANGRY` `SAD` `SLEEP` `MARCH` `BIRTHDAY` 는 라쿤봇에 없다.** 햄스터·비글·터틀 등 다른 로보이드 기기에는 있어 자료가 섞이기 쉽다.
> 없는 ID를 넣으면 **예외 없이 조용히 아무 일도 일어나지 않으므로** 디버깅이 어렵다. 수업 전 실제로 울려 보고 쓸 것.

---

## 11. 전역 함수와 동시 실행

```python
wait(1000)                 # ms 대기, wait(-1) 은 영원히
wait_until(fn)             # fn() 이 True 될 때까지 (약 20ms 주기 호출)
wait_until(fn, args)
wait_until_ready()         # 여러 로봇 모두 연결될 때까지
when_do(cond, do)          # cond 가 True 되는 순간 do 실행 (등록만 하고 다음 줄로)
while_do(cond, do)         # cond 가 True 인 동안 반복 실행
parallel(f1, f2)           # 스레드로 동시 실행, parallel((f, arg), ...)
set_executable(fn)         # 20ms 마다 호출되는 콜백 등록 (안에서 오래 걸리면 안 됨)
scan()                     # 시리얼 포트 목록
dispose()                  # 모든 로봇 해제
```

동시 실행 예:

```python
def move():
    while True:
        raccoon.degree_to(1, 60)
        raccoon.degree_to(1, -60)

def music():
    while True:
        raccoon.note("C4", 0.5); raccoon.note("E4", 0.5); raccoon.note("G4", 0.5)

parallel(move, music)
wait(-1)
```

roboid 는 별도 통신 스레드를 20 ms 주기로 돌린다. 메인 스레드에서 OpenCV 창을 띄우고 `cv2.waitKey()` 를 돌려도 통신에 영향이 없다.

---

## 12. 위키와 설치 버전(roboid 1.7.11)의 차이

| 위키(1.7.3 문서) | 1.7.11 실제 | 대응 방법 |
| --- | --- | --- |
| `playback_button/clicked/long_pressed()` | `play_button/clicked/long_pressed()` | 이름 변경 |
| `set_degree(joint, deg, speed)` | 없음 | `degree_to(..., wait=False)` |
| `deg_to_xyz(d1, d2, d3, d4, length)` | `degree_to_xyz(d1, d2, d3, d4)` | 길이 대신 `end_effector()` 로 기준점 지정 |
| `xyz(length)` | `xyz()` | 위와 동일 |
| `xyz_to_deg(x, y, z)` → 3개 | `xyz_to_degree(x, y, z)` → 4개 (th1~th4) | 이름/반환 개수 변경 |
| 좌표 기준 = 손목 | 기본 기준 = **그리퍼 끝** | 손목 기준이 필요하면 `end_effector("wrist")` |
| `Raccoon('COM52')` | 포트 인자가 무시됨(버그) | `Raccoon(0, 'COM52')` |
| 범위 밖 각도 → 0° 로 설정 | **명령 자체를 보내지 않음** (콘솔·예외 없음, 로봇 부저로 사운드 127) | `can_degree_to()` 로 사전 검사 |
| 배터리 예제 페이지 0/1/2 | 센서 페이지와 같이 0~3 | 3 정상 / 2 중간 / 1 부족 / 0 없음 |
| 사운드 ID에 HAPPY/ANGRY/SAD/SLEEP/MARCH/BIRTHDAY 포함 | 라쿤봇에는 **없음** (다른 로보이드 기기 전용) | 10장의 실측 목록 사용. 없는 ID는 조용히 무시됨 |
| 문서에 없음 | `init_pose()`, `turn_off()`, `precision_mode()`, `unit()`, `end_effector*()`, `can_degree_to/by()`, `is_moving()`, `gripper_state()`, `pick/place_gripper()`, `conveyor()`, `while_do()` | 추가 기능 |

---

## 13. 문제 해결

> ### ⚠️ 가장 먼저 알아야 할 것 — roboid 는 연결 실패해도 예외를 내지 않는다
>
> 동글이 없으면 `No available USB to BLE bridge` 를 **한 줄만** 찍고 그대로 진행하며,
> 이후 모든 읽기가 **기본값**을 돌려준다. 그 값이 그럴듯해서 연결된 줄 착각하기 쉽다. (2026-09-22 실측)
>
> | 함수 | 미연결 시 반환 | 왜 헷갈리는가 |
> | --- | --- | --- |
> | `battery_state()` | **2** | "중간"으로 보인다. **연결 확인에 쓰면 안 된다** — 실제로 2가 나올 수도 있어 구분이 불가능 |
> | `signal_strength()` | **0** | 연결되면 −40~−70 dBm 같은 음수가 나온다 |
> | `encoder(-1)` | **(0, 0, 0, 0)** | Home(0, −10, −140, 60) 이 아니라 **Zero** 자세 |
> | `xyz()` | **(0, 0, 28.25)** | 28.25 = L1+L2+L3. 엔코더 0으로 계산한 값이고 **그리퍼 오프셋도 빠져 있다**(그리퍼 종류를 0으로 읽어서) |
>
> **믿을 수 있는 연결 확인** — 신호와 관절을 함께 본다:
>
> ```python
> def is_connected(bot):
>     sig = bot.signal_strength()
>     enc = tuple(round(float(v)) for v in bot.encoder(-1))
>     return not (sig == 0 and enc == (0, 0, 0, 0))
> ```
>
> `examples/01_connect_test.py` 와 `vision/arm_helper.RaccoonArm` 에 이 검사가 들어 있다.
> `RaccoonArm` 은 미연결이면 `ConnectionError` 를 던진다.
>
> ### 같은 패턴 — roboid 의 실패는 대부분 조용하다 (2026-09-22 실측)
>
> | 상황 | 콘솔 | 예외 | 실제 동작 | 눈에 보이는 유일한 신호 |
> | --- | --- | --- | --- | --- |
> | 동글 미연결 | 한 줄뿐 | 없음 | 기본값 반환 | `signal_strength()==0` + 관절 0 |
> | 없는 사운드 ID (`"HAPPY"`) | 없음 | 없음 | 아무 일도 안 함 | 없음 — 목록을 외우는 수밖에 |
> | **범위 밖 각도** (`degree_to(2, 35)`) | **없음** | 없음 | **명령을 보내지 않음** | `can_degree_to()` 가 `False` + 로봇 부저 |
> | **도달 불가 좌표** (`move_to`) | 없음 | 없음 | 명령을 보내지 않음 | `can_move_to()` 가 `False` + 로봇 부저 |
>
> `degree_to` / `degree_by` / `move_to` 는 거부 시 `_error_sound()` 로 **로봇 부저에 사운드 127** 을 보낸다.
> 127 은 문서화된 사운드 표(10장)에 없는 값이라 **펌웨어에 따라 들리지 않을 수 있다.**
> 따라서 **소리에 의존하지 말고 `can_*()` 로 미리 검사**하는 것이 유일하게 확실한 방법이다.
>
> ```python
> if r.can_degree_to(2, 35):
>     r.degree_to(2, 35)
> else:
>     print("관절 2 는 +30° 까지입니다")   # <- 학생이 볼 수 있는 유일한 메시지
> ```

| 증상 | 확인 사항 |
| --- | --- |
| **값은 찍히는데 로봇이 안 움직임** (배터리 2, 신호 0, 관절 0,0,0,0) | **연결 안 된 것이다.** 위 박스 참조. 동글이 꽂혀 있는지 확인 — 노트북 내장 블루투스로는 안 되고, 동글은 COM 포트로 보인다 |
| **연결은 되는데 로봇이 전혀 움직이지 않음** (Home 자동 이동도 안 함) | `charge_state()` 가 1 이면 충전 케이블이 꽂힌 것. 충전 중에는 모터가 잠긴다(실측). 케이블을 뽑고 전원을 껐다 켠다. `battery_state()` 0 이면 먼저 충전 |
| `scan()` 에 포트가 없음 | 동글 접촉/포트 변경, 장치 관리자에서 COM 포트 확인 |
| `Raccoon()` 후 멈춰 있음 | 로봇 전원, 배터리, 동글과의 거리. 삐 소리로 페어링 확인 |
| 각도 명령이 **아무 반응 없이 무시됨** | 범위 밖이다. 콘솔에는 아무것도 안 나오고 예외도 없다(로봇 부저로 사운드 127 만 전송되며 들리지 않을 수 있다). `can_degree_to()` 로 먼저 검사할 것. 수평/수직 고정 중에는 관절 4 명령이 무시된다 |
| `move_to` 가 반응 없음 | `can_move_to()` 로 확인. 그리퍼 기준 좌표임을 기억(손목보다 8 cm 앞) |
| `wait=False` 뒤 `is_moving()` 루프가 바로 끝남 | 플래그가 약 0.1초 뒤에 갱신됨. `wait(200)` 후 검사 |
| `AttributeError: playback_clicked` 등 | 12장의 이름 차이 |
| 손으로 팔이 안 움직임 | `turn_off()` 로 모터 힘 빼기 |
| 콘솔 한글 깨짐 | `chcp 65001` 또는 환경변수 `PYTHONIOENCODING=utf-8` |
| Ctrl+C 후 예외 메시지 | 정상. roboid 가 `SystemExit` 로 종료함 |
| roboidai/mediapipe import 실패 | Python 3.9.13 권장. 3.11+ 에서 문제 시 다운그레이드 |
| `Connection lost` / `Connected` 가 반복됨 | BLE(2.4 GHz) 간섭. 이 PC 는 팔 카메라와 BLE 동글이 같은 USB 3.0 루트 허브에 꽂혀 있고, 카메라 스트리밍이 시작되면 끊김이 반복됐다. USB 3.0 포트는 2.4 GHz 잡음을 낸다. **동글을 USB 연장 케이블로 카메라 케이블·포트에서 30 cm 이상 떨어뜨리거나** 다른 쪽 USB 컨트롤러(반대편 포트)에 꽂는다. 로봇을 동글 가까이 두고 배터리(`battery_state()` 1 이면 충전)도 확인 |
| `카메라 N 를 열 수 없습니다` | USB 재연결/가상 카메라로 번호가 바뀐 것. 이제 자동으로 선택 창이 뜨니 미리보기에서 팔 카메라를 고른다. 선택 창에 팔 카메라가 없으면 다른 프로그램(이전 실행 창)이 잡고 있는지 확인 |
| 집기 위치가 항상 일정하게 어긋남(예: 앞으로 2 cm) | 보정 오차(0.2 cm)가 아니라 고정 오프셋. 원인 후보는 매트 원점(D) 정렬, 그리퍼 팁 기준(roboid 는 손목에서 8 cm 앞을 팁으로 봄, 실제 집게 중심과 다를 수 있음), 검출 상자 아래 변이 그림자 때문에 바닥에 못 미침. `check_offset.py` 로 카메라 없이 로봇만 매트 점에 내려 보면 로봇/매트 쪽인지 카메라 쪽인지 가려진다. 해결은 시각 서보 사용(권장) 또는 `PICK_OFFSET_UV` |
| 카메라 화면이 세로로 길다 | 카메라가 옆으로 장착돼 `ROTATE="ccw"` 로 세운 결과(원본 640×360 → 360×640). 센서 비율은 못 바꾸지만 `camera_test.py --probe` 로 다른 해상도 모드가 있는지 확인할 수 있다. 가로 시야가 더 필요하면 카메라를 물리적으로 90° 돌려 달고 `ROTATE=None`(또는 `"180"`)으로 바꾼 뒤 다시 보정한다 |

---

## 14. 카메라 피지컬 AI 프로토타입

`vision/` 폴더. UVC 카메라를 **팔 정면에 고정해 관절 1 과 함께 회전**하는 구성 전용이다.

### 14.0 카메라 장착 방식 선택 (`config.CAMERA_MOUNT`)

| 방식 | 장점 | 단점 | 보정 |
| --- | --- | --- | --- |
| `"fixed"` 고정 (권장, 실습용) | 보정 1회로 끝, 팔이 움직여도 시야 불변, 관절 1 회전 보정 불필요, 흐름이 단순 | 팔이 물체를 가릴 수 있어 관측 자세(`OBSERVE_POSE`)로 비켜야 함. 카메라를 낮게 두면 거리 분해능이 나쁨 | **로봇 기준** 방식: 그리퍼를 블록 위에 맞추고 [기록]. 매트 불필요, 매트 정렬·그리퍼 오프셋이 보정에 흡수됨 |
| `"arm"` 팔 장착 | 어느 방향이든 볼 수 있음 | 관측 자세에서만 보정 유효, 관절 1 회전 보정과 2단 측정 필요 | 매트 + 마우스 클릭 |

**고정 카메라 높이/각도**: 테이블 면에 붙여 거의 수평으로 보면 앞뒤 거리가 화면에서 몇 픽셀로 압축되어 1 px 이 1 cm 이상이 되고, 블록끼리 서로 가립니다. 보정 도구가 저장 시 "분해능 최악 1px=?cm" 를 출력하니 **0.3 cm 이하**가 되도록 카메라를 높이고(20~40 cm) 아래로 기울이세요. 가장 좋은 배치는 작업 영역 위에서 내려다보는 것(스탠드/삼각대)이고, 그 다음이 로봇 옆·뒤 대각선 위입니다. 카메라가 정면에서 로봇을 마주 보면 팔이 물체를 가장 많이 가립니다.

**어깨 옆 장착(현재)**: 팔 자세와 무관하게 시야가 고정되므로 보정은 한 번이면 되고, 로봇 기준 보정(그리퍼를 블록 위에 맞추고 [기록])으로 매트 정렬·그리퍼 오프셋을 흡수한다. 집을 때는 팔을 `OBSERVE_POSE` 로 치우고 한 번 재서 바로 내려간다. 카메라가 그리퍼와 같이 움직이지 않으므로 그리퍼 기준 서보는 쓰지 않는다. 팔이 시야를 가리는지는 `find_scan_pose.py` 로 확인하고(프리셋 2 = Zero), 카메라를 다시 달면 화면 방향을 보고 `ROTATE` 를 맞춘다(앞이 왼쪽이면 "cw", 오른쪽이면 "ccw", 아래면 "180").

### 14.1 원리

물체는 테이블 평면 위에 있으므로 카메라 한 대로 위치를 정할 수 있다. 관측 자세(관절 2~4 고정)에서 테이블 평면과 화면 사이의 사영 변환(호모그래피)을 한 번 구해 두면, 검출한 물체의 "상자 아래 변 중앙" 픽셀에서 팔 기준 좌표 (u 좌우, v 앞) cm 가 바로 나온다.

1. **보정(카메라를 달 때마다 1회)**: `calibrate_camera.py` 로 블록을 알고 있는 위치 4~6 점에 놓고 기록 → `camera_calib.json`. 카메라가 팔 중심선에서 비껴 달렸거나 틀어져 있어도 그 오차가 변환에 흡수된다. 실측에서 정면에 놓은 블록의 화면 x 오차가 9 cm 에서 13 px, 18 cm 에서 68 px 로 거리에 따라 커졌는데, 이는 카메라 장착 오프셋 때문이고 이 보정으로 해결된다.
2. **측정**: 검출 → `(u, v)` → 물체 쪽으로 관절 1 을 한 번 돌려 정면 근처(보정점 근처)에서 다시 측정.
3. **변환**: 팔 기준 `(u, v)` 를 현재 관절 1 각도 θ1 로 회전해 베이스 좌표 `(x, y) = (u·cosθ1 − v·sinθ1, u·sinθ1 + v·cosθ1)`.
4. **접근**: 반경에 맞는 그리퍼 기울기 선택(7.2 절 표) → 물체 위 hover 높이로 이동.
5. **시각 서보(피드백)**: hover 에서 카메라로 물체를 보며, 물체가 "기준 픽셀"에 올 때까지 팔을 조금씩 옮긴다. 기준 픽셀은 그리퍼가 물체 바로 위에 있을 때 물체가 보이는 화면 위치로, 기울기별로 한 번 기록한다(패널 [기준점 저장]). 픽셀 오차→cm 변환(자코비언)은 1.5 cm 시험 이동 두 번으로 자동 추정해 `servo_calib.json` 에 저장한다. 이 단계에서 보정·매트 정렬·그리퍼 오프셋의 잔여 오차가 상쇄된다.
6. **집기**: 하강 → 잡기 → 들기 → 놓는 위치 → Home.

보정 파일이 없으면 구식 방법(화면 중앙에 맞추는 1축 시각 서보 + 화면 y→거리표 또는 고정 반경)으로 동작한다.

**카메라 두 대가 필요한가**: 거리 문제 때문이라면 필요 없다. 물체가 평면 위에 있다는 조건 덕분에 한 대로 (u, v) 가 결정된다. 두 번째 카메라를 단다면 팔이 아니라 **테이블 위 고정(천장 방향)** 에 다는 것이 낫다. 고정 카메라는 장착 시 한 번만 보정하면 되고, 팔이 움직여도 시야가 바뀌지 않아 여러 물체를 한 번에 잡을 수 있다. 팔 카메라는 접근 중 최종 미세 조정용으로 남긴다.

### 14.2 파일

| 파일 | 역할 |
| --- | --- |
| `config.py` | 카메라 인덱스, 검출기 종류, HSV 범위, 서보 게인, 자세, 높이 등 모든 튜닝 값 |
| `detectors.py` | `ColorDetector`(HSV, 학습 불필요), `YoloDetector`(ultralytics) |
| `arm_helper.py` | `RaccoonArm`(roboid 래퍼: yaw 제어, 극좌표 이동, 집기 시퀀스), `DummyArm`(로봇 없이 시험) |
| `camera_test.py` | 카메라 목록, 실시간 검출, HSV 트랙바 튜너 |
| `calibrate_camera.py` | **카메라 장착 보정** (픽셀 → 테이블 좌표 호모그래피, `camera_calib.json`). 카메라를 달거나 위치를 바꿀 때마다 실행 |
| `table_mapper.py` | 보정 파일을 읽어 픽셀 → (u, v) → 베이스 (x, y) 변환 |
| `calibrate_distance.py` | 구식: 화면 y → 반경 cm 보정표 (`distance_calib.json`), 카메라 보정이 없을 때만 사용 |
| `pick_by_camera.py` | 메인(버튼 패널 UI): 탐색 → 측정 → 접근 → 시각 서보 → 집기. 로봇 동작은 워커 스레드, 화면은 계속 갱신 |
| `check_offset.py` | 카메라 없이 로봇만으로 매트 점에 그리퍼를 내려 고정 오프셋(매트 정렬/그리퍼 팁) 측정 → `PICK_OFFSET_UV` |

### 14.3 실행 순서

```bash
cd vision
python camera_test.py --list          # 카메라 인덱스 확인 → config.CAMERA_INDEX
python camera_test.py --hsv           # 물체 색 범위 찾기 → config.COLOR_HSV_RANGES
python camera_test.py                 # 검출이 안정적인지 확인
python calibrate_camera.py            # 카메라 장착 보정: 블록을 (u,v)=(0,9) (0,18) (6,12) (-6,12) (6,17) (-6,17) 에 두고 r 키 → "u v" 입력
python pick_by_camera.py --dry-run    # 로봇 없이 흐름 확인
python pick_by_camera.py              # 실기: 패널 [집기]/Space, Home, 관측 자세, 카메라 전환, 색 선택 버튼
python pick_by_camera.py --auto       # 검출되면 자동 집기
```

설정한 카메라 번호가 열리지 않으면 **카메라 선택 창**이 뜬다. 연결된 카메라마다 미리보기가 나오니 팔 카메라(HAMSTER_AI_UVC) 그림을 클릭하거나 번호 키를 누르면 된다. Windows 는 USB 를 다시 꽂거나 가상 카메라가 켜지면 번호를 바꾸므로 이 방식이 안전하다. 세 도구 모두 실행 중 **c 키**를 누르면 다음 번호의 카메라로 전환된다. 노트북 웹캠이나 가상 카메라가 먼저 잡혀도 팔 카메라가 나올 때까지 c 를 누르면 되고, 화면 하단에 현재 카메라 번호가 표시된다. 번호가 정해지면 `config.CAMERA_INDEX` 에 적어 두면 다음부터 바로 열린다. `examples/05_pick_and_place.py` 에도 같은 기능이 [카메라 전환] 버튼으로 있다.

### 14.4 반드시 맞춰야 할 값

- 현재 장비 기준 설정(2026-09-11 사진 확인): 카메라(HAMSTER_AI_UVC)는 **어깨 관절 옆 베이스 기둥에 장착**되어 관절 1 과만 같이 돌고 관절 2/3/4 로는 움직이지 않는다. 따라서 관절 1 = 0° 에서 관측하는 **고정 카메라**로 취급한다(`CAMERA_MOUNT="fixed"`, `ROTATE=None`, 화면 위 = 로봇 앞). 관측 자세 `OBSERVE_POSE` 는 카메라를 향하게 하는 자세가 아니라 **팔을 시야 밖으로 치우는 자세**이며 기본은 Zero(0,0,0,0). 카메라 번호는 USB 구성에 따라 바뀌므로 선택 창에서 고른다. 원본 640×360, 목표 물체는 초록 원통 블록(`COLOR_NAME="green"`). 카메라를 꽂은 직후 "Connecting camera..." 정지 화면이 나오면 내부 부팅 중이므로 30초쯤 기다리거나 다시 꽂는다.
- `SCAN_POSE`: 카메라가 테이블 위 물체를 보는 관측 자세. 카메라 장착 위치에 따라 관절 2, 3 을 조정한다. **보정 후에는 바꾸지 말 것** (바꾸면 `calibrate_camera.py` 다시). 보정 파일에 관측 자세가 기록되어 다르면 경고가 뜬다.
- `PICK_OFFSET_UV`: 팔 기준 고정 오프셋(u, v cm). `check_offset.py` 로 잰 값을 부호 반대로 넣는다. 서보를 쓰면 대부분 불필요.
- `SERVO_*`: 서보 허용 오차(px), 반복 횟수, 이득, 한 번 이동 상한, 시험 이동 거리. 진동하면 `SERVO_GAIN` 을 낮춘다.
- `COLOR_NAME`: 목표 물체 색(`COLOR_PRESETS` 의 blue/green/yellow/red). 보정 도구는 버튼, `pick_by_camera.py` 는 1~4 키로 실행 중 바꿀 수 있다.
- `GRASP_Z`: 그리퍼 끝 기준 높이. **물체 높이의 절반**이 기준이다 (3cm 블록 -> 1.5).
  기준점이 '닫힌 두 날이 만나는 점' 이라, 물체 높이를 그대로 주면 날 끝이 윗면에 걸려 못 집는다.
  재는 방법: `python examples/09_grasp_test.py A3 --cell E4 --find-z`
- `TILT_RULES`: 반경별 그리퍼 기울기와 hover 높이. 기본값은 7.2 절 도달 범위 표에서 도출한 (15.5 이상 수평 / 11 이상 45° / 그 미만 수직).
- `R_MIN_CM`(6), `R_MAX_CM`(26): 이 범위 밖이면 집기를 시도하지 않는다. 6 cm 안쪽은 베이스와 충돌 위험, 27 cm 밖은 관절 2 한계.
- `YAW_SIGN`, `YAW_KP`: 보정 파일이 없을 때의 구식 서보에서만 쓴다.

**인쇄용 보정 매트**: `docs/calibration_mat_A4.pdf` 를 A4 에 **실제 크기(100%, 페이지 맞춤 끄기)** 로 인쇄한다. B4 프린터가 있으면 `docs/calibration_mat_B4.pdf`(250×353 mm, 격자 좌우 ±11 cm·앞 25 cm)가 작업 영역 전체를 덮어 먼 쪽 블록 배치와 검증에 편하다(`python vision/make_calib_mat.py --paper B4`). 보정점 9개는 두 매트가 동일하다. 하단 10 cm 자를 실제 자로 재어 축척을 확인한 뒤, 회갈색 부분을 베이스 밑으로 밀어 넣어 갈색 십자를 관절 1 회전축 아래에 맞춘다. 베이스 옆면은 갈색 점선(좌우 폭 93 mm)에, 앞면은 회전축에서 앞면까지 잰 거리 D 의 v 눈금에 맞춘다. 원 안의 번호(①~⑨)가 보정 도구의 버튼 번호와 같다. 매트는 `vision/make_calib_mat.py` 로 다시 생성하고, 점 위치와 원 지름은 `config.CALIB_POINTS`, `CALIB_BLOCK_DIAMETER_MM` 로 바꾼다.

**집는 높이가 일정하게 어긋날 때**: roboid 는 손목에서 8 cm 앞을 "그리퍼 끝"으로 계산하는데 실제 집게가 무는 지점은 다르다. 수직 자세에서는 이 차이가 그대로 높이 오차가 된다(실측 약 4 cm). 그래서 [오프셋 측정]은 **집게로 블록을 문 자세**에서 눌러야 하며, 그때의 좌우/앞뒤 오프셋과 **집는 높이(grasp_z)** 를 기울기(수평/45°/수직)별로 `pick_calib.json` 에 저장한다. 집기 때 거리로 정해진 기울기의 값을 쓴다. 세 기울기 모두 한 번씩 측정해 두는 것을 권장한다(가까운 블록 = 수직, 중간 = 45°, 먼 블록 = 수평).

**권장 절차(클릭 보정 + 오프셋 1회 측정)**: 매트 십자를 클릭해 6점 이상 기록한 뒤, 블록을 아무 곳에 놓고 패널의 관절별 버튼(관절1 회전 / 2 어깨 / 3 팔꿈치 / 4 손목, ±5°·±1°)으로 집게 사이에 블록이 들어오는 자세를 만든 뒤 **[오프셋+높이 측정](B)** 를 누른다. 기울기(수평/45°/수직)는 그 순간의 관절 각도로 자동 판단해 저장된다. 로봇 좌표를 저장하고 팔이 관측 자세로 비킨 뒤 카메라 예측 좌표와 비교해 차이를 `config.PICK_OFFSET_UV` 에 자동 저장한다. 매트 정렬 오차와 그리퍼 팁 오프셋이 이 한 번으로 보정된다. 그 다음 [저장](S).

**로봇 기준 보정(고정 카메라, 매트 없이)**: `CAMERA_MOUNT = "fixed"` 이면 보정 도구가 로봇 기준 방식으로 시작한다. 블록을 카메라가 보이는 곳에 놓고, 패널의 관절별 버튼으로 그리퍼 중심이 블록 바로 위(집게 사이)에 오게 맞춘 뒤 [기록](R). 로봇 좌표를 저장하고 팔이 자동으로 관측 자세로 비킨 다음 블록 픽셀을 재서 짝짓는다. 블록을 옮겨 가며 4점 이상(작업 영역 네 귀퉁이 + 가운데) 기록하고 [저장]. 매트도, 마우스 클릭도 필요 없다. 집을 때는 팔을 비키고 한 번 재면 바로 베이스 좌표이므로 탐색·회전 보정·서보 단계가 없다.

**보정 도구(버튼 패널 UI, 팔 장착 카메라)**: `calibrate_camera.py` 를 실행하면 카메라 화면 옆에 ①~⑨ 버튼이 뜬다. 기본은 **마우스 클릭 방식**이다. 버튼을 누른 뒤 영상에서 매트의 해당 원 십자 중심을 클릭하면 기록되고, 다음 미기록 필수점이 자동 선택된다. 마우스를 올리면 3배 확대경이 떠서 십자 중심을 정확히 찍을 수 있다. 블록이 필요 없고, 원통 블록의 아래 변이 바닥 중심과 어긋나는 오차(먼 쪽에서 1 cm 이상)가 사라진다. M 키로 블록 검출 방식으로 바꿀 수 있다. 클릭 방식으로 보정하면 집기 때 물체 아래 변에 `OBJECT_RADIUS_CM`(기본 1.5) 을 더해 바닥 중심으로 환산한다. 그 아래 **목표 물체 색** 버튼(초록/파랑/노랑/빨강, F1~F4)으로 블록 색을 고른다. 매트는 어떤 색 검출기에도 잡히지 않도록 일부러 무채색으로 인쇄된다(초기 버전의 파란 원이 파랑 검출기에 잡혔던 문제 수정). 블록을 매트의 ① 원에 올리고 [① 0 9] 버튼을 클릭(또는 숫자 키 1)하면 자동 기록되고, 4점부터 재투영 오차가 실시간으로 표시된다. 파란 버튼 6개(필수)를 채우고 [저장](S). 회색 버튼 3개는 선택. 매트에 없는 위치는 [직접 입력](R)으로 콘솔에 `u v` 를 친다. 기존 파일이 있으면 불러와 개별 점만 다시 잴 수 있다.

**인쇄 축척이 안 맞을 때**: 프린터가 "페이지에 맞춤"으로 줄이면 10 cm 자가 9.5 cm 로 찍힌다(95%). 정석은 100% 재인쇄지만, 그대로 쓰려면 `python calibrate_camera.py --ruler-cm 9.5` 로 실행한다. 버튼 좌표에 0.95 를 곱해 기록하고 패널에 환산값이 표시된다. 베이스 앞면 정렬 눈금 D 도 5% 줄어 있지만 D≈5 cm 에서 오차 0.25 cm 라 그대로 맞춰도 된다.

인쇄 100% 설정: Acrobat 은 "실제 크기", Chrome/Edge 는 인쇄 대화상자 "배율 → 기본값(100)" 과 "페이지에 맞춤" 해제, 프린터 드라이버의 "용지에 맞춤" 도 끈다.

보정 절차 요령: 거리는 베이스 회전축 중심에서 블록 **중심**까지 잰다. 좌우(u)는 로봇이 볼 때 오른쪽이 +. 반드시 u≠0 인 점을 섞어야 하며(모두 정면 선 위면 변환이 안 구해짐), 저장 시 출력되는 재투영 오차가 0.5 cm 이하면 양호하다.

### 14.5 교재화 아이디어

1. 색 검출(HSV) → 2. 1축 시각 서보(비례 제어) → 3. 거리 보정(회귀) → 4. 역기구학 이동 → 5. YOLO 로 교체(`DETECTOR="yolo"`) → 6. 물체 종류별 내려놓는 위치 분류 → 7. 컨베이어 연동(`raccoon.conveyor()`).

roboidai 패키지에도 `Camera`, `ColorDetector`, `ObjectDetector`, `ArucoDetector` 등이 있어 대체 가능하다. 다만 tensorflow 의존성과 난독화된 소스 때문에 이 프로토타입은 OpenCV + ultralytics 로 작성했다.

---

## 15. API 치트시트

```python
from roboid import *
r = Raccoon()                      # Raccoon(index) / Raccoon(index, 'COMx')

# 관절
r.velocity(j, v) / r.velocity(v1, v2, v3, v4)      # -100~100
r.degree_to(j, deg, speed) / r.degree_to(d1, d2, d3, d4, speed, wait=True)
r.degree_by(j, delta, speed) / r.degree_by(d1, d2, d3, d4, speed)
r.can_degree_to(...) / r.can_degree_by(...)
r.stop(j=-1) / r.turn_off(j=-1) / r.is_moving() / r.precision_mode(on)
r.init_pose()                                       # Home

# 좌표 (cm)
r.xyz() / r.degree_to_xyz(d1, d2, d3, d4) / r.xyz_to_degree(x, y, z)
r.can_move_to(x, y, z) / r.move_to(x, y, z, speed=100, wait=True)
r.can_move_by(dx, dy, dz) / r.move_by(dx, dy, dz, speed=100)
r.end_effector("gripper"|"wrist") / r.end_effector_to(y, z) / r.unit("cm"|"inch")

# 그리퍼
r.open_gripper() / r.close_gripper() / r.gripper_state()
r.lock_horz() / r.lock_vert() / r.unlock()

# 센서/버튼
r.encoder(j|-1) / r.battery_state() / r.charge_state() / r.signal_strength()
r.teach_button() r.teach_clicked() r.teach_long_pressed()
r.play_button()  r.play_clicked()  r.play_long_pressed()
r.delete_button() r.delete_clicked() r.delete_long_pressed()

# 소리
r.tempo(bpm) / r.note("C4"[, beats]) / r.sound(id[, repeat]) / r.sound_until_done(id) / r.beep()

# 전역
wait(ms) wait_until(fn) wait_until_ready() when_do(c, d) while_do(c, d) parallel(f1, f2) set_executable(fn) scan() dispose()
r.reset() / r.dispose()
```
