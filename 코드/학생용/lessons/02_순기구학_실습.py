# -*- coding: utf-8 -*-
"""주제 2 — 순기구학 (실습 · 빈칸 채우기)

    python lessons/02_순기구학_실습.py

지금 그대로 실행해도 돌아간다 — 다만 답이 이상하게 나온다.
그 "이상함"이 오늘 수업의 재료다. TODO 는 수업 흐름을 따라 세 번 나온다.

    TODO 1 (tryfk 장)   집게의 누적 각도 — 숫자 0 을 올바른 식으로 고친다
    TODO 2 (sign 장 뒤)  r 전체를 −(  ) 로 감싼다
    TODO 3 (offset 장 뒤) 아래로 0.6cm 두 항을 더한다

막히면 윗줄의 본보기를 보면 된다. 문법은 새로 나오는 것이 없다.
"""
import math

# 라쿤봇의 길이 (cm). 매뉴얼 1장
L1 = 8.25        # 바닥 ~ 어깨
L2 = 10.0        # 어깨 ~ 팔꿈치
L3 = 10.0        # 팔꿈치 ~ 손목
GRIP = 8.0       # 손목 ~ 집게 끝 (앞으로)
GRIP_DOWN = 0.6  # 손목 ~ 집게 끝 (아래로) — TODO 3 에서 쓴다


def 순기구학(j1, j2, j3, j4):
    """관절 각도 4개 -> 집게 끝 (x, y, z) cm"""

    # 각 막대가 '수직에서' 얼마나 기울었는가 (chain 장의 규칙: 각도는 누적된다)
    a2 = math.radians(j2)                 # 어깨 막대
    a3 = math.radians(j2 + j3)            # 팔꿈치 막대 — 본보기: 어깨에서 '더' 기울었다
    a4 = math.radians(0)                  # TODO 1 ─ 집게는? (윗줄을 본보기로, 0 을 고친다)

    # 옆에서 본 그림: 앞으로 = 길이 x sin, 위로 = 길이 x cos  (활동지에서 잰 그대로)
    #
    # TODO 2 ─ sign 장을 본 뒤, 아래 r 의 오른쪽 전체를 -(      ) 로 감싼다
    #   활동지는 '앞으로 눕는 쪽'이 + 였지만, 로봇은 '뒤로 젖히는 쪽'이 + 다.
    #   그래서 지금은 Home 의 y 가 -14.74 — 크기는 맞고 부호만 반대다.
    #   세 항을 따로 고칠 필요 없이, 합 전체의 부호를 한 번만 뒤집으면 된다.
    #
    # TODO 3 ─ offset 장을 본 뒤, r 에는 + GRIP_DOWN * math.cos(a4),
    #                              z 에는 + GRIP_DOWN * math.sin(a4) 를 더한다
    #   집게 끝은 손목 막대에서 '직각 방향(아래)'으로 0.6cm 더 가 있다 — ㄱ자.
    #   직각으로 꺾였으니 sin 과 cos 이 자리를 바꾼다 (앞으로 = cos, 위로 = sin).
    #   둘 다 + 로 적는다 — 방향은 a4 의 sin/cos 이 알아서 정한다.
    #   (Home 은 a4 = -90도: cos = 0 이라 r 그대로, sin = -1 이라 z 가 0.6 내려간다)
    #   r 의 보정항은 TODO 2 에서 감싼 -(      ) 바깥에 더한다.
    r = L2 * math.sin(a2) + L3 * math.sin(a3) + GRIP * math.sin(a4)
    z = L1 + L2 * math.cos(a2) + L3 * math.cos(a3) + GRIP * math.cos(a4)

    # 위에서 본 그림: j1 만큼 돌린다 (이 두 줄은 완성되어 있다)
    a1 = math.radians(j1)
    x = -r * math.sin(a1)
    y = r * math.cos(a1)
    return x, y, z


if __name__ == "__main__":
    x, y, z = 순기구학(0, -10, -140, 60)          # Home 자세
    print(f"내 식의 Home : ({x:.2f}, {y:.2f}, {z:.2f})")
    print("매뉴얼의 Home: (0, 14.7, 8.8)")
    print()
    print("같지 않다면 — 어떻게 다른지(부호? 크기?)를 그대로 적어 두자. 그게 다음 장이다.")
