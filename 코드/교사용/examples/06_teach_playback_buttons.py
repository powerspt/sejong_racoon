# -*- coding: utf-8 -*-
"""06. 직접 시범 보이기(Teaching) 와 따라 하기(Playback) — 화면 UI

    python examples/06_teach_playback_buttons.py

화면에 버튼이 다 나온다. 로봇 본체의 TEACH / PLAY / DELETE 물리 버튼도 그대로 동작하므로
둘 중 편한 쪽을 쓰면 된다 (물리 버튼은 화면에도 '눌림' 으로 표시된다).

하는 법
  1. [모터 힘 빼기] 를 누르면 팔이 흐물흐물해진다 -> 손으로 움직일 수 있다
  2. 손으로 팔을 원하는 자세로 잡는다
  3. [이 자세 저장] -> 목록에 한 줄 쌓인다 (집게 상태도 같이 저장된다)
  4. 2~3 을 반복한다
  5. [재생] -> 저장한 순서대로 로봇이 따라 한다

집게를 쓰려면
  자세를 저장하기 **전에** [집게 열기] 또는 [집게 닫기] 를 눌러 둔다.
  그 상태가 자세와 함께 저장되므로 "집었다 옮겨서 놓기" 까지 가르칠 수 있다.

만든 동작은 [파일로 저장] 해 두었다가 [불러오기] 로 다시 쓸 수 있다 (JSON).
"""
import json
import math
import queue
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from roboid import *                                        # noqa: E402,F401,F403

CONNECT_TIMEOUT_S = 10.0
POLL_MS = 120                   # 화면 갱신 주기. 너무 짧으면 BLE 를 괴롭힌다
FONT = ("Malgun Gothic", 10)
FONT_B = ("Malgun Gothic", 11, "bold")
FONT_BIG = ("Malgun Gothic", 22, "bold")
FONT_MONO = ("Consolas", 11)
BG = "#f4f4f4"


def wait_connected(bot, timeout_s=CONNECT_TIMEOUT_S):
    """roboid 공식 판정. Raccoon() 이 돌아와도 연결이 늦게 될 수 있어 폴링한다."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if bot.is_connected():
            return True
        wait(300)
    return False


class TeachApp:
    def __init__(self, root, bot):
        self.root = root
        self.bot = bot
        self.poses = []             # [(j1, j2, j3, j4, gripper_closed)]
        self.gripper_closed = False
        self.motors_free = False
        self.busy = False           # 재생 중에는 다른 버튼을 막는다
        # 워커 스레드는 tkinter 를 직접 건드리면 안 된다. 할 말은 큐에 넣고
        # 메인 스레드의 _poll 이 꺼내서 반영한다.
        self.q = queue.Queue()
        self.status = tk.StringVar(value="준비됨")
        self._build()
        self.root.after(POLL_MS, self._poll)

    # ────────────────────────── 화면 ──────────────────────────
    def _build(self):
        self.root.title("라쿤봇 — 직접 가르치기")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        left = tk.Frame(self.root, bg=BG)
        left.grid(row=0, column=0, padx=12, pady=12, sticky="n")
        right = tk.Frame(self.root, bg=BG)
        right.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="n")

        # 1) 모터
        box = self._box(left, "1. 팔을 손으로 움직이려면")
        self.btn_free = tk.Button(box, text="모터 힘 빼기", font=FONT_B, height=2,
                                  command=self.toggle_free)
        self.btn_free.pack(fill="x", padx=8, pady=(4, 2))
        self.lbl_free = tk.Label(box, text="", font=FONT, bg=BG, wraplength=300, justify="left")
        self.lbl_free.pack(fill="x", padx=8, pady=(0, 8))

        # 2) 현재 상태
        box = self._box(left, "2. 지금 팔의 자세")
        self.lbl_joint = tk.Label(box, text="", font=FONT_MONO, bg=BG, justify="left", anchor="w")
        self.lbl_joint.pack(fill="x", padx=8, pady=(4, 0))
        self.lbl_xyz = tk.Label(box, text="", font=FONT_MONO, bg=BG, justify="left", anchor="w")
        self.lbl_xyz.pack(fill="x", padx=8, pady=(0, 8))

        # 3) 집게
        box = self._box(left, "3. 집게 — 저장하기 전에 정해 둔다")
        self.lbl_grip = tk.Label(box, text="열림", font=FONT_BIG, bg="#e8f0fe", height=1)
        self.lbl_grip.pack(fill="x", padx=8, pady=(6, 4))
        row = tk.Frame(box, bg=BG)
        row.pack(fill="x", padx=8, pady=(0, 8))
        self.btn_open = tk.Button(row, text="집게 열기", font=FONT_B, height=2,
                                  command=lambda: self.set_gripper(False))
        self.btn_open.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.btn_close = tk.Button(row, text="집게 닫기", font=FONT_B, height=2,
                                   command=lambda: self.set_gripper(True))
        self.btn_close.pack(side="left", fill="x", expand=True)

        # 4) 저장
        box = self._box(left, "4. 이 자세를 기억시키기")
        self.btn_save = tk.Button(box, text="＋  이 자세 저장", font=("Malgun Gothic", 13, "bold"),
                                  height=2, bg="#d6ead6", command=self.save_pose)
        self.btn_save.pack(fill="x", padx=8, pady=(4, 8))

        # 5) 목록
        box = self._box(right, "저장된 자세")
        self.lst = tk.Listbox(box, font=FONT_MONO, height=12, width=38,
                              activestyle="none", selectmode="browse")
        self.lst.pack(fill="both", padx=8, pady=(4, 4))
        row = tk.Frame(box, bg=BG)
        row.pack(fill="x", padx=8, pady=(0, 8))
        for txt, fn in (("마지막 지우기", self.del_last), ("전부 지우기", self.del_all),
                        ("이 자세로 가기", self.goto_selected)):
            tk.Button(row, text=txt, font=FONT, command=fn).pack(side="left",
                                                                 fill="x", expand=True, padx=2)

        # 6) 재생
        box = self._box(right, "따라 하게 하기")
        row = tk.Frame(box, bg=BG)
        row.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(row, text="속도", font=FONT, bg=BG).pack(side="left")
        self.sp_speed = tk.Scale(row, from_=10, to=100, orient="horizontal", bg=BG,
                                 length=110, showvalue=True)
        self.sp_speed.set(50)
        self.sp_speed.pack(side="left", padx=(4, 12))
        tk.Label(row, text="자세 간 대기(ms)", font=FONT, bg=BG).pack(side="left")
        self.sp_wait = tk.Spinbox(row, from_=0, to=3000, increment=100, width=6, font=FONT)
        self.sp_wait.delete(0, "end")
        self.sp_wait.insert(0, "300")
        self.sp_wait.pack(side="left", padx=4)

        self.btn_play = tk.Button(box, text="▶  재생", font=("Malgun Gothic", 13, "bold"),
                                  height=2, bg="#dbe7ff", command=self.play)
        self.btn_play.pack(fill="x", padx=8, pady=(4, 4))
        row = tk.Frame(box, bg=BG)
        row.pack(fill="x", padx=8, pady=(0, 8))
        for txt, fn in (("파일로 저장", self.save_file), ("불러오기", self.load_file),
                        ("Home 자세", self.go_home)):
            tk.Button(row, text=txt, font=FONT, command=fn).pack(side="left",
                                                                 fill="x", expand=True, padx=2)

        # 7) 물리 버튼 / 상태줄
        box = self._box(right, "로봇 본체의 물리 버튼 (그대로 쓸 수 있다)")
        self.lbl_phys = tk.Label(box, text="", font=FONT, bg=BG, justify="left", anchor="w")
        self.lbl_phys.pack(fill="x", padx=8, pady=(4, 8))

        bar = tk.Frame(self.root, bg="#e4e4e4")
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        tk.Label(bar, textvariable=self.status, font=FONT, bg="#e4e4e4",
                 anchor="w").pack(fill="x", padx=10, pady=4)
        self._refresh_list()
        self._refresh_gripper()
        self._refresh_free()

    def _box(self, parent, title):
        f = tk.LabelFrame(parent, text=title, font=FONT_B, bg=BG, padx=2, pady=2)
        f.pack(fill="x", pady=(0, 10))
        return f

    # ────────────────────────── 주기 갱신 ──────────────────────────
    def _poll(self):
        # 워커 스레드가 큐에 넣어 둔 것을 메인 스레드에서 처리한다
        while True:
            try:
                kind, msg = self.q.get_nowait()
            except queue.Empty:
                break
            if kind == "done":
                self._finish(msg)
            else:
                self.status.set(msg)
        try:
            if not self.busy:
                j = tuple(round(float(v), 1) for v in self.bot.encoder(-1))
                x, y, z = (round(float(v), 1) for v in self.bot.xyz())
                self.lbl_joint.config(
                    text=f"관절   J1 {j[0]:>7}   J2 {j[1]:>7}\n       J3 {j[2]:>7}   J4 {j[3]:>7}")
                tilt = round(j[1] + j[2] + j[3] + 90, 1)
                self.lbl_xyz.config(
                    text=f"집게 끝  x {x:>6}   y {y:>6}   z {z:>6}  cm\n"
                         f"반경 {round(math.hypot(x, y), 1):>5} cm    기울기 {tilt:>6}도")

                # 물리 버튼도 같이 처리한다 — clicked 는 한 번만 True 가 된다
                pressed = []
                if self.bot.teach_button():
                    pressed.append("TEACH")
                if self.bot.play_button():
                    pressed.append("PLAY")
                if self.bot.delete_button():
                    pressed.append("DELETE")
                self.lbl_phys.config(
                    text=("TEACH 저장   ·   PLAY 재생   ·   DELETE 전부 지우기\n"
                          + ("지금 눌림: " + ", ".join(pressed) if pressed else "지금 눌림: 없음")))
                if self.bot.teach_clicked():
                    self.save_pose()
                elif self.bot.teach_long_pressed():
                    self.set_gripper(not self.gripper_closed)
                elif self.bot.play_clicked():
                    self.play()
                elif self.bot.delete_clicked():
                    self.del_all()
        except Exception as e:                      # 통신이 끊겨도 창은 살려 둔다
            self.status.set(f"읽기 실패: {type(e).__name__}: {e}")
        self.root.after(POLL_MS, self._poll)

    # ────────────────────────── 동작 ──────────────────────────
    def toggle_free(self):
        if self.busy:
            return
        self.motors_free = not self.motors_free
        if self.motors_free:
            self.bot.turn_off()
        else:
            j = tuple(float(v) for v in self.bot.encoder(-1))
            self.bot.unlock()
            self.bot.degree_to(*j, 50)              # 지금 자세 그대로 잡아 둔다
        self._refresh_free()

    def _refresh_free(self):
        if self.motors_free:
            self.btn_free.config(text="모터 다시 잡기", bg="#ffe0b2")
            self.lbl_free.config(text="지금 팔이 풀려 있습니다. 손으로 움직이세요.\n"
                                      "떨어지지 않게 팔을 받치고 움직이세요.")
        else:
            self.btn_free.config(text="모터 힘 빼기", bg="SystemButtonFace")
            self.lbl_free.config(text="지금 팔이 잠겨 있습니다. 손으로 움직이려면 누르세요.")

    def set_gripper(self, closed):
        if self.busy:
            return
        self.gripper_closed = closed
        self.bot.close_gripper() if closed else self.bot.open_gripper()
        self._refresh_gripper()
        self.status.set("집게 " + ("닫음" if closed else "열음")
                        + " — 이 상태가 다음에 저장할 자세에 같이 기록됩니다")

    def _refresh_gripper(self):
        if self.gripper_closed:
            self.lbl_grip.config(text="닫힘", bg="#fde2e2")
            self.btn_close.config(relief="sunken", bg="#f4b8b8")
            self.btn_open.config(relief="raised", bg="SystemButtonFace")
        else:
            self.lbl_grip.config(text="열림", bg="#e8f0fe")
            self.btn_open.config(relief="sunken", bg="#a9c7f5")
            self.btn_close.config(relief="raised", bg="SystemButtonFace")

    def save_pose(self):
        if self.busy:
            return
        j = tuple(round(float(v), 1) for v in self.bot.encoder(-1))
        self.poses.append((*j, self.gripper_closed))
        self.bot.beep()
        self._refresh_list()
        self.status.set(f"{len(self.poses)}번째 자세를 저장했습니다")

    def del_last(self):
        if self.busy or not self.poses:
            return
        self.poses.pop()
        self._refresh_list()
        self.status.set(f"마지막 자세를 지웠습니다 (남은 {len(self.poses)}개)")

    def del_all(self):
        if self.busy or not self.poses:
            return
        if messagebox.askyesno("전부 지우기", f"자세 {len(self.poses)}개를 모두 지울까요?"):
            self.poses.clear()
            self._refresh_list()
            self.status.set("전부 지웠습니다")

    def goto_selected(self):
        if self.busy or not self.poses:
            return
        sel = self.lst.curselection()
        if not sel:
            self.status.set("목록에서 자세를 하나 고르세요")
            return
        j1, j2, j3, j4, closed = self.poses[sel[0]]
        speed = int(self.sp_speed.get())
        self._run(lambda: self._move_one(j1, j2, j3, j4, closed, speed),
                  f"{sel[0]+1}번 자세로 이동")

    def go_home(self):
        self._run(lambda: (self.bot.unlock(), self.bot.init_pose(), wait(1200)), "Home 으로")

    def _refresh_list(self):
        self.lst.delete(0, "end")
        for i, (j1, j2, j3, j4, closed) in enumerate(self.poses, 1):
            self.lst.insert("end",
                            f"{i:>2}  {j1:>6} {j2:>6} {j3:>7} {j4:>6}  "
                            + ("집게 닫힘" if closed else "집게 열림"))
        self.lst.see("end")
        self.btn_play.config(state="normal" if self.poses else "disabled")

    # ────────────────────────── 재생 ──────────────────────────
    def _move_one(self, j1, j2, j3, j4, closed, speed):
        # speed 는 미리 읽어서 넘긴다 - tkinter 위젯은 워커 스레드에서 읽으면 안 된다
        self.bot.unlock()
        self.bot.degree_to(j1, j2, j3, j4, speed)
        self.bot.close_gripper() if closed else self.bot.open_gripper()

    def play(self):
        if self.busy or not self.poses:
            return
        try:
            gap = int(self.sp_wait.get())
        except ValueError:
            gap = 300
        speed = int(self.sp_speed.get())
        seq = list(self.poses)                      # 재생 중 목록이 바뀌어도 안전하게

        def job():
            for i, (j1, j2, j3, j4, closed) in enumerate(seq, 1):
                if not self.busy:                   # 창이 닫히면 중단
                    return
                self.q.put(("status", f"재생 중 {i}/{len(seq)} …"))
                self._move_one(j1, j2, j3, j4, closed, speed)
                wait(gap)
            self.bot.sound("GOOD JOB")
        self._run(job, "재생", done="재생을 마쳤습니다")

    def _run(self, job, what, done=None):
        """로봇 명령은 워커 스레드에서 돌린다. 화면이 멈추지 않게."""
        if self.busy:
            return
        self.busy = True
        self.motors_free = False
        self._refresh_free()
        self._set_buttons("disabled")
        self.status.set(what + " …")

        def wrapper():
            try:
                job()
                msg = done or (what + " 끝")
            except Exception as e:
                msg = f"{what} 실패: {type(e).__name__}: {e}"
            finally:
                self.busy = False
            self.q.put(("done", msg))
        threading.Thread(target=wrapper, daemon=True).start()

    def _finish(self, msg):
        self._set_buttons("normal")
        self._refresh_list()
        self.status.set(msg)

    def _set_buttons(self, state):
        for b in (self.btn_free, self.btn_open, self.btn_close, self.btn_save, self.btn_play):
            b.config(state=state)
        if state == "normal" and not self.poses:
            self.btn_play.config(state="disabled")

    # ────────────────────────── 파일 ──────────────────────────
    def save_file(self):
        if not self.poses:
            self.status.set("저장할 자세가 없습니다")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("동작 파일", "*.json")],
            initialfile="teach_poses.json")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"poses": self.poses}, f, ensure_ascii=False, indent=2)
        self.status.set(f"저장했습니다: {os.path.basename(path)} ({len(self.poses)}개)")

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("동작 파일", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.poses = [tuple(p) for p in data["poses"]]
        except Exception as e:
            messagebox.showerror("불러오기 실패", f"{type(e).__name__}: {e}")
            return
        self._refresh_list()
        self.status.set(f"불러왔습니다: {os.path.basename(path)} ({len(self.poses)}개)")

    def quit(self):
        self.busy = False
        try:
            self.bot.dispose()
        except Exception:
            pass
        self.root.destroy()


def main():
    bot = Raccoon()
    if not wait_connected(bot):
        bot.dispose()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "연결 안 됨",
            f"{CONNECT_TIMEOUT_S:.0f}초 안에 로봇이 연결되지 않았습니다.\n\n"
            "1. USB to BLE 동글이 꽂혀 있는가\n"
            "   (노트북 내장 블루투스로는 안 됩니다)\n"
            "2. 로봇 전원과 배터리\n"
            "3. 다른 파이썬 창이 포트를 잡고 있지 않은가\n\n"
            "자세한 진단: examples/01_connect_test.py")
        root.destroy()
        return
    print(f"연결됨 (신호 {bot.signal_strength()}dBm, 배터리 {bot.battery_state()})")
    root = tk.Tk()
    TeachApp(root, bot)
    root.mainloop()


if __name__ == "__main__":
    main()
