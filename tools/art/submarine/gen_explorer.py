"""Generates explorer.svg, explorer_blink.svg, explorer_curious.svg (frame 520x300).

Only the face differs between the three files; body, hair, arms and wheel are byte-identical.
"""
import math
import os
import sys

sys.dont_write_bytecode = True  # keep the tools/art tree free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ink import ink_closed, ink_open, poly, _f  # noqa: E402
from svgkit import GRAIN_DEFS, cr, ellipse_path, wobble_ellipse, Doc  # noqa: E402

OUT = '#3b2a22'
SKIN, SKIN_SH, SKIN_LIT = '#f6c9a5', '#dc9f7d', '#fde3cc'
HAIR, HAIR_SH, HAIR_LIT = '#7a3e1d', '#55260f', '#a5643a'
SUIT, SUIT_SH, SUIT_LIT = '#f2a93b', '#c97a22', '#f9c873'
COLLAR, COLLAR_SH = '#e5862f', '#b8601c'
EYE, PUPIL = '#fbf6f2', '#1d1416'
WHEEL, WHEEL_SH, WHEEL_LIT = '#c3c8d6', '#858ba4', '#eef1f7'

# ---------------- shapes ----------------
# face silhouette; the nose is a bulb that grows out of the profile (reference p2/p5), not a separate ball
FACE = cr([(226, 106), (230, 86), (244, 72), (264, 67), (286, 71), (300, 83), (305, 94), (307, 101), (312, 102),
           (318, 106), (321, 113), (318, 120), (311, 123.5), (306, 124, 1), (306.5, 130), (303, 137), (295, 147),
           (279, 155), (261, 154), (245, 148), (233, 136)])
EAR = cr([(238, 106), (229, 101), (221, 106), (220, 116), (224, 126), (232, 131), (240, 128)])
# hair: rounded swoopy clumps (back, crown, fringe) - no sharp points; notches only point inward
HAIR_D = cr([(303, 88), (309, 80), (311, 70), (307, 60), (300, 53, 1), (292, 46), (281, 41), (270, 40, 1),
             (259, 37), (247, 39), (238, 43, 1), (226, 46), (214, 53), (208, 62, 1), (202, 74), (200, 88),
             (203, 100, 1), (200, 112), (203, 126), (208, 134, 1), (209, 142), (215, 148), (222, 146),
             (226, 138, 1), (231, 128), (235, 116), (240, 106), (245, 100), (251, 102), (255, 98), (259, 91, 1),
             (266, 89), (273, 93), (279, 89), (283, 82, 1), (290, 81), (298, 85)])
# one curled tuft on the crown, curling forward (a tapered lock)
TUFT_SPINE = 'M262 46 C261 37 270 31.5 279 33 C285.5 34 288 39 284 42.5'
NECK = cr([(250, 140, 1), (274, 142, 1), (276, 168, 1), (248, 168, 1)])
TORSO = cr([(206, 210, 1), (207, 182), (214, 167), (230, 158), (250, 154), (272, 155), (292, 160), (306, 170),
            (314, 186), (316, 210, 1)])
COLLAR_L = cr([(244, 152, 1), (256, 160), (262, 170, 1), (248, 172), (236, 166), (234, 158)])
COLLAR_R = cr([(274, 152, 1), (288, 156), (292, 164), (282, 172), (266, 171, 1), (268, 160)])
FAR_ARM = cr([(282, 170), (292, 158), (304, 146), (314, 134), (322, 125), (330, 131), (322, 143), (312, 156),
              (302, 170), (290, 180)])
NEAR_ARM = cr([(214, 180), (217, 166), (229, 157), (244, 159), (255, 169), (264, 186), (276, 200), (290, 197),
               (301, 180), (309, 164), (315, 150), (325, 153), (322, 170), (313, 192), (303, 212), (284, 217),
               (262, 212), (244, 202), (226, 192)])
CUFF_N = cr([(320, 152), (327, 143.5), (333, 145), (338, 155), (333, 163), (326, 162.5)])
HAND_N = cr([(331.0, 147.0), (335.4, 142.6), (341.6, 140.8), (347.8, 142.6), (352.2, 146.5), (354.4, 151.4), (353.0, 155.8), (353.9, 160.2), (351.3, 164.6), (345.1, 166.8), (338.1, 165.9), (332.8, 161.5), (330.2, 154.9)])
CUFF_F = cr([(327, 129), (333, 121.5), (339, 122.5), (343, 131), (338, 137), (332, 136)])
HAND_F = cr([(337.6, 121.1), (341.1, 116.3), (347.2, 113.6), (353.4, 114.5), (357.8, 118.0), (358.7, 123.3), (356.0, 127.7), (349.9, 129.9), (342.8, 129.5), (338.4, 126.4)])

WHEEL_C = (353, 141)
HANDS_DX = -9  # wheel, cuffs and gloves sit a little closer to the pilot


def wheel_paths():
    cx, cy = WHEEL_C
    outer = ellipse_path(cx, cy, 14.5, 29, 12)
    inner = ellipse_path(cx + 0.6, cy, 9.2, 23, 12)
    return outer, inner


def face_parts(mode):
    """Eyes, brows, mouth.  mode: 'open' | 'blink' | 'curious'."""
    o = []
    # eye geometry
    if mode == 'curious':
        ne = (274, 107.5, 10.6, 14.2)
        fe = (294.2, 106.5, 8.4, 13.6)
    else:
        ne = (274, 108, 9.6, 12.8)
        fe = (294, 107, 7.6, 12.2)
    NE = ellipse_path(ne[0], ne[1], ne[2], ne[3], -4)
    FE = ellipse_path(fe[0], fe[1], fe[2], fe[3], -4)
    if mode == 'blink':
        # closed lids: skin-coloured lids with a soft lid crease and a curved lash line
        for (e, ph) in ((ne, 0.2), (fe, 1.1)):
            cx, cy, rx, ry = e
            # faint upper-lid crease (the lid itself is just skin)
            dcr = 'M%s %s C%s %s %s %s %s %s' % (_f(cx - rx * 0.85), _f(cy - ry * 0.25), _f(cx - rx * 0.4),
                                                 _f(cy - ry * 0.75), _f(cx + rx * 0.45), _f(cy - ry * 0.75),
                                                 _f(cx + rx * 0.9), _f(cy - ry * 0.3))
            o.append('<path d="%s" fill="%s" opacity="0.9"/>' % (ink_open(dcr, 1.6, taper=(0.4, 0.4)), SKIN_SH))
            o.append('<path d="%s" fill="%s" opacity="0.55" filter="url(#b1_6)"/>' % (
                ellipse_path(cx, cy + ry * 0.05, rx * 0.8, ry * 0.32, -4), SKIN_SH))
            # lash line curving down (closed, relaxed)
            d = 'M%s %s C%s %s %s %s %s %s' % (_f(cx - rx * 1.05), _f(cy + 1.0), _f(cx - rx * 0.5), _f(cy + ry * 0.52),
                                               _f(cx + rx * 0.5), _f(cy + ry * 0.52), _f(cx + rx * 1.08), _f(cy - 0.2))
            o.append('<path d="%s" fill="%s"/>' % (ink_open(d, 3.0, taper=(0.25, 0.3), phase=ph), OUT))
            # two tiny lashes at the outer corner
            o.append('<path d="%s" fill="%s"/>' % (ink_open(
                'M%s %s C%s %s %s %s %s %s' % (_f(cx + rx * 0.9), _f(cy + 1.2), _f(cx + rx * 1.1), _f(cy + 2.5),
                                               _f(cx + rx * 1.3), _f(cy + 3.2), _f(cx + rx * 1.45), _f(cy + 3.4)),
                1.4, taper=(0.1, 0.6)), OUT))
    else:
        o.append('<path d="%s" fill="%s"/>' % (NE, EYE))
        o.append('<path d="%s" fill="%s"/>' % (FE, EYE))
        # soft lid shadow on the eye white
        o.append('<g clip-path="url(#cEyeN)"><path d="%s" fill="#e6d8d4"/></g>' % ellipse_path(ne[0] - 1, ne[1] - ne[3] * 0.9, ne[2] * 1.3, ne[3] * 0.45))
        o.append('<g clip-path="url(#cEyeF)"><path d="%s" fill="#e6d8d4"/></g>' % ellipse_path(fe[0] - 1, fe[1] - fe[3] * 0.9, fe[2] * 1.3, fe[3] * 0.45))
        ps = 0.86 if mode == 'curious' else 1.0
        for (e, px, py, prx, pry) in ((ne, 4.4, 1.4, 4.7, 6.4), (fe, 3.4, 1.0, 3.9, 6.0)):
            cx, cy = e[0] + px, e[1] + py
            o.append('<path d="%s" fill="#5a3320"/>' % ellipse_path(cx, cy, prx * ps * 1.12, pry * ps * 1.1, -4))
            o.append('<path d="%s" fill="%s"/>' % (ellipse_path(cx + 0.3, cy + 0.2, prx * ps * 0.78, pry * ps * 0.8, -4), PUPIL))
            o.append('<path d="%s" fill="#ffffff"/>' % ellipse_path(cx - 1.6, cy - 2.4, 1.7, 1.9))
            o.append('<path d="%s" fill="#ffffff" opacity="0.8"/>' % ellipse_path(cx + 1.6, cy + 2.6, 0.8, 0.8))
        o.append('<path d="%s" fill="%s"/>' % (ink_closed(NE, 0.5, 2.4, phase=0.3, shadow_dir=(0.2, -0.98)), OUT))
        o.append('<path d="%s" fill="%s"/>' % (ink_closed(FE, 0.5, 2.2, phase=1.3, shadow_dir=(0.2, -0.98)), OUT))
        # heavier upper lid lines
        for (e, ph) in ((ne, 0.0), (fe, 0.9)):
            cx, cy, rx, ry = e
            d = 'M%s %s C%s %s %s %s %s %s' % (_f(cx - rx * 1.02), _f(cy - ry * 0.15), _f(cx - rx * 0.8),
                                               _f(cy - ry * 1.12), _f(cx + rx * 0.8), _f(cy - ry * 1.12),
                                               _f(cx + rx * 1.04), _f(cy - ry * 0.2))
            o.append('<path d="%s" fill="%s"/>' % (ink_open(d, 3.0, taper=(0.3, 0.25), phase=ph), OUT))
    # brows
    if mode == 'curious':
        nb = 'M262 86 C267 79 276 77 285 81'
        fb = 'M290 80 C294 76 300 76 305 80'
    else:
        nb = 'M262 91 C267 85 277 84 286 88'
        fb = 'M290 87 C294 83.5 300 83.5 305 87'
    o.append('<path d="%s" fill="%s"/>' % (ink_open(nb, 4.8, taper=(0.35, 0.45), phase=0.5), HAIR_SH))
    o.append('<path d="%s" fill="%s"/>' % (ink_open(fb, 3.8, taper=(0.4, 0.45), phase=1.5), HAIR_SH))
    # mouth
    if mode == 'curious':
        M = wobble_ellipse(293, 134.5, 4.2, 5.2, -6, amp=0.03, n=8)
        o.append('<path d="%s" fill="#7a2a2a"/>' % M)
        o.append('<path d="%s" fill="#d9605a"/>' % ellipse_path(293.4, 137, 2.4, 1.8))
        o.append('<path d="%s" fill="%s"/>' % (ink_closed(M, 1.3, 2.6), OUT))
        # little cheek dimple
        o.append('<path d="%s" fill="%s" opacity="0.6"/>' % (ink_open('M283 128 C282 131 282 134 284 136', 1.3,
                                                                       taper=(0.4, 0.4)), OUT))
    else:
        M = cr([(279, 127, 1), (290, 131), (303, 125, 1), (302, 135), (294, 142), (285, 140)])
        o.append('<path d="%s" fill="#7a2a2a"/>' % M)
        o.append('<g clip-path="url(#cMouth)"><path d="%s" fill="#de6a62"/>'
                 '<path d="M279 126 C288 131 296 130 304 124 L304 130 C296 134 288 134 279 130 Z" fill="#fbf2ec"/></g>'
                 % cr([(282, 141), (288, 134), (296, 133), (302, 138), (296, 146), (286, 146)]))
        o.append('<path d="%s" fill="%s"/>' % (ink_closed(M, 1.2, 2.8), OUT))
        # smile creases
        o.append('<path d="%s" fill="%s"/>' % (ink_open('M276 124 C277 126 278 128 280 128.5', 1.5, taper=(0.4, 0.3)), OUT))
        o.append('<path d="%s" fill="%s"/>' % (ink_open('M302 122 C304 123 305 124 305 126', 1.3, taper=(0.4, 0.4)), OUT))
    return o, NE, FE


def explorer(mode):
    doc = Doc(520, 300)
    doc.d(GRAIN_DEFS)
    for s in (1, 1.6, 2.5):
        doc.d('<filter id="b%s" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="%s"/></filter>'
              % (str(s).replace('.', '_'), s))
    face, NE, FE = face_parts(mode)
    doc.clip('cFace', FACE)
    doc.clip('cHair', HAIR_D)
    doc.clip('cTorso', TORSO)
    doc.clip('cNear', NEAR_ARM)
    doc.clip('cFar', FAR_ARM)
    doc.clip('cGN', HAND_N)
    doc.clip('cGF', HAND_F)
    doc.clip('cEyeN', NE)
    doc.clip('cEyeF', FE)
    doc.clip('cMouth', cr([(279, 127, 1), (290, 131), (303, 125, 1), (302, 135), (294, 142), (285, 140)]))
    P_FACE = poly(FACE)
    P_HAIR = poly(HAIR_D)
    P_TORSO = poly(TORSO)

    # ---- far arm (behind torso) ----
    doc.path(FAR_ARM, SUIT)
    doc.a('<g clip-path="url(#cFar)">')
    doc.path(cr([(280, 170, 1), (300, 162), (320, 148), (340, 134), (350, 150, 1), (300, 200, 1)]), SUIT_SH)
    doc.a('</g>')
    doc.path(ink_closed(FAR_ARM, 1.6, 3.8, phase=0.6), OUT)

    # ---- steering column + wheel ----
    doc.a('<g transform="translate(%s 0)">' % _f(HANDS_DX))
    COL = cr([(352, 150, 1), (360, 148, 1), (376, 200, 1), (364, 202, 1)])
    doc.path(COL, '#6c7390')
    doc.path(ink_open('M355 152 C359 166 363 182 367 198', 1.6, taper=(0.2, 0.2)), '#a7aec4')
    doc.path(ink_closed(COL, 1.2, 2.6), OUT)
    outer, inner = wheel_paths()
    RING = outer + inner
    doc.a('<path d="%s" fill="%s" fill-rule="evenodd"/>' % (RING, WHEEL))
    doc.d('<clipPath id="cRing"><path d="%s" clip-rule="evenodd"/></clipPath>' % RING)
    doc.a('<g clip-path="url(#cRing)">')
    doc.path(ellipse_path(WHEEL_C[0] + 4, WHEEL_C[1] + 4, 14.5, 29, 12), WHEEL_SH)
    doc.a('</g>')
    # spokes + hub
    cx, cy = WHEEL_C
    for (ang) in (-80, 40, 160):
        a = math.radians(ang)
        x2 = cx + math.cos(a) * 8.0 * 0.6
        y2 = cy + math.sin(a) * 20.0
        doc.path(ink_open('M%s %s L%s %s' % (_f(cx), _f(cy), _f(x2), _f(y2)), 3.2, taper=(0.0, 0.0), wend=2.6), WHEEL_SH)
    HUB = ellipse_path(cx + 0.5, cy, 4.6, 6.6, 14)
    doc.path(HUB, '#cf2c43')
    doc.path(ellipse_path(cx - 0.8, cy - 2, 1.5, 2.0, 14), '#fbd3d3')
    doc.path(ink_closed(HUB, 1.0, 2.0), OUT)
    doc.path(ink_open('M%s %s C%s %s %s %s %s %s' % (_f(cx - 9.5), _f(cy + 8), _f(cx - 11), _f(cy - 6), _f(cx - 7),
                                                     _f(cy - 18), _f(cx - 1), _f(cy - 23)), 2.0, taper=(0.3, 0.3)),
             WHEEL_LIT)
    doc.path(ink_closed(outer, 1.5, 3.4, phase=0.2), OUT)
    doc.path(ink_closed(inner, 1.0, 2.2, phase=1.2), OUT)
    doc.a('</g>')

    # ---- torso ----
    doc.path(TORSO, SUIT)
    doc.a('<g clip-path="url(#cTorso)">')
    doc.path(cr([(290, 150, 1), (300, 168), (308, 190), (304, 214, 1), (330, 214, 1), (330, 150, 1)]), SUIT_SH)
    doc.path(cr([(250, 156, 1), (262, 160), (276, 158, 1), (276, 176, 1), (250, 176, 1)]), SUIT_SH)
    doc.path(ink_open('M224 170 C232 162 244 158 254 157', 4, taper=(0.3, 0.3)), SUIT_LIT, 'filter="url(#b1)"')
    doc.a('</g>')
    doc.path(ink_open('M263 172 C264 182 265 194 266 206', 1.6, taper=(0.1, 0.1)), SUIT_SH)
    doc.path(TORSO, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(TORSO, 1.8, 4.2, phase=2.2), OUT)

    # ---- neck ----
    doc.path(NECK, SKIN_SH)
    doc.path(ink_closed(NECK, 1.2, 2.6, inner_polys=[P_FACE, P_TORSO]), OUT)

    # ---- collar ----
    for C, ph in ((COLLAR_L, 0.1), (COLLAR_R, 1.4)):
        doc.path(C, COLLAR)
        doc.path(ink_closed(C, 1.4, 3.0, phase=ph), OUT)
    doc.path(ink_open('M238 160 C242 164 248 168 256 168', 2.2, taper=(0.3, 0.3)), '#f7b56a')
    doc.path(ink_open('M276 166 C282 166 286 164 289 160', 1.8, taper=(0.3, 0.3)), COLLAR_SH)
    # zipper pull
    ZIP = cr([(261, 172, 1), (266, 172, 1), (266.5, 180), (263.5, 182), (260.5, 180)])
    doc.path(ZIP, '#d9d2c6')
    doc.path(ink_closed(ZIP, 0.9, 1.8), OUT)

    # ---- hair back mass is part of HAIR_D; draw ear first under? ear sits on top of hair ----
    # head skin
    doc.path(FACE, SKIN)
    doc.a('<g clip-path="url(#cFace)">')
    # cel shadow: back of the head and under the jaw (light from upper left -> shadow lower right)
    doc.path(cr([(250, 156, 1), (270, 150), (290, 140), (302, 128), (308, 126, 1), (324, 160, 1)]), SKIN_SH)
    doc.path(ink_open('M234 120 C236 104 244 92 256 86', 7, taper=(0.4, 0.4)), SKIN_LIT, 'filter="url(#b2_5)"')
    # blush
    doc.path(ellipse_path(279, 124, 8.5, 5.2, -8), '#f0927c', 'opacity="0.55" filter="url(#b1_6)"')
    # nose bulb: one cel shadow tucked underneath, a soft highlight on top
    doc.path(ellipse_path(314, 120.5, 9.5, 4.6, -12), SKIN_SH)
    doc.path(ellipse_path(312.5, 107.6, 3.0, 1.8, -15), SKIN_LIT)
    doc.path(ellipse_path(312.8, 107.4, 1.4, 0.9, -15), '#fff6ec')
    doc.a('</g>')
    # silhouette ink, thin (almost gone) on the lit top edges so the nose top melts into the face
    doc.path(ink_closed(FACE, 1.6, 4.4, inner_polys=[P_HAIR], inner_factor=0.6, phase=0.9, gap_lit=True), OUT)
    # the nose is inked on its underside and tip only
    doc.path(ink_open('M305 123.5 C309 125.6 315 124.6 318.6 121 C321.4 118 322 112.6 319.6 108.4', 3.6,
                      taper=(0.25, 0.55)), OUT)
    doc.path(ink_open('M307.5 119.5 C308.6 121 310.4 121.6 312 121.2', 1.2, taper=(0.4, 0.4)), OUT, 'opacity="0.6"')

    # ---- hair: rounded clumps ----
    doc.path(HAIR_D, HAIR)
    doc.a('<g clip-path="url(#cHair)">')
    # cel shadow: underside of the mop and the nape
    doc.path(cr([(200, 92, 1), (214, 100), (228, 112), (238, 126), (232, 152, 1), (196, 152, 1)]), HAIR_SH)
    # shadow tucked under each fringe clump
    doc.path(cr([(240, 112, 1), (246, 99), (256, 96), (262, 88), (272, 90), (280, 86), (286, 79), (296, 80),
                 (306, 86), (312, 96, 1), (312, 112, 1)]), HAIR_SH)
    # shine: broken band on the upper-left of the mop (light from the upper left)
    doc.path(ink_open('M214 86 C217 72 226 60 240 52', 5.5, taper=(0.35, 0.45)), HAIR_LIT, 'filter="url(#b1)"')
    doc.path(ink_open('M248 48 C256 45 265 45 273 47', 4.4, taper=(0.4, 0.4)), HAIR_LIT, 'filter="url(#b1)"')
    doc.path(ink_open('M219 82 C222 74 227 67 234 61', 1.6, taper=(0.4, 0.4)), '#c98a5c')
    doc.a('</g>')
    # clump separations: soft shadow wedges sweeping from the crown into each notch, plus a few strands
    for d, w in (('M262 56 C264 68 263 80 259 91', 3.4), ('M281 58 C286 66 287 74 283 82', 3.0),
                 ('M226 66 C222 88 222 112 226 137', 3.0), ('M300 53 C292 58 288 64 287 70', 2.6),
                 ('M270 40 C268 46 268 52 270 58', 2.6), ('M238 43 C236 50 236 57 238 63', 2.6),
                 ('M208 62 C214 66 218 72 220 78', 2.6), ('M203 100 C209 102 213 106 215 111', 2.6),
                 ('M208 134 C213 133 217 132 220 130', 2.2)):
        doc.path(ink_open(d, w, taper=(0.45, 0.25)), HAIR_SH, 'opacity="0.9"')
    for d, w in (('M212 74 C210 92 211 112 214 126', 1.2), ('M252 60 C254 72 254 82 252 92', 1.0),
                 ('M270 56 C274 66 276 76 274 86', 1.0)):
        doc.path(ink_open(d, w, taper=(0.4, 0.4)), HAIR_SH)
    doc.path(HAIR_D, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(HAIR_D, 1.8, 4.4, inner_polys=[P_FACE], inner_factor=0.7, phase=0.2), OUT)
    # the curled tuft
    TUFT = ink_open(TUFT_SPINE, 7.5, step=2.0, taper=(0.02, 0.9), wobble=0.0)
    doc.path(TUFT, HAIR)
    doc.path(ink_open('M265 40 C267 36 271 34 276 34', 1.8, taper=(0.4, 0.4)), HAIR_LIT)
    doc.path(ink_closed(TUFT, 1.2, 2.8, inner_polys=[P_HAIR], inner_factor=0.4, phase=0.7), OUT)

    # ---- ear (over the hair) ----
    doc.path(EAR, SKIN)
    doc.path('M228 108 C224 112 224 120 228 125 C226 120 226 113 228 108 Z', SKIN_SH)
    doc.path(ink_open('M234 110 C229 110 227 116 230 122', 1.5, taper=(0.3, 0.3)), OUT, 'opacity="0.85"')
    doc.path(ink_closed(EAR, 1.4, 3.0, inner_polys=[P_FACE], inner_factor=0.6), OUT)

    # ---- face features ----
    for s in face:
        doc.a(s)

    # ---- near arm ----
    doc.path(NEAR_ARM, SUIT)
    doc.a('<g clip-path="url(#cNear)">')
    doc.path(cr([(214, 186, 1), (236, 182), (252, 178), (262, 194), (290, 200), (306, 184), (314, 166),
                 (319, 152), (334, 156, 1), (310, 230, 1), (210, 230, 1)]), SUIT_SH)
    doc.path(ink_open('M220 172 C226 163 236 160 246 163', 3.6, taper=(0.3, 0.3)), SUIT_LIT, 'filter="url(#b1)"')
    doc.path(ink_open('M302 186 C305 176 309 166 313 157', 2.8, taper=(0.3, 0.3)), SUIT_LIT, 'filter="url(#b1)"')
    doc.a('</g>')
    # sleeve folds
    doc.path(ink_open('M240 168 C244 172 246 176 247 181', 1.4, taper=(0.3, 0.3)), SUIT_SH)
    doc.path(ink_open('M311 176 C314 175 317 175 320 176', 1.3, taper=(0.3, 0.3)), SUIT_SH)
    doc.path(ink_open('M313 167 C316 166 319 166 322 167', 1.2, taper=(0.3, 0.3)), SUIT_SH)
    doc.path(NEAR_ARM, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(NEAR_ARM, 1.8, 4.2, inner_polys=[P_TORSO], inner_factor=0.65, phase=1.0), OUT)

    # ---- bare hands (fists wrapped round the wheel rim); the cuffs are the suit sleeves ----
    doc.a('<g transform="translate(%s 0)">' % _f(HANDS_DX))
    for (CF, G, cid, fingers, ph) in (
            (CUFF_F, HAND_F, 'cGF', [('M352 116 C355 117.5 357 119.5 358 122', 1.1),
                                     ('M351.5 122.5 C354 123.8 356 125.2 357 127.4', 1.1),
                                     ('M340 121 C344 118.5 348 117.5 351.5 118.2', 1.2)], 0.5),
            (CUFF_N, HAND_N, 'cGN', [('M346 147 C349.5 148 352 149.6 353.6 152', 1.3),
                                     ('M346 155 C349.5 155.5 351.6 156.8 353.4 158.4', 1.3),
                                     ('M344 161.5 C347 162 349.4 163.2 350.6 165', 1.2),
                                     ('M334.5 149 C338 146.5 343 145.5 347.5 146.6', 1.4)], 1.5)):
        doc.path(CF, SUIT)
        doc.path(ink_open(cr(poly(CF)[2:6], False), 1.6, taper=(0.3, 0.3)), SUIT_SH)
        doc.path(ink_closed(CF, 1.2, 2.6, phase=ph), OUT)
        doc.path(G, SKIN)
        doc.a('<g clip-path="url(#%s)">' % cid)
        bb = poly(G)
        xs = [p[0] for p in bb]
        ys = [p[1] for p in bb]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        doc.path(ellipse_path(cx + 7, cy + 8, 14, 9, -25), SKIN_SH)
        doc.path(ellipse_path(cx - 4, cy - 4.5, 4.5, 2.2, -25), SKIN_LIT, 'opacity="0.9" filter="url(#b1)"')
        doc.a('</g>')
        for d, w in fingers:
            doc.path(ink_open(d, w, taper=(0.3, 0.35)), OUT, 'opacity="0.85"')
        doc.path(ink_closed(G, 1.3, 3.2, phase=ph), OUT)

    doc.a('</g>')
    return doc.render()


def write(outdir):
    for mode, name in (('open', 'explorer'), ('blink', 'explorer_blink'), ('curious', 'explorer_curious')):
        with open(os.path.join(outdir, name + '.svg'), 'w') as f:
            f.write(explorer(mode))


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else '.')
    print('ok')
