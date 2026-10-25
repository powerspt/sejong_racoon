# -*- coding: utf-8 -*-
"""
라쿤봇 팔 제어 헬퍼
- RaccoonArm : roboid.Raccoon 을 감싸서 "관절 1 회전 / 반경 r 로 이동 / 집기 시퀀스" 를 제공
- DummyArm   : 로봇 없이 비전 부분만 시험할 때 쓰는 가짜 팔 (--dry-run)

roboid 1.7.11 기준으로 작성. 좌표 기준은 기본값(그리퍼 끝)을 사용합니다.
"""
import math
import time
from typing import Optional, Tuple

import config as cfg


def polar_to_xy(r_cm: float, yaw_deg: float) -> Tuple[float, float]:
    """베이스 회전축에서 반경 r, 관절 1 각도 yaw 인 지점의 (x, y).
    roboid 순기구학과 같은 부호 규약: θ1>0 이면 -x(왼쪽), 정면은 +y."""
    th = math.radians(yaw_deg)
    return -r_cm * math.sin(th), r_cm * math.cos(th)


def xy_to_polar(x: float, y: float) -> Tuple[float, float]:
    """(x, y) -> (r, yaw_deg)"""
    return math.hypot(x, y), math.degrees(math.atan2(-x, y))


def tilt_for(r_cm: float) -> Tuple[int, float]:
    """반경 r 에 맞는 (그리퍼 기울기 alpha°, hover 높이 cm). config.TILT_RULES 참조."""
    for r_min, alpha, hover in cfg.TILT_RULES:
        if r_cm >= r_min:
            return alpha, hover
    return cfg.TILT_RULES[-1][1], cfg.TILT_RULES[-1][2]


# 기울기를 바꾸기 전에 거쳐 가는 '세운' 자세의 어깨/팔꿈치 각도.
# J2 + J3 = -90 이므로 J4 = alpha 가 되어 계산이 깔끔하다.
# 이 자세에서는 기울기가 -90도여도 집게 끝이 8.9cm 높이에 있어 바닥에 닿지 않는다.
J2_SAFE, J3_SAFE = -30.0, -60.0


class RaccoonArm:
    def __init__(self, port: Optional[str] = None, precision: bool = False):
        from roboid import Raccoon, wait
        self._wait = wait
        # 주의: Raccoon('COM5') 처럼 문자열 하나만 주면 1.7.11 에서는 포트가 무시됩니다.
        #       반드시 Raccoon(0, 'COM5') 형태로 전달합니다.
        self.bot = Raccoon(0, port) if port else Raccoon()
        self.bot.unit("cm")
        self.bot.end_effector("gripper")   # xyz/move_to 의 기준점 = 그리퍼 끝 (기본값)
        # roboid 는 연결 실패해도 예외를 내지 않는다. Raccoon() 이 돌아와도
        # 아직 연결되지 않았을 수 있으므로 is_connected() 를 폴링한다.
        t0 = time.time()
        while time.time() - t0 < 10.0 and not self.bot.is_connected():
            self._wait(300)
        if not self.bot.is_connected():
            self.bot.dispose()
            raise ConnectionError(
                "로봇이 연결되지 않았습니다 (동글 미인식 또는 로봇 전원 꺼짐).\n"
                "  · USB to BLE 동글이 꽂혀 있는지 (노트북 내장 블루투스로는 안 됩니다)\n"
                "  · 로봇 전원과 배터리\n"
                "  · 포트 직접 지정: RaccoonArm(port='COM26')\n"
                "  자세한 진단은 examples/01_connect_test.py 를 실행하세요."
            )
        self._wait(500)
        # 공식 API. 켜면 이동 후 같은 목표를 한 번 더 보내 잔여 오차를 줄인다(시간 약 2배)
        self.bot.precision_mode(precision)
        self.current_tilt = 0

    # ── 기본 상태 ──
    def yaw(self) -> float:
        return float(self.bot.encoder(1))

    def joints(self):
        return tuple(self.bot.encoder(-1))

    def xyz(self):
        return self.bot.xyz()

    def battery(self) -> int:
        return self.bot.battery_state()

    def precision(self, on: bool):
        """정밀 모드. 켜면 반복정밀도가 좋아지고 이동 시간이 약 2배가 된다 (공식 API)."""
        self.bot.precision_mode(on)

    # ── 자세 ──
    def init_pose(self):
        """공식 init_pose(): unlock + 그리퍼 열기 + Home.
        ⚠️ 그리퍼를 열므로 물체를 쥔 상태에서 부르면 놓친다. 시작/종료용."""
        self.bot.init_pose()

    def home(self, speed: int = cfg.SCAN_SPEED):
        self.bot.unlock()
        self.bot.degree_to(*cfg.HOME_POSE, speed)

    def scan_pose(self, keep_yaw: bool = True, speed: int = cfg.SCAN_SPEED):
        """관측 자세로 이동. keep_yaw=True 면 관절 1 은 현재 값을 유지."""
        j1 = self.yaw() if keep_yaw else cfg.SCAN_POSE[0]
        self.bot.lock_horz()                       # 그리퍼(=카메라)를 수평으로 고정
        self.bot.degree_to(j1, cfg.SCAN_POSE[1], cfg.SCAN_POSE[2], cfg.SCAN_POSE[3], speed)

    # ── 관절 1 (시각 서보용) ──
    def yaw_to(self, deg: float, speed: int = cfg.SERVO_SPEED):
        deg = max(-cfg.YAW_LIMIT, min(cfg.YAW_LIMIT, deg))
        self.bot.degree_to(1, deg, speed)

    def yaw_by(self, delta: float, speed: int = cfg.SERVO_SPEED):
        self.yaw_to(self.yaw() + delta, speed)

    # ── 좌표 이동 ──
    def can_reach(self, x, y, z) -> bool:
        return bool(self.bot.can_move_to(x, y, z))

    def move_xyz(self, x, y, z, speed: int = cfg.APPROACH_SPEED) -> bool:
        if not self.can_reach(x, y, z):
            print(f"[arm] 도달 불가: ({x:.1f}, {y:.1f}, {z:.1f})")
            return False
        self.bot.move_to(x, y, z, speed)
        return True

    def move_polar(self, r_cm: float, yaw_deg: float, z: float, speed: int = cfg.APPROACH_SPEED) -> bool:
        x, y = polar_to_xy(r_cm, yaw_deg)
        return self.move_xyz(x, y, z, speed)

    # ── 그리퍼 기울기 ──
    def _raise_before_tilt(self, cur_alpha: float):
        """기울기를 바꾸기 전에 팔을 세운다. 지금 기울기는 그대로 둔 채 올리기만 한다."""
        j1 = float(self.joints()[0])
        self.bot.unlock()
        if self.bot.can_degree_to(j1, J2_SAFE, J3_SAFE, cur_alpha):
            self.bot.degree_to(j1, J2_SAFE, J3_SAFE, cur_alpha)
            self._wait(1000)
        else:
            print("[arm] 경유 자세가 한계를 넘어 그냥 돌립니다 - 집게가 바닥에 닿는지 보세요")

    def set_tilt(self, alpha: float, speed: int = cfg.APPROACH_SPEED):
        """그리퍼 기울기 설정. alpha 0 = 수평(lock_horz), -90 = 수직 아래(lock_vert), 그 사이는 관절 4 직접 설정.
        move_to 는 현재 손목 방향(관절 2+3+4)을 유지하므로, 먼저 기울기를 잡아 두면 이후 좌표 이동 내내 유지됩니다.

        ⚠️ 낮은 곳에서 그냥 손목을 돌리면 집게가 바닥을 긁는다.
           집게 끝은 손목에서 8cm 떨어져 있어서, 손목을 제자리에 두고 기울기만 바꾸면
           끝이 원을 그리며 내려온다. 0도 -> -90도 면 **7.4cm** 내려간다.
           Home(끝 높이 8.84cm)에서 -90도로 바꾸면 끝이 1.4cm 까지 내려와 책상을 긁는다.
           그래서 돌리기 전에 먼저 팔을 세운다. 세운 자세에서는 -90도라도 끝이 8.9cm 에 있다.
        """
        cur = self.current_tilt
        try:
            _j1, j2, j3, j4 = (float(v) for v in self.joints())
            cur = j2 + j3 + j4 + 90
        except Exception:       # 연결이 불안정해도 기울기 설정 자체는 진행한다
            pass
        if abs(cur - alpha) < 1.0:
            self.current_tilt = alpha
            return True
        self._raise_before_tilt(cur)

        if alpha == 0:
            self.bot.lock_horz(); self.current_tilt = 0
            return True
        if alpha == -90:
            self.bot.lock_vert(); self.current_tilt = -90
            return True
        self.bot.unlock()
        _, j2, j3, _ = self.joints()
        j4 = alpha - 90 - j2 - j3
        if not self.bot.can_degree_to(4, j4):
            print(f"[arm] 기울기 {alpha}° 불가 (관절4 {j4:.0f}° 범위 밖)")
            return False
        self.bot.degree_to(4, j4, speed)
        self.current_tilt = alpha
        return True

    # ── 그리퍼 ──
    def open(self):
        self.bot.open_gripper()
        self._wait(cfg.GRIPPER_SETTLE_MS)

    def close(self):
        self.bot.close_gripper()
        self._wait(cfg.GRIPPER_SETTLE_MS)

    # ── 집기 시퀀스 ──
    def pick_and_place(self, r_cm: float, yaw_deg: float) -> bool:
        """반경 r, 관절1 각도 yaw 에 놓인 물체를 집어 DROP_XYZ 에 내려놓습니다."""
        x, y = polar_to_xy(r_cm, yaw_deg)
        print(f"[arm] 목표: r={r_cm:.1f}cm yaw={yaw_deg:.1f}° -> (x={x:.1f}, y={y:.1f})")
        return self.pick_and_place_xy(x, y)

    def pick_and_place_xy(self, x: float, y: float) -> bool:
        """베이스 좌표 (x, y) 에 놓인 물체를 집어 DROP_XYZ 에 내려놓습니다."""
        r_cm = math.hypot(x, y)
        if not (cfg.R_MIN_CM <= r_cm <= cfg.R_MAX_CM):
            print(f"[arm] 반경 {r_cm:.1f}cm 가 허용 범위({cfg.R_MIN_CM}~{cfg.R_MAX_CM}) 밖입니다.")
            return False
        alpha, hover = tilt_for(r_cm)
        print(f"[arm] r={r_cm:.1f}cm -> 그리퍼 기울기 {alpha}°, hover {hover}cm")
        if not self.approach(x, y, alpha, hover):
            return False
        if not self.grasp_here(x, y, hover):
            return False
        return self.place_and_home()

    def approach(self, x, y, alpha, hover) -> bool:
        """그리퍼 열고 기울기 맞춘 뒤 (x, y) 위 hover 높이로 이동"""
        self.open()
        if not self.set_tilt(alpha):
            return False
        return self.move_xyz(x, y, hover, cfg.APPROACH_SPEED)

    def grasp_here(self, x, y, hover, grasp_z=None) -> bool:
        """(x, y) 에서 grasp_z(기본 GRASP_Z) 까지 내려 집고 hover 로 들어올림"""
        gz = cfg.GRASP_Z if grasp_z is None else grasp_z
        if not self.move_xyz(x, y, gz, 30):
            return False
        self.close()
        self.bot.beep()
        return self.move_xyz(x, y, hover, cfg.LIFT_SPEED)

    def place_and_home(self) -> bool:
        """DROP_XYZ 에 내려놓고 Home"""
        dx, dy, dz = cfg.DROP_XYZ
        d_alpha, d_hover = tilt_for(math.hypot(dx, dy))
        if d_alpha != self.current_tilt:
            self.set_tilt(d_alpha)
        if not self.move_xyz(dx, dy, d_hover, cfg.LIFT_SPEED):
            return False
        self.move_xyz(dx, dy, dz, 30)
        self.open()
        self.move_xyz(dx, dy, d_hover, cfg.LIFT_SPEED)
        self.home()
        return True

    # ── 종료 ──
    def stop(self):
        try:
            self.bot.stop()
        except Exception:
            pass

    def close_connection(self):
        try:
            self.bot.stop()
            self.bot.dispose()
        except Exception:
            pass


class DummyArm:
    """로봇 없이 프로그램 흐름만 확인하는 가짜 팔. 모든 동작을 콘솔에 출력합니다."""

    def __init__(self, port: Optional[str] = None, precision: bool = False):
        self._yaw = 0.0
        print("[dummy] 로봇 없이 실행합니다 (dry-run)")

    def yaw(self): return self._yaw
    def joints(self): return (self._yaw, *cfg.SCAN_POSE[1:])
    def xyz(self): return tuple(self._pos)
    def battery(self): return 3
    def precision(self, on): print(f"[dummy] precision_mode {on}")
    def init_pose(self): print("[dummy] init_pose")
    def home(self, speed=0): print("[dummy] home")
    def scan_pose(self, keep_yaw=True, speed=0): print("[dummy] scan pose")

    def yaw_to(self, deg, speed=0):
        self._yaw = max(-cfg.YAW_LIMIT, min(cfg.YAW_LIMIT, deg))
        print(f"[dummy] yaw_to {self._yaw:+.1f}°")
        time.sleep(0.2)

    def yaw_by(self, delta, speed=0): self.yaw_to(self._yaw + delta)
    def can_reach(self, x, y, z): return True
    def move_xyz(self, x, y, z, speed=0):
        print(f"[dummy] move_to ({x:.1f}, {y:.1f}, {z:.1f})"); self._pos = [x, y, z]; return True
    def move_polar(self, r, yaw, z, speed=0):
        return self.move_xyz(*polar_to_xy(r, yaw), z)
    def open(self): print("[dummy] open gripper")
    def close(self): print("[dummy] close gripper")
    def set_tilt(self, alpha, speed=0): print(f"[dummy] tilt {alpha}"); self.current_tilt = alpha; return True
    current_tilt = 0
    _pos = [0.0, 14.0, 10.0]
    def approach(self, x, y, alpha, hover): self.set_tilt(alpha); return self.move_xyz(x, y, hover)
    def grasp_here(self, x, y, hover, grasp_z=None): print(f"[dummy] grasp at ({x:.1f},{y:.1f}) z={grasp_z}"); return True
    def place_and_home(self): print("[dummy] place & home"); return True

    def pick_and_place(self, r_cm, yaw_deg):
        return self.pick_and_place_xy(*polar_to_xy(r_cm, yaw_deg))

    def pick_and_place_xy(self, x, y):
        r = math.hypot(x, y); alpha, hover = tilt_for(r)
        print(f"[dummy] PICK ({x:.1f},{y:.1f}) r={r:.1f} tilt={alpha} hover={hover} / drop {cfg.DROP_XYZ}")
        return True

    def stop(self): pass
    def close_connection(self): print("[dummy] disconnect")


def make_arm(dry_run: bool, port: Optional[str] = None, precision: bool = False):
    return DummyArm(port, precision) if dry_run else RaccoonArm(port, precision)
