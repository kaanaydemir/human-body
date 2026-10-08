import Phaser from 'phaser';
import { DEPTH, GAME_HEIGHT, GAME_WIDTH, WORLD_WIDTH } from '../config';
import { BloodFlow } from '../fx/BloodFlow';
import { Controls } from '../input/Controls';
import { Submarine } from '../objects/Submarine';
import { Heartbeat } from '../world/Heartbeat';
import { Vessel } from '../world/Vessel';

/** Kameranın denizaltının önünü görmesi için hedefi ekran merkezinin solunda tuttuğu mesafe. */
const BASE_LOOKAHEAD = 240;

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
    const startX = Phaser.Math.Clamp(Number(params.get('x') ?? 420), 280, WORLD_WIDTH - 280);
    const startY = Phaser.Math.Clamp(Number(params.get('y') ?? 520), 300, 760);

    this.moved = false;
    this.lookahead = BASE_LOOKAHEAD;
    this.heart = new Heartbeat();
    this.vessel = new Vessel(this);
    this.flow = new BloodFlow(this);
    this.sub = new Submarine(this, startX, startY);
    this.controls = new Controls(this);

    // Ekran sabiti kaplamalar: sıcak ışık ve kenarları koyulaştıran vinyet.
    this.glow = this.add
      .image(GAME_WIDTH * 0.42, GAME_HEIGHT * 0.42, 'glow')
      .setScrollFactor(0)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setAlpha(0.16)
      .setScale(1.6)
      .setDepth(DEPTH.glow);
    this.add
      .image(0, 0, 'vignette')
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(DEPTH.vignette);

    const cam = this.cameras.main;
    cam.setBounds(0, 0, WORLD_WIDTH, GAME_HEIGHT);
    cam.startFollow(this.sub, false, 0.08, 0.08);
    cam.setFollowOffset(-this.lookahead, 0);
    cam.centerOn(startX + this.lookahead, GAME_HEIGHT / 2);
    cam.fadeIn(700, 26, 6, 9);

    this.registry.set('progress', 0);
    this.registry.set('moved', false);
    this.scene.launch('Hud');

    this.events.on('resumed', () => this.controls.reset());

    if (params.has('debug')) {
      this.debugText = this.add
        .text(GAME_WIDTH - 20, GAME_HEIGHT - 20, '', { fontFamily: 'monospace', fontSize: '22px', color: '#fff' })
        .setOrigin(1, 1)
        .setScrollFactor(0)
        .setDepth(200);
    }

    // Ekran görüntüsü / otomatik test aracı sahnenin hazır olduğunu buradan anlar.
    this.time.delayedCall(300, () => {
      (window as unknown as { __ready: boolean }).__ready = true;
    });
  }

  update(_time: number, deltaMs: number): void {
    const dt = Math.min(deltaMs, 50) / 1000;
    this.heart.update(dt);

    const input = this.controls.axis;
    if (this.controls.scanPressed) this.scanPulse();
    if (this.controls.interactPressed) this.sub.interact();

    this.sub.step(dt, input);
    this.flow.update(dt, this.heart.surge);
    this.vessel.pulse(this.heart.pulse);
    this.glow.setAlpha(0.15 + this.heart.pulse * 0.035);

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

  /** Boşluk: burundan yayılan yumuşak bir tarama halkası (Aşama 5'te tıkanıklık taramasında kullanılacak). */
  private scanPulse(): void {
    this.sub.interact(1.0);
    const origin = this.sub.getWorldTransformMatrix();
    const ring = this.add.graphics().setDepth(DEPTH.player + 3);
    const state = { r: 30, a: 0.9 };
    const nose = new Phaser.Math.Vector2(200, 30);
    origin.transformPoint(nose.x, nose.y, nose);
    this.tweens.add({
      targets: state,
      r: 520,
      a: 0,
      duration: 1100,
      ease: 'Sine.easeOut',
      onUpdate: () => {
        ring.clear();
        ring.lineStyle(10, 0xfbe7c8, state.a * 0.55);
        ring.strokeCircle(nose.x, nose.y, state.r);
        ring.lineStyle(4, 0xffffff, state.a * 0.7);
        ring.strokeCircle(nose.x, nose.y, state.r - 8);
      },
      onComplete: () => ring.destroy(),
    });
  }
}
