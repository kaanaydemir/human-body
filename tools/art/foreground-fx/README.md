# foreground-fx generator (layer 5 foreground, overlays, loose discs, FX)

Writes, straight into `public/assets/svg/`:

| File | What |
|---|---|
| `environment/fg_bottom_1..3.svg` | near mounds on the 1.3 plane (2–3 fat cel-painted crescents each) |
| `environment/fg_top_1..2.svg` | long overhanging fold lips, content ≤ 560×150 centred in the 760×240 / 620×220 contract canvas |
| `environment/disc_cell.svg` | plain biconcave disc in the open 3/4 view of panels 4/7 |
| `environment/disc_cell_far.svg` | hazed, thin-outlined version of the same disc for the scroll-.55 traffic (new; needs wiring in code, see below) |
| `environment/disc_cell_blur.svg` | the same disc, softly out of focus, for the 1.3+ plane |
| `environment/vignette.svg` | corners-only warm vignette, tuned for code alpha .45 |
| `environment/glow.svg` | saturated amber ADD glow, tuned for code alpha .15–.185 at scale 1.6 |
| `fx/particle.svg`, `fx/bubble.svg`, `fx/streak.svg` | unchanged since round 1 (reproduced byte for byte) |

```sh
# from the repo root
python3 -I tools/art/foreground-fx/gen.py              # everything -> public/assets/svg/...
python3 -I tools/art/foreground-fx/gen.py --out DIR    # everything -> DIR (for comparisons)
python3 -I tools/art/foreground-fx/gen_fg.py [b1 b2 b3 t1 t2] [--out DIR]
python3 -I tools/art/foreground-fx/gen_misc.py [disc far blur vignette glow particle bubble streak] [--out DIR]
python3 -I tools/art/foreground-fx/check.py [SVG_DIR]  # contract + raw HSV check of the fg pieces
```

Pure Python 3 standard library for the generators (no randomness, so a re-run reproduces the SVGs byte for byte).
`check.py` also needs numpy, Pillow and node/playwright (`tools/render-svg.mjs`).

## Files

- `geo.py`: Catmull-Rom → cubic Bézier helpers, variable-width ribbons (ink, crescents, strokes) and
  `FILTERS_FG` (the shared `grain` from ART_DIRECTION §7 plus the lower-saturation `mottle` matrix that
  far/floor adopted; the fg pieces only use `grain`).
- `crescent.py`: `Fold`, the cel painter for one fat crescent: flat base → one opaque cel shadow below a
  hand-placed terminator → one broad `#ea6a55` highlight crescent → broken pale `#f3b2a2` streak → a few short
  hatches → `#5a1a1c` silhouette ink (≈6 px on the bottom/shadow side, 2 px and broken on the lit top-left).
  A fold in front drops a crisp cel shadow (same single shadow tone) on the folds behind it. No blurred volume
  layers, no pores, no specular dots.
- `gen_fg.py`: the hand-placed silhouettes, terminators, crescents, streaks, ink breaks and hatches of the five
  pieces, plus the two palettes (`PAL` bottom, `PAL_TOP` hanging lips).
- `gen_misc.py`: the discs (`CELL`, `CELL_FAR`, `DISC_GEOM`, `DOF_BLUR`), the vignette (`VIG`), the glow (`GLOW`)
  and the unchanged particle / bubble / streak.
- `gen.py`: runs both generators.

## Numbers the code relies on

- `vignette.svg` assumes `setAlpha(0.45)`; `glow.svg` assumes ADD, `setAlpha(0.15 + pulse * 0.035)`, `setScale(1.6)`.
- `disc_cell_far.svg` is meant to be used with **no tint and alpha 1** (its haze is baked in). Wiring it needs
  `env('disc_cell_far', 140, 140)` in `src/assets.ts` and, in `src/fx/BloodFlow.ts`, the far-disc loop using
  `'disc_cell_far'` without `tint` and with `alpha: 1`.
