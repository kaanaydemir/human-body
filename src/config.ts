// Oyunun tüm sabit ölçüleri tek yerde. Koordinatlar 1920×1080 tasarım çözünürlüğündedir.

export const GAME_WIDTH = 1920;
export const GAME_HEIGHT = 1080;

/** Yatay olarak döşenen ortam parçalarının genişliği. */
export const SEGMENT_WIDTH = 1920;

/** Damar sahnesinin dünya uzunluğu (kamera yalnızca yatay kayar). */
export const WORLD_SEGMENTS = 6;
export const WORLD_WIDTH = SEGMENT_WIDTH * WORLD_SEGMENTS;

/** Paralaks katmanlarının kaydırma katsayıları (ART_DIRECTION.md §4). */
export const PARALLAX = {
  far: 0.12,
  rear: 0.35,
  traffic: 0.55,
  main: 1,
  foreground: 1.3,
} as const;

/** Ana düzlemdeki tavan ve zemin bantlarının dünya içindeki konumu (ASSET_MANIFEST.md A). */
export const CEILING_BAND = { y: 0, height: 340, edgeY: 210 } as const;
export const FLOOR_BAND = { y: 720, height: 360, edgeY: 840 } as const;

/**
 * Denizaltının merkezinin dolaşabileceği dikey aralık. Tavan konturu en fazla ~260'a,
 * zemin konturu en az ~780'e iner; denizaltının görünür yarı yüksekliği ~85 px.
 */
export const LUMEN = { top: 360, bottom: 690 } as const;

/** Görüntü katmanlarının çizim sırası. */
export const DEPTH = {
  far: 0,
  rear: 10,
  traffic: 20,
  ceiling: 30,
  floor: 31,
  player: 50,
  playerFx: 49,
  foreground: 80,
  glow: 85,
  vignette: 90,
} as const;

export const FONT_FAMILY = '"Baloo 2", "Trebuchet MS", sans-serif';

export const COLORS = {
  panelFill: 0xf9e9d0,
  panelEdge: 0x463d32,
  text: '#2b241d',
  textSoft: '#5a4c3d',
  badge: 0x1f2433,
  accent: 0xcf2c43,
  maroon: 0x3a0c14,
} as const;
