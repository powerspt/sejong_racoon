# -*- coding: utf-8 -*-
"""주제 9 — 음성 명령과 방어 (골격 · 스위치만 바꾼다)

    pip install vosk sounddevice
    python lessons/09_음성명령_틀.py
    (실행하면 로봇 연결 여부를 묻는다 — 그냥 Enter = 인식만, 로봇 없이)

방어 장치 네 가지는 전부 완성되어 있다. 여러분이 할 일은 **스위치를 바꿔 조합을
만들고, 비명령 발화 20개로 오작동률을 재는 것**이다. 코드를 새로 짜지 않는다.

    USE_LENGTH  발화 길이 제한 — 인식 단어가 2개를 넘으면 버린다
    USE_WAKE    호출어 — "라쿤" 뒤의 발화만 명령으로
    USE_CONFIRM 복창 확인 — 로봇이 되묻고 Enter 를 눌러야 실행

단, "멈춰" 는 어떤 방어도 거치지 않는다 — 수업에서 그 이유를 다룬다.
※ 교사 사전 실행 필수. 모델 폴더(vosk-model-small-ko-0.22)가 옆에 있어야 한다.
"""
import json
import queue
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ───────── 설정 — 여기만 바꿔 보세요 ─────────
USE_LENGTH = False      # [조합 실험] 발화 길이 제한
USE_WAKE = False        # [조합 실험] 호출어 ("라쿤")
USE_CONFIRM = False     # [조합 실험] 복창 확인
WAKE_WORD = "라쿤"
MAX_WORDS = 2
# ─────────────────────────────────────────────

COMMANDS = ["집어", "놓아", "멈춰", "집으로", "왼쪽", "오른쪽", "앞으로", "뒤로"]


def defend(text):
    """방어 사슬. 통과하면 명령 문자열, 버리면 (None, 이유)."""
    words = text.split()
    if not words:
        return None, "빈 발화"
    if "멈춰" in words:                       # 정지는 무조건 통과 (fail-safe)
        return "멈춰", "정지 — 방어 없이 즉시"
    if USE_WAKE:
        if words[0] != WAKE_WORD:
            return None, f"호출어 '{WAKE_WORD}' 없음"
        words = words[1:]
    if USE_LENGTH and len(words) > MAX_WORDS:
        return None, f"{len(words)}단어 — 길이 초과"
    hits = [w for w in words if w in COMMANDS]
    if not hits:
        return None, "명령 어휘 없음"
    cmd = hits[0]
    if USE_CONFIRM:
        ok = input(f'  로봇: "{cmd}" 맞나요? (Enter=실행 / 아무 글자=취소) ')
        if ok.strip():
            return None, "복창에서 취소"
    return cmd, "통과"


def act(bot, cmd):
    """명령 -> 동작. 완성되어 있다."""
    if bot is None:
        print(f"  [가상] 실행: {cmd}")
        return
    from roboid import wait
    step = {"왼쪽": (-3, 0), "오른쪽": (3, 0), "앞으로": (0, 3), "뒤로": (0, -3)}
    if cmd == "멈춰":
        bot.stop()
    elif cmd == "집으로":
        bot.degree_to(0, -10, -140, 60)
    elif cmd == "집어":
        bot.close_gripper(); wait(700)
    elif cmd == "놓아":
        bot.open_gripper(); wait(500)
    elif cmd in step:
        x, y, z = bot.xyz()
        dx, dy = step[cmd]
        if bot.can_move_to(x + dx, y + dy, z):
            bot.move_to(x + dx, y + dy, z, 40)
        else:
            print("  (작업 공간 밖 — 무시)")


def main():
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer

    bot = None
    ans = input("로봇을 연결했나요? [y = 로봇도 움직임 / 그냥 Enter = 인식만]: ").strip().lower()
    if ans in ("y", "yes", "ㅛ"):
        from roboid import Raccoon, wait
        bot = Raccoon()
        while not bot.is_connected():
            wait(100)

    model = Model("vosk-model-small-ko-0.22")
    grammar = json.dumps(COMMANDS + [WAKE_WORD, "[unk]"], ensure_ascii=False)
    rec = KaldiRecognizer(model, 16000, grammar)
    q = queue.Queue()

    def cb(data, frames, t, status):
        q.put(bytes(data))

    n_total = n_fired = 0
    print(f"방어: 길이={USE_LENGTH} 호출어={USE_WAKE} 복창={USE_CONFIRM}")
    print("말해 보세요. 비명령 발화 20개로 오작동률을 잽니다. (Ctrl+C 종료)\n")
    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                           dtype="int16", channels=1, callback=cb):
        try:
            while True:
                if rec.AcceptWaveform(q.get()):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if not text:
                        continue
                    n_total += 1
                    cmd, why = defend(text)
                    mark = f"실행 {cmd}" if cmd else f"버림({why})"
                    if cmd:
                        n_fired += 1
                        act(bot, cmd)
                    print(f'[{n_total:2}] 들림: "{text}"  ->  {mark}')
        except KeyboardInterrupt:
            pass
    print(f"\n발화 {n_total}건 중 실행 {n_fired}건 — 기록 양식에 옮겨 적으세요.")
    if bot is not None:
        bot.degree_to(0, -10, -140, 60)
        bot.dispose()


if __name__ == "__main__":
    main()
