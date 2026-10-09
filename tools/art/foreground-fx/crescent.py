"""Cel-painted foreground folds (layer 5, scroll 1.3) for the foreground-fx group.

A Fold is one fat crescent of tissue: a hand-placed silhouette contour (anchors -> centripetal
Catmull-Rom cubic Beziers), painted the way the reference panels 6/7/9 paint their near mounds:

  flat base  ->  ONE opaque cel shadow (below a hand-placed terminator)  ->  ONE broad highlight
  crescent on the lit upper-left  ->  a broken pale streak inside it  ->  a few short hatches
  ->  silhouette ink, thick (5-6 px) on the bottom / shadow side, tapering to ~2 px and broken
  on the lit top-left.

No Gaussian-blurred volume layers, no pores, no specular dots.  A fold in front of another one
drops a crisp (unblurred) cel shadow onto it.

kind 'bottom': the contour runs left -> right over the top of a mound; the shape is closed
below the canvas bottom.  kind 'top': the contour runs left -> right along the underside of a
hanging lip; the shape is closed above the canvas top.
"""
import math
from geo import (P, add, sub, mul, dot, unit, smoothstep, spline, sample, d_segs, ribbon_runs, pip,
                 stroke_along)

# light comes from the front / upper-left; S is the direction the shadow side faces
LIGHT = unit((-0.6, -0.8))
SHADE = unit((0.75, 0.66))


def in_ranges(x, ranges):
    """1 inside any (x0, x1, soft) range, smooth falloff of `soft` px at both ends."""
    k = 0.0
    for r in ranges:
        x0, x1 = r[0], r[1]
        soft = r[2] if len(r) > 2 else 6.0
        k = max(k, smoothstep(x0 - soft, x0, x) * (1 - smoothstep(x1, x1 + soft, x)))
    return k


def bump(x, x0, x1, power=0.8):
    """0 outside [x0, x1], sin-shaped hump inside."""
    if x <= x0 or x >= x1:
        return 0.0
    return math.sin(math.pi * (x - x0) / (x1 - x0)) ** power


class Fold:
    def __init__(self, name, kind, contour, lit, *, W, H, pal, hl=None, streaks=(), ink=(2.0, 6.0),
                 ink_breaks=(), ink_thin=None, hatches=(), cast=None, step=2.0):
        """
        contour : anchors left -> right; first/last anchors only steer the end tangents.
        lit     : closed list of hand-placed points; the lit (base-colour) area is this polygon clipped to
                  the silhouette, everything else inside the silhouette is the cel shadow.
        hl      : (x0, x1, inset, width, power)  broad highlight crescent hugging the contour.
        streaks : [(x0, x1, inset, width)]       broken pale streak dashes (inset from the contour).
        ink     : (thin, thick) px.  ink_breaks: [(x0, x1)] gaps.  ink_thin: [(x0, x1)] forced thin.
        hatches : [(x, depth, n, length, tilt)]   short stroke clusters following the contour.
        cast    : (dx, dy) offset of the crisp cel shadow this fold drops on the folds behind it.
        """
        self.name, self.kind, self.W, self.H, self.pal = name, kind, W, H, pal
        self.segs = spline(contour, phantoms=True)
        sm = sample(self.segs, step)
        self.pts = [p for p, t in sm]
        self.tans = [t for p, t in sm]
        if kind == 'bottom':
            self.nrm = [(t[1], -t[0]) for t in self.tans]   # outward = up
            first, last = self.pts[0], self.pts[-1]
            closure = [(last[0], H + 80), (first[0], H + 80)]
        else:
            self.nrm = [(-t[1], t[0]) for t in self.tans]   # outward = down
            first, last = self.pts[0], self.pts[-1]
            closure = [(last[0], -80), (first[0], -80)]
        self.d = d_segs(self.segs) + ''.join('L' + P(c) for c in closure) + 'Z'
        self.poly = self.pts + closure
        lsegs = spline(lit, closed=True)
        self.lit_d = d_segs(lsegs, close=True)
        self.lit_poly = [p for p, t in sample(lsegs, 4)]
        self.hl = hl
        self.streaks = streaks
        self.ink = ink
        self.ink_breaks = ink_breaks
        self.ink_thin = ink_thin or []
        self.hatches = hatches
        self.cast = cast

    # ------------------------------------------------------------------ helpers
    def _band(self, x0, x1, inset, width, power=0.8, bias=1.0):
        ws, pts = [], []
        for p, n in zip(self.pts, self.nrm):
            ws.append(width * bump(p[0], x0, x1, power))
            pts.append(sub(p, mul(n, inset)))
        return ribbon_runs(pts, self.nrm, ws, bias=bias, every=2, thr=0.3)

    def _near(self, x):
        """contour sample (point, tangent, normal) closest in x (contours are x-monotonic)."""
        i = min(range(len(self.pts)), key=lambda k: abs(self.pts[k][0] - x))
        return self.pts[i], self.tans[i], self.nrm[i], i

    def inside(self, q):
        return pip(q, self.poly) and 0 <= q[0] <= self.W and 0 <= q[1] <= self.H

    # ------------------------------------------------------------------ pieces
    def ink_d(self):
        lo, hi = self.ink
        ws = []
        for p, n in zip(self.pts, self.nrm):
            s = smoothstep(-0.25, 0.85, dot(n, SHADE))
            w = lo + (hi - lo) * s
            w = w + (lo - w) * in_ranges(p[0], self.ink_thin)
            w *= 1 - in_ranges(p[0], self.ink_breaks)
            ws.append(w)
        return ribbon_runs(self.pts, self.nrm, ws, bias=0.62, every=2, thr=0.35)

    def hl_d(self):
        if not self.hl:
            return ''
        x0, x1, inset, width, power = self.hl
        return self._band(x0, x1, inset, width, power)

    def streak_d(self):
        out = []
        for x0, x1, inset, width in self.streaks:
            out.append(self._band(x0, x1, inset, width, 0.6))
        return ''.join(out)

    def hatch_svg(self):
        lit_out, shade_out = [], []
        for x, depth, n, length, tilt in self.hatches:
            p, t, nn, i = self._near(x)
            for k in range(n):
                dd = depth + k * 5.0
                xs = x + k * length * 0.18
                a = self._near(xs - length / 2)[3]
                b = self._near(xs + length / 2)[3]
                if b - a < 3:
                    continue
                seg = []
                for j in range(a, b + 1):
                    s = (j - a) / (b - a)
                    off = dd + tilt * (s - 0.5)
                    seg.append(sub(self.pts[j], mul(self.nrm[j], off)))
                mid = seg[len(seg) // 2]
                if not (self.inside(seg[0]) and self.inside(seg[-1]) and self.inside(mid)):
                    continue
                w = 2.4 - 0.4 * k
                path = stroke_along(seg, w, 0.7)
                (lit_out if pip(mid, self.lit_poly) else shade_out).append(path)
        o = []
        if lit_out:
            o.append(f'<path d="{"".join(lit_out)}" fill="{self.pal["hatch_lit"]}" opacity=".75"/>')
        if shade_out:
            o.append(f'<path d="{"".join(shade_out)}" fill="{self.pal["hatch_shade"]}" opacity=".6"/>')
        return ''.join(o)

    # ------------------------------------------------------------------ assembly
    def svg(self, behind_clip=None):
        pal = self.pal
        o = []
        if behind_clip and self.cast:
            dx, dy = self.cast
            o.append(f'<path d="{self.d}" transform="translate({dx} {dy})" fill="{pal["cast"]}" '
                     f'clip-path="url(#{behind_clip})"/>')
        o.append(f'<path d="{self.d}" fill="{pal["shadow"]}"/>')
        o.append(f'<g clip-path="url(#clip_{self.name})">')
        o.append(f'<path d="{self.lit_d}" fill="{pal["base"]}"/>')
        hd = self.hl_d()
        if hd:
            o.append(f'<path d="{hd}" fill="{pal["hl"]}"/>')
        sd = self.streak_d()
        if sd:
            o.append(f'<path d="{sd}" fill="{pal["streak"]}"/>')
        o.append(self.hatch_svg())
        o.append('</g>')
        o.append(f'<path d="{self.ink_d()}" fill="{pal["ink"]}"/>')
        return ''.join(o)

    def clip_def(self):
        return f'<clipPath id="clip_{self.name}"><path d="{self.d}"/></clipPath>'
