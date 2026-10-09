# Near floor generator (layer 4, main plane, scroll 1.0)

Generates `public/assets/svg/environment/floor_a.svg`, `floor_b.svg`, `floor_c.svg` (1920x360, placed at y=720).

```sh
# from the repo root; writes straight into public/assets/svg/environment/
python3 -I tools/art/floor/gen_floor.py
# or write somewhere else (e.g. for a comparison render), optionally only some variants
python3 -I tools/art/floor/gen_floor.py /path/to/out_dir [a b c]
# verification: renders, shared-zone identity, seam continuity, zone-edge cut check, HSV stats
FLOOR_REF_CROPS=/path/to/reference/crops python3 -I tools/art/floor/check.py OUT_DIR [SVG_DIR]
```

Pure Python 3 standard library (check.py also needs numpy, Pillow and node/playwright). The output is
deterministic (seeded RNGs, no time or hash dependence), so a re-run reproduces the SVGs byte for byte.
Each run prints, per variant, the skyline range, the longest flat run, and any warning (zone rule,
flat shelf, hole in the silhouette, border y). A clean run prints `'warn': []`.

## Files

- `layouts.py`: the hand-placed dunes. `dune(key, row, xc, yc, w, h, rise, 'R'|'L')` gives a dune of
  width w and height h with its crest at (xc, yc), with a 2:1 asymmetric superellipse (m = 1.5) that rises
  `rise` px across its length. `SEAM` is the shared seam stack in seam coordinates. `LAYOUTS` holds the
  draw order of each variant, back to front, in five staggered sub-rows (far back, near back, mid 1,
  mid 2, front), with `('S', key)` slots where the shared dune of that sub-row is drawn.
- `gen_floor.py`: geometry and painting. `Ridge` is one dune: a superellipse cap whose flanks keep
  diving at a gentle slope (`smax`), so it has no vertical walls. `Painter` paints each dune in cel style:
  - the trough: an opaque `#93201e` cel shadow on the farther dune, in the valley just above this dune
  - a flat body
  - one opaque cel shadow below a terminator
  - an opaque `#e8705f` crest band over the top 18-21 % of the height, with `#f3b8a6` dry-brush rim
    and streaks
  - 2-3 clusters of 6-14 px comma or dash marks
  - `#6e1a24` ink, 2.4-4 px, opaque, only along the lower overlap crease (where the dune passes in
    front of a farther one). It tapers out and stops 15-27 % short of the farther dune's ends. The
    floor's lit skyline gets no outline.
  `ROWS` holds the per-row palette. The back row is hazed toward `#c86a6e`.
- `check.py`: verification renders and numbers (see the docstring).

## Tiling contract (shared seam motif)

- The contour is at **y = 72 on both borders**. This is the apex of the shared seam mound `S1`, and it
  has a horizontal tangent exactly on the border.
- Every variant draws the same `SEAM` stack (one dune per sub-row) at x=0 and again at x=1920, from
  identical path data, so a dune always spans the join. Each shared dune is drawn right after the variant
  dunes of its own sub-row.
- Variant art is clipped to x in [150, 1770]. The silhouette is three separate paths, split exactly at
  x=150 and x=1770. As a result, **x < 150 and x >= 1770 are pixel-identical in every variant**
  (check.py: "max channel diff 0").
- Zone rule (checked by gen_floor.py): within 150 px of a border, a variant dune must be hidden behind
  the shared dunes drawn after it, so the clip never shows as a vertical cut.
- Flat check: any contour run with |dy| < 2 px for more than 40 px is classified. A *shelf* is flat and
  straight, like the old y=120 base trench, and is rejected with a warning. A *curved* run is a rounded
  dune crest and is allowed. The longest runs are about 80 px, on the crests of the 360-420 px far dunes.
- The base gradient is unchanged: `#d83635` (0) to `#9b2023` (1). `grain` is as in ART_DIRECTION §7.
  `mottle` uses the new shared values `0.94 / 0.36 / 0.30`, alpha `0.08`.

## Superseded

`tools/out/floor/gen_floor.py` and `layouts.py` are the previous generator. It drew closed domed mounds
with base-only 48 px margins and a y=120 border contour. It is kept only for reference.
