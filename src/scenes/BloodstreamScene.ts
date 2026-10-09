import Phaser from 'phaser';
import { DEPTH, GAME_HEIGHT, GAME_WIDTH, WORLD_WIDTH } from '../config';
import { BloodFlow } from '../fx/BloodFlow';
import { Controls } from '../input/Controls';
import { Submarine } from '../objects/Submarine';
import { Heartbeat } from '../world/Heartbeat';
import { Vessel } from '../world/Vessel';

/** Kameranın denizaltının önünü görmesi için hedefi ekran merkezinin solunda tuttuğu mesafe. */
const BASE_LOOKAHEAD = 240;
const GLOW_ALPHA = 0.12;

/**
 * Ana oynanabilir sahne: kan damarının içinde soldan sağa yolculuk.
 * Aşama 2 kapsamı: kapalı damar ortamı, paralaks, denizaltı hareketi ve kamera takibi.
 */
export class BloodstreamScene extends Phaser.Scene {
  private vessel!: Vessel;
  private flow!: BloodFlow;
  private heart!: Heartbeat;
  private sub!: Submarine;
  private controls!: Controls;
  private glow!: Phaser.GameObjects.Image;
  private lookahead = BASE_LOOKAHEAD;
  private moved = false;
  private debugText?: Phaser.GameObjects.Text;

  constructor() {
    super('Bloodstream');
  }

  create(): void {
    const params = new URLSearchParams(window.location.search);
    const num = (key: string, fallback: number): number => {
      const v = Number(params.get(key));
      return params.has(key) && Number.isFinite(v) ? v : fallback;
    };
    const startX = Phaser.Math.Clamp(num('x', 420), 280, WORLD_WIDTH - 280);
    const startY = Phaser.Math.Clamp(num('y', 520), 300, 760);

    this.moved = false;
    this.lookahead = BASE_LOOKAHEAD;
    this.heart = new Heartbeat();
    this.vessel = new Vessel(this);
    this.flow = new BloodFlow(this);
    this.sub = new Submarine(this, startX, startY);
    this.controls = new Controls(this);

    // Ekran sabiti kaplamalar: sol üstten gelen sıcak ana ışık ve köşeleri koyulaştıran vinyet.
    // Işık, derindeki tünel deliklerini aydınlatmasın diye merkezden uzakta durur.
    this.glow = this.add
      .image(GAME_WIDTH * 0.3, GAME_HEIGHT * 0.24, 'glow')
      .setScrollFactor(0)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setAlpha(GLOW_ALPHA)
      .setScale(1.35)
      .setDepth(DEPTH.glow);
    this.add
      .image(0, 0, 'vignette')
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(DEPTH.vignette)
      .setAlpha(0.45);

    const cam = this.cameras.main;
    cam.setBounds(0, 0, WORLD_WIDTH, GAME_HEIGHT);
    cam.startFollow(this.sub, false, 0.08, 0.08);
    cam.setFollowOffset(-this.lookahead, 0);
    cam.centerOn(startX + this.lookahead, GAME_HEIGHT / 2);
    cam.fadeIn(700, 26, 6, 9);

    this.registry.set('progress', 0);
    this.registry.set('moved', false);
    this.scene.launch('Hud');

    // Duraklatmadan dönünce takılı kalmış tuşları temizle. Sahne olay dinleyicileri kapanışta
    // kendiliğinden silinmez; yeniden başlatmada birikmesin diye elle kaldırılır.
    const onResume = (): void => this.controls.reset();
    this.events.on(Phaser.Scenes.Events.RESUME, onResume);
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.events.off(Phaser.Scenes.Events.RESUME, onResume));

    if (params.has('debug')) {
      this.debugText = this.add
        .text(GAME_WIDTH - 20, GAME_HEIGHT - 20, '', { fontFamily: 'monospace', fontSize: '22px', color: '#fff' })
        .setOrigin(1, 1)
        .setScrollFactor(0)
        .setDepth(200);
    }

    // Ekran görüntüsü / otomatik test aracı sahnenin hazır olduğunu buradan anlar.
    // Açılış kararması bitmeden çekilen görüntüler olduğundan koyu çıkar, o yüzden bitişi beklenir.
    cam.once(Phaser.Cameras.Scene2D.Events.FADE_IN_COMPLETE, () => {
      this.time.delayedCall(300, () => {
        (window as unknown as { __ready: boolean }).__ready = true;
      });
    });
  }

  update(_time: number, deltaMs: number): void {
    // Yavaş cihazlarda oyun hızı düşmesin diye uzun kareler küçük fizik adımlarına bölünür.
    // (Phaser, fps.min'e göre 250 ms'yi aşan kareleri zaten önceki bir değerle değiştirir.)
    const dt = deltaMs / 1000;
    this.heart.update(dt);

    const cam = this.cameras.main;
    const input = this.controls.axis({ x: this.sub.x - cam.scrollX, y: this.sub.y - cam.scrollY });
    if (this.controls.consumeScan()) this.scanPulse();
    if (this.controls.consumeInteract()) this.sub.interact();

    const steps = Math.ceil(dt / (1 / 30));
    for (let i = 0; i < steps; i++) this.sub.step(dt / steps, input);
    this.flow.update(dt, this.heart.surge);
    this.vessel.pulse(this.heart.pulse);
    this.glow.setAlpha(GLOW_ALPHA + this.heart.pulse * 0.03);

    // Kamera, hızla birlikte gidilen yöne doğru biraz daha önü gösterir.
    const target = BASE_LOOKAHEAD + Phaser.Math.Clamp(this.sub.vel.x * 0.35, -380, 160);
    this.lookahead = Phaser.Math.Linear(this.lookahead, target, 1 - Math.exp(-1.6 * dt));
    this.cameras.main.setFollowOffset(-this.lookahead, 0);

    if (!this.moved && (input.x !== 0 || input.y !== 0)) {
      this.moved = true;
      this.registry.set('moved', true);
    }
    this.registry.set('progress', (this.sub.pos.x - 280) / (WORLD_WIDTH - 560));

    if (this.debugText) {
      this.debugText.setText(
        `${Math.round(this.game.loop.actualFps)} FPS  x=${Math.round(this.sub.pos.x)} y=${Math.round(
          this.sub.pos.y,
        )}  ${this.sub.subState}`,
      );
    }
  }

  /**
   * Boşluk: burundan yayılan, elle çizilmiş gibi kesik kesik bir tarama halkası
   * (Aşama 5'te tıkanıklık taramasında kullanılacak). Her yay uçlarda incelir ve halka
   * genişledikçe çizgi kalınlığı 9 px'ten 3 px'e iner.
   */
  private scanPulse(): void {
    this.sub.interact(1.0);
    const nose = new Phaser.Math.Vector2();
    this.sub.getWorldTransformMatrix().transformPoint(200, 30, nose);
    const ring = this.add.graphics().setDepth(DEPTH.player + 3);

    // 3–4 yay, aralarında 15–30°'lik boşluklar.
    const arcs: { start: number; length: number }[] = [];
    const count = Phaser.Math.Between(3, 4);
    const gaps = Array.from({ length: count }, () => Phaser.Math.DegToRad(Phaser.Math.Between(15, 30)));
    const free = Math.PI * 2 - gaps.reduce((a, b) => a + b, 0);
    let angle = Phaser.Math.FloatBetween(0, Math.PI * 2);
    for (let i = 0; i < count; i++) {
      const length = (free / count) * Phaser.Math.FloatBetween(0.8, 1.2);
      arcs.push({ start: angle, length });
      angle += length + gaps[i];
    }

    // Yarıçap yumuşakça yavaşlayarak büyür; saydamlık ise zamana göre geç söner ki halka okunsun.
    const state = { t: 0 };
    this.tweens.add({
      targets: state,
      t: 1,
      duration: 1300,
      ease: 'Linear',
      onUpdate: () => {
        const grow = Phaser.Math.Easing.Sine.Out(state.t);
        const r = 40 + 520 * grow;
        const width = Phaser.Math.Linear(12, 4, grow);
        const fade = 1 - state.t ** 1.8;
        ring.clear();
        for (const a of arcs) {
          this.drawTaperedArc(ring, nose.x, nose.y, r, a.start, a.length, width * 2.6, 0xffe79e, 0.35 * fade);
          this.drawTaperedArc(ring, nose.x, nose.y, r, a.start, a.length, width, 0xfff4e0, 0.95 * fade);
        }
      },
      onComplete: () => ring.destroy(),
    });
  }

  /** Uçlara doğru incelen dolu bir yay şeridi çizer. */
  private drawTaperedArc(
    g: Phaser.GameObjects.Graphics,
    cx: number,
    cy: number,
    r: number,
    start: number,
    length: number,
    width: number,
    color: number,
    alpha: number,
  ): void {
    const steps = 28;
    const outer: Phaser.Math.Vector2[] = [];
    const inner: Phaser.Math.Vector2[] = [];
    for (let i = 0; i <= steps; i++) {
      const u = i / steps;
      const a = start + length * u;
      const w = (width / 2) * (0.25 + 0.75 * Math.sin(Math.PI * u));
      outer.push(new Phaser.Math.Vector2(cx + Math.cos(a) * (r + w), cy + Math.sin(a) * (r + w)));
      inner.push(new Phaser.Math.Vector2(cx + Math.cos(a) * (r - w), cy + Math.sin(a) * (r - w)));
    }
    g.fillStyle(color, alpha);
    g.fillPoints([...outer, ...inner.reverse()], true);
  }
}
