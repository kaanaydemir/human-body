#!/usr/bin/env python3
"""Foreground tissue (layer 5, scroll 1.3): fg_bottom_1..3, fg_top_1..2.

Every silhouette, terminator, highlight crescent, streak, ink break and hatch below is placed by hand;
crescent.py only does the cel painting.  Run from the repo root:
    python3 -I tools/art/foreground-fx/gen.py          (everything)
    python3 -I tools/art/foreground-fx/gen_fg.py [b1 b2 b3 t1 t2] [--out DIR]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geo import FILTERS_FG  # noqa: E402
from crescent import Fold  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ENV = os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')

# One palette for the whole foreground plane (finding 4; reference p6 front mound #b0262e V .69 S .78).
PAL = {
    'base': '#c8262d',       # flat base
    'shadow': '#891a24',     # the one cel shadow
    'cast': '#891a24',       # shadow a front fold drops on the fold behind (same single shadow tone)
    'hl': '#ea6a55',         # broad highlight crescent
    'streak': '#f3b2a2',     # broken pale streak inside the crescent
    'ink': '#5a1a1c',        # silhouette ink
    'hatch_lit': '#7c1721',  # short hatches on the lit base
    'hatch_shade': '#a92e36',  # short hatches inside the shadow
}

# Hanging lips: no reference panel shows a near overhang, so the top plane is read by value: one step deeper
# than the ceiling (V ~.62 base vs ceiling ~.66-.72) and more saturated, with the same cel structure.
PAL_TOP = dict(PAL)
PAL_TOP.update({
    'base': '#9e2029',
    'shadow': '#6c1620',
    'cast': '#6c1620',
    'hl': '#d0544a',
    'streak': '#e8a092',
    'ink': '#4c1219',
    'hatch_lit': '#7a1620',
    'hatch_shade': '#8e2a32',
})

# softness of the whole near plane (body + ink together), see README "depth of field"
SOFT = 0.0


def build(W, H, kind, folds, fname, out_dir):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', '<defs>']
    o.append(FILTERS_FG)
    if SOFT:
        o.append(f'<filter id="soft" x="-40" y="-40" width="{W + 80}" height="{H + 80}" filterUnits="userSpaceOnUse">'
                 f'<feGaussianBlur stdDeviation="{SOFT}"/></filter>')
    for f in folds:
        o.append(f.clip_def())
    for i in range(1, len(folds)):
        o.append(f'<clipPath id="behind{i}">' + ''.join(f'<path d="{folds[j].d}"/>' for j in range(i)) + '</clipPath>')
    o.append('</defs>')
    o.append('<g filter="url(#soft)">' if SOFT else '<g>')
    for i, f in enumerate(folds):
        o.append(f'<g id="{f.name}">')
        o.append(f.svg(behind_clip=(f'behind{i}' if i > 0 else None)))
        o.append('</g>')
    # shared low-contrast painterly grain over the silhouettes (no mottle: its pink wash cost .03 S and the
    # reference's near mounds are flat cel fills)
    union = ''.join(f'<path d="{f.d}"/>' for f in folds)
    o.append(f'<g filter="url(#grain)">{union}</g>')
    o.append('</g>')
    o.append('</svg>')
    s = '\n'.join(o) + '\n'
    path = os.path.join(out_dir, fname)
    with open(path, 'w') as fh:
        fh.write(s)
    print(fname, f'{len(s) / 1024:.0f} KB')


# =========================================================================== fg_bottom_1  640x300
def fg_bottom_1(out):
    W, H = 640, 300
    A = Fold('b1A', 'bottom',
             [(-10, 360), (14, 300), (40, 238), (92, 172), (168, 124), (262, 100), (356, 104), (436, 132),
              (490, 178), (518, 238), (528, 300), (530, 360)],
             [(-60, 40), (300, 30), (440, 84), (474, 146), (440, 182), (376, 204), (300, 222), (220, 242),
              (140, 266), (70, 296), (10, 344), (-60, 344)],
             W=W, H=H, pal=PAL, hl=(34, 340, 5, 23, 1.0),
             streaks=[(66, 136, 14, 2.6), (164, 246, 13, 2.7), (262, 310, 14, 2.1)],
             ink_breaks=[(126, 150), (236, 252)],
             hatches=[(120, 44, 3, 26, 3), (214, 36, 2, 22, -2), (402, 54, 3, 24, 2)])
    B = Fold('b1B', 'bottom',
             [(262, 380), (282, 300), (312, 250), (366, 208), (440, 182), (520, 178), (584, 198), (620, 236),
              (630, 300), (632, 360)],
             [(240, 110), (500, 110), (552, 168), (534, 202), (480, 222), (404, 242), (336, 266), (288, 300),
              (250, 344)],
             W=W, H=H, pal=PAL, hl=(298, 552, 4, 19, 1.0), cast=(14, -6),
             streaks=[(330, 398, 12, 2.4), (420, 500, 12, 2.2)],
             ink_breaks=[(384, 398)],
             hatches=[(474, 36, 2, 24, 2), (566, 44, 3, 20, 3)])
    C = Fold('b1C', 'bottom',
             [(30, 380), (44, 300), (74, 262), (130, 234), (206, 222), (278, 230), (330, 258), (352, 300),
              (356, 360)],
             [(0, 170), (240, 170), (290, 222), (276, 248), (226, 262), (160, 274), (100, 290), (40, 330)],
             W=W, H=H, pal=PAL, hl=(62, 262, 4, 16, 1.0), cast=(12, -5),
             streaks=[(92, 150, 11, 2.1), (172, 226, 11, 1.9)],
             ink_breaks=[(150, 162)],
             hatches=[(122, 26, 2, 20, 2), (252, 24, 2, 22, -2)])
    build(W, H, 'bottom', [A, B, C], 'fg_bottom_1.svg', out)


# =========================================================================== fg_bottom_2  820x320
def fg_bottom_2(out):
    W, H = 820, 320
    A = Fold('b2A', 'bottom',
             [(300, 400), (318, 320), (352, 250), (420, 180), (510, 128), (612, 104), (706, 112), (772, 150),
              (802, 214), (808, 320), (810, 400)],
             [(260, 60), (640, 40), (756, 116), (754, 180), (714, 212), (640, 234), (560, 254), (480, 274),
              (410, 302), (360, 340), (260, 360)],
             W=W, H=H, pal=PAL, hl=(336, 650, 5, 25, 1.0),
             streaks=[(370, 440, 15, 2.7), (462, 560, 14, 2.9), (580, 630, 14, 2.1)],
             ink_breaks=[(450, 470), (570, 586)],
             hatches=[(430, 50, 3, 26, 3), (560, 40, 2, 24, -2), (720, 58, 3, 24, 2)])
    B = Fold('b2B', 'bottom',
             [(10, 380), (16, 320), (40, 268), (96, 216), (176, 186), (262, 182), (336, 204), (384, 246),
              (404, 320), (406, 380)],
             [(-40, 100), (290, 100), (338, 186), (322, 222), (270, 240), (200, 256), (130, 276), (70, 304),
              (20, 340), (-40, 360)],
             W=W, H=H, pal=PAL, hl=(30, 300, 5, 20, 1.0), cast=(14, -6),
             streaks=[(58, 120, 13, 2.4), (142, 230, 13, 2.6), (246, 282, 13, 1.9)],
             ink_breaks=[(124, 140), (234, 246)],
             hatches=[(150, 38, 3, 24, 2), (300, 40, 2, 22, -2)])
    C = Fold('b2C', 'bottom',
             [(330, 380), (340, 320), (380, 280), (446, 252), (520, 244), (590, 260), (634, 292), (646, 320),
              (648, 380)],
             [(320, 180), (580, 180), (600, 262), (560, 284), (490, 294), (420, 306), (360, 330), (330, 350)],
             W=W, H=H, pal=PAL, hl=(360, 560, 4, 16, 1.0), cast=(12, -5),
             streaks=[(392, 450, 11, 2.1), (470, 528, 11, 1.9)],
             ink_breaks=[(452, 466)],
             hatches=[(430, 24, 2, 20, 2), (590, 26, 2, 18, -2)])
    build(W, H, 'bottom', [A, B, C], 'fg_bottom_2.svg', out)


# =========================================================================== fg_bottom_3  560x280
def fg_bottom_3(out):
    W, H = 560, 280
    A = Fold('b3A', 'bottom',
             [(0, 340), (10, 280), (34, 220), (88, 152), (170, 104), (262, 88), (350, 104), (418, 150),
              (452, 214), (462, 280), (464, 340)],
             [(-60, 30), (300, 20), (380, 100), (384, 150), (344, 178), (280, 196), (200, 212), (120, 232),
              (56, 262), (10, 300), (-60, 320)],
             W=W, H=H, pal=PAL, hl=(26, 316, 5, 23, 1.0),
             streaks=[(52, 120, 14, 2.6), (140, 230, 13, 2.7), (248, 290, 14, 2.1)],
             ink_breaks=[(124, 140), (232, 246)],
             hatches=[(110, 44, 3, 26, 3), (240, 40, 2, 22, -2), (400, 58, 3, 22, 2)])
    B = Fold('b3B', 'bottom',
             [(300, 340), (316, 280), (350, 236), (414, 208), (484, 202), (530, 222), (548, 252), (552, 280),
              (553, 340)],
             [(280, 140), (490, 140), (500, 208), (474, 230), (420, 242), (362, 258), (318, 284), (300, 320)],
             W=W, H=H, pal=PAL, hl=(330, 500, 4, 16, 1.0), cast=(14, -6),
             streaks=[(356, 420, 11, 2.2), (440, 488, 11, 1.9)],
             ink_breaks=[(424, 436)],
             hatches=[(470, 26, 2, 20, 2)])
    C = Fold('b3C', 'bottom',
             [(8, 340), (14, 280), (40, 250), (96, 232), (162, 232), (210, 254), (226, 280), (228, 340)],
             [(-20, 180), (170, 180), (190, 240), (160, 256), (110, 264), (60, 278), (20, 300), (-20, 320)],
             W=W, H=H, pal=PAL, hl=(30, 170, 3, 13, 1.0), cast=(12, -5),
             streaks=[(58, 112, 10, 1.9)],
             ink_breaks=[(114, 124)],
             hatches=[(150, 22, 2, 18, 2)])
    build(W, H, 'bottom', [A, B, C], 'fg_bottom_3.svg', out)


# =========================================================================== fg_top_1  760x240
# Long overhanging fold lips (not pouches), content <= 560 x 150, centred in the contract canvas.
# Light from the front / upper-left: the rolled lower rim catches the light (reference p7, top right),
# the part that tucks back up into the ceiling and the right end are in the cel shadow.
def fg_top_1(out):
    W, H = 760, 240
    L0 = Fold('t1L0', 'top',
              [(440, -60), (452, 0), (474, 40), (524, 76), (588, 92), (633, 80), (652, 46), (658, 0), (658, -60)],
              [(430, -50), (466, 6), (520, 30), (580, 44), (624, 44), (640, 120), (440, 140)],
              W=W, H=H, pal=PAL_TOP, hl=(470, 600, 4, 13, 1.0),
              streaks=[(500, 560, 11, 1.9)],
              ink=(2.0, 5.5), ink_breaks=[],
              hatches=[(560, 30, 2, 18, 2)])
    L1 = Fold('t1L1', 'top',
              [(96, -60), (104, 0), (122, 46), (170, 92), (246, 124), (338, 140), (432, 138), (510, 120),
               (572, 90), (614, 50), (632, 0), (636, -60)],
              [(60, -40), (120, 0), (190, 36), (290, 54), (390, 60), (480, 56), (550, 44), (596, 60),
               (640, 140), (400, 220), (60, 160)],
              W=W, H=H, pal=PAL_TOP, hl=(130, 470, 5, 22, 1.0), cast=(12, 8),
              streaks=[(160, 240, 14, 2.6), (262, 360, 14, 2.7), (382, 430, 14, 2.1)],
              ink=(2.0, 6.0), ink_breaks=[(150, 166), (246, 260)],
              hatches=[(220, 48, 3, 24, -3), (420, 44, 2, 22, 2), (560, 30, 2, 18, 2)])
    build(W, H, 'top', [L0, L1], 'fg_top_1.svg', out)


# =========================================================================== fg_top_2  620x220
def fg_top_2(out):
    W, H = 620, 220
    L0 = Fold('t2L0', 'top',
              [(60, -60), (66, 0), (80, 36), (116, 66), (170, 78), (214, 66), (236, 34), (244, 0), (244, -60)],
              [(40, -50), (80, -4), (130, 24), (180, 32), (222, 26), (260, 100), (60, 120)],
              W=W, H=H, pal=PAL_TOP, hl=(84, 190, 4, 12, 1.0),
              streaks=[(100, 150, 10, 1.8)],
              ink=(2.0, 5.0),
              hatches=[(160, 26, 2, 16, 2)])
    L1 = Fold('t2L1', 'top',
              [(120, -60), (128, 0), (150, 44), (204, 88), (280, 114), (360, 124), (440, 114), (500, 88),
               (538, 50), (552, 0), (554, -60)],
              [(100, -40), (156, 6), (226, 36), (310, 50), (390, 52), (450, 46), (496, 36), (530, 50),
               (560, 120), (340, 200), (100, 140)],
              W=W, H=H, pal=PAL_TOP, hl=(156, 420, 5, 19, 1.0), cast=(-12, 8),
              streaks=[(180, 250, 13, 2.4), (276, 360, 13, 2.6)],
              ink=(2.0, 6.0), ink_breaks=[(166, 180), (260, 272)],
              hatches=[(240, 40, 2, 22, -2), (440, 38, 2, 20, 2)])
    build(W, H, 'top', [L0, L1], 'fg_top_2.svg', out)


ALL = {'b1': fg_bottom_1, 'b2': fg_bottom_2, 'b3': fg_bottom_3, 't1': fg_top_1, 't2': fg_top_2}


def main(argv):
    out = ENV
    if '--out' in argv:
        i = argv.index('--out')
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    os.makedirs(out, exist_ok=True)
    for k in (argv or list(ALL)):
        ALL[k](out)


if __name__ == '__main__':
    main(sys.argv[1:])
