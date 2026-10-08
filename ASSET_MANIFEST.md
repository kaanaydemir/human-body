# Asset Manifest

All authored art lives in `public/assets/svg/**` as hand-made SVG. Phaser rasterises SVGs at load time
(`this.load.svg(key, url, { width, height })`) at the size listed here, so **viewBox = width/height = the
size below**. Status: ☐ planned · ◐ in progress · ☑ done (passed the visual checkpoint).

Coordinates are at the 1920×1080 design resolution. The camera only scrolls horizontally; world height = 1080.

---

## A. Blood vessel environment (Stage 2) — `public/assets/svg/environment/`

### Tiling contract (all repeating segments)
Segments are placed edge to edge in any order (`a b a c b …`), so **every variant of a layer must share
identical left and right edges**:
- Within 48 px of the left/right border, draw only the layer's *base* (its exact shared gradient + the shared
  `grain`/`mottle` filters from `ART_DIRECTION.md` §7, whose region is the full canvas). No features may cross
  or touch these margins unless stated below.
- Any silhouette contour (ceiling bottom edge, floor top edge, receding strips) must hit the border at
  exactly the contract Y and be **flat (horizontal tangent) for the first/last 48 px**.
- Gradients that are part of the base must be vertical-only (`x1=x2`) and use the exact stops listed.

| File | Size | Layer / scroll | Contract | Status |
|---|---|---|---|---|
| `far_a.svg`, `far_b.svg` | 1920×1080, opaque | 1 · far tunnel · 0.12 | Base: vertical gradient `#7a2530` (0) → `#8e2f38` (0.5) → `#6a1d29` (1). Each variant has 2 receding ring-fold openings (concentric fat crescents converging to a maroon `#4a1220`–`#641a28` hole), different sizes/heights, warm pink haze, low contrast. | ◐ |
| `rear_a.svg`, `rear_b.svg` | 1920×1080, transparent | 2 · rear wall · 0.35 | Top strip: opaque from y=0 down to a soft contour that is at **y=300** on both borders. Bottom strip: opaque from a contour at **y=720** on both borders down to 1080. Base fill of strips: vertical gradient `#a22b33` → `#8a2330`. Between strips: 2–3 big crescent **ring ribs** per segment rising from the bottom strip and curving into the top strip (no rib within 48 px of the borders). Transparent elsewhere so the far tunnel shows through. | ◐ |
| `ceiling_a.svg`, `ceiling_b.svg`, `ceiling_c.svg` | 1920×340, transparent below contour | 4 · main plane · 1.0 (placed at y=0) | Opaque from top; lower contour at **y=210** on both borders. Contour wanders between ~150 and ~260 with soft overhanging folds. Base gradient `#8f2430` (0) → `#b9343a` (1). | ◐ |
| `floor_a.svg`, `floor_b.svg`, `floor_c.svg` | 1920×360, transparent above contour | 4 · main plane · 1.0 (placed at y=720) | Opaque to bottom; upper contour at **y=120** (global 840) on both borders, flat near borders. Contour = rounded fleshy mounds between ~60 and ~170. Base gradient `#d83635` (0) → `#9b2023` (1). | ◐ |
| `fg_bottom_1..3.svg` | 640×300 / 820×320 / 560×280 | 5 · foreground · 1.3 | Big rounded fleshy lumps; bottom edge fully opaque and flat (sits on the screen bottom). Darker/more saturated than the floor. | ◐ |
| `fg_top_1..2.svg` | 760×240 / 620×220 | 5 · foreground · 1.3 | Overhanging folds; top edge fully opaque and flat (hangs from the screen top). | ◐ |
| `disc_cell.svg` | 140×140 | 3 & 5 | A plain (non-character) biconcave red blood cell disc seen in 3/4 view, like the loose discs in panel 7. | ◐ |
| `disc_cell_blur.svg` | 220×220 | 5 | Same disc, softly out of focus (feGaussianBlur), for foreground drift. | ◐ |
| `vignette.svg` | 1920×1080 | overlay · 0 | Transparent centre, warm maroon `#3a0c14` edges (stronger top/bottom corners). | ◐ |
| `glow.svg` | 1200×800 | overlay · 0 (ADD blend) | Soft warm radial light `#ffb38a` → transparent. | ◐ |

### FX — `public/assets/svg/fx/`
| File | Size | Use | Status |
|---|---|---|---|
| `particle.svg` | 24×24 | small pinkish blood speck (plasma particle) | ◐ |
| `bubble.svg` | 40×40 | oxygen / jet bubble: pale blue glass circle with highlight | ◐ |
| `streak.svg` | 220×24 | soft horizontal flow streak (pale pink, feathered ends) | ◐ |

---

## B. Player — `public/assets/svg/player/`

All submarine parts share one coordinate frame: **viewBox 0 0 520 300**, the sub faces **right**, the
container origin is the frame centre (260,150). Parts are stacked back → front:
`sub_back` → `explorer*` → `sub_front`. Fixed anchors (the code relies on them):
- **Headlight anchor** (centre of the headlight lens on the nose): **(498, 178)**
- **Jet anchor** (centre of the rear nozzle opening): **(24, 168)**
- Explorer head centre ≈ (262, 112); the hull rim in front of his chest is at y ≈ 170.

| File | Size | Description | Status |
|---|---|---|---|
| `sub_back.svg` | 520×300 | Everything *behind* the explorer: dome interior back wall (deep blue `#223973`), seat back, dashboard back. | ◐ |
| `explorer.svg` | 520×300 | The explorer only (head, hair, yellow-orange suit, arms, gloved hands on a round steering wheel), smiling, eyes open, looking right. | ◐ |
| `explorer_blink.svg` | 520×300 | Identical pose, eyes closed (for blinking). | ◐ |
| `explorer_curious.svg` | 520×300 | Same pose, eyebrows up, small "o" mouth, eyes slightly wider (scan / interact). | ◐ |
| `sub_front.svg` | 520×300 | Hull, red tail fin, red nose cap, portholes/lights, side slot, rear nozzle, headlight housing, top antenna light, and the **transparent dome glass** (tint + white specular streaks) over the explorer. | ◐ |
| `sub_light.svg` | 640×320 | Headlight beam cone; origin at left-centre (0,160), opening to the right, warm pale yellow, feathered. | ◐ |
| `jet.svg` | 160×90 | Rear jet wash; anchor right-centre (160,45), pointing left: pale blue-white turbulent wash with a warm core. | ◐ |

---

## C. UI — `public/assets/svg/ui/`
| File | Size | Description | Status |
|---|---|---|---|
| `panel.svg` | 600×200 | Cream dialogue / caption panel (`#f9e9d0`, outline `#463d32` 5 px, radius 26, slight paper grain, inner lower edge tone). Must 9-slice cleanly with 40 px margins. | ◐ |
| `badge.svg` | 96×96 | Dark navy `#1f2433` numbered-caption circle (no numeral baked in; the game prints it). | ◐ |
| `key_e.svg` | 96×96 | Cartoon cream keycap with a hand-drawn "E" (as a path). Interaction icon. | ◐ |
| `key_space.svg` | 220×96 | Cartoon cream wide keycap, empty face (game prints "Boşluk"). | ◐ |
| `icon_objective.svg` | 96×96 | Small illustrated magnifying glass over a red cell — objective marker. | ◐ |

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
