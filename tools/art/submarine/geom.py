"""Shared submarine geometry and palette (frame 520x300, the sub faces right).

Fixed anchors (ASSET_MANIFEST.md B, the game code relies on them):
  headlight (498, 178) - a soft glow spot on the upper front of the red nose ball
  jet       (24, 168)  - the opening at the tip of the white tail stub
Explorer head centre stays at about (262, 112); the cockpit rim in front of his chest is at y ~ 170-176.

Shape language (reference.png panels 2 and 4): a swollen glossy teardrop. One convex belly curve runs from the
tail band to the big red nose ball; a long, low glass canopy; a white hood behind it with a red ball fin peeking
out; a red ring band and a short white rounded stub at the tail.
"""

OUT = '#3b2a22'
HULL = '#efddd0'
HULL_LIT = '#f7ebe0'
HULL_SH = '#bda79c'
# red parts, sampled from the vessel panels (p4/p6/p9: #da403c / #d14438), not from the cool hospital light of p2
RED = '#cf3a3a'
RED_LIT = '#e0443c'
RED_SH = '#a32a2e'
RED_DEEP = '#86222a'

HEADLIGHT = (498, 178)
JET = (24, 168)

# ---- canopy ------------------------------------------------------------
J_TOP = (194, 34)          # top of the glass rear edge (meets the hood)
J_BOT = (166, 166)         # bottom of the glass rear edge
F = (456, 154)             # front bottom of the glass, where the deck starts sloping into the nose
# hood back: from the hood's rear foot (84,148) up to J_TOP
S1 = 'C90 112 124 66 166 46 C176 41 185 37 194 34'
# glass top and the long, low front slope down to F
S2 = 'C228 26 264 23 300 25 C358 28 408 46 434 82 C447 102 455 128 456 154'
# rim, front -> back (sags a little under the explorer)
R = 'C396 180 240 180 166 166'
B = 'C156 122 164 66 194 34'          # glass rear edge, bottom -> top
B_REV = 'C164 66 156 122 166 166'
DECK_BACK = 'C136 156 104 148 84 148'  # J_BOT -> hood foot

GLASS = 'M194 34 ' + S2 + ' ' + R + ' ' + B + ' Z'
HOOD = 'M84 148 ' + S1 + ' ' + B_REV + ' ' + DECK_BACK + ' Z'
DOME = 'M84 148 ' + S1 + ' ' + S2 + ' ' + R + ' ' + DECK_BACK + ' Z'

# ---- hull: teardrop ------------------------------------------------------
# rear cap -> top line (hidden under hood/glass) -> deck sloping ~20 px into the nose -> nose (hidden under the
# ball) -> ONE convex belly cubic back to the tail -> rear cap
HULL_D = ('M60 148 C92 136 136 140 168 152 '
          'C250 168 380 168 456 154 '
          'C468 153 480 160 488 172 '
          'C500 194 486 236 446 252 '
          'C404 282 186 284 58 216 '
          'C40 202 38 162 60 148 Z')

# ring band around the tail (crescent seen in 3/4), 20-24 px wide
BAND = ('M72 134 C58 156 56 204 72 236 L96 244 C84 210 84 156 96 128 Z')  # clipped to the hull

# white rounded stub behind the band; the jet comes out of its tip
STUB = 'M62 154 C46 152 30 153 21 157 C14 161 14 176 21 180 C30 184 46 185 62 184 Z'

# red ball fin peeking out from behind the hood (upper left)
FIN_PTS = [(134, 150, 1), (126, 130), (124, 104), (118, 78), (100, 64), (79, 68), (69, 88), (71, 110), (83, 127),
           (100, 140), (114, 154, 1)]

# glossy red nose ball, ~96 px tall, bulging past the hull outline
NOSE_C = (467, 206)
NOSE_R = (47, 45)
NOSE_ROT = 8
