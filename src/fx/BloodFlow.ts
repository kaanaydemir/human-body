import Phaser from 'phaser';
import { DEPTH, GAME_WIDTH, PARALLAX } from '../config';

/** Akışla sürüklenen tek bir öğe (plazma zerresi, akış çizgisi ya da serbest kan diski). */
interface Drifter {
  sprite: Phaser.GameObjects.Image;
  /** Kaydırma katsayısı = derinlik. Küçük değer uzak demek. */
  f: number;
  /** Akışa eklenen kendi hızı (px/sn). */
  ownSpeed: number;
  baseY: number;
  swayAmp: number;
  swayFreq: number;
  phase: number;
  /** Diskler için yavaş takla (3B dönüş taklidi) hızı. */
  tumble: number;
  baseScale: number;
}

const MARGIN = 260;

/**
 * Kan akışını canlandırır: soldan sağa sürüklenen plazma zerreleri, yumuşak akış çizgileri,
 * uzakta ve önde süzülen serbest kan diskleri. Her öğe kendi derinliğinde (scrollFactor)
 * durur; ekrandan çıkınca diğer kenardan geri girer, böylece yoğunluk her yerde aynı kalır.
 */
export class BloodFlow {
  private readonly drifters: Drifter[] = [];
  private readonly rng = new Phaser.Math.RandomDataGenerator(['akis-1']);
  private time = 0;

  constructor(private readonly scene: Phaser.Scene) {
    // Uzak serbest diskler: arka trafik katmanında, puslu.
    for (let i = 0; i < 9; i++) {
      const f = this.rng.realInRange(PARALLAX.traffic - 0.08, PARALLAX.traffic + 0.05);
      const scale = this.rng.realInRange(0.32, 0.5);
      this.add('disc_cell', f, DEPTH.traffic, {
        y: this.rng.between(330, 740),
        scale,
        alpha: 0.78,
        tint: 0xf0a7a0,
        ownSpeed: this.rng.realInRange(-10, 25),
        swayAmp: this.rng.realInRange(8, 22),
        tumble: this.rng.realInRange(0.25, 0.6),
      });
    }

    // Plazma zerreleri: çoğu ana düzlemin hemen önünde ve arkasında.
    for (let i = 0; i < 80; i++) {
      const f = this.rng.realInRange(0.4, 1.25);
      const near = f > 0.8;
      this.add('particle', f, near ? DEPTH.player + 2 : DEPTH.traffic + 1, {
        y: this.rng.between(250, 830),
        scale: Phaser.Math.Linear(0.45, 1.15, (f - 0.4) / 0.85),
        alpha: Phaser.Math.Linear(0.35, 0.85, (f - 0.4) / 0.85),
        ownSpeed: this.rng.realInRange(0, 40),
        swayAmp: this.rng.realInRange(4, 16),
        tumble: 0,
      });
    }

    // Akış çizgileri: hızın okunabilmesi için çok hafif.
    for (let i = 0; i < 14; i++) {
      const f = this.rng.realInRange(0.5, 1.0);
      this.add('streak', f, DEPTH.traffic + 2, {
        y: this.rng.between(300, 780),
        scale: this.rng.realInRange(0.7, 1.4),
        alpha: this.rng.realInRange(0.12, 0.26),
        ownSpeed: this.rng.realInRange(30, 70),
        swayAmp: this.rng.realInRange(2, 6),
        tumble: 0,
      });
    }

    // Ön planda kameraya çok yakın, odak dışı diskler: üst ve alt kenara yakın, görüşü kapatmaz.
    for (let i = 0; i < 4; i++) {
      const f = this.rng.realInRange(PARALLAX.foreground, PARALLAX.foreground + 0.25);
      const top = i % 2 === 0;
      this.add('disc_cell_blur', f, DEPTH.foreground + 1, {
        y: top ? this.rng.between(90, 210) : this.rng.between(900, 1010),
        scale: this.rng.realInRange(0.95, 1.4),
        alpha: 0.92,
        ownSpeed: this.rng.realInRange(10, 40),
        swayAmp: this.rng.realInRange(10, 24),
        tumble: this.rng.realInRange(0.15, 0.35),
      });
    }
  }

  /**
   * @param dt saniye
   * @param surge 0…1 kalp atışından sonra sönen akış dalgası
   */
  update(dt: number, surge: number): void {
    this.time += dt;
    const cam = this.scene.cameras.main;
    const flow = 46 + 110 * surge;
    const wrapWidth = GAME_WIDTH + MARGIN * 2;

    for (const d of this.drifters) {
      const s = d.sprite;
      s.x += (flow * d.f + d.ownSpeed) * dt;
      s.y = d.baseY + Math.sin(this.time * d.swayFreq + d.phase) * d.swayAmp;

      // Ekran dışına çıkan öğeyi karşı kenara sar (kamera sıçrasa bile tek adımda).
      const screenX = s.x - cam.scrollX * d.f;
      if (screenX > GAME_WIDTH + MARGIN || screenX < -MARGIN) {
        const wrapped = Phaser.Math.Wrap(screenX + MARGIN, 0, wrapWidth) - MARGIN;
        s.x = wrapped + cam.scrollX * d.f;
      }

      if (d.tumble > 0) {
        // Disk kendi ekseninde döner gibi: yatay ölçek daralıp genişler, hafifçe yatar.
        s.scaleX = d.baseScale * (0.55 + 0.45 * Math.abs(Math.cos(this.time * d.tumble + d.phase)));
        s.rotation = Math.sin(this.time * d.tumble * 0.7 + d.phase) * 0.5;
      }
    }
  }

  private add(
    key: string,
    f: number,
    depth: number,
    o: {
      y: number;
      scale: number;
      alpha: number;
      tint?: number;
      ownSpeed: number;
      swayAmp: number;
      tumble: number;
    },
  ): void {
    // Başlangıçta ekran genişliği boyunca dağıt (kamera henüz 0'da).
    const x = this.rng.between(-MARGIN, GAME_WIDTH + MARGIN);
    const sprite = this.scene.add
      .image(x, o.y, key)
      .setScale(o.scale)
      .setAlpha(o.alpha)
      .setScrollFactor(f, 1)
      .setDepth(depth);
    if (o.tint !== undefined) sprite.setTint(o.tint);
    this.drifters.push({
      sprite,
      f,
      ownSpeed: o.ownSpeed,
      baseY: o.y,
      swayAmp: o.swayAmp,
      swayFreq: this.rng.realInRange(0.4, 1.1),
      phase: this.rng.realInRange(0, Math.PI * 2),
      tumble: o.tumble,
      baseScale: o.scale,
    });
  }
}
