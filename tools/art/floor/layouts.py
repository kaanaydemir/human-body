# Hand-placed dune layouts for floor_a/b/c (1920x360; contour y=72 on both borders = seam-mound apex).
#
#   dune(key, row, xc, yc, w, h, rise, d, **opts)
#        a dune of total width w (= al + ar) and height h, crest at (xc, yc). d='R': long gentle slope on
#        the left (al = 2/3 w), short end on the right, and the right foot sits `rise` px higher than the
#        left one, so the dune rises to the right; d='L' mirrors that. Keep h/w <= 0.18 (back, mid) and
#        <= 0.25 (front). opts: m (superellipse exponent, 1.4-1.7), lobes [(dx, raise, width)], wob, ...
#   ('r', key, row, xc, yc, al, ar, hl, hr, {opts})   the raw form dune() expands to
#   ('S', key)                      slot of a shared seam dune (drawn at x=0 and x=1920 in every variant)
#   ('n', parent, cx, w, h, depth)  small oval lump lying `depth` px below the parent's contour
#
# Draw order = list order (later = nearer). Five staggered sub-rows, back to front:
#   far back  crests y  76-100  320-420 x 34-42      near back crests y 108-130  340-440 x 38-46
#   mid 1     crests y 145-170  460-620 x 64-78      mid 2     crests y 192-215  480-650 x 66-80
#   front     crests y 255-272  800-1000 x 150-170 (cropped by the canvas bottom)
# (dune lengths follow the bands measured in panel 4: ~350-450 px far, ~500-650 mid, 600-1000 front)
# Inside a sub-row, right-rising dunes are drawn left to right, so each one's raised end tucks behind
# the low start of the next (the diagonal shingles of panel 4).
#
# Seam contract: SEAM is in seam coordinates (x=0 is the tile border) and is drawn at x=0 and x=1920 by
# every variant; each shared dune is drawn right after the variant dunes of its own sub-row. Inside
# ZONE=150 px of a border only shared dunes may be visible (gen_floor.py checks this), variant dunes overlap
# them from 150 px in.


def dune(key, row, xc, yc, w, h, rise, d='R', **opts):
    if d == 'R':
        al, ar, hl, hr = round(w * 2 / 3), round(w / 3), h, h - rise
    else:
        al, ar, hl, hr = round(w / 3), round(w * 2 / 3), h - rise, h
    return ('r', key, row, xc, yc, al, ar, hl, hr, opts)


SEAM = [
    # far back: the seam mound. Apex exactly on the border at y=72 with a horizontal tangent.
    ('r', 'S1', 'back', 0, 72, 230, 150, 66, 36, dict(m=1.4, wob=0)),
    # near back, mid 1, mid 2, front: one shared dune per sub-row spanning the join
    dune('S1b', 'back', -50, 116, 400, 44, 28, 'R', m=1.5),
    dune('S2', 'mid', 80, 158, 500, 74, 38, 'L', m=1.5, lobes=[(150, 3, 60)]),
    dune('S2b', 'mid', -40, 206, 540, 78, 40, 'R', m=1.5),
    ('r', 'S3', 'front', 70, 264, 540, 420, 165, 148, dict(m=1.5, lobes=[(-240, 4, 80), (190, 3, 70)])),
]

LAYOUTS = {
    'a': dict(seed=11, items=[
        dune('fa1', 'back', 420, 86, 380, 40, 26),
        dune('fa2', 'back', 730, 92, 360, 38, 24),
        dune('fa4', 'back', 920, 98, 340, 36, 24, 'L'),
        dune('fa3', 'back', 1100, 80, 400, 42, 28),
        dune('fa5', 'back', 1400, 90, 380, 40, 26),
        dune('fa6', 'back', 1570, 84, 380, 40, 26, 'L'),
        ('S', 'S1'),
        dune('na1', 'back', 480, 120, 420, 44, 28),
        dune('na2', 'back', 820, 112, 400, 44, 28),
        dune('na4', 'back', 1000, 128, 360, 40, 26, 'L'),
        dune('na3', 'back', 1180, 116, 420, 46, 30),
        dune('na5', 'back', 1520, 122, 420, 44, 28),
        ('S', 'S1b'),
        dune('ma1', 'mid', 560, 148, 540, 76, 44),
        dune('ma2', 'mid', 980, 160, 560, 78, 46, lobes=[(-160, 3, 50)]),
        dune('ma3', 'mid', 1180, 168, 480, 70, 34, 'L'),
        dune('ma4', 'mid', 1520, 150, 520, 76, 44),
        ('S', 'S2'),
        dune('mb1', 'mid', 500, 202, 560, 80, 46),
        dune('mb2', 'mid', 900, 194, 580, 80, 48),
        dune('mb3', 'mid', 1300, 208, 560, 78, 44),
        dune('mb4', 'mid', 1560, 200, 480, 72, 36, 'L'),
        ('n', 'mb2', 800, 56, 14, 26),
        ('S', 'S2b'),
        dune('fr1', 'front', 830, 260, 1050, 165, 44, 'L', lobes=[(260, 4, 90)]),
        ('S', 'S3'),
    ]),
    'b': dict(seed=23, items=[
        dune('fb1', 'back', 380, 90, 360, 38, 24),
        dune('fb3', 'back', 640, 98, 340, 36, 24, 'L'),
        dune('fb2', 'back', 700, 80, 400, 42, 28),
        dune('fb4', 'back', 1010, 88, 380, 40, 26),
        dune('fb5', 'back', 1310, 82, 400, 42, 28),
        dune('fb6', 'back', 1600, 94, 360, 38, 24),
        ('S', 'S1'),
        dune('nb1', 'back', 430, 126, 420, 44, 28),
        dune('nb2', 'back', 760, 116, 420, 46, 30),
        dune('nb3', 'back', 1080, 124, 400, 44, 28),
        dune('nb5', 'back', 1330, 130, 360, 40, 26, 'L'),
        dune('nb4', 'back', 1420, 114, 420, 44, 28),
        dune('nb6', 'back', 1660, 124, 300, 40, 26),
        ('S', 'S1b'),
        dune('mc1', 'mid', 480, 158, 540, 76, 44),
        dune('mc3', 'mid', 820, 170, 500, 72, 40, 'L'),
        dune('mc2', 'mid', 900, 150, 560, 78, 46, lobes=[(-170, 3, 50)]),
        dune('mc4', 'mid', 1290, 162, 540, 76, 44),
        dune('mc5', 'mid', 1560, 158, 440, 70, 40),
        ('S', 'S2'),
        dune('md1', 'mid', 560, 198, 580, 80, 48),
        dune('md2', 'mid', 960, 210, 560, 78, 44),
        dune('md4', 'mid', 1260, 214, 500, 72, 40, 'L'),
        dune('md3', 'mid', 1380, 196, 560, 80, 46),
        dune('md5', 'mid', 1640, 214, 380, 66, 36),
        ('n', 'md1', 470, 54, 14, 26),
        ('S', 'S2b'),
        dune('fr1', 'front', 960, 262, 1080, 165, 46, lobes=[(-250, 4, 90)]),
        ('S', 'S3'),
    ]),
    'c': dict(seed=37, items=[
        dune('fc1', 'back', 400, 82, 400, 42, 28),
        dune('fc2', 'back', 690, 92, 360, 38, 24),
        dune('fc4', 'back', 900, 98, 340, 36, 24, 'L'),
        dune('fc3', 'back', 1040, 80, 400, 42, 28),
        dune('fc5', 'back', 1350, 88, 360, 40, 28),
        dune('fc6', 'back', 1580, 84, 360, 40, 26, 'L'),
        ('S', 'S1'),
        dune('nc2', 'back', 560, 128, 360, 40, 26, 'L'),
        dune('nc1', 'back', 470, 116, 420, 44, 28),
        dune('nc3', 'back', 820, 122, 420, 46, 30),
        dune('nc4', 'back', 1150, 114, 420, 44, 28),
        dune('nc5', 'back', 1470, 124, 400, 44, 28),
        dune('nc6', 'back', 1660, 118, 260, 38, 24),
        ('S', 'S1b'),
        dune('me1', 'mid', 520, 152, 540, 76, 44),
        dune('me2', 'mid', 900, 162, 540, 78, 46),
        dune('me3', 'mid', 1230, 150, 520, 76, 44, lobes=[(-150, 3, 50)]),
        dune('me4', 'mid', 1470, 168, 460, 70, 40, 'L'),
        ('S', 'S2'),
        dune('mf2', 'mid', 640, 212, 500, 72, 40, 'L'),
        dune('mf1', 'mid', 520, 196, 560, 80, 46),
        dune('mf3', 'mid', 960, 202, 580, 80, 48),
        dune('mf4', 'mid', 1360, 208, 560, 78, 44),
        dune('mf5', 'mid', 1630, 214, 400, 66, 36),
        ('n', 'mf3', 870, 56, 15, 26),
        ('S', 'S2b'),
        dune('fr1', 'front', 1090, 264, 1000, 160, 40, lobes=[(-230, 4, 90)]),
        ('S', 'S3'),
    ]),
}
