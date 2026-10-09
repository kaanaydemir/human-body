# UI kit generator (`public/assets/svg/ui/*.svg`)

These scripts generate the HUD art: the caption/dialogue panel, the number badge, the two keycaps, the objective icon, and the progress-bar submarine marker.

## Run

From the repo root:

```sh
python3 -I tools/art/ui/gen_ui.py                    # writes all six SVGs into public/assets/svg/ui/
python3 -I tools/art/ui/gen_ui.py panel badge        # writes only the named assets
python3 -I tools/art/ui/gen_ui.py --out DIR          # writes somewhere else, e.g. a scratch dir to diff against
python3 -I tools/art/ui/check.py [OUT_DIR] [--svg-dir DIR]   # renders and runs the numeric checks (Pillow + node)
```

`gen_ui.py` uses only the standard library. It has no clock and no RNG, so a re-run reproduces the committed SVGs byte for byte. Paths resolve from the script's own location, so the working directory does not matter.

## Files

| File | What it does |
|---|---|
| `gen_ui.py` | Draws every asset. Each asset is one function (`panel`, `badge`, `key_e`, `key_space`, `icon_objective`, `icon_progress`). The tunables sit at the bottom of the file (`PANEL_*`, `BADGE_*`, `GRAIN_OP`, `ICON_*`). The helpers turn anchor loops into Catmull-Rom cubic Béziers (`smooth_closed`, `loop`), turn centre-lines with a width profile into brush strokes (`brush`, `profile`), and build straight-edged rounded rectangles (`rrect`, `rquad`). |
| `nineslice.py` | Stretches a 600×200 panel the way Phaser's NineSlice does (40 px margins, bilinear). |
| `check.py` | Renders every SVG with `tools/render-svg.mjs`, at 1× on a transparent background and at 3× on cream. It prints the panel fill mean (RGB/HSV, V std), the outline width and core colour for each side, the badge mean and how flat it is, and the progress-icon bounding box. It also writes these images: `nine_sheet.png` (the panel at every HUD size, with the badge and the icon), `cmp_caption.png` (reference caption 4 scaled to the game caption, above our 980×150 caption) and `cmp_corner.png` (an 8× corner close-up of both). |

## Assets

| File | Size | Notes |
|---|---|---|
| `panel.svg` | 600×200 | A printed caption box like the numbered captions in `reference.png`. It has one flat fill, base `#fcedd6`, which with the shared `grain` overlay at .35 averages `#faead3`. The outline is near-black `#2e241c`, 3.5 px and even on all four sides. The corners are circular, r=24 outside and 20.5 inside. There is no bevel, highlight, lip or mottle. The straight edges are exactly straight, and all curvature is inside the 40 px 9-slice corners. A 1 px transparent margin is kept outside the line. |
| `badge.svg` | 96×96 | A flat navy-black disc `#0d1424` with r=45 and a wobble under 0.3 px. The colour is sampled from the interiors of reference badges 1, 4, 5 and 9 (mean `#0c1322`). It has no ring, outline, specular or grain. The game prints the numeral. |
| `key_e.svg`, `key_space.svg` | 96×96, 220×96 | Cream keycaps in a 3/4 view. `key_e` has a hand-lettered "E" drawn as brush paths. |
| `icon_objective.svg` | 96×96 | A magnifying glass over a red cell disc. |
| `icon_progress.svg` | 64×36 | The progress-bar marker: the sub reduced to a cream teardrop hull, a light-blue dome with no explorer, a red nose ball and a red tail fin. The outer line is 3 px `#3b2a22`, the inner separation lines are 1.8 px, and each part has one cel shade and one highlight. It faces right. Its anchor is the centre. |
