# -*- coding: utf-8 -*-
"""[콘텐츠 ①] Teach & Playback · 가상 — 기록과 역재생을 화면으로

    python 01_티칭_플레이백_가상.py

**티칭은 손으로 팔을 직접 움직이는 활동이라 본래 로봇이 있어야 한다.**
로봇이 없을 때 이 파일로 '기록 → 재생 → 역재생' 이 무엇인지만 먼저 본다.
진짜로 가르치는 것은 01_티칭_플레이백_실기기.py 다.

핵심 포인트
  - 가르친 동작의 정체는 '각도 4개 + 집게 상태'의 리스트다.
  - 역재생(r) = 리스트를 뒤에서부터 — 스택(LIFO)을 몸으로 보는 순간.
  - 산업용 로봇의 '티칭 펜던트'가 하는 일이 정확히 이것이다.

이 파일 하나만 있으면 돌아간다 (robot_helpers.py 도 필요 없다).
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ───────── 설정 — 여기만 바꿔 보세요 ─────────
자세들 = [(0, 0, 0, 0), (0, -30, -60, 0), (0, -10, -140, 60)]
#   손으로 가르쳤다고 **치는** 자세 세 개. 숫자를 바꿔 보면 재생 순서가 바뀐다.
# ─────────────────────────────────────────────


def record_logic_selftest():
    """기록은 append, 역재생은 reversed — 그게 전부다."""
    poses = [{"joints": p, "grip": "open"} for p in 자세들]
    forward = [p["joints"] for p in poses]
    backward = [p["joints"] for p in reversed(poses)]
    assert backward == forward[::-1]
    assert backward[0] == 자세들[-1], "역재생은 마지막 자세부터"
    print("selftest OK — 기록은 append, 역재생은 reversed (스택)")
    return poses


def 보여주기(poses, 거꾸로=False):
    seq = list(reversed(poses)) if 거꾸로 else poses
    print(f"\n[{'역재생' if 거꾸로 else '재생'}] {len(seq)}자세")
    for i, p in enumerate(seq, 1):
        print(f"  {i}/{len(seq)}  관절 {p['joints']}  집게 {p['grip']}")


def main(arm=None):
    """arm 은 안 쓴다 — 실기기 쪽과 부르는 꼴을 맞추려고 받아 둔다."""
    print("[가상] Teach & Playback — 손으로 가르친 자세는 리스트가 된다")
    print("  진짜로 가르치려면 01_티칭_플레이백_실기기.py 로 돌린다.")
    print("\n손으로 가르친 자세가 리스트에 이렇게 쌓인다:")
    poses = record_logic_selftest()
    for i, p in enumerate(poses, 1):
        print(f"  저장 {i}번째: {p['joints']} (집게 {p['grip']})")
    보여주기(poses)
    보여주기(poses, 거꾸로=True)
    print("\n[질문] 역재생은 왜 공짜일까?")
    print("       — 동작의 정체가 리스트라서, 뒤에서부터 읽기만 하면 된다.")
    print("\n[해보기] 맨 위 자세들 에 네 번째 자세를 더하면 재생이 어떻게 달라지나?")
    print("[다음]   로봇이 있으면 01_티칭_플레이백_실기기.py 로 직접 가르친다.")


if __name__ == "__main__":
    main()
