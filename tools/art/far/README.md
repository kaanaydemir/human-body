# Far tunnel generator (layer 1, scroll 0.12)

Generates `public/assets/svg/environment/far_a.svg` and `far_b.svg`.

```sh
# from the repo root; writes straight into public/assets/svg/environment/
python3 -I tools/art/far/gen_far.py
# or write somewhere else (e.g. for a comparison render)
python3 -I tools/art/far/gen_far.py /path/to/out_dir
```

Pure Python 3 standard library. The output is deterministic (seeded RNGs), so re-running
reproduces the committed SVGs byte for byte.

## What `gen_far.py` draws

Each 1920x1080 opaque segment has two receding tunnel openings (one big with 5 folds, one small
with 4), modelled on panels 4/5 of `reference.png`:

- **Folds** are arches: a superellipse top, legs that stand on the floor. Band widths shrink
  toward the hole (big: 118/82/56/38/26 px, crease gaps 14 to 8 px). Each band has a dark
  valley on its outer edge, a lit face and a broken `#e0505a` lip on the upper-left, an opaque
  `#93201e` cel shadow, and a 3 px `#6e1a24` crease on the lower-right.
- **Hole**: a hard-edged arch, `#5a1520`/`#6c1b26`/`#771e29` gradient, a `#4e141d` core
  window, one ghost fold, the floor running in, and 3-5 dim `#7a2a30` cell silhouettes.
- **Floor wedge** (`#8e2f38` far to `#b0353c` near, saturation-compensated): converges into
  the hole base, with soft transverse swells and 2-3 tiny mounds.
- **Shared fold**: the outer folds of the two openings meet at one crease (`fold_line`).
- **Seam folds** (`draw_seam_folds`): half a fold at each border, identical in every variant,
  so a tile seam reads as one more fold. These are the only features inside the 48 px
  margins. All other features fade in over 48 to 64 px (`edgemask`).
- **Shared filters**: `grain` and `mottle` from ART_DIRECTION section 7, using the new mottle
  values `0.94 / 0.36 / 0.30`, alpha `0.08`.

The arch set is sized for the window the game shows of this layer (about y = 300..720
between the rear wall strips): hole centres sit at y 518..560 and the inner arch tops at
y 300..470.

`VARIANTS` at the bottom holds the per-variant composition (anchors, hole sizes, drift, lean
and light). `BASE_STOPS` is the shared base gradient and must stay identical for every variant.

## Superseded

`tools/out/far/gen_far.py` is the previous (concentric oval) generator. It is kept only for
reference.
