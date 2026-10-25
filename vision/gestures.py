# -*- coding: utf-8 -*-
"""
주제 8 · 2층 [의도] — 손 모양의 '흐름' 을 명령으로 바꾼다.

왜 이 층이 필요한가
    카메라는 1초에 30장을 찍는다. 주먹을 1초 쥐고 있으면 "집어!" 가 30번 나간다.
    로봇은 밀린 명령을 몇 초 뒤까지 수행하며 덜컥거린다.
    그래서 '지금 무슨 모양인가(상태)' 를 '무엇을 하라는가(사건)' 로 바꿔 주는 층을 둔다.

규칙 세 가지 (config.py 에서 숫자를 바꿀 수 있다)
    STABLE_FRAMES  같은 모양이 N번 연속 보여야 '확정' 한다        — 바꾸는 중간의 쓰레기 라벨 거르기
    HOLD_FRAMES    큰 동작(홈 복귀)은 N번 유지해야 발행한다        — 실수 방지
    LOST_FRAMES    손이 N번 안 보이면 바로 STOP                   — 인식 실패의 기본값은 정지

혼자 확인해 보기 (카메라도 로봇도 없이)
    python gestures.py
"""
import sys as _sys
for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dataclasses import dataclass
from typing import List, Optional, Tuple

import config as cfg
from hand_tracker import HandSignal

# 명령 이름을 화면에 한글로 보여 줄 때 쓴다
COMMAND_KO = {
    "STOP": "정지",
    "GRIP_CLOSE": "집기",
    "GRIP_OPEN": "놓기",
    "HOME": "홈 복귀",
    "OBSERVE": "관측 자세",
    "TRACK_ON": "조종 시작",
    "TRACK_OFF": "조종 해제",
    "JOG": "따라가기",
}


@dataclass
class Command:
    """의도층이 동작층에 넘기는 유일한 값."""
    kind: str                  # STOP GRIP_CLOSE GRIP_OPEN HOME OBSERVE TRACK_ON TRACK_OFF JOG
    dx: float = 0.0            # JOG 일 때 — 앵커에서 좌우로 이동할 거리(cm)
    dy: float = 0.0            # JOG 일 때 — 앵커에서 앞뒤로 이동할 거리(cm)
    dz: float = 0.0

    @property
    def urgent(self) -> bool:
        """밀려도 버리면 안 되는 명령.

        JOG 는 매 프레임 새로 나오므로 밀린 것을 버려도 된다 (오히려 버려야 안전하다).
        나머지는 한 번뿐인 사건이라 버리면 동작이 통째로 사라진다.
        """
        return self.kind != "JOG"

    @property
    def ko(self) -> str:
        return COMMAND_KO.get(self.kind, self.kind)

    def __str__(self):
        if self.kind == "JOG":
            return f"JOG(dx={self.dx:+.1f}, dy={self.dy:+.1f})"
        return self.kind


class GestureIntent:
    """HandSignal 을 계속 넣으면 필요한 순간에만 Command 를 돌려준다."""

    def __init__(self, gesture_map=None, stable=None, hold=None, lost=None,
                 gain_x=None, gain_y=None, deadzone=None):
        self.map = dict(gesture_map or cfg.GESTURE_MAP)
        self.stable = cfg.STABLE_FRAMES if stable is None else stable
        self.hold = cfg.HOLD_FRAMES if hold is None else hold
        self.lost = cfg.LOST_FRAMES if lost is None else lost
        self.gain_x = cfg.TRACK_GAIN_X if gain_x is None else gain_x
        self.gain_y = cfg.TRACK_GAIN_Y if gain_y is None else gain_y
        self.deadzone = cfg.TRACK_DEADZONE if deadzone is None else deadzone
        self.reset()

    def reset(self):
        self.pending = "None"          # 지금 들어오는 모양
        self.pending_count = 0         # 그 모양이 몇 번 연속인가
        self.confirmed = "None"        # 확정된 모양
        self.hold_count = 0
        self.hold_fired = False
        self.lost_count = 0
        self.tracking = False
        self.anchor: Optional[Tuple[float, float]] = None   # 조종 시작 순간의 손 위치
        self.last: Optional[Command] = None

    # ── 화면 표시용 ──
    @property
    def stable_ratio(self) -> float:
        """확정까지 얼마나 왔나 (0~1)"""
        return min(1.0, self.pending_count / float(self.stable)) if self.stable else 1.0

    @property
    def hold_ratio(self) -> float:
        """길게 누르기 진행률 (0~1). 해당 없으면 0"""
        if self._mode(self.confirmed) != "hold" or self.hold_fired:
            return 0.0
        return min(1.0, self.hold_count / float(self.hold)) if self.hold else 1.0

    def _mode(self, label: str) -> Optional[str]:
        entry = self.map.get(label)
        return entry[1] if entry else None

    def _kind(self, label: str) -> Optional[str]:
        entry = self.map.get(label)
        return entry[0] if entry else None

    # ── 본체 ──
    def update(self, sig: HandSignal) -> List[Command]:
        """프레임마다 한 번 부른다. 이번 프레임에 발행할 명령 목록을 돌려준다."""
        out: List[Command] = []

        # (1) 손이 안 보인다 — 인식 실패의 기본값은 정지
        if not sig.found:
            self.lost_count += 1
            if self.lost_count == self.lost:        # 딱 한 번만 발행
                if self.tracking:
                    self.tracking = False
                    self.anchor = None
                    out.append(Command("TRACK_OFF"))
                out.append(Command("STOP"))
                self.pending, self.pending_count = "None", 0
                self.confirmed = "None"
                self.hold_count, self.hold_fired = 0, False
            self.last = out[-1] if out else self.last
            return out
        self.lost_count = 0

        # (2) 같은 모양이 몇 번 연속인지 센다
        label = sig.gesture or "None"
        if label == self.pending:
            self.pending_count += 1
        else:
            self.pending, self.pending_count = label, 1

        # (3) 충분히 연속되면 '확정' 으로 올린다
        if self.pending_count >= self.stable and self.pending != self.confirmed:
            if self.tracking:                       # 조종 중이었다면 먼저 푼다
                self.tracking = False
                self.anchor = None
                out.append(Command("TRACK_OFF"))
            self.confirmed = self.pending
            self.hold_count, self.hold_fired = 0, False

            mode = self._mode(self.confirmed)
            kind = self._kind(self.confirmed)
            if mode == "edge" and kind:             # 바뀌는 순간 한 번만
                out.append(Command(kind))
            elif mode == "level" and kind:          # 유지하는 동안 계속
                self.tracking = True
                self.anchor = (sig.palm_x, sig.palm_y)
                out.append(Command(kind))

        # (4) 확정된 모양을 유지하는 동안 할 일
        mode = self._mode(self.confirmed)
        if mode == "hold":
            self.hold_count += 1
            if not self.hold_fired and self.hold_count >= self.hold:
                self.hold_fired = True
                out.append(Command(self._kind(self.confirmed)))
        elif mode == "level" and self.tracking and self.anchor:
            ax, ay = self.anchor
            ddx, ddy = sig.palm_x - ax, ay - sig.palm_y      # 손을 위로 = 팔은 앞으로
            if abs(ddx) < self.deadzone:
                ddx = 0.0
            if abs(ddy) < self.deadzone:
                ddy = 0.0
            out.append(Command("JOG", dx=ddx * self.gain_x, dy=ddy * self.gain_y))

        if out:
            self.last = out[-1]
        return out


# ───────────────────────── 혼자 확인하기 ─────────────────────────
def _fake(label, x=0.5, y=0.5, found=True):
    return HandSignal(found=found, gesture=label, score=0.9, palm_x=x, palm_y=y)


def _script():
    """카메라 대신 '손 모양 대본' 을 흘려보내 규칙이 맞는지 본다."""
    intent = GestureIntent()
    print(f"설정  STABLE={intent.stable}  HOLD={intent.hold}  LOST={intent.lost}\n")

    def run(title, frames):
        print(f"── {title}")
        intent.reset()                 # 장면마다 처음 상태에서 시작한다
        fired = []
        for i, sig in enumerate(frames):
            for c in intent.update(sig):
                fired.append(c)
                print(f"   {i + 1:3d}프레임  ->  {c}  ({c.ko})")
        if not fired:
            print("       (명령 없음)")
        print()
        return fired

    ok = True

    # 1) 주먹을 1초(30프레임) 쥐고 있어도 '집기' 는 한 번만
    f = run("주먹 30프레임 — 집기는 한 번만 나와야 한다",
            [_fake("Closed_Fist") for _ in range(30)])
    ok &= [c.kind for c in f] == ["GRIP_CLOSE"]

    # 2) 손을 풀었다가 다시 쥐면 한 번 더
    f = run("손바닥 10 -> 주먹 10 — 정지 한 번, 집기 한 번",
            [_fake("Open_Palm") for _ in range(10)] + [_fake("Closed_Fist") for _ in range(10)])
    ok &= [c.kind for c in f] == ["STOP", "GRIP_CLOSE"]

    # 3) 짧게 스쳐 간 모양(3프레임)은 무시된다
    f = run("브이를 3프레임만 — STABLE 미만이라 무시",
            [_fake("Victory") for _ in range(3)] + [_fake("Closed_Fist") for _ in range(10)])
    ok &= [c.kind for c in f] == ["GRIP_CLOSE"]

    # 4) 엄지 위는 길게 유지해야 홈 복귀
    f = run("엄지 위 20프레임 — HOLD 미만이라 아직 안 나간다",
            [_fake("Thumb_Up") for _ in range(20)])
    ok &= [c.kind for c in f] == []
    f = run("엄지 위 60프레임 — 이제 홈 복귀 한 번",
            [_fake("Thumb_Up") for _ in range(60)])
    ok &= [c.kind for c in f] == ["HOME"]

    # 5) 검지를 세우면 조종 시작, 손을 움직인 만큼 따라간다
    frames = [_fake("Pointing_Up", 0.50, 0.50) for _ in range(6)]
    frames += [_fake("Pointing_Up", 0.60, 0.40) for _ in range(2)]      # 오른쪽 위로
    f = run("검지 유지 — 조종 시작 뒤 매 프레임 따라가기",
            frames)
    kinds = [c.kind for c in f]
    ok &= kinds[0] == "TRACK_ON" and set(kinds[1:]) == {"JOG"}
    jog = f[-1]
    ok &= abs(jog.dx - 0.10 * cfg.TRACK_GAIN_X) < 0.01
    ok &= abs(jog.dy - 0.10 * cfg.TRACK_GAIN_Y) < 0.01

    # 6) 손이 사라지면 조종 해제 + 정지
    f = run("손이 화면 밖으로 — 조종 해제 + 정지",
            [_fake("Pointing_Up", 0.5, 0.5) for _ in range(6)]
            + [HandSignal(found=False) for _ in range(5)])
    ok &= [c.kind for c in f][-2:] == ["TRACK_OFF", "STOP"]

    print("결과:", "전부 통과" if ok else "⚠️ 기대와 다른 결과가 있습니다")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_script())
