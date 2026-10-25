from roboid import *
r = Raccoon()
import math

r.close_gripper(); wait(700)      # 두 날이 만나는 점 = 기준점
input("집게 끝에 실+클립(다림추)을 매달고 Enter ")

for deg in [(0,-10,-140,60), (30,-20,-120,40), (-45,0,-90,10)]:
    input(f"{deg} 로 이동합니다. 팔 주변을 비우고 Enter ")
    r.degree_to(*deg); wait(1500)

    cx, cy, cz = r.degree_to_xyz(*deg)
    print(f"  계산값   x = {cx*10:7.1f} mm    y = {cy*10:7.1f} mm    (높이 z = {cz*10:.1f} mm)")
    print("  다림추가 매트에 닿는 점을 읽으세요. 로봇은 멈춰서 기다립니다.")

    mx = float(input("  실측 x (mm, 오른쪽이 +): "))
    my = float(input("  실측 y (mm, 앞쪽이 +): "))
    dx, dy = mx - cx*10, my - cy*10
    print(f"  → 오차 {math.hypot(dx, dy):.1f} mm   (x {dx:+.1f} / y {dy:+.1f})")