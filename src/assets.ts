// Yüklenecek tüm SVG varlıklarının listesi. Boyutlar ASSET_MANIFEST.md ile birebir aynıdır:
// Phaser her SVG'yi bu boyutta rasterize eder.

export interface SvgAsset {
  key: string;
  url: string;
  width: number;
  height: number;
}

const env = (name: string, width: number, height: number): SvgAsset => ({
  key: name,
  url: `assets/svg/environment/${name}.svg`,
  width,
  height,
});
const player = (name: string, width: number, height: number): SvgAsset => ({
  key: name,
  url: `assets/svg/player/${name}.svg`,
  width,
  height,
});
const fx = (name: string, width: number, height: number): SvgAsset => ({
  key: name,
  url: `assets/svg/fx/${name}.svg`,
  width,
  height,
});
const ui = (name: string, width: number, height: number): SvgAsset => ({
  key: name,
  url: `assets/svg/ui/${name}.svg`,
  width,
  height,
});

/** Döşenen katman parçaları: anahtar önekine göre varyantlar. */
export const SEGMENT_VARIANTS = {
  far: ['far_a', 'far_b'],
  rear: ['rear_a', 'rear_b'],
  ceiling: ['ceiling_a', 'ceiling_b', 'ceiling_c'],
  floor: ['floor_a', 'floor_b', 'floor_c'],
} as const;

export const FOREGROUND_PIECES = {
  bottom: ['fg_bottom_1', 'fg_bottom_2', 'fg_bottom_3'],
  top: ['fg_top_1', 'fg_top_2'],
} as const;

export const BLOODSTREAM_ASSETS: SvgAsset[] = [
  ...SEGMENT_VARIANTS.far.map((k) => env(k, 1920, 1080)),
  ...SEGMENT_VARIANTS.rear.map((k) => env(k, 1920, 1080)),
  ...SEGMENT_VARIANTS.ceiling.map((k) => env(k, 1920, 340)),
  ...SEGMENT_VARIANTS.floor.map((k) => env(k, 1920, 360)),
  env('fg_bottom_1', 640, 300),
  env('fg_bottom_2', 820, 320),
  env('fg_bottom_3', 560, 280),
  env('fg_top_1', 760, 240),
  env('fg_top_2', 620, 220),
  env('disc_cell_far', 140, 140),
  env('disc_cell_blur', 220, 220),
  env('vignette', 1920, 1080),
  env('glow', 1200, 800),
  fx('particle', 24, 24),
  fx('streak', 220, 24),
  player('sub_back', 520, 300),
  player('explorer', 520, 300),
  player('explorer_blink', 520, 300),
  player('explorer_curious', 520, 300),
  player('sub_front', 520, 300),
  player('sub_light', 640, 320),
  player('jet', 160, 90),
  player('jet_bubble', 32, 32),
  ui('panel', 600, 200),
  ui('badge', 96, 96),
  ui('key_e', 96, 96),
  ui('key_space', 220, 96),
  ui('icon_objective', 96, 96),
  ui('icon_progress', 64, 36),
];
