# UnoTube のアイコン・ヘッダーロゴを描く(画像生成AIは使わない)。
# 出力: branding/icon (Custom branding の customIcon)
#       branding/header (Change header の custom)
#       branding/preview.png (目視用)
# usage: python -I tools/make_branding.py
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "branding")
SS = 4  # 縮小前の拡大率(アンチエイリアス用)

# Catppuccin Mocha / Latte
BASE = (24, 24, 37)        # #181825 Mantle(テーマ背景と同じ)
BASE_HI = (30, 30, 46)     # #1E1E2E Base
MAUVE = (203, 166, 247)    # #CBA6F7
PINK = (245, 194, 231)     # #F5C2E7
TEXT_DARK = (205, 214, 244)  # #CDD6F4 Mocha Text
TEXT_LIGHT = (76, 79, 105)   # #4C4F69 Latte Text

ICON_SIZES = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
# Morphe の推奨寸法より大きくすると、そのぶんヘッダーのロゴが大きく表示される(横 1.25 倍・縦 1.1 倍)
HEADER_SIZES = {dpi: (round(w * 1.25), round(h * 1.1)) for dpi, (w, h) in
                {"hdpi": (194, 72), "xhdpi": (258, 96), "xxhdpi": (387, 144), "xxxhdpi": (512, 192)}.items()}
NOTIF_SIZES = {"mdpi": 24, "hdpi": 36, "xhdpi": 48, "xxhdpi": 72, "xxxhdpi": 96}


def rounded_triangle(cx, cy, r, corner, steps=24):
    """右向きの再生三角形(角丸)。重心(cx,cy)、外接円半径 r、角の丸め半径 corner。"""
    verts = [(cx + r * math.cos(a), cy + r * math.sin(a))
             for a in (0, 2 * math.pi / 3, 4 * math.pi / 3)]
    # 角丸: 各頂点を内側へ寄せた円の弧で置き換える
    inset = corner / math.sin(math.pi / 6)  # 60度の角に内接する円の中心までの距離
    pts = []
    for i, (vx, vy) in enumerate(verts):
        dx, dy = cx - vx, cy - vy
        d = math.hypot(dx, dy)
        ox, oy = vx + dx / d * inset, vy + dy / d * inset
        mid = math.atan2(vy - cy, vx - cx)
        for s in range(steps + 1):
            a = mid - math.pi / 3 + (2 * math.pi / 3) * s / steps
            pts.append((ox + corner * math.cos(a), oy + corner * math.sin(a)))
    return pts


def gradient(size, box, c0, c1):
    """box(x0,y0,x1,y1) の左上 c0 → 右下 c1 の斜めグラデーション。外側は端の色。"""
    w, h = size
    x0, y0, x1, y1 = box
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        ty = min(max((y - y0) / (y1 - y0), 0), 1)
        for x in range(w):
            t = (min(max((x - x0) / (x1 - x0), 0), 1) + ty) / 2
            px[x, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
    return g


def glyph(size, cx, cy, r, corner):
    """グラデーションの再生マーク(RGBA)。色は三角形の範囲いっぱいに Mauve → Pink。"""
    pts = rounded_triangle(cx, cy, r, corner)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    g = gradient(size, (min(xs), min(ys), max(xs), max(ys)), MAUVE, PINK).convert("RGBA")
    g.putalpha(mask)
    return g


def icon_background(px):
    s = px * SS
    img = Image.new("RGB", (s, s), BASE)
    # 中央をわずかに明るく(のっぺり防止)
    glow = Image.new("L", (s, s), 0)
    ImageDraw.Draw(glow).ellipse([s * 0.15, s * 0.1, s * 0.85, s * 0.8], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(s * 0.18))
    img = Image.composite(Image.new("RGB", (s, s), BASE_HI), img, glow)
    return img.resize((px, px), Image.LANCZOS)


def icon_foreground(px):
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # 安全領域(108dp 中の直径 66dp)に収める。三角形は重心を少し左へ寄せて見た目の中心を合わせる
    r = s * 0.235
    cx, cy = s * 0.5 + r * 0.08, s * 0.5
    # 柔らかい光彩
    halo = glyph((s, s), cx, cy, r * 1.05, r * 0.2)
    a = halo.split()[3].filter(ImageFilter.GaussianBlur(s * 0.035)).point(lambda v: v * 0.45)
    halo.putalpha(a)
    img.alpha_composite(halo)
    img.alpha_composite(glyph((s, s), cx, cy, r, r * 0.2))
    return img.resize((px, px), Image.LANCZOS)


def vector_triangle_path(cx, cy, r, corner, steps=6):
    pts = rounded_triangle(cx, cy, r, corner, steps)
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"


def write_vectors(icon_dir):
    d = os.path.join(icon_dir, "drawable")
    os.makedirs(d, exist_ok=True)
    mono = vector_triangle_path(54 + 25.4 * 0.08, 54, 25.4, 5.1)
    with open(os.path.join(d, "morphe_adaptive_monochrome_custom.xml"), "w", encoding="utf-8") as f:
        f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#FFFFFFFF" android:pathData="{mono}"/>
</vector>
''')
    notif = vector_triangle_path(12 + 9.5 * 0.08, 12, 9.5, 1.9)
    with open(os.path.join(d, "morphe_notification_icon_custom.xml"), "w", encoding="utf-8") as f:
        f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="{notif}"/>
</vector>
''')


# アプリ内で選べるアイコン(Morphe のロゴ)を UnoTube の絵で置き換える: 名前 → (背景, 前景の色 2 つ)
VARIANTS = {
    "black": ("#000000", "#CBA6F7", "#F5C2E7"),
    "dark": ("#1E1E2E", "#CBA6F7", "#F5C2E7"),
    "light": ("#EFF1F5", "#8839EF", "#EA76CB"),  # Latte の Mauve / Pink
    "play": ("#CBA6F7", "#181825", "#181825"),
    "play_black": ("#000000", "#FFFFFF", "#FFFFFF"),
}
VECTOR_HEAD = '<?xml version="1.0" encoding="utf-8"?>\n<!-- UnoTube: tools/make_branding.py が生成 -->\n'


def foreground_vector(c0, c1):
    path = vector_triangle_path(54 + 25.4 * 0.08, 54, 25.4, 5.1)
    if c0 == c1:
        fill = f'android:fillColor="{c0}"'
        body = ""
    else:
        fill = ""
        body = f'''
        <aapt:attr name="android:fillColor">
            <gradient android:type="linear"
                android:startX="32" android:startY="32" android:endX="76" android:endY="76">
                <item android:offset="0" android:color="{c0}"/>
                <item android:offset="1" android:color="{c1}"/>
            </gradient>
        </aapt:attr>
    '''
    return VECTOR_HEAD + f'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path {fill} android:pathData="{path}">{body}</path>
</vector>
'''


def write_overrides(icon_dir):
    """Morphe 本体のリソースを上書きするファイル(build.sh が morphe-patches の resources へ写す)。"""
    res = os.path.join(OUT, "res-overrides")
    d = os.path.join(res, "custom-branding", "drawable")
    os.makedirs(d, exist_ok=True)
    mono = open(os.path.join(icon_dir, "drawable", "morphe_adaptive_monochrome_custom.xml"), encoding="utf-8").read()
    notif = open(os.path.join(icon_dir, "drawable", "morphe_notification_icon_custom.xml"), encoding="utf-8").read()
    for name, (bg, c0, c1) in VARIANTS.items():
        files = {
            f"morphe_adaptive_background_{name}.xml": VECTOR_HEAD + f'<color xmlns:android="http://schemas.android.com/apk/res/android"\n    android:color="{bg}" />\n',
            f"morphe_adaptive_foreground_{name}.xml": foreground_vector(c0, c1),
            f"morphe_adaptive_monochrome_{name}.xml": mono,
            f"morphe_notification_icon_{name}.xml": notif,
        }
        for fn, text in files.items():
            with open(os.path.join(d, fn), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
    # ヘッダーロゴの「Morphe」も UnoTube のロゴ画像(Change header の custom)を指す
    d = os.path.join(res, "change-header", "drawable")
    os.makedirs(d, exist_ok=True)
    for theme in ("dark", "light"):
        with open(os.path.join(d, f"morphe_header_{theme}.xml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(VECTOR_HEAD + f'<bitmap xmlns:android="http://schemas.android.com/apk/res/android"\n    android:src="@drawable/morphe_header_custom_{theme}" />\n')


def header(w, h, text_color):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text = "UnoTube"
    fontfile = r"C:\Windows\Fonts\segoeuib.ttf"
    # 画像いっぱいに描く: 横幅に収まる最大の文字サイズ(縦は高さの 62% まで)
    margin = W * 0.01
    left = H * 0.08  # 左端で再生マークが切れないように
    probe = ImageFont.truetype(fontfile, 100)
    pb = probe.getbbox(text)
    per_f = 1.6 * 0.475 + 0.25 + (pb[2] - pb[0]) / 100  # 文字サイズ 1 あたりの全体の幅
    f = min((W - left - margin) / per_f, H * 0.62)
    font = ImageFont.truetype(fontfile, int(f))
    tb = font.getbbox(text)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    r = f * 0.475
    gw = r * 1.6  # 三角形の幅のぶん
    gap = f * 0.25
    total = gw + gap + tw
    # 公式ロゴと同じく左寄せで、縦は中央
    x0 = left
    cy = H / 2
    img.alpha_composite(glyph((W, H), x0 + r * 0.55, cy, r, r * 0.22))
    ImageDraw.Draw(img).text((x0 + gw + gap - tb[0], cy - th / 2 - tb[1]), text, font=font, fill=text_color + (255,))
    if x0 + total > W:
        sys.exit(f"header: text overflows ({x0 + total:.0f} > {W})")
    return img.resize((w, h), Image.LANCZOS)


def main():
    icon_dir = os.path.join(OUT, "icon")
    for dpi, px in ICON_SIZES.items():
        d = os.path.join(icon_dir, f"mipmap-{dpi}")
        os.makedirs(d, exist_ok=True)
        icon_background(px).save(os.path.join(d, "morphe_adaptive_background_custom.png"))
        icon_foreground(px).save(os.path.join(d, "morphe_adaptive_foreground_custom.png"))
    write_vectors(icon_dir)
    write_overrides(icon_dir)

    header_dir = os.path.join(OUT, "header")
    for dpi, (w, h) in HEADER_SIZES.items():
        d = os.path.join(header_dir, f"drawable-{dpi}")
        os.makedirs(d, exist_ok=True)
        header(w, h, TEXT_DARK).save(os.path.join(d, "morphe_header_custom_dark.png"))
        header(w, h, TEXT_LIGHT).save(os.path.join(d, "morphe_header_custom_light.png"))

    # 目視用: 角丸マスクしたアイコン + 暗/明背景のヘッダー
    px = 432
    ic = icon_background(px).convert("RGBA")
    ic.alpha_composite(icon_foreground(px))
    m = Image.new("L", (px, px), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, px - 1, px - 1], radius=px * 0.3, fill=255)
    pv = Image.new("RGB", (1140, 460), (40, 40, 40))
    pv.paste(ic, (14, 14), m)
    for i, (bg, col) in enumerate((((24, 24, 37), TEXT_DARK), ((239, 241, 245), TEXT_LIGHT))):
        hd = header(*HEADER_SIZES["xxxhdpi"], col)
        box = Image.new("RGB", (660, 212), bg)
        box.paste(hd, (0, 0), hd)
        pv.paste(box, (466, 14 + i * 226))
    pv.save(os.path.join(OUT, "preview.png"))
    print("ok:", OUT)


if __name__ == "__main__":
    main()
