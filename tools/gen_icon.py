# -*- coding: utf-8 -*-
"""
Generate multi-resolution ICO using pure Pillow (no Cairo dependency).
"""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, os.pardir))
ICO_PATH = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
SIZES = [16, 32, 48, 64, 128, 256]


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)


def draw_icon(size=512):
    img = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(img)

    # Gradient background (dark teal -> near black)
    top = (10, 15, 13)
    bottom = (13, 31, 23)
    for y in range(size):
        t = y / (size - 1)
        color = _lerp_color(top, bottom, t)
        draw.line([(0, y), (size, y)], fill=color)

    # Radial glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy = size // 2, int(size * 0.43)
    r = int(size * 0.39)
    gdraw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(0, 255, 136, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=size * 0.05))
    img.alpha_composite(glow)

    # Matrix rain lines
    teal = (10, 169, 110, 100)
    for x in [int(size * t) for t in [0.12, 0.2, 0.27, 0.35, 0.43, 0.51, 0.59, 0.67, 0.75, 0.83]]:
        y0 = int(size * (0.02 + ((x % 37) / 300)))
        y1 = int(size * (0.35 + ((x % 23) / 250)))
        draw.line([(x, y0), (x, y1)], fill=teal, width=max(1, size // 256 * 2))

    # Hooded figure
    hood = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(hood)
    # Hood silhouette
    path = [
        (size*0.5, size*0.215), (size*0.41, size*0.27), (size*0.35, size*0.35), (size*0.33, size*0.43),
        (size*0.31, size*0.65), (size*0.33, size*0.71), (size*0.37, size*0.69), (size*0.45, size*0.65),
        (size*0.47, size*0.64), (size*0.5, size*0.65), (size*0.53, size*0.64), (size*0.55, size*0.65),
        (size*0.63, size*0.69), (size*0.67, size*0.71), (size*0.69, size*0.65), (size*0.67, size*0.43),
        (size*0.65, size*0.35), (size*0.59, size*0.27)
    ]
    hdraw.polygon(path, fill=(15, 18, 22, 255))
    # Outline glow
    outline = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(outline)
    odraw.line(path + [path[0]], fill=(0, 255, 136, 120), width=max(2, size // 128))
    outline = outline.filter(ImageFilter.GaussianBlur(radius=size * 0.004))
    img.alpha_composite(hood)
    img.alpha_composite(outline)

    # Face circle
    hdraw.ellipse([(size*0.5 - size*0.075, size*0.45 - size*0.075), (size*0.5 + size*0.075, size*0.45 + size*0.075)],
                  fill=(15, 20, 24, 255), outline=(0, 255, 136, 180), width=max(2, size // 128))

    # Eyes
    for ex in [size*0.466, size*0.534]:
        e = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ed = ImageDraw.Draw(e)
        ed.ellipse([(ex - size*0.013, size*0.45 - size*0.01), (ex + size*0.013, size*0.45 + size*0.01)], fill=(0, 255, 136, 255))
        e = e.filter(ImageFilter.GaussianBlur(radius=size * 0.006))
        img.alpha_composite(e)

    # Neon badge (without text)
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bx, by = size*0.305, size*0.69
    bw, bh, br = size*0.39, size*0.17, size*0.035
    bd.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=int(br), fill=(11, 15, 18, 255), outline=(0, 255, 136, 255), width=max(3, size // 128 * 3))
    bd.line([(bx + size*0.05, by + size*0.05), (bx + size*0.105, by + size*0.05)], fill=(0, 255, 136, 255), width=max(4, size // 128 * 4))
    bd.line([(bx + size*0.08, by + size*0.03), (bx + size*0.08, by + size*0.08)], fill=(0, 255, 136, 255), width=max(4, size // 128 * 4))
    badge = badge.filter(ImageFilter.GaussianBlur(radius=size * 0.003))
    img.alpha_composite(badge)

    # Subtle border
    draw.rounded_rectangle([(size*0.012, size*0.012), (size*0.988, size*0.988)], radius=int(size*0.06), outline=(10, 169, 110, 100), width=max(3, size // 128 * 3))

    return img


def build_ico():
    os.makedirs(os.path.dirname(ICO_PATH), exist_ok=True)
    base = draw_icon(512)
    sizes = [(s, s) for s in SIZES]
    base.save(ICO_PATH, format="ICO", sizes=sizes)
    print(f"[OK] Generated ICO: {ICO_PATH}")


if __name__ == "__main__":
    build_ico()