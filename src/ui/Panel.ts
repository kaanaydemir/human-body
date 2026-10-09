import Phaser from 'phaser';
import { CAPTION_FONT, COLORS, FONT_FAMILY } from '../config';

/** Referanstaki krem rengi altyazı kutuları gibi 9 dilimli panel (40 px kenar payı). */
export function createPanel(
  scene: Phaser.Scene,
  x: number,
  y: number,
  width: number,
  height: number,
): Phaser.GameObjects.NineSlice {
  return scene.add.nineslice(x, y, 'panel', undefined, width, height, 40, 40, 40, 40);
}

export function textStyle(
  size: number,
  weight: '500' | '700' | '800' = '700',
  color: string = COLORS.text,
): Phaser.Types.GameObjects.Text.TextStyle {
  return {
    fontFamily: FONT_FAMILY,
    fontSize: `${size}px`,
    fontStyle: weight,
    color,
  };
}

/** Altyazı ve görev metinleri: referanstaki gibi sade grotesk, normal kalınlık, koyu renk. */
export function captionStyle(
  size: number,
  weight: '400' | '700' = '400',
  color: string = COLORS.text,
): Phaser.Types.GameObjects.Text.TextStyle {
  return {
    fontFamily: CAPTION_FONT,
    fontSize: `${size}px`,
    fontStyle: weight,
    color,
  };
}

/** Numaralı altyazı rozeti: lacivert daire + ortasında rakam. */
export function createBadge(
  scene: Phaser.Scene,
  x: number,
  y: number,
  label: string,
  size = 64,
): Phaser.GameObjects.Container {
  const img = scene.add.image(0, 0, 'badge').setDisplaySize(size, size);
  const txt = scene.add
    .text(0, 1, label, captionStyle(Math.round(size * 0.58), '700', '#ffffff'))
    .setOrigin(0.5);
  return scene.add.container(x, y, [img, txt]);
}
