"""Generates sub_light.svg (640x320) and jet.svg (160x90)."""
import math
import os
import random
import sys

sys.dont_write_bytecode = True  # keep the tools/art tree free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ink import ink_open, ink_closed, _f  # noqa: E402
from svgkit import cr, ellipse_path, wobble_ellipse, Doc  # noqa: E402


def sub_light():
    """Headlight beam, origin (0,160), opening to the right.

    Authored for NORMAL blend, untinted, alpha ~0.95 (reference p7): pale yellow at the lens, turning
    orange and then red towards the tip, plus a wide warm spill that tints the walls around the cone.
    """
    doc = Doc(640, 320)
    for s in (2, 4, 8, 14, 22):
        doc.d('<filter id="b%d" x="-30%%" y="-60%%" width="160%%" height="220%%"><feGaussianBlur stdDeviation="%d"/></filter>' % (s, s))
    doc.d('<linearGradient id="gCone" x1="0" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fff6d6" stop-opacity="1"/>'
          '<stop offset="0.12" stop-color="#ffe08a" stop-opacity="0.92"/>'
          '<stop offset="0.35" stop-color="#fbb85c" stop-opacity="0.78"/>'
          '<stop offset="0.58" stop-color="#fc805a" stop-opacity="0.5"/>'
          '<stop offset="0.8" stop-color="#eb594f" stop-opacity="0.2"/>'
          '<stop offset="1" stop-color="#e04740" stop-opacity="0"/></linearGradient>')
    doc.d('<linearGradient id="gCore" x1="0" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fffbe8" stop-opacity="1"/>'
          '<stop offset="0.1" stop-color="#fff0c0" stop-opacity="0.7"/>'
          '<stop offset="0.3" stop-color="#ffd27a" stop-opacity="0"/></linearGradient>')
    doc.d('<linearGradient id="gRay" x1="0" y1="0" x2="560" y2="0" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fff2c4"/><stop offset="1" stop-color="#ffd27a"/></linearGradient>')
    doc.d('<radialGradient id="gHot" cx="12" cy="160" r="46" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fffdf2" stop-opacity="1"/>'
          '<stop offset="0.35" stop-color="#fff3cc" stop-opacity="0.6"/>'
          '<stop offset="1" stop-color="#ffe8b0" stop-opacity="0"/></radialGradient>')
    # warm spill: an ellipse ~1.6x the cone height, outside the cone mask, fading to 0 well inside the canvas
    doc.d('<radialGradient id="gSpill" cx="340" cy="160" r="300" gradientUnits="userSpaceOnUse" '
          'gradientTransform="translate(340 160) scale(1 0.5) translate(-340 -160)">'
          '<stop offset="0" stop-color="#ff6a3c" stop-opacity="0.55"/>'
          '<stop offset="0.55" stop-color="#ff6a3c" stop-opacity="0.48"/>'
          '<stop offset="0.8" stop-color="#ff6a3c" stop-opacity="0.2"/>'
          '<stop offset="1" stop-color="#ff6a3c" stop-opacity="0"/></radialGradient>')
    # the spill must not sit on the sub's nose: fade it in over the first ~90 px
    doc.d('<linearGradient id="gSpillRamp" x1="0" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.14" stop-color="#fff" stop-opacity="1"/>'
          '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>')
    doc.d('<mask id="mSpill" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="320">'
          '<rect width="640" height="320" fill="url(#gSpillRamp)"/></mask>')
    doc.a('<rect width="640" height="320" fill="url(#gSpill)" mask="url(#mSpill)"/>')
    # beam mask: feathered cone, ~200 px tall at 400 px out (half-angle ~14 deg), a thin point at the lens
    doc.d('<linearGradient id="gRamp" x1="0" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.012" stop-color="#fff" stop-opacity="0.55"/>'
          '<stop offset="0.07" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>')
    MASKC = cr([(0, 155, 1), (60, 140), (200, 100), (400, 50), (560, 28), (628, 24), (634, 160), (628, 296),
                (560, 292), (400, 270), (200, 220), (60, 180), (0, 165, 1)])
    doc.d('<filter id="mb" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="9 14"/></filter>')
    doc.d('<mask id="mBeam" maskUnits="userSpaceOnUse" x="0" y="0" width="640" height="320">'
          '<path d="%s" fill="url(#gRamp)" filter="url(#mb)"/></mask>' % MASKC)
    doc.a('<g mask="url(#mBeam)">')
    # outer glow body
    cone = cr([(0, 148, 1), (120, 118), (300, 74), (470, 40), (600, 28), (614, 160), (600, 292), (470, 280),
               (300, 246), (120, 202), (0, 172, 1)])
    doc.path(cone, 'url(#gCone)', 'filter="url(#b14)"')
    # inner core (pale yellow, short)
    core = cr([(0, 153, 1), (90, 142), (200, 128), (300, 118), (330, 160), (300, 202), (200, 192), (90, 178),
               (0, 167, 1)])
    doc.path(core, 'url(#gCore)', 'filter="url(#b8)"')
    # painterly light rays
    rays = [(-11, 430, 7, 0.22), (-5, 520, 10, 0.18), (1, 480, 6, 0.24), (6, 540, 9, 0.16), (12, 420, 6, 0.2),
            (-16, 360, 5, 0.13), (17, 380, 5, 0.13), (-2, 300, 4, 0.2), (9, 330, 4, 0.16)]
    for ang, length, w, op in rays:
        a = math.radians(ang)
        x2, y2 = 10 + math.cos(a) * length, 160 + math.sin(a) * length
        xm, ym = 10 + math.cos(a) * length * 0.5, 160 + math.sin(a) * length * 0.5 + ang * 0.4
        d = 'M10 160 C%s %s %s %s %s %s' % (_f(xm - 60), _f(ym), _f(xm + 60), _f(ym), _f(x2), _f(y2))
        doc.path(ink_open(d, w, step=6, taper=(0.15, 0.7), wobble=0.15), 'url(#gRay)',
                 'opacity="%s" filter="url(#b4)"' % op)
    # hot spot right in front of the lens
    doc.path(ellipse_path(12, 160, 46, 24), 'url(#gHot)', 'filter="url(#b4)"')
    # a few motes caught in the beam
    rnd = random.Random(5)
    for i in range(18):
        x = rnd.uniform(60, 470)
        spread = 10 + x * 0.2
        y = 160 + rnd.uniform(-spread, spread)
        r = rnd.uniform(0.9, 2.2)
        op = 0.6 * (1 - x / 560)
        doc.path(ellipse_path(x, y, r, r * rnd.uniform(0.8, 1.1)), '#fff8e2', 'opacity="%.2f" filter="url(#b2)"' % op)
    doc.a('</g>')
    return doc.render()


JET_FILL, JET_LIT, JET_INK, JET_MID = '#8cc4f0', '#bfe2fb', '#3d6fa8', '#6aa6dc'


def _lobe(x1, x0, p1, p0, h_up, h_dn, tilt, n=10):
    """One bow-tie lobe of the water jet between pinches at x1 (right) and x0 (left).

    Returns (closed path, upper edge points, lower edge points); tilt shifts the lobe's belly up/down
    so consecutive lobes read as one twisted ribbon."""
    up, dn = [], []
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        bulge = math.sin(math.pi * t) ** 1.1
        pin = p1 + (p0 - p1) * t
        c = 45 + tilt * math.sin(math.pi * t) * (t - 0.2)
        up.append((x, c - pin - h_up * bulge))
        dn.append((x, c + pin + h_dn * bulge))
    from ink import smooth
    return smooth(up + dn[::-1], True), up, dn


def jet():
    """Rear jet wash (160x90), anchor right-centre (160,45), pointing left: a saturated sky-blue twisted
    ribbon of 3 bow-tie pulses with a broken dark-blue outline (reference p4/p9/p10)."""
    doc = Doc(160, 90)
    from ink import smooth
    for s in (0.6, 1.2):
        doc.d('<filter id="b%s" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="%s"/></filter>'
              % (str(s).replace('.', '_'), s))
    # (right pinch x, left pinch x, right pinch half, left pinch half, upper bulge, lower bulge, tilt, opacity)
    lobes = [(160, 114, 4.5, 3.2, 13, 12, -10, 1.0),
             (114, 62, 3.2, 2.6, 17, 19, 12, 1.0),
             (62, 14, 2.6, 1.0, 12, 11, -9, 0.85)]
    for k, (x1, x0, p1, p0, hu, hd, tilt, op) in enumerate(lobes):
        d, up, dn = _lobe(x1, x0, p1, p0, hu, hd, tilt)
        cid = 'cL%d' % k
        doc.clip(cid, d)
        doc.a('<g opacity="%s">' % op)
        doc.path(d, JET_FILL)
        doc.a('<g clip-path="url(#%s)">' % cid)
        # the ribbon's turned-over half: a slightly deeper tone on one side of the twist line
        mid = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + (2.5 if k % 2 == 0 else -2.5)) for a, b in zip(up, dn)]
        side = (mid + dn[::-1]) if k % 2 == 0 else (up + mid[::-1])
        doc.path(smooth(side, True), JET_MID, 'opacity="0.55"')
        # pale highlight band on the upper half
        hl = [(a[0], a[1] + (m[1] - a[1]) * 0.35) for a, m in zip(up, mid)]
        hl2 = [(a[0], a[1] + (m[1] - a[1]) * 0.75) for a, m in zip(up, mid)]
        doc.path(smooth(hl[1:-1] + hl2[1:-1][::-1], True), JET_LIT, 'filter="url(#b0_6)"')
        # the twist line and a white glint along it
        doc.path(ink_open(smooth(mid[1:-1], False), 1.3, taper=(0.3, 0.3)), JET_INK, 'opacity="0.55"')
        g = mid[2:-3]
        doc.path(ink_open(smooth([(p[0], p[1] - 2.2) for p in g], False), 1.8, taper=(0.35, 0.5)), '#ffffff',
                 'opacity="0.85"')
        doc.a('</g>')
        # broken outline: heavier on the lower edge, gaps on the lit upper edge
        n = len(up)
        doc.path(ink_open(smooth(dn, False), 2.6, taper=(0.12, 0.12)), JET_INK)
        doc.path(ink_open(smooth(up[:n // 2 - 1], False), 2.2, taper=(0.15, 0.4)), JET_INK)
        doc.path(ink_open(smooth(up[n // 2 + 2:], False), 2.0, taper=(0.4, 0.15)), JET_INK)
        doc.a('</g>')
    # a few droplets flicked off the pinches
    for (x, y, r) in ((112, 33, 1.8), (64, 60, 2.0), (90, 22, 1.4), (36, 31, 1.5), (140, 59, 1.4)):
        doc.path(ellipse_path(x, y, r, r), JET_LIT)
        doc.a('<path d="%s" fill="none" stroke="%s" stroke-width="0.9"/>' % (ellipse_path(x, y, r, r), JET_INK))
    return doc.render()


def jet_bubble():
    """Ring bubble for the jet particles (32x32, shown at 16-28 px): pale glass, blue rim, white highlight."""
    doc = Doc(32, 32)
    c = wobble_ellipse(16, 16, 13, 12.6, amp=0.012, n=8, phase=0.4)
    doc.path(c, '#cfe6f8', 'opacity="0.55"')
    doc.a('<path d="%s" fill="none" stroke="#e8f4fd" stroke-width="2.4" opacity="0.7" transform="translate(16 16) '
          'scale(0.78) translate(-16 -16)"/>' % c)
    doc.a('<path d="%s" fill="none" stroke="#7aa6d6" stroke-width="2"/>' % c)
    doc.path(ink_open('M7.5 14 C8 10.5 10.5 8 14 7.2', 2.2, taper=(0.3, 0.4)), '#ffffff', 'opacity="0.95"')
    doc.path(ellipse_path(20.5, 9.6, 1.6, 1.4), '#ffffff')
    return doc.render()


def write(outdir):
    for name, fn in (('sub_light', sub_light), ('jet', jet), ('jet_bubble', jet_bubble)):
        with open(os.path.join(outdir, name + '.svg'), 'w') as f:
            f.write(fn())


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else '.')
    print('ok')
