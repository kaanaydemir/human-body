import Phaser from 'phaser';
import { FOREGROUND_PIECES, SEGMENT_VARIANTS } from '../assets';
import {
  CEILING_BAND,
  DEPTH,
  FLOOR_BAND,
  GAME_HEIGHT,
  GAME_WIDTH,
  PARALLAX,
  SEGMENT_WIDTH,
  WORLD_WIDTH,
} from '../config';

type Variants = readonly string[];

/** Katman başına parça kayması (px). Değerler eklerin birbirine kilitlenmemesi için seçildi. */
const PHASE = { far: 300, rear: 700, ceiling: 1440, floor: 480 } as const;

/**
 * Kan damarının paralaks katmanlarını kurar (ART_DIRECTION.md §4):
 * uzak tünel → arka duvar halkaları → (hücre trafiği, BloodFlow'da) → ana tavan/zemin → ön plan dokusu.
 * Döşenen parçalar kenar sözleşmesine uyduğu için herhangi bir sırada yan yana dizilebilir.
 */
export class Vessel {
  private readonly far: Phaser.GameObjects.Image[] = [];
  private readonly rear: Phaser.GameObjects.Image[] = [];
  private readonly ceiling: Phaser.GameObjects.Image[] = [];
  private readonly floor: Phaser.GameObjects.Image[] = [];
  private readonly rng: Phaser.Math.RandomDataGenerator;

  constructor(private readonly scene: Phaser.Scene) {
    this.rng = new Phaser.Math.RandomDataGenerator(['damar-1']);

    // Her katmanın ekleri farklı x'e düşsün diye katmanlar farklı kaymayla başlar: böylece
    // tavan ve zemin ekleri üst üste binmez ve oyuncunun ilk karesinde hiçbir kenar payı görünmez.
    this.tile(this.far, SEGMENT_VARIANTS.far, PARALLAX.far, DEPTH.far, PHASE.far, (img) =>
      img.setOrigin(0, 0.5).setY(GAME_HEIGHT / 2),
    );
    this.tile(this.rear, SEGMENT_VARIANTS.rear, PARALLAX.rear, DEPTH.rear, PHASE.rear, (img) =>
      img.setOrigin(0, 0.5).setY(GAME_HEIGHT / 2),
    );
    this.tile(this.ceiling, SEGMENT_VARIANTS.ceiling, PARALLAX.main, DEPTH.ceiling, PHASE.ceiling, (img) =>
      img.setOrigin(0, 0).setY(CEILING_BAND.y),
    );
    // Zemin alttan sabitlenir ki nabızda yukarı/aşağı esnesin ama ekranın altından kopmasın.
    this.tile(this.floor, SEGMENT_VARIANTS.floor, PARALLAX.main, DEPTH.floor, PHASE.floor, (img) =>
      img.setOrigin(0, 1).setY(FLOOR_BAND.y + FLOOR_BAND.height),
    );

    this.scatterForeground();
  }

  /**
   * Kalp atışıyla damar duvarı hafifçe genişler: tavan yukarı, zemin aşağı çekilir.
   * Yalnızca dikey ölçek değişir, böylece yan yana parçaların ekleri hiç açılmaz.
   */
  pulse(p: number): void {
    const ceilingScale = 1 - 0.04 * p;
    const floorScale = 1 - 0.035 * p;
    const rearScale = 1 + 0.014 * p;
    const farScale = 1 + 0.006 * p;
    for (const img of this.ceiling) img.scaleY = ceilingScale;
    for (const img of this.floor) img.scaleY = floorScale;
    for (const img of this.rear) img.scaleY = rearScale;
    for (const img of this.far) img.scaleY = farScale;
  }

  /** Bir katmanı, kamera dünyanın sonuna gidene kadar ekranı dolduracak sayıda parçayla döşer. */
  private tile(
    into: Phaser.GameObjects.Image[],
    variants: Variants,
    scrollFactor: number,
    depth: number,
    phase: number,
    place: (img: Phaser.GameObjects.Image) => void,
  ): void {
    const span = GAME_WIDTH + scrollFactor * (WORLD_WIDTH - GAME_WIDTH);
    const count = Math.ceil((span + phase) / SEGMENT_WIDTH) + 1;
    let prev = '';
    for (let i = 0; i < count; i++) {
      const key = this.pickVariant(variants, prev);
      prev = key;
      const img = this.scene.add.image(i * SEGMENT_WIDTH - phase, 0, key);
      place(img);
      img.setScrollFactor(scrollFactor, 1).setDepth(depth);
      into.push(img);
    }
  }

  private pickVariant(variants: Variants, prev: string): string {
    if (variants.length === 1) return variants[0];
    let key = prev;
    while (key === prev) key = this.rng.pick(variants as string[]);
    return key;
  }

  /** Ön plan doku parçalarını aralıklarla, ekranın altından ve üstünden taşacak şekilde yerleştirir. */
  private scatterForeground(): void {
    const f = PARALLAX.foreground;
    const span = GAME_WIDTH + f * (WORLD_WIDTH - GAME_WIDTH);

    // Başlangıçta denizaltının önü açık kalsın diye ilk parçalar ekranın dışından başlar.
    let x = 1500;
    let prev = '';
    while (x < span + 400) {
      const key = this.pickVariant(FOREGROUND_PIECES.bottom, prev);
      prev = key;
      const s = this.rng.realInRange(0.92, 1.12);
      this.scene.add
        .image(x, GAME_HEIGHT + this.rng.between(10, 40), key)
        .setOrigin(0.5, 1)
        .setScale(s)
        .setScrollFactor(f, 1)
        .setDepth(DEPTH.foreground);
      x += this.rng.between(1100, 1900);
    }

    x = 2300;
    prev = '';
    while (x < span + 400) {
      const key = this.pickVariant(FOREGROUND_PIECES.top, prev);
      prev = key;
      const s = this.rng.realInRange(0.9, 1.08);
      this.scene.add
        .image(x, -this.rng.between(6, 30), key)
        .setOrigin(0.5, 0)
        .setScale(s)
        .setScrollFactor(f, 1)
        .setDepth(DEPTH.foreground);
      // Üstten sarkan ön plan kıvrımları seyrek olsun: oyun alanının üstünü sık sık kapatmasın.
      x += this.rng.between(2700, 3400);
    }
  }
}
