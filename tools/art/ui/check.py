#!/usr/bin/env python3
"""Render + numeric checks for the ui group.

    python3 -I tools/art/ui/check.py [OUT_DIR] [--svg-dir DIR]

Needs Pillow and node (tools/render-svg.mjs). Writes into OUT_DIR (default tools/out/ui/check):
  <name>.png            raw 1x render (transparent)          <name>_x3.png  3x on panel cream
  nine_sheet.png        panel 9-sliced at every HUD size over vessel red, with badge + progress icon
  cmp_caption.png       reference caption 4 (scaled to the game's caption height) above our 980x150 caption
Prints: panel fill mean (RGB/HSV, V std), outline width + core colour per side, badge mean and
flatness, progress-icon bounding box (must not touch the canvas border).
"""
import colorsys
import os
import subprocess
import sys

from PIL import Image, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
from nineslice import nine  # noqa: E402

NAMES = ['panel', 'badge', 'key_e', 'key_space', 'icon_objective', 'icon_progress']
CREAM = '#f9e9d0'
VESSEL = (142, 47, 56, 255)


def hx(c):
    return '#%02x%02x%02x' % tuple(int(round(v)) for v in c[:3])


def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    return 'H%3d S%.2f V%.2f' % (h * 360, s, v)


def render(svg, png, scale=1, bg='transparent'):
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'render-svg.mjs'), svg, png, str(scale), bg],
                   check=True, cwd=ROOT, capture_output=True)


def ink_width(pixels):
    w = 0.0
    for r, g, b, a in pixels:
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        w += max(0.0, min(1.0, (0.9 - lum) / (0.9 - 0.16))) * a / 255
    return w


def check_panel(png):
    im = Image.open(png).convert('RGBA')
    W, H = im.size
    c = im.crop((60, 50, W - 60, H - 50)).convert('RGB')
    m = ImageStat.Stat(c).mean
    vstd = ImageStat.Stat(c.convert('HSV')).stddev[2] / 255
    print('panel  fill %s %s Vstd %.3f' % (hx(m), hsv(m), vstd))
    for y0, y1, tag in ((6, 14, 'top inner band'), (H - 14, H - 6, 'bottom inner band')):
        mb = ImageStat.Stat(im.crop((60, y0, W - 60, y1)).convert('RGB')).mean
        print('panel  %-17s %s %s' % (tag, hx(mb), hsv(mb)))
    sides = {
        'top': [im.getpixel((W // 2, y)) for y in range(0, 16)],
        'bottom': [im.getpixel((W // 2, y)) for y in range(H - 16, H)],
        'left': [im.getpixel((x, H // 2)) for x in range(0, 16)],
        'right': [im.getpixel((x, H // 2)) for x in range(W - 16, W)],
    }
    for k, px in sides.items():
        dark = [p for p in px if p[3] > 200 and sum(p[:3]) < 300]
        core = hx([sum(p[i] for p in dark) / len(dark) for i in range(3)]) if dark else '-'
        print('panel  outline %-6s %.2f px core %s' % (k, ink_width(px), core))


def check_badge(png):
    im = Image.open(png).convert('RGBA')
    mask = im.getchannel('A').point(lambda a: 255 if a > 250 else 0)
    m = ImageStat.Stat(im.convert('RGB'), mask).mean
    sd = ImageStat.Stat(im.crop((14, 14, 82, 82)).convert('RGB')).stddev
    print('badge  opaque mean %s %s  interior RGB std %.1f %.1f %.1f' % (hx(m), hsv(m), *sd))


def check_icon(png):
    im = Image.open(png).convert('RGBA')
    bb = im.getchannel('A').getbbox()
    W, H = im.size
    ok = bb and bb[0] > 0 and bb[1] > 0 and bb[2] < W and bb[3] < H
    print('icon_progress  bbox %s in %dx%d  %s' % (bb, W, H, 'OK (clear of border)' if ok else 'TOUCHES BORDER'))


def sheets(out):
    panel = Image.open(os.path.join(out, 'panel.png')).convert('RGBA')
    badge = Image.open(os.path.join(out, 'badge.png')).convert('RGBA')
    icon = Image.open(os.path.join(out, 'icon_progress.png')).convert('RGBA')
    sizes = [(700, 112), (460, 112), (980, 150), (940, 92), (720, 420)]
    pad = 30
    Wd = max(w for w, _ in sizes) + 2 * pad
    Hd = sum(h for _, h in sizes) + pad * (len(sizes) + 1)
    bg = Image.new('RGBA', (Wd, Hd), VESSEL)
    y = pad
    for w, h in sizes:
        bg.alpha_composite(nine(panel, w, h), (pad, y))
        if (w, h) == (980, 150):
            b = badge.resize((76, 76), Image.LANCZOS)
            bg.alpha_composite(b, (pad + 70 - 38, y + 75 - 38))
        if (w, h) == (460, 112):
            bg.alpha_composite(icon, (pad + 40 + 150 - 32, y + 72 - 18))
        y += h + pad
    bg.save(os.path.join(out, 'nine_sheet.png'))
    # reference caption 4 (1536 px sheet) scaled to the game caption's height, above ours
    ref = Image.open(os.path.join(ROOT, 'reference.png')).convert('RGBA').crop((8, 254, 396, 318))
    s = 150 / 58.0
    ref = ref.resize((int(ref.width * s), int(ref.height * s)), Image.LANCZOS).crop((0, 0, 1000, int(64 * s)))
    cap = Image.new('RGBA', (1000, 150 + 20), VESSEL)
    cap.alpha_composite(nine(panel, 980, 150), (10, 10))
    cap.alpha_composite(badge.resize((76, 76), Image.LANCZOS), (10 + 70 - 38, 10 + 75 - 38))
    sheet = Image.new('RGBA', (1000, ref.height + cap.height + 10), (40, 40, 40, 255))
    sheet.alpha_composite(ref, (0, 0))
    sheet.alpha_composite(cap, (0, ref.height + 10))
    sheet.save(os.path.join(out, 'cmp_caption.png'))
    # 8x corner zoom: reference caption 4 top-left vs ours (same on-screen scale)
    rz = ref.crop((0, 0, 90, 90)).resize((360, 360), Image.NEAREST)
    gz = cap.crop((0, 0, 90, 90)).resize((360, 360), Image.NEAREST)
    z = Image.new('RGBA', (730, 360), (40, 40, 40, 255))
    z.alpha_composite(rz, (0, 0))
    z.alpha_composite(gz, (370, 0))
    z.save(os.path.join(out, 'cmp_corner.png'))


def main():
    args = sys.argv[1:]
    svg_dir = os.path.join(ROOT, 'public', 'assets', 'svg', 'ui')
    if '--svg-dir' in args:
        i = args.index('--svg-dir')
        svg_dir = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    out = os.path.abspath(args[0]) if args else os.path.join(ROOT, 'tools', 'out', 'ui', 'check')
    os.makedirs(out, exist_ok=True)
    for n in NAMES:
        svg = os.path.join(svg_dir, n + '.svg')
        render(svg, os.path.join(out, n + '.png'))
        render(svg, os.path.join(out, n + '_x3.png'), 3, CREAM)
    check_panel(os.path.join(out, 'panel.png'))
    check_badge(os.path.join(out, 'badge.png'))
    check_icon(os.path.join(out, 'icon_progress.png'))
    sheets(out)
    print('wrote renders + nine_sheet.png, cmp_caption.png, cmp_corner.png to', out)


if __name__ == '__main__':
    main()
