# Art Direction — "Vücut Macerası" (Human Body Adventure)

`reference.png` (the 12-panel comic strip in the repo root) is the single source of truth.
Every asset is judged against it. When this document and the reference disagree, the reference wins.

The goal is not "a medical game". The goal is that the player feels they have stepped
*inside the illustrated cartoon world of the reference*: a warm, hand-drawn, classic European
educational TV cartoon about the body.

---

## 1. What the reference actually looks like (observed, not assumed)

Studied panel by panel (panel numbers refer to `reference.png`):

| Panel | What it teaches us |
|---|---|
| 1, 12 | Hospital room: cool blue-grey walls, monitors with green traces, IV bag, patient in bed under a blue blanket, scientist with a huge white fluffy beard/hair. Indoor light is soft and cool. |
| 2 | **The submarine**: cream-white rounded hull, big transparent dome cockpit (blue-tinted glass, white specular streaks), red rounded nose cap on the right, red rounded tail fin on the upper-left, small round red porthole/light dots, a thin dark slot on the side, a small antenna/light bump on top of the dome. The explorer holds a round steering wheel. |
| 3 | Syringe injection: metallic syringe needle entering a red vessel; inset of the sub inside the bloodstream. |
| 4, 5 | **The vessel** (most important): a wide, enclosed, *ribbed* tunnel. The walls are made of concentric ring folds that recede into darkness — openings narrow towards deep maroon centres. The floor is a field of soft, rounded, fleshy mounds. Light is warm and comes from the viewer side; ring edges catch a pale pink rim light. Many anthropomorphic red blood cells walk on the floor carrying transparent blue oxygen bubbles. |
| 5, 8 | **Commander**: a bigger red blood cell with a white captain's cap, black visor, gold emblem; pointing gesture, one hand on hip. |
| 6 | Vitamin C (orange-yellow, white "C" on chest), Vitamin B (green, white "B"), blue-ish immune cells, a white blood cell with a builder helmet + shield, a white spiky/fluffy cell. Big pink-red blobby cells in the background. |
| 7 | **Blockage**: yellow-orange lumpy, cauliflower-like plaque piled on the right side of a narrowing vessel; red cells queue in front of it. The headlight of the sub throws a warm yellow beam. Floating loose discs (plain biconcave red cells) drift in the lumen. |
| 8 | **Platelets**: small golden-yellow workers with yellow hard hats and tools/boxes. |
| 9 | Restored flow: dense crowd of happy cells, the sub cruising. |
| 10 | Heart: interlaced pink muscle tubes. |
| 11 | Brain control room: purple neuron characters, blue screens. |

### Rendering characteristics
- **Line art**: clean but organic dark outlines. Lines are not mechanical: slight thickness variation,
  thicker on the shadow side and at the bottom of shapes, thinner (or broken) on lit edges.
  - Characters: outline `#5a1a1c` (on red cells) / `#3b2a22` (on cream/white/yellow objects), ~5–6 px at 1920×1080.
  - Environment: outline is *darker red*, never black: `#6e1a24`, 2–4 px, often only on the lower/shadow side of a fold.
- **Fills**: flat colour with **one cel shadow tone** and **one soft highlight**. No noisy gradients.
  Gradients are allowed only for large-scale atmosphere (depth falloff in the tunnel, glass, light beams).
- **Texture**: subtle hand-painted grain over environment surfaces (very low contrast), plus a few
  painterly hatch strokes/pores on fleshy surfaces. Never photographic.
- **Shapes**: everything is rounded and soft. Folds are fat crescents and blobs. No straight lines in the anatomy.
- **Light**: warm, from the front/upper-left. Deep areas fall off to maroon, never to pure black.
  Rim light on fold edges is pale pink-peach.
- **Atmosphere**: slight warm haze in the distance (lower contrast, slightly lighter-pinker), which is what
  sells depth in panels 4–5.

---

## 2. Palette (sampled from `reference.png`)

### Vessel
| Role | Hex | Notes |
|---|---|---|
| Wall base (lit) | `#ce3a3e` | ring folds, floor mounds |
| Wall mid | `#b72931` | |
| Wall shadow | `#93201e` | under folds |
| Deep shadow | `#771d26` | inside creases |
| Tunnel depth | `#641a28` → `#4a1220` | vanishing openings (never pure black) |
| Floor lit | `#e13a33` / `#d83635` | foreground mounds are more saturated |
| Fold rim light | `#e7a99e` / `#d8635f` | thin crescent on lit edges |
| Haze (distance) | `#c86a6e` at low alpha | lifts far layers |
| Environment line | `#6e1a24` | |

### Characters / objects
| Role | Hex |
|---|---|
| Red blood cell body | `#f43a2e` (lit `#fb4d3c`, shade `#c4281f`, deep shade `#98231c`) |
| Cell outline | `#5a1a1c` |
| Eye white | `#fbf6f2`, pupil `#1d1416` |
| Oxygen bubble glass | `#bcd8f2` at ~55% alpha, rim `#7aa6d6`, highlight `#ffffff` |
| Sub hull | `#efddd0` (lit `#f7ebe0`, shade `#bda79c`) |
| Sub red parts | `#cf3a3a` (lit `#e0443c`, shade `#a32a2e`, white specular) |
| Dome glass | `#d2d8e4` tint at low alpha (≈.16 at the top), interior `#223973` → `#1c2450` → `#121838`, white streaks at .85–.92 |
| Headlight beam | `#ffe79e` at the lens → `#fbb85c` → `#fc805a` → `#eb594f` fading to transparent; drawn with NORMAL blend, never tinted |
| Explorer suit | `#f2a93b` (shade `#c97a22`) |
| Explorer hair | `#7a3e1d` (shade `#55260f`) |
| Explorer skin | `#f6c9a5` (shade `#dc9f7d`) |
| Vitamin C | `#f9aa3e` (lit `#fabf6b`) |
| Vitamin B | `#5f9a3a` (lit `#86b85a`) |
| White blood cell | `#efedf5` (shade `#c9c6da`) |
| Platelet | `#f2b63c` (shade `#c98a22`), helmet `#f7d23a` |
| Plaque / blockage | `#ec9536`, `#fabb59`, shade `#cb7928`, deep `#b24023` |
| Foreground lumps (bottom) | base `#c8262d`, shadow `#891a24`, highlight `#ea6a55`, streak `#f3b2a2`, ink `#5a1a1c` |
| Foreground folds (top) | base `#9e2029`, shadow `#6c1620`, highlight `#d0544a`, streak `#e8a092`, ink `#4c1219` |
| Far loose discs | body `#ac3e3c`, shade `#923035`, outline `#842f35` (haze is baked in, never tinted in code) |
| Captain cap | white `#f7f4ee`, visor `#1f1a1c`, emblem `#e2b33c` |

### UI
| Role | Hex |
|---|---|
| Panel fill | `#f9e9d0`, flat right up to the line (the reference captions have no inner bevel or shading) |
| Panel outline / text | `#2e241c`, even 3.5 px, corner radius 24 / text `#1b1714` |
| Number badge | flat `#0d1424` disc (measured from the reference badges), white bold numeral |
| Accent button | `#cf2c43` with cream text |
| Caption type | plain grotesk like the reference captions: **Arimo** (metric-compatible with Arial), regular, ~34 px. The rounded **Baloo 2** is only for short labels, titles and buttons |

---

## 3. Proportions (at 1920×1080 design resolution)

- Submarine on screen: ~440 × 255 px. Dome is ~45% of hull length. Nose cap faces **right**.
- Explorer head: ~70 px tall inside the dome. Big eyes (~1/4 of face height), rounded face, brown hair tuft.
- Red blood cell character: ~150–190 px tall incl. legs; body is a fat rounded disc/bean seen in 3/4,
  with a visible shallow dimple; arms and legs are thick rubber-hose limbs with white-less cartoon hands
  (red hands, 4 fingers). Eyes are tall ovals, close together, near the top of the body.
- Commander: ~1.3× a normal cell.
- Vitamins / platelets: ~0.8× a red cell. White blood cells ~1.1×.
- Vessel: lumen (free space) spans roughly y = 230 … 820 at 1920×1080. Ceiling and floor are
  always visible. The camera never shows anything outside the vessel.

---

## 4. The vessel in a side-scrolling camera

The reference shows the tunnel *in perspective* (rings receding to a vanishing opening).
A side-scroller cannot literally keep that perspective, so we fake it with parallax:

1. **Far tunnel interior** (scroll 0.12): opaque. Concentric ring folds converging to deep maroon
   openings (2 openings per segment, at different heights/sizes, like panel 4's background).
   Lower contrast + slight pink haze.
2. **Rear vessel wall** (scroll 0.35): transparent PNG. Large crescent-shaped *ring ribs* that arch from
   floor to ceiling (the near edges of the rings in panel 4/5), plus the receding inner ceiling and floor
   strips that connect them. The far tunnel shows *between* the ribs.
3. **Background cell traffic** (scroll 0.55): small, hazier cells and loose discs walking/drifting.
4. **Main gameplay plane** (scroll 1.0): the near ceiling (top band) and the near floor (bottom band of
   fleshy mounds). Full saturation, strongest outlines. The submarine and NPCs live here.
5. **Foreground tissue** (scroll 1.3): big out-of-focus-ish fleshy lumps poking in from the bottom and
   overhanging folds at the top, plus a few large drifting discs. Slightly darker and more saturated,
   so they frame the shot like the cropped cells at the edges of panel 4.

Plus screen-space overlays: a vignette that darkens **only the four corners** (top/bottom edge midpoints stay
almost untouched, so the near ceiling and floor are not dimmed as a block) and a soft warm key light (`#ff8a28`,
ADD at ~.12) placed off-axis at the upper left, never over the vanishing holes: the deepest point of the tunnel
must stay the darkest.

**The ceiling and floor must visually connect** through the rear-wall ribs: every rib starts in the
floor and ends in the ceiling.

**Never**: sky, clouds, mountains, trees, open-air scenery, empty void above or below.

---

## 5. Animation language

Gentle, cartoon, never twitchy. Ease in/out everywhere.
- Submarine: idle bob (±6 px, ~2.2 s), tilt into movement (±6°), slight squash on stop, bubbles from the
  rear jet, headlight beam softly flickers.
- Explorer: blink every 3–6 s, small head bob offset from the hull bob.
- Vessel: whole-wall "pulse" synced to a heartbeat (~1 s period, two-beat lub-dub), 1–1.5% scale on the
  wall layers; blood particles drift with the flow (left → right) and a gentle sine sway.
- Characters (later stages): walk cycles via layered limbs (body bob + leg swing + arm swing), oxygen
  bubble bob, blinking.

---

## 6. Absolutely avoid

Pixel art · 3D models · low-poly · photorealistic organs · neon / cyberpunk · heavy bloom ·
Unreal-style lighting · glossy plastic characters · emoji faces · plain circles as finished characters ·
placeholder rectangles · generic geometric tubes · random procedural backgrounds that don't match the
reference · copying the copyrighted characters of the original TV series (designs here are original;
we keep only the broad qualities: rounded anthropomorphic cells, expressive faces, playful medical
storytelling, traditional cartoon rendering).

---

## 7. Shared SVG authoring rules (every asset author must follow)

- Hand-authored SVG with custom `path` geometry (cubic Béziers). Circles/ellipses are fine as *parts*
  (eyes, bubbles), never as a whole finished character or fold.
- Root element: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H" width="W" height="H">` with the
  exact size from `ASSET_MANIFEST.md`.
- Self-contained: no external fonts, images or CSS. Text in SVG must be converted to paths or avoided
  (UI labels are rendered by the game, not baked in), except single big glyph-like letters drawn as paths.
- Shared environment texture filters (use **exactly** these definitions when an asset needs grain, so all
  layers share the same grain and tiles stitch seamlessly). `mottle` below is the warm v2 matrix used by the far and
  floor layers; the original pink matrix (`0.98 / 0.55 / 0.55`, alpha `0.16`) desaturates and lightens the reds by
  ~8%, so wherever it is still used (ceiling, rear) it sits under the painted colours or at ≤ 0.5 group opacity:

  ```xml
  <filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.94  0 0 0 0 0.36  0 0 0 0 0.30  0 0 0 0.08 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  ```
  Apply as an overlay: draw the shape once normally, then again with `filter="url(#grain)"` / `url(#mottle)`.
  For tileable segments the filter region must be the whole canvas (`x=0 y=0 width=W height=H`
  in user space) so `stitchTiles` makes the noise periodic with the segment width.
- Render-check every asset with `node tools/render-svg.mjs <svg> <png> [scale] [bg]` and look at it
  next to the matching crop of `reference.png` before calling it done. Then check it **in the game**
  (`node tools/screenshot.mjs …`): the composite is what counts.
- Inks and cel tones are **opaque**. Translucent line work and airbrushed blur volumes read as "vector clip art",
  not as a painted cartoon; blur is reserved for out-of-focus foreground discs and light.
- Every asset is produced by a generator script under `tools/art/<group>/` (see each README). Change the generator,
  re-run it, and commit both; never hand-edit the emitted SVG.

## 8. Lessons from the Stage 2 visual QA

- **Measure only after the camera fade has finished.** The first brightness measurements were taken mid fade-in
  and overstated the gap to the reference by ~20 percentage points.
- Forms the reviewers rejected and why: floor mounds that read as stacked cushions (fixed with long, low,
  overlapping dunes), a ceiling that read as a theatre pelmet (fixed with long overhanging folds and vault arcs),
  rear ribs that read as vertical posts (fixed with full ring arches whose legs lean and bow), far rings that read
  as tree rings / targets (fixed with fewer, wider folds and a floor running into the hole).
- Tile seams must carry structure, not a bald margin: every tiling layer now draws an identical *seam motif*
  straddling the border, and the game offsets each layer's tiling phase so seams never line up across layers.
