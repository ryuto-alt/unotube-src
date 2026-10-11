# UnoTube の起動アニメーション(Lottie JSON)を作る。
# 再生マークが力をためて → 回転ジャンプ(紙吹雪) → 着地でぷにっと弾んで波紋 → 落ち着く。
# 最初と最後のコマはアイコンと同じ見た目なので、起動画面の静止アイコンから途切れずにつながる。
# 出力: branding/res-overrides/custom-branding/raw/morphe_startup_animation.json (+ _play)
# usage: python -I tools/make_splash.py
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_branding import OUT, rounded_triangle  # noqa: E402

W = H = 432          # Morphe の元のアニメーションと同じ(108dp の 4 倍)
FPS = 60
END = 72             # 1.2 秒
CX, CY = W / 2, H / 2
R = W * 0.235        # アイコン前景の三角形と同じ大きさ
OFFSET_X = R * 0.08  # 見た目の中心合わせ(アイコンと同じ)

MAUVE, PINK = "#CBA6F7", "#F5C2E7"
CONFETTI = ["#F5E0DC", "#F38BA8", "#FAB387", "#F9E2AF", "#A6E3A1",
            "#94E2D5", "#89DCEB", "#74C7EC", "#89B4FA", "#B4BEFE", "#F5C2E7", "#CBA6F7"]


def rgba(hex_, a=1.0):
    h = hex_.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


# ── キーフレーム ─────────────────────────────────────────
EASE_OUT = ({"x": 0.2, "y": 0.0}, {"x": 0.3, "y": 1.0})   # 素早く出て、ゆっくり止まる
EASE_IN = ({"x": 0.7, "y": 0.0}, {"x": 0.8, "y": 1.0})    # ゆっくり出て、勢いよく着く
EASE = ({"x": 0.42, "y": 0.0}, {"x": 0.58, "y": 1.0})


def static(v):
    return {"a": 0, "k": v}


def anim(keys, ease=EASE):
    """keys: [(frame, value)] または [(frame, value, ease)]。ease はその区間の出だし側。"""
    out = []
    for i, k in enumerate(keys):
        t, v = k[0], k[1]
        kf = {"t": t, "s": v if isinstance(v, list) else [v]}
        if i < len(keys) - 1:
            o, inn = k[2] if len(k) > 2 else ease
            kf["o"], kf["i"] = o, inn
        out.append(kf)
    return {"a": 1, "k": out}


def transform(p=None, s=None, r=None, o=None, a=(0, 0)):
    return {
        "a": static([a[0], a[1], 0]),
        "p": p if isinstance(p, dict) else static(list(p) + [0] if p else [CX, CY, 0]),
        "s": s if isinstance(s, dict) else static([100, 100, 100]),
        "r": r if isinstance(r, dict) else static(0),
        "o": o if isinstance(o, dict) else static(100),
    }


def layer(name, ind, shapes, ks, ip=0, op=END):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ks": ks, "ao": 0,
            "shapes": shapes, "ip": ip, "op": op, "st": 0, "bm": 0}


def group(items):
    return {"ty": "gr", "it": items + [{"ty": "tr", "p": static([0, 0]), "a": static([0, 0]),
                                         "s": static([100, 100]), "r": static(0), "o": static(100),
                                         "sk": static(0), "sa": static(0)}]}


def path(points):
    n = len(points)
    return {"ty": "sh", "ks": static({"i": [[0, 0]] * n, "o": [[0, 0]] * n,
                                      "v": [[round(x, 2), round(y, 2)] for x, y in points], "c": True})}


def fill(hex_, opacity=100):
    return {"ty": "fl", "c": static(rgba(hex_)), "o": static(opacity), "r": 1, "bm": 0}


def gradient_fill(c0, c1, start, end):
    return {"ty": "gf", "o": static(100), "r": 1, "bm": 0, "t": 1,
            "g": {"p": 2, "k": static([0] + rgba(c0)[:3] + [1] + rgba(c1)[:3])},
            "s": static(list(start)), "e": static(list(end))}


# ── 部品 ──────────────────────────────────────────────
def play_button(ind):
    # 三角形の重心を原点に描き、レイヤーの位置で動かす。潰れ・伸びは下端を支点にしたいので、
    # アンカーを三角形の下寄り(R*0.5)に置く。
    pts = rounded_triangle(0, 0, R, R * 0.2, steps=8)
    ground = R * 0.5
    base = [CX + OFFSET_X, CY + ground]
    jump = 120
    pos = anim([
        (0, base),
        (8, base, EASE_OUT),                         # ため
        (24, [base[0], base[1] - jump], EASE_IN),    # 頂点
        (36, base),                                  # 着地
        (END, base),
    ])
    scale = anim([
        (0, [100, 100, 100]),
        (8, [118, 78, 100], EASE_OUT),     # ぐっと潰れて力をためる
        (13, [86, 118, 100]),              # 飛び出しで縦に伸びる
        (24, [100, 100, 100], EASE_IN),
        (35, [94, 108, 100], EASE_OUT),    # 落下中は少し縦長
        (39, [126, 72, 100], EASE_OUT),    # 着地でぷにっ
        (46, [92, 110, 100], EASE),
        (52, [104, 96, 100], EASE),
        (58, [100, 100, 100]),
        (END, [100, 100, 100]),
    ])
    rot = anim([(0, 0), (9, 0, EASE_OUT), (33, 360), (END, 360)])
    # 親(ヌル): 位置と潰れ・伸び(支点は下端)。子: 三角形の中心まわりの回転。
    body = {"ddd": 0, "ind": ind, "ty": 3, "nm": "body", "sr": 1, "ao": 0,
            "ks": transform(p=pos, s=scale), "ip": 0, "op": END, "st": 0, "bm": 0}
    shapes = [group([path(pts), gradient_fill(MAUVE, PINK, (-R * 0.5, -R * 0.9), (R, R * 0.9))])]
    tri = layer("play", ind + 1, shapes, transform(p=[0, -ground], r=rot))
    tri["parent"] = ind
    return [tri, body]


def ripple(ind):
    size = anim([(36, [R * 2.3, R * 2.3]), (64, [R * 3.9, R * 3.9], EASE_OUT), (END, [R * 3.9, R * 3.9])])
    opacity = anim([(0, 0), (36, 0), (37, 70), (64, 0, EASE_OUT), (END, 0)])
    shapes = [group([
        {"ty": "el", "p": static([0, 0]), "s": size, "d": 1},
        {"ty": "st", "c": static(rgba(MAUVE)), "o": static(100), "w": anim([(36, 9), (64, 1)]),
         "lc": 2, "lj": 2, "bm": 0},
    ])]
    return layer("ripple", ind, shapes, transform(p=[CX + OFFSET_X, CY], o=opacity))


def confetti(ind, i, n, rng):
    ang = -math.pi / 2 + (i / n) * 2 * math.pi + rng.uniform(-0.2, 0.2)
    dist = rng.uniform(R * 1.25, R * 1.75)
    start = [CX + OFFSET_X, CY - 40]
    mid = [start[0] + math.cos(ang) * dist, start[1] + math.sin(ang) * dist]
    end = [mid[0], mid[1] + rng.uniform(25, 45)]          # 少し落ちる
    t0 = 12 + rng.randint(0, 4)
    t1 = t0 + 20
    t2 = t1 + 18
    pos = anim([(0, start), (t0, start, EASE_OUT), (t1, mid, EASE_IN), (t2, end), (END, end)])
    s = rng.uniform(0.8, 1.2)
    scale = anim([(0, [0, 0, 100]), (t0, [0, 0, 100], EASE_OUT), (t0 + 6, [100 * s, 100 * s, 100]),
                  (t1, [100 * s, 100 * s, 100]), (t2, [0, 0, 100]), (END, [0, 0, 100])])
    spin = rng.choice([-1, 1]) * rng.randint(180, 540)
    rot = anim([(0, 0), (t0, 0), (t2, spin), (END, spin)])
    color = CONFETTI[i % len(CONFETTI)]
    kind = i % 3
    if kind == 0:
        shape = {"ty": "el", "p": static([0, 0]), "s": static([20, 20]), "d": 1}
    elif kind == 1:
        shape = {"ty": "rc", "p": static([0, 0]), "s": static([26, 12]), "r": static(6), "d": 1}
    else:
        shape = path(rounded_triangle(0, 0, 14, 3, steps=3))
    return layer(f"confetti{i}", ind, [group([shape, fill(color)])], transform(p=pos, s=scale, r=rot))


def main():
    rng = random.Random(11)  # 毎回同じ散り方にする
    n = 14
    layers = play_button(1)  # ind 1, 2
    layers += [confetti(3 + i, i, n, rng) for i in range(n)]
    layers.append(ripple(3 + n))
    doc = {"v": "5.12.1", "fr": FPS, "ip": 0, "op": END, "w": W, "h": H, "nm": "UnoTube", "ddd": 0,
           "assets": [], "layers": layers, "markers": []}
    d = os.path.join(OUT, "res-overrides", "custom-branding", "raw")
    os.makedirs(d, exist_ok=True)
    text = json.dumps(doc, separators=(",", ":"))
    for fn in ("morphe_startup_animation.json", "morphe_startup_animation_play.json"):
        with open(os.path.join(d, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    # 目視用(lottie-web で開く)
    with open(os.path.join(OUT, "splash.json"), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"splash: {len(layers)} レイヤー, {END / FPS:.2f} 秒")


if __name__ == "__main__":
    main()
