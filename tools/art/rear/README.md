# Rear vessel wall generator (`rear_a.svg`, `rear_b.svg`)

Layer 2 of the bloodstream parallax (scroll 0.35, 1920×1080, transparent between the strips).

## Run

From the repo root:

```sh
python3 -I tools/art/rear/gen.py                      # writes public/assets/svg/environment/rear_a.svg + rear_b.svg
python3 -I tools/art/rear/check.py tools/out/rear/chk  # optional: renders + numeric checks (needs numpy, Pillow, node)
```

The output is deterministic (seeded RNG), so a re-run reproduces the committed SVGs byte for byte.

## Files

| File | What it does |
|---|---|
| `gen.py` | The whole generator (stdlib only). Hand-placed layout data for both variants is at the bottom (`SPEC_A`, `SPEC_B`). `--debug DIR` also writes rib/echo mask SVGs and prints the arch geometry (crown height, leg bow, lean, widths). |
| `check.py` | Re-runs `gen.py --debug`, renders the SVGs (and the current `far_*` layer) with `tools/render-svg.mjs`, writes composites, seam strips and seam crops, and prints the tiling and colour checks: margin identity, seam continuity, strip contour ranges and flat runs, HSV of the strips, ribs and echo rings, pale-rim area, a/b overlap and the edge-orientation mix. |

## What is drawn (back to front)

1. **Top strip.** Base gradient `topBase`. Its contour forms receding vaults between the ribs, with the apex at 280–300 and the sides dropping to 380–420 into the rib shoulders. Each vault has two nested arch soffits: a `#d8635f` rim on the lower edge and a `#771d26` recess under it. Two receding outer-ring soffits sit above every crown.
2. **Bottom strip.** Base gradient `botBase` plus the `hazeBot` distance haze (`#cc4c4e`, α .12, applied the same way to every body).
3. **Back mound row.** Its tops at 700–735 define the dipping contour inside the arch openings.
4. **Echo rings.** One per hero arch, concentric and tucked about 12 px behind the hero's inner edge. They have no outline and use hazy cel colours.
5. **Mid mound row.**
6. **Hero ring arches.** Full arches on an ellipse centred below the floor, each a fat crescent: crown 148–178 px, mid-height 116–141 px, feet 80–90 px. Shading is cel shading of a tube cross-section lit from the front/upper-left, made of these opaque shapes:
   - lit face `#d13b3f`
   - one highlight shape `#f34f49`
   - one shadow band `#93201e`, capped at about 40 px
   - a crease `#771d26` on the shadow edge
   - 30–90 px dashes that follow the curve, clustered on the lit shoulder
   - a saturated lit-edge stroke `#f66a62`
   - a broken pale rim `#f4a69c` (≤1 % of rib area)
   - a tapered `#6e1a24` ink line, only on the shadow side
7. **Front mounds.** These include the foot mounds that swallow the rib feet (tops 644–665), then the front rows. They are opaque cel mounds: base-gradient body, lit cap, one shadow crescent, rim, tapered ink, and an opaque contact crease clipped to the strip.
8. **Shared `grain` + `mottle` overlay** over the union silhouette, with the filter region set to the full canvas.

The only translucency left is the shared mottle overlay (opacity .5) and the `hazeBot` gradient stops.

## Tiling contract

- The strips are exactly at y=300 (top) and y=720 (bottom) at both borders, and flat for 48 px.
- **Shared seam motif.** `SEAM_*` in `gen.py` is drawn in seam coordinates at x=0 and x=1920 in *both* files. It contains:
  - the seam vault contour and its small soffit
  - a valley recess plus a low mound whose top touches the 720 lip
  - two foot mounds

  So every border column is pixel-identical across variants (`check.py` → `margin identity 0`), and the seam reads as a vault and a mound instead of a ruled ledge. The motif mound is clipped to the strip, so it never lifts the silhouette above 720.
- Variant features keep ≥60 px from the borders (asserted at build time: `MARGIN VIOLATION` on stderr).
- Base gradient stops, identical in both variants: `#b42c35` (offset 0, at the strip lip) → `#9a2530` (offset 1, at the canvas edge).
