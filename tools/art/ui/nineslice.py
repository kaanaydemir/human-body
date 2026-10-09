"""9-slice test harness that mimics Phaser NineSlice (stretched, bilinear)."""
from PIL import Image


def nine(img, w, h, m=40):
    W, H = img.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    xs_src = [0, m, W - m, W]
    ys_src = [0, m, H - m, H]
    xs_dst = [0, m, w - m, w]
    ys_dst = [0, m, h - m, h]
    for i in range(3):
        for j in range(3):
            box = (xs_src[i], ys_src[j], xs_src[i + 1], ys_src[j + 1])
            dw = xs_dst[i + 1] - xs_dst[i]
            dh = ys_dst[j + 1] - ys_dst[j]
            if dw <= 0 or dh <= 0:
                continue
            tile = img.crop(box).resize((dw, dh), Image.BILINEAR)
            out.alpha_composite(tile, (xs_dst[i], ys_dst[j]))
    return out
