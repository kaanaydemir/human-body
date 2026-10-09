# Asset Manifest

All authored art lives in `public/assets/svg/**` as SVG produced by generator scripts in `tools/art/<group>/`
(each folder has a README; `python3 -I tools/art/<group>/<main>.py` re-emits the group byte-for-byte). Phaser rasterises
SVGs at load time (`this.load.svg(key, url, { width, height })`) at the size listed here, so **viewBox = width/height =
the size below**. Status: ☐ planned · ◐ in progress · ☑ done (passed the in-game visual checkpoint).

Coordinates are at the 1920×1080 design resolution. The camera only scrolls horizontally; world height = 1080.

| Group | Generator |
|---|---|
| far | `python3 -I tools/art/far/gen_far.py` |
| rear | `python3 -I tools/art/rear/gen.py` |
| ceiling | `python3 -I tools/art/ceiling/gen_ceiling.py` |
| floor | `python3 -I tools/art/floor/gen_floor.py` |
| foreground-fx | `python3 -I tools/art/foreground-fx/gen.py` |
| submarine | `python3 -I tools/art/submarine/gen_submarine.py` |
| ui | `python3 -I tools/art/ui/gen_ui.py` |

---

## A. Blood vessel environment (Stage 2) — `public/assets/svg/environment/`

### Tiling contract (all repeating segments)
Segments are placed edge to edge in any order (`a b a c b …`), so **every variant of a layer must share identical
left and right edges**:
- Each layer draws an identical **seam motif** straddling its left/right border (a fold, lobe, vault or dune that is
  cut in half by the border). Inside the shared zone the variants are pixel-identical; variant art starts after it.
  A bald, featureless margin is not allowed: it shows up as a repeating notch in the game.
- Silhouette contours (ceiling bottom edge, floor top edge, rear strips) hit the border at the contract Y below with a
  **horizontal tangent**.
- Base gradients are vertical-only (`x1=x2`) and use the exact stops listed; the shared `grain` / `mottle` filters
  (ART_DIRECTION.md §7) use the full canvas as their region so `stitchTiles` makes the noise periodic.
- In the game each layer starts at a different tiling phase (`src/world/Vessel.ts`, `PHASE`), so seams of different
  layers never coincide.

| File | Size | Layer / scroll | Contract | Status |
|---|---|---|---|---|
| `far_a.svg`, `far_b.svg` | 1920×1080, opaque | 1 · far tunnel · 0.12 | Base gradient `#84202d` (0) → `#9a2832` (0.5) → `#701a28` (1). Two arched tunnel openings per tile (5 and 4 receding folds) with a floor running into a dark `#4e141d`–`#771e29` hole; holes centred at y 518–560. Seam motif: the same half-fold in the 48 px margins; features fade in 48→64 px. | ☑ |
| `rear_a.svg`, `rear_b.svg` | 1920×1080, transparent | 2 · rear wall · 0.35 | Top strip contour **y=300**, bottom strip contour **y=720** at both borders (flat 48 px). Strip base `#b42c35` at the lip → `#9a2530` at the canvas edge. Full ring arches (legs leaning/bowing, crowns under the ceiling); a shared vault-and-mound seam motif. Transparent between ribs so the far tunnel shows through. | ☑ |
| `ceiling_a.svg`, `ceiling_b.svg`, `ceiling_c.svg` | 1920×340, transparent below contour | 4 · main plane · 1.0 (placed at y=0) | Lower contour **y=248** at both borders (lowest point of a shared 320 px seam lobe, horizontal tangent); wanders 193–266. Base `#a31f2b` (0) → `#c72a35` (1). 2–3 long overhanging folds + 3–4 vault arcs per tile. | ☑ |
| `floor_a.svg`, `floor_b.svg`, `floor_c.svg` | 1920×360, transparent above contour | 4 · main plane · 1.0 (placed at y=720) | Upper contour **y=72** (global 792) at both borders: apex of the shared seam dune. The outer 150 px of each tile is identical in all variants; variant art lives in x 150–1770. Base `#d83635` (0) → `#9b2023` (1). Long, low, overlapping dunes in five staggered sub-rows. | ☑ |
| `fg_bottom_1..3.svg` | 640×300 / 820×320 / 560×280 | 5 · foreground · 1.3 | Fat crescent lumps; bottom edge fully opaque and flat (sits on the screen bottom). | ☑ |
| `fg_top_1..2.svg` | 760×240 / 620×220 | 5 · foreground · 1.3 | Two long hanging lips each (content ≤ 560×150); top edge fully opaque and flat. Placed sparsely (every ~2700–3400 px). | ☑ |
| `disc_cell.svg` | 140×140 | 5 | Plain biconcave red blood cell disc in 3/4 view (face ratio 0.8, dimple at 57%), like the loose discs in panel 7. | ☑ |
| `disc_cell_far.svg` | 140×140 | 3 | Hazier, darker version for the background traffic layer (no tint in code). | ☑ |
| `disc_cell_blur.svg` | 220×220 | 5 | Same disc, out of focus (blur 2.6) for foreground drift along the bottom edge. | ☑ |
| `vignette.svg` | 1920×1080 | overlay · 0 (alpha .45) | Corners only (`#3a0c14`); top/bottom edge midpoints stay almost untouched. | ☑ |
| `glow.svg` | 1200×800 | overlay · 0 (ADD ~.12) | Soft warm radial light `#ff8a28` (peak .37) → transparent; placed off-axis upper left. | ☑ |

### FX — `public/assets/svg/fx/`
| File | Size | Use | Status |
|---|---|---|---|
| `particle.svg` | 24×24 | small pinkish blood speck (plasma particle) | ☑ |
| `bubble.svg` | 40×40 | oxygen bubble: pale blue glass circle with highlight (for Stage 3 oxygen containers) | ☑ |
| `streak.svg` | 220×24 | soft horizontal flow streak (pale pink, feathered ends) | ☑ |

---

## B. Player — `public/assets/svg/player/`

All submarine parts share one coordinate frame: **viewBox 0 0 520 300**, the sub faces **right**, the container origin
is the frame centre (260,150). Parts are stacked back → front: `sub_back` → `explorer*` → `sub_front`.
Fixed anchors (the code in `src/objects/Submarine.ts` relies on them):
- **Headlight anchor** (glow spot on the red nose ball): **(498, 178)**
- **Jet anchor** (centre of the rear opening): **(24, 168)**
- Explorer head centre ≈ (262, 112); the canopy rim in front of the chest is at y ≈ 172.

| File | Size | Description | Status |
|---|---|---|---|
| `sub_back.svg` | 520×300 | Cockpit interior clipped to the dome: deep blue wall with a see-through lavender upper third, seat, dash. | ☑ |
| `explorer.svg` | 520×300 | The explorer only (brown hair in rounded clumps, nose bulb, orange suit, bare hands on a round steering wheel), smiling, looking right. | ☑ |
| `explorer_blink.svg` | 520×300 | Identical pose, eyes closed. Differs only inside the face box. | ☑ |
| `explorer_curious.svg` | 520×300 | Brows up, small "o" mouth (scan / interact). Differs only inside the face box. | ☑ |
| `sub_front.svg` | 520×300 | Teardrop cream hull, glossy red nose ball, red tail ball and ring band, side slot, porthole, dome glass with white streaks. | ☑ |
| `sub_light.svg` | 640×320 | Headlight cone, origin left-centre (0,160): `#ffe79e` core → `#fbb85c` → `#fc805a` → `#eb594f`, plus a soft warm spill. Authored for NORMAL blend at alpha .95. | ☑ |
| `jet.svg` | 160×90 | Sky-blue twisted bow-tie wash; anchor right-centre (160,45), pointing left. | ☑ |
| `jet_bubble.svg` | 32×32 | Ring bubble for the jet trail. | ☑ |

---

## C. UI — `public/assets/svg/ui/`
| File | Size | Description | Status |
|---|---|---|---|
| `panel.svg` | 600×200 | Flat cream caption panel (`#f9e9d0`), even 3.5 px `#2e241c` outline, radius 24. 9-slices cleanly with 40 px margins. | ☑ |
| `badge.svg` | 96×96 | Flat `#0d1424` numbered-caption disc (the game prints the numeral). | ☑ |
| `key_e.svg` | 96×96 | Cartoon cream keycap with a hand-drawn "E". | ☑ |
| `key_space.svg` | 220×96 | Wide cartoon keycap, empty face (the game prints "Boşluk"). | ☑ |
| `icon_objective.svg` | 96×96 | Magnifying glass over a red cell, objective marker. | ☑ |
| `icon_progress.svg` | 64×36 | Small submarine for the progress track. | ☑ |

---

## D. Later stages (planned, not authored yet)

| File (planned) | Stage | Description |
|---|---|---|
| `characters/rbc_1..3` (layered: body, eyes, arms, legs, oxygen bubble) | 3 | Three red blood cell variations: backpack carrier, two-hand carrier, cheerful walker. |
| `characters/commander_*` | 4 | Larger cell, white captain cap, black visor, gold emblem; pointing & hand-on-hip poses. |
| `characters/vitamin_c_*`, `vitamin_b_*` | 3 | Orange "C" and green "B" walkers. |
| `characters/wbc_*` | 3 | Fluffy white cell (one with a simple guard helmet, no weapons). |
| `characters/platelet_*` | 5 | Golden repair worker, yellow hard hat, tool belt. |
| `environment/blockage_*` | 5 | Yellow-orange lumpy plaque (layered so it can shrink/clear), narrowing vessel walls. |
| `scenes/hospital_*` | 6 | Hospital room background, bed + patient (sick / recovered), monitors, scientist. |
| `scenes/syringe_*` | 6 | Syringe cinematic background and needle. |
