"""Generates sub_front.svg and sub_back.svg (frame 520x300).

sub_front: tail stub, ring band, ball fin, teardrop hull, hood, transparent dome glass, rim, beacon, red nose ball.
sub_back : the cockpit interior behind the explorer. Its upper third is see-through, so the red vessel shows
           through the glass as lavender-pink (reference panels 4 and 5).
"""
import math
import os
import sys

sys.dont_write_bytecode = True  # keep the tools/art tree free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ink import ink_closed, ink_open, poly, smooth, _f  # noqa: E402
from svgkit import GRAIN_DEFS, cr, ellipse_path, wobble_ellipse, Doc  # noqa: E402
from geom import *  # noqa: E402,F401,F403


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


RIM_C = [F, (392, 180), (236, 180), J_BOT]
NOSE = wobble_ellipse(NOSE_C[0], NOSE_C[1], NOSE_R[0], NOSE_R[1], NOSE_ROT, amp=0.012, n=10, phase=0.6)
FIN = cr(FIN_PTS)

# uniform-ish brush outline (finding: 4-5 px #3b2a22)
W_MIN, W_MAX = 3.8, 5.4


def rim_pt(t, dy=0.0):
    p = bez(*RIM_C, t)
    return (p[0], p[1] + dy)


def soft_filters(doc):
    for s in (1, 1.6, 2.5, 4, 7):
        doc.d('<filter id="b%s" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="%s"/></filter>'
              % (str(s).replace('.', '_'), s))


# =====================================================================
#  SUB FRONT
# =====================================================================

def sub_front():
    doc = Doc(520, 300)
    doc.d(GRAIN_DEFS)
    soft_filters(doc)
    P_HULL, P_HOOD, P_GLASS, P_FIN, P_NOSE, P_STUB, P_BAND = (
        poly(x) for x in (HULL_D, HOOD, GLASS, FIN, NOSE, STUB, BAND))
    for cid, d in (('cHull', HULL_D), ('cHood', HOOD), ('cGlass', GLASS), ('cFin', FIN), ('cNose', NOSE),
                   ('cStub', STUB), ('cBand', BAND)):
        doc.clip(cid, d)

    # ---------- tail stub (behind the hull) ----------
    doc.a('<g id="stub">')
    doc.path(STUB, HULL)
    doc.a('<g clip-path="url(#cStub)">')
    doc.path('M14 171 C30 174 46 175 64 174 L64 190 L14 190 Z', HULL_SH)
    doc.path(ink_open('M26 160.5 C36 158.5 46 158 58 158.5', 3.0, taper=(0.3, 0.3)), '#ffffff', 'opacity="0.95"')
    doc.a('</g>')
    doc.path(STUB, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(STUB, 3.0, 4.4, inner_polys=[P_HULL, P_BAND], inner_factor=0.6, wobble=0.06), OUT)
    # the opening at the tip (jet anchor 24,168)
    lip = ellipse_path(22.5, 168.5, 4.2, 9.6)
    doc.path(lip, '#f4e8de')
    doc.path(ellipse_path(22.5, 168.8, 2.5, 7.0), '#5a4a55')
    doc.path(ellipse_path(23.0, 170.2, 1.2, 4.0), '#9cc8ee', 'opacity="0.9"')
    doc.path(ink_closed(lip, 1.4, 2.6, wobble=0.04), OUT)
    doc.a('</g>')

    # ---------- red ball fin (behind hood and hull) ----------
    doc.a('<g id="fin">')
    doc.path(FIN, RED)
    doc.a('<g clip-path="url(#cFin)">')
    # cel shadow on the lower right of the ball and down the neck
    doc.path(cr([(67, 114), (85, 124), (107, 118), (119, 98), (119, 74, 1), (140, 74, 1), (140, 170, 1),
                 (40, 170, 1)]), RED_SH)
    doc.path(ellipse_path(91, 90, 16, 14, -30), RED_LIT, 'filter="url(#b2_5)"')
    # white comma specular
    doc.path(ink_open('M77 98 C77 88 82 80 90 76', 4.6, taper=(0.15, 0.6)), '#ffffff', 'opacity="0.95"')
    doc.path(ellipse_path(97, 74.5, 1.7, 1.4), '#ffffff', 'opacity="0.9"')
    doc.a('</g>')
    doc.path(FIN, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(FIN, W_MIN, W_MAX, inner_polys=[P_HULL, P_HOOD], inner_factor=0.6, phase=1.2, wobble=0.06), OUT)
    doc.a('</g>')

    # ---------- hull ----------
    doc.a('<g id="hull">')
    doc.path(HULL_D, HULL)
    doc.a('<g clip-path="url(#cHull)">')
    # soft light along the upper flank, following the swell of the body
    doc.path(cr([(40, 156), (120, 168), (230, 180), (340, 182), (430, 172), (470, 160), (470, 200), (420, 214),
                 (330, 222), (220, 220), (110, 208), (52, 190)]), HULL_LIT, 'filter="url(#b2_5)"')
    doc.path(cr([(70, 176), (130, 188), (230, 194), (340, 195), (420, 188), (446, 184), (442, 202),
                 (350, 210), (230, 210), (120, 202), (66, 192)]), '#fcf6ef', 'filter="url(#b4)"')
    # long glossy specular along the shoulder
    doc.path(ink_open('M124 194 C200 202 300 205 404 196', 3.6, taper=(0.25, 0.35)), '#ffffff', 'opacity="0.95"')
    doc.path(ink_open('M412 194 C418 193 424 191 430 189', 2.4, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.9"')
    # cel shadow: the belly (one shadow tone, follows the belly curve ~24 px inside)
    SHADE = cr([(20, 200, 1), (70, 225), (150, 244), (250, 250), (340, 249), (420, 238), (470, 222), (530, 196, 1),
                (530, 300, 1), (20, 300, 1)])
    doc.d('<clipPath id="cShade"><path d="%s"/></clipPath>' % SHADE)
    doc.a('<g clip-path="url(#cShade)">')
    doc.path(HULL_D, HULL_SH)
    doc.a('</g>')
    # cast shadow just under the cockpit rim
    up = [rim_pt(i / 40, 3.0) for i in range(41)]
    lo = [rim_pt(i / 40, 9.5 + 4.0 * math.sin(math.pi * i / 40)) for i in range(41)][::-1]
    doc.path(smooth(up + lo, True), HULL_SH)
    # warm bounce light from the vessel floor along the belly
    doc.path(ink_open('M96 243 C160 263 260 273 340 271 C400 267 436 257 452 249', 3.8, taper=(0.3, 0.3)),
             '#dba79c', 'filter="url(#b1)" opacity="0.8"')
    # a few hatch strokes in the belly shade
    for (x, y, l, a) in [(150, 252, 10, 64), (160, 256, 10, 66), (170, 259, 9, 68),
                         (404, 256, 9, 112), (414, 252, 9, 114), (424, 247, 8, 116)]:
        r = math.radians(a)
        x2, y2 = x + math.cos(r) * l, y + math.sin(r) * l
        doc.path(ink_open('M%s %s L%s %s' % (_f(x), _f(y), _f(x2), _f(y2)), 1.3, taper=(0.4, 0.4)), OUT,
                 'opacity="0.3"')
    doc.a('</g>')
    # mottle + grain over the whole hull
    doc.path(HULL_D, '#000', 'filter="url(#mottle)" opacity="0.22"')
    doc.path(HULL_D, '#000', 'filter="url(#grain)"')
    # two faint hand-painted scuffs
    doc.path(ellipse_path(318, 240, 1.8, 0.7, -10), '#a48d80', 'opacity="0.7"')
    doc.path(ink_open('M222 238 C226 237 230 237 233 238', 0.9, taper=(0.4, 0.4)), '#a48d80', 'opacity="0.75"')

    # ---- ring band around the tail ----
    doc.a('<g clip-path="url(#cHull)">')
    doc.path(BAND, RED)
    doc.a('<g clip-path="url(#cBand)">')
    doc.a('<g clip-path="url(#cShade)">')
    doc.path(BAND, RED_SH)
    doc.a('</g>')
    doc.path(ink_open('M71 156 C66 168 65 182 67 198', 4.0, taper=(0.3, 0.4)), RED_LIT, 'filter="url(#b1)"')
    doc.path(ink_open('M75 152 C71 160 69 168 69 177', 2.2, taper=(0.3, 0.5)), '#ffffff', 'opacity="0.9"')
    doc.a('</g>')
    doc.path(ink_open('M72 134 C58 156 56 204 72 236', 2.4, taper=(0.05, 0.05)), OUT)
    doc.path(ink_open('M96 128 C84 156 84 210 96 244', 2.4, taper=(0.05, 0.05)), OUT)
    doc.a('</g>')

    # ---- one curved seam ----
    doc.a('<g clip-path="url(#cHull)">')
    doc.path(ink_open('M180 160 C170 190 168 226 176 268', 1.9, taper=(0.12, 0.25)), OUT, 'opacity="0.85"')
    doc.path(ink_open('M183.5 162 C174 192 172 226 180 266', 1.3, taper=(0.2, 0.3)), '#fbf4ec', 'opacity="0.8"')
    doc.a('</g>')
    # ---- red oval marker light near the tail ----
    ML = cr([(110, 190), (122, 188), (126, 192.5), (122, 197), (110, 197.5), (107, 193.5)])
    doc.path(ML, RED)
    doc.path('M110 195 C116 196.5 122 196.5 125 194 C124 197 122 198 116 198.4 C112 198.4 109 197 110 195 Z', RED_SH)
    doc.path(ink_open('M111 191 C115 190 119 190 122 190.5', 1.4, taper=(0.3, 0.3)), '#ffffff')
    doc.path(ink_closed(ML, 1.3, 2.4), OUT)
    # ---- side slot ----
    SLOT = cr([(262, 218), (266, 213.5), (304, 214.5), (310, 218.5), (307, 225.5), (267, 225.5)])
    doc.path(SLOT, '#3f2c27')
    doc.path(cr([(266, 222.5), (286, 224), (306, 222), (305, 225), (286, 226.5), (267, 225)]), '#7b6259')
    doc.path(ink_open('M267 217 C280 216.5 294 217 304 217.8', 1.4, taper=(0.3, 0.3)), '#5a453d')
    doc.path(ink_closed(SLOT, 1.8, 3.6), OUT)
    doc.path(ink_open('M268 230 C282 231.5 296 231.5 306 229.5', 1.6, taper=(0.3, 0.3)), '#fdf8f2', 'opacity="0.9"')
    # ---- red dot with a stem ----
    doc.path(ink_open('M386 238.5 C392 238.8 400 239 408 238.6', 2.0, taper=(0.05, 0.3)), OUT)
    PH = wobble_ellipse(380, 238, 6.2, 6.6, amp=0.02, n=8)
    doc.path(PH, RED)
    doc.path('M376 241 C378 244 383 245 385 242 C386 240 386 237 385 235 C386 240 382 243 376 241 Z', RED_SH)
    doc.path(ellipse_path(378, 235.4, 2.1, 1.5, -30), '#ffffff')
    doc.path(ink_closed(PH, 1.5, 2.8), OUT)
    doc.path(ink_closed(HULL_D, W_MIN, W_MAX, inner_polys=[P_HOOD, P_GLASS, P_NOSE, P_FIN, P_STUB], inner_factor=0.6,
                        phase=0.4, wobble=0.06), OUT)
    doc.a('</g>')

    # ---------- hood (opaque rear of the canopy) ----------
    doc.a('<g id="hood">')
    doc.path(HOOD, HULL)
    doc.a('<g clip-path="url(#cHood)">')
    doc.path(cr([(76, 136, 1), (100, 136), (126, 142), (148, 154), (168, 154, 1), (168, 190, 1), (60, 190, 1)]), HULL_SH)
    doc.path(cr([(166, 70, 1), (161, 94), (158, 118), (158, 142), (162, 164, 1), (200, 164, 1), (200, 38, 1)]), HULL_SH)
    doc.path(cr([(98, 126), (104, 100), (120, 76), (146, 58), (170, 49), (158, 66), (136, 86), (120, 108), (108, 130)]),
             '#fcf7f1', 'filter="url(#b4)"')
    doc.path(ink_open('M106 114 C112 94 126 76 148 61', 3.8, taper=(0.35, 0.4)), '#ffffff', 'opacity="0.95"')
    doc.path(ink_open('M155 57 C159 55 163 53 167 52', 2.4, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.9"')
    doc.a('</g>')
    doc.path(HOOD, '#000', 'filter="url(#mottle)" opacity="0.22"')
    doc.path(HOOD, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(HOOD, W_MIN, W_MAX, inner_polys=[P_GLASS, P_HULL, P_FIN], inner_factor=0.55, phase=2.0,
                        wobble=0.06), OUT)
    doc.a('</g>')

    # ---------- dome glass ----------
    # a light tint only: the upper third is nearly clear so the vessel shows through (sub_back is see-through there)
    doc.d('<linearGradient id="gTint" x1="0" y1="26" x2="0" y2="180" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#eef2fa" stop-opacity="0.16"/>'
          '<stop offset="0.35" stop-color="#dfe5f2" stop-opacity="0.08"/>'
          '<stop offset="0.7" stop-color="#d2d8e4" stop-opacity="0.06"/>'
          '<stop offset="1" stop-color="#b8c6e2" stop-opacity="0.08"/></linearGradient>')
    # deep interior: the cockpit falls into shadow just above the rim
    doc.d('<linearGradient id="gDeep" x1="0" y1="146" x2="0" y2="172" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#0b0f2a" stop-opacity="0"/>'
          '<stop offset="0.5" stop-color="#0b0f2a" stop-opacity="0.55"/>'
          '<stop offset="1" stop-color="#0b0f2a" stop-opacity="0.9"/></linearGradient>')
    doc.a('<g id="glass">')
    doc.path(GLASS, 'url(#gTint)')
    doc.a('<g clip-path="url(#cGlass)">')
    doc.path(GLASS, 'url(#gDeep)')
    # fresnel: a little lighter towards the rim of the bubble
    doc.a('<path d="%s" fill="none" stroke="#f2e6ee" stroke-width="18" opacity="0.18" filter="url(#b7)"/>' % GLASS)
    # milky reflection near the rear edge of the glass
    doc.path(cr([(196, 36), (184, 62), (174, 100), (174, 150), (180, 170, 1), (160, 172, 1), (154, 100), (180, 40)]),
             '#f3f0f6', 'opacity="0.36" filter="url(#b4)"')
    # bold white specular streaks (#ffffff, alpha >= .85)
    doc.path(ink_open('M296 35 C350 37 396 52 418 80 C428 94 434 110 437 130', 10.5, taper=(0.35, 0.3)), '#ffffff',
             'opacity="0.92"')
    doc.path(ink_open('M382 66 C400 80 412 96 420 114', 4.2, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.88"')
    doc.path(cr([(284, 48), (304, 42), (328, 43), (340, 48), (328, 52), (304, 52)]), '#ffffff', 'opacity="0.9"')
    doc.path(ink_open('M214 44 C205 52 198 62 192 76', 4.2, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.88"')
    doc.path(ink_open('M189 85 C187 91 185 97 184 102', 2.6, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.85"')
    doc.path(ink_open('M442 142 C443 146 443 150 442 154', 2.6, taper=(0.4, 0.4)), '#ffffff', 'opacity="0.85"')
    # faint lower reflection of the deck
    doc.path(ink_open('M190 162 C250 170 330 172 400 166', 5, taper=(0.4, 0.4)), '#dfe6f4', 'opacity="0.2" filter="url(#b2_5)"')
    doc.a('</g>')
    doc.path(ink_closed(GLASS, W_MIN - 0.4, W_MAX - 0.2, inner_polys=[P_HOOD, P_HULL], inner_factor=0.55, phase=0.8,
                        wobble=0.06), OUT)
    doc.a('</g>')

    # ---------- cockpit rim lip ----------
    ts = [0.015 + 0.97 * i / 48 for i in range(49)]
    up = [rim_pt(t, -1.0) for t in ts]
    lo = [rim_pt(t, -1.0 + 5.0 * math.sin(math.pi * (t - 0.015) / 0.97) ** 0.35) for t in ts][::-1]
    LIP = smooth(up + lo, True)
    doc.a('<g id="rim">')
    doc.path(LIP, HULL_LIT)
    doc.path(ink_open(smooth([rim_pt(i / 30, 0.8) for i in range(3, 28)], False), 1.8, taper=(0.2, 0.2)), '#ffffff')
    doc.path(ink_closed(LIP, 1.2, 3.0, inner_polys=[P_HOOD], phase=0.3), OUT)
    doc.a('</g>')

    # ---------- top beacon on the dome ----------
    doc.a('<g id="beacon">')
    PAD = cr([(222, 30, 1), (226, 23), (242, 19), (258, 20.5), (266, 28, 1), (244, 30.5)])
    doc.path(PAD, HULL)
    doc.path('M226 27 C238 29 254 28.5 264 26.5 L266 28 C252 31.5 236 31.5 222 30 Z', HULL_SH)
    doc.path(ink_closed(PAD, 1.6, 3.6), OUT)
    LAMP = cr([(233, 21.5, 1), (233, 14.5), (238, 9), (245, 8), (252, 10), (256, 15.5), (256, 21.5, 1), (245, 23)])
    doc.path(LAMP, RED)
    doc.path('M248 9.5 C253 11.5 256 15.5 256 21.5 L250 22.5 C251 17.5 250 12.5 248 9.5 Z', RED_SH)
    doc.path(ink_open('M237 17.5 C237 13.5 240 11 244 10.5', 2.4, taper=(0.4, 0.4)), '#ffffff')
    doc.path(ink_closed(LAMP, 1.5, 3.4), OUT)
    doc.a('</g>')

    # ---------- small orange knob where the glass meets the deck ----------
    NUB = cr([(444, 155, 1), (446, 147), (452, 143), (458, 145), (461, 152, 1)])
    doc.path(NUB, '#ec8a3a')
    doc.path(ink_open('M448 149 C449 146 451 145 454 145', 1.4, taper=(0.4, 0.4)), '#fbd9a8')
    doc.path(ink_closed(NUB, 1.3, 2.6), OUT)

    # ---------- glossy red nose ball ----------
    doc.a('<g id="nose">')
    doc.path(NOSE, RED_SH)
    doc.a('<g clip-path="url(#cNose)">')
    # lit body (leaves a cel-shadow crescent on the lower right)
    doc.path(wobble_ellipse(NOSE_C[0] - 9, NOSE_C[1] - 8, NOSE_R[0] - 2, NOSE_R[1] - 4, 12, amp=0.01, n=10), RED)
    # soft lit zone on the upper left
    doc.path(ellipse_path(NOSE_C[0] - 16, NOSE_C[1] - 18, 26, 20, 12), RED_LIT, 'filter="url(#b4)"')
    # warm reflected light inside the shadow, along the lower-right edge
    doc.path(ink_open('M446 248 C470 252 494 242 508 222', 2.6, taper=(0.4, 0.4)), '#c23a36', 'opacity="0.9"')
    # white comma specular along the top
    doc.path(ink_open('M442 178 C444 168 452 162 464 160 C472 159 480 160 486 163', 6.0,
                      profile=lambda t: max(0.15, (1 - t) ** 0.7 * min(1, t * 8))), '#ffffff', 'opacity="0.96"')
    doc.path(ellipse_path(436.5, 190, 1.8, 2.6, 12), '#ffffff', 'opacity="0.85"')
    # headlight: a soft warm glow spot centred exactly on (498,178) - no lens, no rim
    hx, hy = HEADLIGHT
    doc.d('<radialGradient id="gSpot" cx="%s" cy="%s" r="15" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fffbe8" stop-opacity="1"/>'
          '<stop offset="0.3" stop-color="#ffe79e" stop-opacity="0.95"/>'
          '<stop offset="0.65" stop-color="#fbb85c" stop-opacity="0.55"/>'
          '<stop offset="1" stop-color="#fc805a" stop-opacity="0"/></radialGradient>' % (hx, hy))
    doc.path(ellipse_path(hx, hy, 15, 15), 'url(#gSpot)')
    doc.path(ellipse_path(hx + 0.5, hy, 3.2, 4.6, -8), '#ffffff', 'opacity="0.95" filter="url(#b1)"')
    doc.a('</g>')
    doc.path(NOSE, '#000', 'filter="url(#grain)"')
    doc.path(ink_closed(NOSE, W_MIN, W_MAX + 0.4, inner_polys=[P_HULL], inner_factor=0.7, phase=1.7, wobble=0.06), OUT)
    doc.a('</g>')
    return doc.render()


# =====================================================================
#  SUB BACK (cockpit interior behind the explorer)
# =====================================================================

def sub_back():
    doc = Doc(520, 300)
    soft_filters(doc)
    doc.clip('cGlass', GLASS)
    # far glass (upper third) is see-through lavender; below it the deep blue back wall, darkest behind the seat
    doc.d('<linearGradient id="gIn" x1="0" y1="24" x2="0" y2="182" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#7c80bc" stop-opacity="0.42"/>'
          '<stop offset="0.2" stop-color="#5f68a8" stop-opacity="0.5"/>'
          '<stop offset="0.36" stop-color="#2d4383" stop-opacity="0.9"/>'
          '<stop offset="0.52" stop-color="#223973" stop-opacity="1"/>'
          '<stop offset="0.66" stop-color="#1c2450" stop-opacity="1"/>'
          '<stop offset="0.84" stop-color="#121838" stop-opacity="1"/>'
          '<stop offset="1" stop-color="#0b0f2a" stop-opacity="1"/></linearGradient>')
    NAVY = '#10163a'
    PALE = '#6f88c8'
    doc.path(GLASS, 'url(#gIn)')
    doc.a('<g clip-path="url(#cGlass)">')
    # far half of the bubble: its rim seen through the near glass
    far = 'M200 52 C250 36 322 36 370 54 C406 68 428 100 434 140'
    doc.path(ink_open(far, 3.4, taper=(0.2, 0.3)), '#c9c6e6', 'opacity="0.5"')
    # two dome frame ribs arching over the cabin (far side)
    for d in ('M214 170 C206 122 214 78 246 46', 'M404 152 C406 114 398 80 376 56'):
        doc.path(ink_open(d, 4.2, taper=(0.15, 0.3)), '#24397a', 'opacity="0.85"')
        doc.path(ink_open(d, 1.4, taper=(0.15, 0.3)), PALE, 'opacity="0.55" transform="translate(-1.5 0)"')
    # rear bulkhead panel
    BULK = cr([(160, 172, 1), (162, 112), (174, 68), (198, 44), (212, 46), (198, 82), (194, 122), (198, 172, 1)])
    doc.path(BULK, '#182552')
    doc.path(ink_open('M204 52 C194 78 190 118 194 168', 1.6, taper=(0.2, 0.2)), NAVY, 'opacity="0.7"')
    doc.path(ink_open('M176 72 C168 92 166 120 167 152', 2.0, taper=(0.3, 0.3)), '#3b56a0', 'opacity="0.75"')
    # little pressure gauge on the bulkhead
    GA = wobble_ellipse(182, 104, 7.5, 8.2, amp=0.015, n=8)
    doc.path(GA, '#d8d6dc')
    doc.path(ellipse_path(182.8, 105.2, 6.2, 6.8), '#b9b8c6', 'clip-path="url(#cGa)"')
    doc.d('<clipPath id="cGa"><path d="%s"/></clipPath>' % GA)
    doc.path(ellipse_path(181.6, 103.4, 5.2, 5.8), '#e9e7ee')
    for k in range(5):
        ang = math.radians(200 + k * 35)
        x0, y0 = 182 + math.cos(ang) * 4.2, 104 + math.sin(ang) * 4.6
        x1, y1 = 182 + math.cos(ang) * 5.4, 104 + math.sin(ang) * 6.0
        doc.path(ink_open('M%s %s L%s %s' % (_f(x0), _f(y0), _f(x1), _f(y1)), 0.8, taper=(0, 0), wend=0.6), NAVY)
    doc.path(ink_open('M182 104.5 L186 100', 1.3, taper=(0.0, 0.5)), RED)
    doc.path(ellipse_path(182, 104.5, 1.2, 1.2), NAVY)
    doc.path(ink_closed(GA, 1.0, 2.2), NAVY)
    # pipe with brackets running down the bulkhead
    doc.path(ink_open('M172 122 C174 136 175 152 175 172', 4.0, taper=(0.0, 0.0), wend=3.6), '#3f5596')
    doc.path(ink_open('M171.2 124 C173 138 174 154 174 172', 1.2, taper=(0.0, 0.0)), '#7d96d4', 'opacity="0.8"')
    for y in (130, 152):
        doc.path(cr([(169, y - 2, 1), (180, y - 2, 1), (180, y + 2, 1), (169, y + 2, 1)]), '#22336a')
    # far cockpit wall (lower interior) with a padded rail
    WALL = cr([(150, 152, 1), (220, 148), (330, 150), (452, 150, 1), (452, 192, 1), (150, 192, 1)])
    doc.path(WALL, '#0e1434')
    doc.path(ink_open('M156 152 C230 147 330 149 440 152', 2.4, taper=(0.2, 0.2)), '#4c67ad', 'opacity="0.85"')
    RAIL = cr([(160, 158, 1), (250, 154), (340, 156), (440, 159, 1), (440, 165, 1), (340, 162), (250, 160),
               (160, 164, 1)])
    doc.path(RAIL, '#2a3c78')
    doc.path(ink_open('M166 158.5 C250 154.5 340 156.5 436 159.5', 1.2, taper=(0.1, 0.1)), '#6d86c6', 'opacity="0.6"')
    # pilot seat: back + separate headrest
    SEAT = cr([(184, 180, 1), (183, 142), (187, 122), (198, 114), (222, 113), (236, 120), (240, 136), (241, 180, 1)])
    HEAD = cr([(190, 106), (192, 92), (204, 86), (222, 86), (232, 92), (233, 104), (226, 110), (198, 110)])
    doc.d('<clipPath id="cSeat"><path d="%s"/></clipPath>' % SEAT)
    doc.d('<clipPath id="cHead"><path d="%s"/></clipPath>' % HEAD)
    for x in (202, 222):
        doc.path(cr([(x - 1.6, 106, 1), (x + 1.6, 106, 1), (x + 1.6, 116, 1), (x - 1.6, 116, 1)]), '#7b84a2')
    for P, cid in ((SEAT, 'cSeat'), (HEAD, 'cHead')):
        doc.path(P, '#3f4a74')
        doc.a('<g clip-path="url(#%s)">' % cid)
        doc.path(cr([(226, 72, 1), (236, 112), (240, 152), (238, 192, 1), (260, 192, 1), (260, 72, 1)]), '#1e2446')
        doc.path(ink_open('M193 172 C190 148 192 126 202 116' if P is SEAT else 'M196 104 C196 96 202 91 210 90',
                          5, taper=(0.3, 0.3)), '#8d98bc', 'filter="url(#b1_6)"')
        doc.a('</g>')
    # tufting seams on the seat back
    for d in ('M204 122 C203 138 203 158 204 178', 'M220 122 C220 138 220 158 221 178',
              'M190 148 C204 146 222 146 238 148'):
        doc.path(ink_open(d, 1.2, taper=(0.2, 0.2)), '#2e3558', 'opacity="0.85"')
    doc.path(ink_closed(SEAT, 1.5, 3.4), NAVY)
    doc.path(ink_closed(HEAD, 1.4, 3.0), NAVY)
    # dashboard console at the front
    DASH = cr([(350, 180, 1), (354, 162), (368, 150), (396, 142), (424, 138), (442, 142), (450, 172, 1)])
    doc.d('<clipPath id="cDash"><path d="%s"/></clipPath>' % DASH)
    doc.path(DASH, '#28396f')
    doc.a('<g clip-path="url(#cDash)">')
    doc.path(cr([(344, 162, 1), (374, 156), (424, 152), (456, 154, 1), (456, 192, 1), (344, 192, 1)]), '#141d44')
    doc.path(ink_open('M360 156 C376 147 400 141 430 140', 3.2, taper=(0.3, 0.3)), '#7086c4')
    for k in range(4):
        doc.path(ink_open('M%s %s L%s %s' % (_f(404 + k * 6), _f(162), _f(406 + k * 6), _f(172)), 1.4, taper=(0.2, 0.2)),
                 NAVY, 'opacity="0.7"')
    doc.a('</g>')
    # small monitor with a heartbeat trace (nods to the hospital monitors)
    MON = cr([(392, 134, 1), (418, 130, 1), (420, 148, 1), (394, 152, 1)])
    doc.path(MON, '#1b3644')
    doc.path(ink_open('M395 144 L401 143.4 L403.5 138 L406 148 L408.5 141.6 L411 142.6 L417 142', 1.3,
                      taper=(0.1, 0.1)), '#9ad6a2')
    doc.path(ink_open('M395 135.5 C402 134.5 409 133.5 416 132.5', 1.2, taper=(0.2, 0.2)), '#5f8ea0', 'opacity="0.7"')
    doc.path(ink_closed(MON, 1.2, 2.6), NAVY)
    # round compass dial on the dash
    DI = wobble_ellipse(431, 152, 5.4, 5.6, amp=0.015, n=8)
    doc.path(DI, '#d8d6dc')
    doc.path(ellipse_path(430.4, 151.3, 3.8, 3.9), '#eceaf0')
    doc.path(ink_open('M428.5 154.5 L433.5 149.5', 1.2, taper=(0.1, 0.5)), RED)
    doc.path(ink_closed(DI, 0.9, 2.0), NAVY)
    # throttle lever
    doc.path(ink_open('M382 160 C381 154 380 149 378 144', 2.2, taper=(0.0, 0.1)), '#9aa3bf')
    LEV = wobble_ellipse(377.6, 142.5, 3.0, 3.0, amp=0.02, n=8)
    doc.path(LEV, '#f2b63c')
    doc.path(ink_closed(LEV, 0.8, 1.8), NAVY)
    for (x, y, c) in ((366, 161, '#e0484f'), (372, 159, '#f2b63c'), (388, 154.5, '#8fd09a'), (440, 160, '#e0484f')):
        doc.path(ellipse_path(x, y, 2.2, 2.0), c)
        doc.path(ellipse_path(x - 0.6, y - 0.6, 0.8, 0.7), '#ffffff', 'opacity="0.8"')
    doc.path(ink_closed(DASH, 1.4, 3.2), NAVY)
    # depth: the lower interior falls off into deep shadow
    doc.path(cr([(150, 156, 1), (452, 156, 1), (452, 194, 1), (150, 194, 1)]), '#0a0f2c', 'opacity="0.6" filter="url(#b4)"')
    doc.a('</g>')
    return doc.render()


def write(outdir):
    for name, fn in (('sub_front', sub_front), ('sub_back', sub_back)):
        with open(os.path.join(outdir, name + '.svg'), 'w') as f:
            f.write(fn())


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else '.')
    print('ok')
