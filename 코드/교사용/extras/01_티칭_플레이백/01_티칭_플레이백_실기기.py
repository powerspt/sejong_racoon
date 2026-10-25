# -*- coding: utf-8 -*-
"""[콘텐츠 ①] Teach & Playback · 실기기 — 코드 없이 가르치고, 리스트로 되돌아본다

    python 01_티칭_플레이백_실기기.py

**이 활동은 실기기 전용이다.** 손으로 팔을 직접 움직여 가르치는 것이 전부라
가상으로는 성립하지 않는다 — 로봇이 없으면 01_티칭_플레이백_가상.py 로
'기록 → 역재생' 로직만 먼저 본다.

(화면 버튼 GUI 가 필요하면 examples/06_teach_playback_buttons.py 를 쓴다.
 이 파일은 CLI 최소판 — '자세 목록 = 리스트' 라는 자료구조 관점에 집중한다.)

하는 법
  turn_off() → 팔이 흐물흐물 → 손으로 자세를 잡고 Enter → 한 줄 쌓인다 (append)
  (unlock() 은 힘빼기가 아니다 — 수평/수직 잠금 해제용. 힘빼기는 turn_off())
  p = 재생 · r = 역재생 · s/l = JSON 저장/불러오기 · q = 종료

시작하기 전에
    1) 팔 주변 30cm 를 비운다
    2) 힘을 빼면 팔이 떨어진다 — **한 손으로 받치면서** 자세를 잡는다
    3) 블록 하나를 책상에 놓아 두면 집기→옮기기까지 가르쳐 볼 수 있다

핵심 포인트
  - 가르친 동작의 정체는 '각도 4개 + 집게 상태'의 리스트다.
  - 역재생(r) = 리스트를 뒤에서부터 — 스택(LIFO)을 몸으로 보는 순간.
  - 산업용 로봇의 '티칭 펜던트'가 하는 일이 정확히 이것이다.
"""
import json
import os
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ───────── 설정 — 여기만 바꿔 보세요 ─────────
# [레벨1] 코드가 아니라 데이터를 고친다 — 저장된 poses.json 을 메모장으로 열어
#         각도 숫자 하나를 바꾸고 다시 불러와 재생. "동작의 정체 = 숫자 리스트".
# ─────────────────────────────────────────────
POSES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poses.json")


def main():
    print("[실기기] 팔 주변 30cm 를 비우세요. 힘을 빼면 팔이 떨어집니다 — 받치세요.")
    from roboid import Raccoon, wait
    bot = Raccoon()
    while not bot.is_connected():
        wait(100)
    poses = []
    grip = "open"
    bot.open_gripper()
    print("\n[Enter]=자세 저장  o/c=집게 열/닫  p=재생  r=역재생  s=저장  l=불러오기  q=종료")
    bot.turn_off()                     # 모터 힘 빼기 — 손으로 움직일 수 있다
    print("팔의 힘을 뺐습니다. 떨어지지 않게 한 손으로 받치면서, 자세를 잡고 Enter.")

    def play(seq):
        for i, p in enumerate(seq, 1):
            print(f"  재생 {i}/{len(seq)} {p['joints']}")
            bot.degree_to(*p["joints"], 40)
            (bot.open_gripper if p["grip"] == "open" else bot.close_gripper)()
            wait(700)
        bot.turn_off()
        print("끝 — 다시 힘을 뺐습니다. (팔을 받치세요)")

    while True:
        cmd = input("> ").strip().lower()
        if cmd == "":
            j = tuple(round(v, 1) for v in bot.encoder(-1))
            poses.append({"joints": j, "grip": grip})
            print(f"  저장 {len(poses)}번째: {j} (집게 {grip})")
        elif cmd == "o":
            grip = "open"; bot.open_gripper()
        elif cmd == "c":
            grip = "close"; bot.close_gripper()
        elif cmd == "p" and poses:
            play(poses)
        elif cmd == "r" and poses:
            play(list(reversed(poses)))   # ← 스택처럼 뒤에서부터
        elif cmd == "s":
            json.dump(poses, open(POSES_FILE, "w", encoding="utf-8"))
            print(f"  {POSES_FILE} 저장 ({len(poses)}자세)")
        elif cmd == "l":
            poses = json.load(open(POSES_FILE, encoding="utf-8"))
            poses = [{"joints": tuple(p["joints"]), "grip": p["grip"]} for p in poses]
            print(f"  불러옴 ({len(poses)}자세)")
        elif cmd == "q":
            break
    bot.degree_to(0, -10, -140, 60)
    bot.dispose()


if __name__ == "__main__":
    main()
