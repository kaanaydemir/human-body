import Phaser from 'phaser';
import { DEPTH, LUMEN, WORLD_WIDTH } from '../config';

export type SubState =
  | 'idle'
  | 'forward'
  | 'backward'
  | 'up'
  | 'down'
  | 'slowing'
  | 'landing'
  | 'interacting';

/** ASSET_MANIFEST.md B: 520×300 çerçevede sabit bağlantı noktaları (çerçeve merkezine göre). */
const FRAME_CENTER = { x: 260, y: 150 };
const HEADLIGHT = { x: 498 - FRAME_CENTER.x, y: 178 - FRAME_CENTER.y };
const JET = { x: 24 - FRAME_CENTER.x, y: 168 - FRAME_CENTER.y };

const SCALE = 0.85;
const LIGHT_ALPHA = 0.8;
const MAX_SPEED_X = 470;
const MAX_SPEED_Y = 300;
const ACCEL_X = 820;
const ACCEL_Y = 760;
/** Girdi bırakılınca yumuşak yavaşlama (üstel sürtünme, 1/sn). */
const DRAG_X = 1.9;
const DRAG_Y = 3.2;

/**
 * Oyuncunun minyatür denizaltısı. Katmanlar arkadan öne: jet → kabin içi → kâşif → gövde+kubbe → far ışığı.
 * Fizik konumu (pos) ile görüntü (salınım, eğilme, esneme) ayrı tutulur.
 */
export class Submarine extends Phaser.GameObjects.Container {
  readonly pos: Phaser.Math.Vector2;
  readonly vel = new Phaser.Math.Vector2();
  subState: SubState = 'idle';

  private readonly explorer: Phaser.GameObjects.Image;
  private readonly jet: Phaser.GameObjects.Image;
  private readonly light: Phaser.GameObjects.Image;
  private readonly bubbles: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly noseBubbles: Phaser.GameObjects.Particles.ParticleEmitter;

  private time = 0;
  private thrust = 0;
  private blinkTimer = 3;
  private blinking = 0;
  private interactTimer = 0;
  private landed = false;
  private prevInputX = 0;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y);
    this.pos = new Phaser.Math.Vector2(x, y);

    this.jet = scene.add.image(JET.x, JET.y, 'jet').setOrigin(1, 0.5).setAlpha(0.6);
    const back = scene.add.image(0, 0, 'sub_back');
    this.explorer = scene.add.image(0, 0, 'explorer');
    const front = scene.add.image(0, 0, 'sub_front');
    this.light = scene.add
      .image(HEADLIGHT.x - 6, HEADLIGHT.y, 'sub_light')
      .setOrigin(0, 0.5)
      .setBlendMode(Phaser.BlendModes.ADD)
      // Referanstaki (7. pano) far ışığı kırmızının üstünde doygun sarı-turuncu parlar.
      .setTint(0xffa848)
      .setAlpha(LIGHT_ALPHA);

    this.add([this.jet, back, this.explorer, front, this.light]);
    this.setScale(SCALE).setDepth(DEPTH.player);
    scene.add.existing(this);

    // Arka jetten çıkan kabarcıklar ve geri giderken burundan çıkan kabarcıklar.
    this.bubbles = scene.add
      .particles(0, 0, 'bubble', {
        lifespan: { min: 700, max: 1300 },
        speedX: { min: -190, max: -70 },
        speedY: { min: -40, max: 20 },
        scale: { start: 0.55, end: 0.15 },
        alpha: { start: 0.85, end: 0 },
        gravityY: -40,
        frequency: 60,
        emitting: false,
      })
      .setDepth(DEPTH.playerFx);
    this.noseBubbles = scene.add
      .particles(0, 0, 'bubble', {
        lifespan: { min: 500, max: 900 },
        speedX: { min: 60, max: 160 },
        speedY: { min: -30, max: 30 },
        scale: { start: 0.4, end: 0.1 },
        alpha: { start: 0.75, end: 0 },
        gravityY: -30,
        frequency: 80,
        emitting: false,
      })
      .setDepth(DEPTH.player + 1);
  }

  /** Etkileşim / tarama sırasında kâşifin meraklı yüzü ve küçük bir duraksama. */
  interact(duration = 1.2): void {
    this.interactTimer = duration;
  }

  /** @param input -1…1 yön girdisi */
  step(dt: number, input: { x: number; y: number }): void {
    this.time += dt;
    this.interactTimer = Math.max(0, this.interactTimer - dt);

    this.integrate(dt, input);
    this.updateState(input);
    this.animate(dt, input);
    this.prevInputX = input.x;
  }

  private integrate(dt: number, input: { x: number; y: number }): void {
    const v = this.vel;
    if (input.x !== 0) v.x += input.x * ACCEL_X * dt;
    else v.x *= Math.exp(-DRAG_X * dt);
    if (input.y !== 0) v.y += input.y * ACCEL_Y * dt;
    else v.y *= Math.exp(-DRAG_Y * dt);
    // Girdiye ters yöndeyken daha çabuk dönsün (fren hissi).
    if (input.x !== 0 && Math.sign(input.x) !== Math.sign(v.x)) v.x *= Math.exp(-2.5 * dt);
    v.x = Phaser.Math.Clamp(v.x, -MAX_SPEED_X, MAX_SPEED_X);
    v.y = Phaser.Math.Clamp(v.y, -MAX_SPEED_Y, MAX_SPEED_Y);

    this.pos.x += v.x * dt;
    this.pos.y += v.y * dt;

    // Damar içinde kal: kenara yaklaşınca yumuşak bir yay geri iter, en dipte zemine oturur.
    const minX = 280;
    const maxX = WORLD_WIDTH - 280;
    if (this.pos.x < minX) {
      this.pos.x = minX;
      v.x = Math.max(0, v.x);
    } else if (this.pos.x > maxX) {
      this.pos.x = maxX;
      v.x = Math.min(0, v.x);
    }
    if (this.pos.y < LUMEN.top) {
      v.y += (LUMEN.top - this.pos.y) * 14 * dt;
      this.pos.y = Math.max(this.pos.y, LUMEN.top - 24);
    }
    const wasLanded = this.landed;
    if (this.pos.y >= LUMEN.bottom) {
      this.pos.y = LUMEN.bottom;
      if (v.y > 0) v.y = 0;
      this.landed = true;
    } else if (this.pos.y < LUMEN.bottom - 6) {
      this.landed = false;
    }
    if (this.landed && !wasLanded) this.touchdown();
  }

  private updateState(input: { x: number; y: number }): void {
    const vx = this.vel.x;
    let s: SubState;
    if (this.interactTimer > 0) s = 'interacting';
    else if (this.landed && input.y >= 0 && Math.abs(vx) < 120) s = 'landing';
    else if (input.x > 0 && vx > 30) s = 'forward';
    else if (input.x < 0 && vx < -30) s = 'backward';
    else if (input.y < 0) s = 'up';
    else if (input.y > 0) s = 'down';
    else if (Math.abs(vx) > 60 || Math.abs(this.vel.y) > 60) s = 'slowing';
    else s = 'idle';

    // İleri giderken gaz bırakılırsa gövde hafifçe öne yaslanıp toparlanır.
    if (this.prevInputX !== 0 && input.x === 0 && Math.abs(vx) > 220) this.squash(1.035, 0.965);
    this.subState = s;
  }

  private animate(dt: number, input: { x: number; y: number }): void {
    const vx = this.vel.x;
    const vy = this.vel.y;
    const nx = vx / MAX_SPEED_X;
    const ny = vy / MAX_SPEED_Y;

    // Süzülme: yerdeyken neredeyse durur.
    const bobAmp = this.landed ? 1.2 : 6;
    const bob = Math.sin((this.time * Math.PI * 2) / 2.2) * bobAmp;
    this.setPosition(this.pos.x, this.pos.y + bob);

    // Eğilme: yukarı çıkarken burun kalkar, hızlanırken hafif burun yukarı, geri giderken burun aşağı.
    let targetRot = ny * 0.11;
    if (this.subState === 'forward') targetRot -= 0.035;
    if (this.subState === 'backward') targetRot += 0.05 * Math.abs(nx);
    if (this.subState === 'slowing') targetRot += 0.04 * nx;
    targetRot += Math.sin(this.time * 1.3) * (this.landed ? 0.004 : 0.015);
    this.rotation = Phaser.Math.Linear(this.rotation, targetRot, 1 - Math.exp(-5 * dt));

    // İtki: ileri basılıyken güçlü, boşta hafif, geri giderken kapalı.
    const targetThrust =
      this.subState === 'backward' ? 0 : input.x > 0 ? 1 : input.y !== 0 ? 0.55 : this.landed ? 0.05 : 0.22;
    this.thrust = Phaser.Math.Linear(this.thrust, targetThrust, 1 - Math.exp(-6 * dt));
    const flicker = 0.92 + Math.sin(this.time * 31) * 0.05 + Math.sin(this.time * 17.3) * 0.03;
    this.jet.setScale((0.35 + 0.8 * this.thrust) * flicker, 0.75 + 0.35 * this.thrust);
    this.jet.setAlpha(0.25 + 0.65 * this.thrust);

    // Far: çok hafif titreme.
    this.light.setAlpha(LIGHT_ALPHA + Math.sin(this.time * 5.1) * 0.04 + Math.sin(this.time * 13.7) * 0.025);

    // Kabarcıklar parçacık sisteminde dünya koordinatında doğar.
    const jetWorld = this.localToWorld(JET.x - 4, JET.y);
    this.bubbles.setPosition(jetWorld.x, jetWorld.y);
    this.bubbles.frequency = Phaser.Math.Linear(170, 28, this.thrust);
    this.bubbles.emitting = this.thrust > 0.12;
    const noseWorld = this.localToWorld(HEADLIGHT.x + 4, HEADLIGHT.y + 10);
    this.noseBubbles.setPosition(noseWorld.x, noseWorld.y);
    this.noseBubbles.emitting = this.subState === 'backward';

    this.animateExplorer(dt);
  }

  private animateExplorer(dt: number): void {
    // Gövdeden biraz gecikmeli küçük baş salınımı.
    this.explorer.y = Math.sin((this.time * Math.PI * 2) / 2.2 - 0.9) * 1.6;
    this.explorer.x = Phaser.Math.Linear(this.explorer.x, -this.vel.x * 0.006, 1 - Math.exp(-4 * dt));

    this.blinkTimer -= dt;
    if (this.blinkTimer <= 0 && this.blinking <= 0) {
      this.blinking = 0.13;
      this.blinkTimer = Phaser.Math.FloatBetween(2.8, 6);
    }
    let key = this.interactTimer > 0 ? 'explorer_curious' : 'explorer';
    if (this.blinking > 0) {
      this.blinking -= dt;
      key = 'explorer_blink';
    }
    if (this.explorer.texture.key !== key) this.explorer.setTexture(key);
  }

  private touchdown(): void {
    this.squash(1.05, 0.94);
    // Zemine değerken birkaç kabarcık ve zerre savrulur.
    const p = this.localToWorld(0, 120);
    this.noseBubbles.explode(8, p.x + 60, p.y);
    this.bubbles.explode(8, p.x - 60, p.y);
  }

  private squash(sx: number, sy: number): void {
    if (this.scene.tweens.isTweening(this)) return;
    this.scene.tweens.add({
      targets: this,
      scaleX: SCALE * sx,
      scaleY: SCALE * sy,
      duration: 140,
      yoyo: true,
      ease: 'Sine.easeOut',
      onComplete: () => this.setScale(SCALE),
    });
  }

  /** Kap içindeki yerel bir noktanın dünya konumu (döndürme ve ölçek dahil). */
  private localToWorld(lx: number, ly: number): Phaser.Math.Vector2 {
    const cos = Math.cos(this.rotation);
    const sin = Math.sin(this.rotation);
    const x = lx * this.scaleX;
    const y = ly * this.scaleY;
    return new Phaser.Math.Vector2(this.x + x * cos - y * sin, this.y + x * sin + y * cos);
  }
}
