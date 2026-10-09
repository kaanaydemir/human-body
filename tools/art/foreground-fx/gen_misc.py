#!/usr/bin/env python3
"""disc_cell, disc_cell_far, disc_cell_blur, vignette, glow, particle, bubble, streak (foreground-fx group).

Run from the repo root:
    python3 -I tools/art/foreground-fx/gen.py                 (everything)
    python3 -I tools/art/foreground-fx/gen_misc.py [--out DIR] [disc far blur vignette glow particle bubble streak]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import (fmt, P, add, sub, mul, dot, unit, lerp, clamp, smoothstep, spline, sample, d_segs,  # noqa
                 d_closed, ribbon_d, stroke_along, ellipse_pts, rot, length)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ENV = os.path.join(ROOT, 'public', 'assets', 'svg', 'environment') + os.sep
FX = os.path.join(ROOT, 'public', 'assets', 'svg', 'fx') + os.sep


def write(path, s):
    with open(path, 'w') as fh:
        fh.write(s)
    print(os.path.basename(path), f'{len(s) / 1024:.1f} KB')


def head(W, H):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'


# =============================================================================== disc cell
# Plain biconcave disc, opened up like the loose discs of panels 4 and 7: face ellipse ratio ~0.8,
# a thin side band (<= 8 % of the height) on the lower right, a fat torus rim and a centred dimple
# (~57 % of the face).  Cel painted: one shade, one soft highlight on the rim, no white glints.
CELL = {
    'body': '#f43a2e', 'lit': '#fb4d3c', 'hl': '#fb6a5a', 'shade': '#c4281f', 'deep': '#98231c',
    'dimple': '#c4281f', 'dimple_wall': '#98231c', 'dimple_lit': '#e2372a', 'line': '#5a1a1c',
    'line_w': (4.0, 5.0), 'crease': 0.5, 'soft_hl': True,
}
# Hazed variant for the background traffic plane (scroll .55): lower saturation and contrast, thin warm
# outline, no highlight -- it must sit back with the far walls instead of popping out like a sticker.
CELL_FAR = {
    'body': '#ac3e3c', 'lit': '#ac3e3c', 'hl': None, 'shade': '#923035', 'deep': '#923035',
    'dimple': '#9e3839', 'dimple_wall': '#923035', 'dimple_lit': None, 'line': '#842f35',
    'line_w': (1.5, 1.5), 'crease': 0.0, 'soft_hl': False,
}


def ell(c, rx, ry, ang, a):
    """point and outward normal of a rotated ellipse at parameter a."""
    p = (rx * math.cos(a), ry * math.sin(a))
    n = unit((math.cos(a) / rx, math.sin(a) / ry))
    return add(c, rot(p, ang)), rot(n, ang)


def disc_body(c, rx, ry, ang, thick, k=1.0, uid='', pal=CELL):
    """svg fragment of the biconcave disc: face ellipse + thin side band towards `thick`."""
    tdir = unit(thick)
    N = 120
    # gentle hand wobble so the face is not a perfect ellipse
    wob = lambda a: 1 + 0.012 * math.sin(3 * a + 0.7) + 0.008 * math.sin(5 * a + 2.1)
    top, topn, hull, hulln = [], [], [], []
    for i in range(N):
        a = 2 * math.pi * i / N
        p, n = ell(c, rx * wob(a), ry * wob(a), ang, a)
        top.append(p)
        topn.append(n)
        s = smoothstep(-0.35, 0.45, dot(n, tdir))
        hull.append(add(p, mul(thick, s)))
        hulln.append(n)
    o = []
    hull_d = d_closed(hull[::3])
    top_d = d_closed(top[::3])
    o.append(f'<clipPath id="top{uid}"><path d="{top_d}"/></clipPath>')
    # side band
    o.append(f'<path d="{hull_d}" fill="{pal["deep"]}"/>')
    o.append(f'<clipPath id="hull{uid}"><path d="{hull_d}"/></clipPath>')
    o.append(f'<g clip-path="url(#hull{uid})"><path d="{d_closed([add(p, mul(tdir, -1.6 * k)) for p in hull[::3]])}" '
             f'fill="{pal["shade"]}"/></g>')
    # face
    o.append(f'<path d="{top_d}" fill="{pal["body"]}"/>')
    o.append(f'<g clip-path="url(#top{uid})">')
    # outer lower-right slope of the torus turns away from the light: one cel-shade crescent
    o.append(f'<path d="{top_d}" fill="{pal["shade"]}"/>')
    o.append(f'<path d="{d_closed([add(p, mul(tdir, -6.5 * k)) for p in top[::3]])}" fill="{pal["body"]}"/>')
    # lit upper-left slope of the torus
    if pal['lit'] != pal['body']:
        lp, ln, lw = [], [], []
        for p, n in zip(top, topn):
            lp.append(sub(p, mul(n, 3.0 * k)))
            ln.append(n)
            lw.append(11 * k * smoothstep(0.0, 0.8, dot(n, unit((-0.72, -0.69)))))
        o.append(f'<path d="{ribbon_d(lp + lp[:1], ln + ln[:1], lw + lw[:1], bias=1.0, every=2)}" fill="{pal["lit"]}"/>')
    # dimple: centred, ~57 % of the face
    dc = add(c, mul(tdir, 1.4 * k))
    drx, dry = rx * 0.57, ry * 0.57
    dim, dimn = [], []
    for i in range(N):
        a = 2 * math.pi * i / N
        p, n = ell(dc, drx * (1 + 0.015 * math.sin(2 * a + 1)), dry, ang, a)
        dim.append(p)
        dimn.append(n)
    dim_d = d_closed(dim[::3])
    if pal['soft_hl']:
        # the torus' inner slope falls softly into the dimple
        o.append(f'<path d="{d_closed([add(p, mul(n, 5.5 * k)) for p, n in zip(dim[::3], dimn[::3])])}" '
                 f'fill="{pal["dimple_lit"]}" opacity=".55" filter="url(#soft{uid})"/>')
    o.append(f'<path d="{dim_d}" fill="{pal["dimple"]}"/>')
    o.append(f'<clipPath id="dim{uid}"><path d="{dim_d}"/></clipPath>')
    o.append(f'<g clip-path="url(#dim{uid})">')
    # inner wall on the upper-left faces away from the light -> deep crescent
    o.append(f'<path d="{dim_d}" fill="{pal["dimple_wall"]}"/>')
    o.append(f'<path d="{d_closed([add(p, mul(tdir, 5.0 * k)) for p in dim[::3]])}" fill="{pal["dimple"]}"/>')
    if pal['dimple_lit']:
        # lower-right inner wall catches a little light
        lw, lp = [], []
        for p, n in zip(dim, dimn):
            lp.append(sub(p, mul(n, 1.0 * k)))
            lw.append(3.2 * k * smoothstep(0.25, 0.9, dot(n, tdir)))
        o.append(f'<path d="{ribbon_d(lp + lp[:1], dimn + dimn[:1], lw + lw[:1], bias=1.0, every=2)}" '
                 f'fill="{pal["dimple_lit"]}"/>')
    o.append('</g>')
    if pal['crease']:
        cw = [1.5 * k * smoothstep(0.1, 0.85, -dot(n, tdir)) for n in dimn]
        o.append(f'<path d="{ribbon_d(dim + dim[:1], dimn + dimn[:1], cw + cw[:1], bias=0.5, every=2)}" '
                 f'fill="{pal["line"]}" opacity="{pal["crease"]}"/>')
    o.append('</g>')  # end face clip
    # one soft highlight on the upper-left of the rim (no white glints)
    if pal['hl']:
        sp = []
        for i in range(N):
            a = 2 * math.pi * i / N
            p, n = ell(c, rx * 0.8, ry * 0.79, ang, a)
            sp.append((a, p))
        arc = [p for a, p in sp if 3.5 < a < 4.55]
        o.append(f'<path d="{stroke_along(arc, 6.5 * k, 0.8)}" fill="{pal["hl"]}" filter="url(#soft{uid})"/>')
    # face / side band boundary on the lower right
    if pal['crease']:
        bw = [1.2 * k * smoothstep(0.3, 0.85, dot(n, tdir)) for n in topn]
        o.append(f'<path d="{ribbon_d(top + top[:1], topn + topn[:1], bw + bw[:1], bias=0.5, every=2)}" '
                 f'fill="{pal["line"]}" opacity="{pal["crease"]}"/>')
    # outline: thicker on the lower right
    lo, hi = pal['line_w']
    ow = [k * (lo + (hi - lo) * smoothstep(-0.5, 0.9, dot(n, tdir))) for n in hulln]
    o.append(f'<path d="{ribbon_d(hull + hull[:1], hulln + hulln[:1], ow + ow[:1], bias=0.55, every=2)}" '
             f'fill="{pal["line"]}"/>')
    return ''.join(o)


DISC_GEOM = dict(c=(70, 68), rx=60, ry=48, ang=math.radians(-14), thick=(3.2, 4.6))


def soft_filter(fid, std, W):
    return (f'<filter id="{fid}" x="-20" y="-20" width="{W + 40}" height="{W + 40}" filterUnits="userSpaceOnUse">'
            f'<feGaussianBlur stdDeviation="{std}"/></filter>')


def disc_cell(out):
    W = H = 140
    g = DISC_GEOM
    s = [head(W, H), '<defs>' + soft_filter('soft', 2.0, W) + '</defs>']
    s.append(disc_body(g['c'], g['rx'], g['ry'], g['ang'], g['thick'], 1.0, pal=CELL))
    s.append('</svg>')
    write(out + 'disc_cell.svg', ''.join(s))


def disc_cell_far(out):
    W = H = 140
    g = DISC_GEOM
    s = [head(W, H), '<defs>' + soft_filter('soft', 2.0, W) + '</defs>']
    s.append(disc_body(g['c'], g['rx'], g['ry'], g['ang'], g['thick'], 1.0, pal=CELL_FAR))
    s.append('</svg>')
    write(out + 'disc_cell_far.svg', ''.join(s))


DOF_BLUR = 2.6


def disc_cell_blur(out):
    W = H = 220
    k = 1.45
    g = DISC_GEOM
    s = [head(W, H), '<defs>' + soft_filter('soft', 2.6, W) +
         f'<filter id="dof" x="0" y="0" width="220" height="220" filterUnits="userSpaceOnUse">'
         f'<feGaussianBlur stdDeviation="{DOF_BLUR}"/></filter></defs>']
    s.append('<g filter="url(#dof)">')
    s.append(disc_body((110, 107), g['rx'] * k, g['ry'] * k, g['ang'], (g['thick'][0] * k, g['thick'][1] * k), k,
                       pal=CELL))
    s.append('</g></svg>')
    write(out + 'disc_cell_blur.svg', ''.join(s))


# =============================================================================== vignette
def eased_stops(color, a0, a1, t0, t1, n=10, power=1.0, extra=''):
    out = []
    for i in range(n + 1):
        u = i / n
        e = smoothstep(0, 1, u) ** power
        a = a0 + (a1 - a0) * e
        out.append(f'<stop offset="{t0 + (t1 - t0) * u:.3f}" stop-color="{color}" stop-opacity="{a:.3f}"/>')
    return ''.join(out)


# Corners-only vignette, tuned for the code alpha .45 (BloodstreamScene).  No top/bottom band: the
# reference has no band darkening, so the edge centres stay within -.003 V of the bare frame and the
# corners lose .04-.09 V (bottom corners stronger than the already dark ceiling corners).
VIG = dict(color='#3a0c14', ov_max=0.22, ov_scale_y=0.92, corner_top=0.06, corner_bottom=0.17)


def vignette(out):
    W, H = 1920, 1080
    C = VIG['color']
    s = [head(W, H), '<defs>']
    s.append(f'<radialGradient id="ov" gradientUnits="userSpaceOnUse" cx="960" cy="540" r="1150" '
             f'gradientTransform="translate(960 540) scale(1 {VIG["ov_scale_y"]}) translate(-960 -540)">'
             f'<stop offset="0" stop-color="{C}" stop-opacity="0"/>'
             + eased_stops(C, 0, VIG['ov_max'], 0.42, 1.0, 14, 1.25) + '</radialGradient>')
    for i, (cx, cy) in enumerate([(0, 0), (1920, 0), (0, 1080), (1920, 1080)]):
        a = VIG['corner_top'] if cy == 0 else VIG['corner_bottom']
        s.append(f'<radialGradient id="c{i}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="760" '
                 f'gradientTransform="translate({cx} {cy}) scale(1.25 0.8) translate({-cx} {-cy})">'
                 + eased_stops(C, a, 0, 0, 1, 12, 1.0) + '</radialGradient>')
    s.append('</defs>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#ov)"/>')
    for i in range(4):
        s.append(f'<rect width="{W}" height="{H}" fill="url(#c{i})"/>')
    s.append('</svg>')
    write(out + 'vignette.svg', ''.join(s))


# =============================================================================== glow
# Saturated warm light (ADD blend, code alpha .15-.185, scale 1.6).  The amber hue pushes the walls toward
# orange (+2..+3 deg) without washing them out; the peak is scaled so the walls at the glow centre gain
# at most ~+.06 V and lose <= .01 S.
GLOW = dict(color='#ff8a28', peak=0.37)


def glow(out):
    W, H = 1200, 800
    stops = []
    n = 24
    for i in range(n + 1):
        t = i / n
        a = GLOW['peak'] * math.exp(-3.4 * t * t) * (1 - smoothstep(0.72, 1.0, t))
        stops.append(f'<stop offset="{t:.3f}" stop-color="{GLOW["color"]}" stop-opacity="{a:.3f}"/>')
    s = [head(W, H), '<defs>',
         f'<radialGradient id="g" gradientUnits="userSpaceOnUse" cx="600" cy="400" r="596" '
         f'gradientTransform="translate(600 400) scale(1 0.665) translate(-600 -400)">' + ''.join(stops)
         + '</radialGradient>', '</defs>', f'<rect width="{W}" height="{H}" fill="url(#g)"/>', '</svg>']
    write(out + 'glow.svg', ''.join(s))


# =============================================================================== particle
def particle(out):
    W = H = 24
    c = (12, 12)
    blob = [(12.2, 7.4), (15.6, 8.6), (16.8, 12.1), (15.2, 15.6), (11.6, 16.7), (8.4, 15.2), (7.3, 11.6),
            (8.9, 8.4)]
    inner = [(11.3, 9.3), (13.3, 9.6), (13.6, 11.3), (12.1, 12.1), (10.4, 11.6), (10.2, 10.1)]
    s = [head(W, H), '<defs>',
         '<filter id="halo" x="-6" y="-6" width="36" height="36" filterUnits="userSpaceOnUse">'
         '<feGaussianBlur stdDeviation="2.4"/></filter>',
         '<filter id="sft" x="-6" y="-6" width="36" height="36" filterUnits="userSpaceOnUse">'
         '<feGaussianBlur stdDeviation="0.5"/></filter>', '</defs>']
    s.append(f'<path d="{d_closed([add(c, mul(sub(p, c), 1.35)) for p in blob])}" fill="#f29a9c" opacity=".38" '
             f'filter="url(#halo)"/>')
    s.append('<g filter="url(#sft)">')
    s.append(f'<path d="{d_closed(blob)}" fill="#e9737c"/>')
    s.append(f'<path d="{d_closed([add(p, (-0.7, -0.8)) for p in [add(c, mul(sub(q, c), 0.82)) for q in blob]])}" '
             f'fill="#f7a9a8"/>')
    s.append(f'<path d="{d_closed(inner)}" fill="#ffd6cf" opacity=".8"/>')
    s.append('</g>')
    s.append('</svg>')
    write(out + 'particle.svg', ''.join(s))


# =============================================================================== bubble
def bubble(out):
    W = H = 40
    c = (20, 20)
    r = 16.6
    # slightly irregular circle (hand drawn)
    wob = [1.0, 1.012, 0.995, 1.008, 0.99, 1.01, 0.998, 1.006, 0.992, 1.004]
    ring = ellipse_pts(c, r, r * 0.985, 0.2, 10, wob)
    ring_d = d_closed(ring)
    rs = [p for p, t in sample(spline(ring, closed=True), 0.8)]
    rn = [unit(sub(p, c)) for p in rs]
    s = [head(W, H), '<defs>',
         '<radialGradient id="gl" gradientUnits="userSpaceOnUse" cx="17" cy="16" r="19">'
         '<stop offset="0" stop-color="#e3f0fb" stop-opacity=".55"/>'
         '<stop offset=".55" stop-color="#bcd8f2" stop-opacity=".5"/>'
         '<stop offset=".88" stop-color="#9cc0e8" stop-opacity=".62"/>'
         '<stop offset="1" stop-color="#7aa6d6" stop-opacity=".8"/></radialGradient>',
         '<filter id="sb" x="-10" y="-10" width="60" height="60" filterUnits="userSpaceOnUse">'
         '<feGaussianBlur stdDeviation="0.9"/></filter>',
         f'<clipPath id="in"><path d="{ring_d}"/></clipPath>', '</defs>']
    s.append(f'<path d="{ring_d}" fill="url(#gl)"/>')
    s.append('<g clip-path="url(#in)">')
    # inner rim band (glass thickness), stronger lower-right
    w = [0.9 + 2.0 * smoothstep(-0.6, 0.9, dot(n, unit((0.7, 0.7)))) for n in rn]
    s.append(f'<path d="{ribbon_d(rs + rs[:1], rn + rn[:1], w + w[:1], bias=1.0, every=2)}" fill="#7aa6d6" '
             f'opacity=".6" filter="url(#sb)"/>')
    # reflected light crescent lower-right inside the rim
    lw = [2.0 * smoothstep(0.35, 0.95, dot(n, unit((0.55, 0.83)))) for n in rn]
    lp = [sub(p, mul(n, 3.6)) for p, n in zip(rs, rn)]
    s.append(f'<path d="{ribbon_d(lp + lp[:1], rn + rn[:1], lw + lw[:1], bias=1.0, every=2)}" fill="#f2f8ff" '
             f'opacity=".75"/>')
    # faint internal reflection line (like the bubbles carried in the reference)
    for br, wd, op in [([(11.5, 27.5), (16.5, 24.6), (21.6, 21.8)], 1.3, .5),
                       ([(21.2, 22.2), (23.4, 17.4), (28.6, 12.6)], 1.2, .45),
                       ([(21, 21.9), (25.6, 24.2), (31.2, 25.4)], 1.1, .4)]:
        s.append(f'<path d="{stroke_along([p for p, t in sample(spline(br), 0.8)], wd, 0.6)}" fill="#6a95cc" '
                 f'opacity="{op}"/>')
    s.append('</g>')
    # outline: thin dark blue, thicker lower-right, broken at the top-left
    ow = [(0.7 + 1.5 * smoothstep(-0.4, 0.9, dot(n, unit((0.6, 0.8))))) * (1 - 0.85 * smoothstep(0.75, 0.97, dot(n, unit((-0.6, -0.8))))) for n in rn]
    s.append(f'<path d="{ribbon_d(rs + rs[:1], rn + rn[:1], ow + ow[:1], bias=0.4, every=2)}" fill="#35588a" '
             f'opacity=".9"/>')
    # white highlights: big soft oval upper-left + small dot
    hl = ellipse_pts((13.6, 12.4), 4.6, 2.5, math.radians(-42), 8)
    s.append(f'<path d="{d_closed(hl)}" fill="#ffffff" opacity=".95"/>')
    s.append(f'<path d="{d_closed(ellipse_pts((21.6, 9.2), 1.6, 1.3, 0.3, 6))}" fill="#ffffff" opacity=".9"/>')
    s.append(f'<path d="{d_closed(ellipse_pts((9.6, 19.4), 1.1, 2.0, 0.25, 6))}" fill="#ffffff" opacity=".55"/>')
    s.append('</svg>')
    write(out + 'bubble.svg', ''.join(s))


# =============================================================================== streak
def streak(out):
    W, H = 220, 24
    # feathered lens: thin tail on the left, fuller body toward the right (flow left -> right)
    top = [(4, 12.4), (40, 10.6), (100, 8.6), (150, 7.6), (186, 8.6), (210, 11.2), (216, 12)]
    bot = [(216, 12), (208, 13.2), (184, 15.4), (146, 16.2), (96, 14.8), (40, 13.2), (4, 12.4)]
    body = d_segs(spline(top)) + d_segs(spline(bot), move=False)[0:] + 'Z'
    body = body.replace('Z', '') + 'Z'
    core_top = [(30, 11.9), (90, 11.0), (150, 10.6), (196, 11.4)]
    core = [p for p, t in sample(spline(core_top), 2)]
    s = [head(W, H), '<defs>',
         '<linearGradient id="fx" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="220" y2="0">'
         '<stop offset="0" stop-color="#ffc9c4" stop-opacity="0"/>'
         '<stop offset=".25" stop-color="#ffc9c4" stop-opacity=".24"/>'
         '<stop offset=".6" stop-color="#ffc3be" stop-opacity=".55"/>'
         '<stop offset=".8" stop-color="#ffc3be" stop-opacity=".62"/>'
         '<stop offset=".93" stop-color="#ffc9c4" stop-opacity=".3"/>'
         '<stop offset="1" stop-color="#ffc9c4" stop-opacity="0"/></linearGradient>',
         '<linearGradient id="fc" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="220" y2="0">'
         '<stop offset="0" stop-color="#fff1ee" stop-opacity="0"/>'
         '<stop offset=".45" stop-color="#ffe2dd" stop-opacity=".4"/>'
         '<stop offset=".78" stop-color="#ffe6e1" stop-opacity=".65"/>'
         '<stop offset="1" stop-color="#fff1ee" stop-opacity="0"/></linearGradient>',
         '<filter id="fe" x="-20" y="-20" width="260" height="64" filterUnits="userSpaceOnUse">'
         '<feGaussianBlur stdDeviation="1.8 1.5"/></filter>',
         '<filter id="fe2" x="-20" y="-20" width="260" height="64" filterUnits="userSpaceOnUse">'
         '<feGaussianBlur stdDeviation="0.8"/></filter>', '</defs>']
    s.append(f'<path d="{body}" fill="url(#fx)" filter="url(#fe)"/>')
    s.append(f'<path d="{stroke_along(core, 2.4, 0.6)}" fill="url(#fc)" filter="url(#fe2)"/>')
    s.append('</svg>')
    write(out + 'streak.svg', ''.join(s))



ALL = {
    'disc': lambda env, fx: disc_cell(env),
    'far': lambda env, fx: disc_cell_far(env),
    'blur': lambda env, fx: disc_cell_blur(env),
    'vignette': lambda env, fx: vignette(env),
    'glow': lambda env, fx: glow(env),
    'particle': lambda env, fx: particle(fx),
    'bubble': lambda env, fx: bubble(fx),
    'streak': lambda env, fx: streak(fx),
}


def main(argv):
    env, fx = ENV, FX
    if '--out' in argv:
        i = argv.index('--out')
        env = fx = os.path.join(argv[i + 1], '')
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(env, exist_ok=True)
    for k in (argv or list(ALL)):
        ALL[k](env, fx)


if __name__ == '__main__':
    main(sys.argv[1:])
