# Near ceiling generator (`ceiling_a.svg`, `ceiling_b.svg`, `ceiling_c.svg`)

This generates layer 4 of the bloodstream parallax: the main plane at scroll 1.0. Each SVG is 1920×340, placed at y=0, and is transparent below the contour.

## Run

From the repo root:

```sh
python3 -I tools/art/ceiling/gen_ceiling.py              # writes public/assets/svg/environment/ceiling_{a,b,c}.svg
python3 -I tools/art/ceiling/gen_ceiling.py b --out DIR  # one variant, somewhere else
python3 -I tools/art/ceiling/check.py tools/out/ceiling/check --ctx   # optional checks (Pillow, numpy, node)
```

The generator uses only the standard library. Its output is deterministic: there is no clock, and the RNGs are seeded per variant. A re-run reproduces the committed SVGs byte for byte, from any working directory.

## Files

| File | What it does |
|---|---|
| `gen_ceiling.py` | Paints the pieces (folds, arcs, marks) and assembles the SVG. It runs the margin check: a `MARGIN VIOLATION` on stderr means a variant piece left `layout.SAFE`. |
| `layout.py` | All hand-placed geometry: the shared seam set (`SEAM_FOLD`, `SEAM_ARC`, `SEAM_BACK`, `LAST_END`) and the three variants. It uses one row per control point. The header comment explains every column. |
| `geom.py` | Catmull-Rom sampling that keeps the control-point index (`cr_param`), per-point value interpolation (`at`), offset bands (`band_poly`) and closed smooth paths. |
| `check.py` | Renders the three files with `tools/render-svg.mjs`. It prints margin identity, border contour y, contour range, raw HSV and the largest plain-base patch. With `--ctx` it adds a composite over the current far_a + rear_a + floor_a + vignette (45 %) and that composite's HSV. It also writes seam strips, seam close-ups and a variant sheet. |

## What is drawn (back to front)

1. **Base.** The union silhouette (body rectangle down to y=166 plus every fold outline), filled with the shared vertical gradient `#a31f2b` (0) → `#c72a35` (1).
2. **Far vault arcs.** These are only visible in the V gaps above two overlapping arcs.
3. **Vault arcade.** These are 3–4 upward-convex ring folds per tile, 400–650 px wide, plus the shared seam arc. They overlap like shingles: each arc comes out from behind its left neighbour. Each arc has:
   - a crest-lit face `#db3a3d`, 28–38 px thick, with one cel shadow `#a8272f` on the leg turned away from the light
   - a thin crease `#8f212b` on its back edge
   - a broken 3 px rim `#e7a99e` on its lower edge
   - a recess under the rim: a `#771d26` core inside a `#93201e` band
   - one concave hollow cel `#8a1d28`

   Feet end inside a fold's round-end cap, inside the arc in front, or taper out on a fold face. So the hanging lobes read as the descending ends of the arcs.
4. **Folds.** These are the contour. Every fold is the same asymmetric kind. Its left end is tucked behind the fold before it. A long gentle slope runs down to the right into a round end, which sits in front of the next fold. The round end has a filled cap, and its outline continues over the top as a short inked crease. Lengths range from 370 to 980 px, and drops from about 30 to 70 px. Each fold is painted with:
   - an opaque lit band `#d73b3d`
   - an opaque ledge `#d8635f` with broken `#e7a99e` streaks
   - an opaque underside `#93201e`
   - an opaque, tapered 2–4 px `#6e1a24` ink line on the underside only

   A fold's paint is clipped by the outlines of the folds in front of it.
5. **Marks.** Pores, 2–3 dark spots, and 2–3 long thin `#e65450` streaks.
6. **Shared overlays.** The `mottle` overlay (opacity .3) and the `grain` overlay sit over the union silhouette. Both use the exact filter definitions from ART_DIRECTION §7, with the full-canvas region.

There is no translucent line work. The only partial opacity is the shared mottle overlay.

## Tiling

- **Shared seam set.** Every piece that crosses a border belongs to the shared seam set and is painted at x=0 and x=1920 in all three variants:
  - the seam lobe: 320 px visible, lowest point y=248 exactly at the border with a horizontal tangent, round end + cap at x 72–180
  - the seam arc, which stands in that cap and in the last fold's cap
  - two far arcs
- **Last fold end.** Every variant ends its last fold with the same capped round end (`LAST_END`, x 1630–1754).
- **Variant pieces** stay inside x 164–1756. A few start further left (`hidden=True`), but only behind the seam arc or seam lobe.
- **Result.** The 48 px margins are pixel-identical across variants (`check.py` → `margin identity 0`). The contour is at y=248–249 on both borders and flat within 1 px over the 48 px margins.
