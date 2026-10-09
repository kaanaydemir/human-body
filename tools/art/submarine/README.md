# Submarine generator (`public/assets/svg/player/*.svg`)

This generates the player submarine: the hull and dome, the explorer (three faces), the headlight beam, the jet
wash and the jet's ring bubble. All parts share the 520×300 frame from ASSET_MANIFEST.md B. The sub faces right.

## Run

From the repo root (stdlib only):

```sh
python3 -I tools/art/submarine/gen_submarine.py              # writes all 8 SVGs into public/assets/svg/player/
python3 -I tools/art/submarine/gen_submarine.py --out DIR    # same files, somewhere else
```

The output is deterministic: the RNGs are seeded and there is no clock. A re-run reproduces the committed SVGs
byte for byte.

## Generator files

| File | What it does |
|---|---|
| `gen_submarine.py` | Entry point. Calls the three writers below. |
| `geom.py` | Palette and shared geometry: teardrop hull, canopy (hood, glass, rim), ring band, tail stub, ball fin, nose ball, and the fixed anchors. These are headlight (498,178) and jet (24,168). |
| `gen_sub.py` | `sub_front.svg` and `sub_back.svg`. `sub_front.svg` holds the stub, fin, hull, band, seam, slot, two red dots, hood, glass tint and streaks, rim, beacon and nose ball. The headlight is a soft glow spot centred on (498,178). `sub_back.svg` is the cockpit interior. Its upper third is see-through lavender, so the vessel shows through the glass. |
| `gen_explorer.py` | `explorer.svg`, `explorer_blink.svg`, `explorer_curious.svg`. Only the face differs between them. The nose is part of the face silhouette and is inked on its underside only. The hair is rounded clumps plus one curled tuft. The hands are bare. |
| `gen_fx.py` | `sub_light.svg`: the beam, authored for NORMAL blend. `jet.svg`: a twisted blue bow-tie ribbon. `jet_bubble.svg`: a 32×32 ring bubble for the jet particles. |
| `ink.py`, `svgkit.py` | Brush-outline helpers (thick–thin ribbons, tapered strokes) and small SVG utilities. |

## Verification tools

These are optional. They need Pillow, node and playwright.

| File | What it does |
|---|---|
| `probe_sub.mjs` | Opens the live game headless, drives keys and takes a screenshot. `--mode current` is src/ as it is. `--mode recommended` applies the runtime settings this art is authored for, at runtime only (see below). |
| `measure.py` | HSV of the dome, hull and red parts in a screenshot, given the sub's screen position. The probe prints that position. |
| `beam_check.py` | Beam colour along the axis, and 80 px off-axis at mid-beam. |
| `context.py` | Pastes the layered sub, jet, bubbles and beam onto a reference panel for a side-by-side check. |

## Runtime settings the art expects (src/objects/Submarine.ts, owned by the lead)

- **Headlight:** `sub_light` with NORMAL blend, no tint, alpha 0.95 (keep the flicker). Today the code uses ADD with tint 0xffa848 at alpha 0.8. That still works, but the beam then reads orange from the lens instead of pale yellow.
- **Jet:** alpha 0.5 + 0.45·thrust, so the jet is at 0.95 when thrusting.
- **Jet bubbles:** use the `jet_bubble` texture (register `player('jet_bubble', 32, 32)`). Settings:
  - lifespan 1200–2000 ms, speedX −150…−50, speedY −60…60
  - scale 0.5–0.875 (16–28 px), alpha 1→0 with Quad.easeIn
  - Keep the emitter at (0,0) and move `particleX`/`particleY` to the jet anchor each frame. Do not call `setPosition`, or the bubbles move with the sub instead of trailing behind it.
