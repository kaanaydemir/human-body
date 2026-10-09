import Phaser from 'phaser';
import { COLORS, GAME_HEIGHT, GAME_WIDTH } from '../config';
import { captionStyle, createBadge, createPanel, textStyle } from '../ui/Panel';

/** İlk hareketten sonra kontrol ipuçlarının ekranda kalma süresi (ms). */
const HINT_LINGER = 6000;

/**
 * Oyun dünyasının üstünde sabit duran arayüz: numaralı altyazı, görev paneli, ilerleme şeridi,
 * kontrol ipuçları ve ESC duraklatma menüsü. Damar sahnesinden bağımsız çalışır ki duraklatmada da canlı kalsın.
 *
 * Referanstaki gibi numaralı altyazı sol üst köşede, sahnenin üstünde durur; oyun alanını kapatmaz.
 * Altyazı görünürken görev paneli gizlenir, altyazı kaybolunca görev paneli onun yerine gelir.
 */
export class HudScene extends Phaser.Scene {
  private pauseLayer?: Phaser.GameObjects.Container;
  private caption?: Phaser.GameObjects.Container;
  private objective!: Phaser.GameObjects.Container;
  private progress!: Phaser.GameObjects.Container;
  private hints!: Phaser.GameObjects.Container;
  private progressIcon!: Phaser.GameObjects.Image;
  private readonly track = { x: 0, width: 0 };
  private hintTimer?: Phaser.Time.TimerEvent;

  constructor() {
    super('Hud');
  }

  create(): void {
    this.pauseLayer = undefined;
    this.caption = undefined;
    this.hintTimer = undefined;

    this.objective = this.createObjective().setAlpha(0);
    this.progress = this.createProgress();
    this.hints = this.createControlsHint();
    this.showCaption('3', 'Kan damarının içindesin! Alyuvarlar oksijeni tüm\nvücuda taşıyor. İleri doğru ilerle ve keşfet.');

    this.input.keyboard?.on('keydown-ESC', () => this.togglePause());
    this.registry.events.on('changedata-moved', this.onFirstMove, this);
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.registry.events.off('changedata-moved', this.onFirstMove, this);
    });
  }

  update(): void {
    const p = Phaser.Math.Clamp((this.registry.get('progress') as number | undefined) ?? 0, 0, 1);
    // Simge yarısı şeridin dışına taşmasın.
    const minX = this.track.x + 30;
    const maxX = this.track.x + this.track.width - 30;
    this.progressIcon.x = Phaser.Math.Linear(minX, maxX, p);
  }

  private onFirstMove(_parent: unknown, moved: boolean): void {
    if (!moved || this.hintTimer) return;
    this.hideCaption(1800);
    this.hintTimer = this.time.delayedCall(HINT_LINGER, () => this.fade(this.hints, 0, 600));
  }

  private createObjective(): Phaser.GameObjects.Container {
    const w = 690;
    const h = 108;
    const panel = createPanel(this, 0, 0, w, h).setOrigin(0, 0);
    const icon = this.add.image(58, h / 2, 'icon_objective').setDisplaySize(76, 76);
    const label = this.add.text(108, 16, 'GÖREV', textStyle(24, '800', '#a3283a'));
    const body = this.add.text(108, 48, 'Kan damarında ilerle ve çevreni keşfet.', captionStyle(32));
    return this.add.container(24, 20, [panel, icon, label, body]);
  }

  private createProgress(): Phaser.GameObjects.Container {
    const w = 380;
    const h = 80;
    const x = GAME_WIDTH - 24 - w;
    const panel = createPanel(this, 0, 0, w, h).setOrigin(0, 0);
    const label = this.add.text(28, 10, 'Damar yolculuğu', textStyle(22, '800', '#a3283a'));
    const trackX = 30;
    const trackW = w - 60;
    const trackY = 56;
    const g = this.add.graphics();
    g.fillStyle(0xecddc7, 1).fillRoundedRect(trackX - 4, trackY - 7, trackW + 8, 14, 7);
    g.lineStyle(3, COLORS.panelEdge, 1).strokeRoundedRect(trackX - 4, trackY - 7, trackW + 8, 14, 7);
    this.track.x = trackX;
    this.track.width = trackW;
    this.progressIcon = this.add.image(trackX + 30, trackY - 4, 'icon_progress').setDisplaySize(58, 33);
    return this.add.container(x, 20, [panel, label, g, this.progressIcon]);
  }

  private createControlsHint(): Phaser.GameObjects.Container {
    const h = 84;
    const items: Phaser.GameObjects.GameObject[] = [];
    const cy = h / 2;
    let cx = 30;
    const label = (t: string): void => {
      const txt = this.add.text(cx, cy, t, captionStyle(26)).setOrigin(0, 0.5);
      items.push(txt);
      cx += txt.width + 28;
    };
    const key = (t: string): void => {
      const txt = this.add.text(cx, cy, t, textStyle(25, '800', '#a3283a')).setOrigin(0, 0.5);
      items.push(txt);
      cx += txt.width + 10;
    };
    key('WASD / Oklar');
    label('Hareket');
    items.push(this.add.image(cx + 50, cy, 'key_space').setDisplaySize(100, 44));
    items.push(this.add.text(cx + 50, cy - 1, 'Boşluk', textStyle(19, '800')).setOrigin(0.5));
    cx += 110;
    label('Tara');
    items.push(this.add.image(cx + 22, cy, 'key_e').setDisplaySize(46, 46));
    cx += 54;
    label('Etkileşim');
    key('ESC');
    label('Duraklat');
    const w = cx + 2;
    const panel = createPanel(this, 0, 0, w, h).setOrigin(0, 0);
    return this.add.container(24, GAME_HEIGHT - 24 - h, [panel, ...items]);
  }

  /** Referanstaki numaralı altyazılar gibi: sol üstte rozet + krem panel, yalnızca saydamlıkla belirir. */
  showCaption(number: string, text: string): void {
    this.caption?.destroy();
    const txt = this.add.text(118, 0, text, captionStyle(34)).setOrigin(0, 0.5).setLineSpacing(8);
    const w = Math.min(920, txt.width + 160);
    const h = Math.max(120, txt.height + 44);
    txt.setY(h / 2);
    const panel = createPanel(this, 0, 0, w, h).setOrigin(0, 0);
    const badge = createBadge(this, 62, h / 2, number, 76);
    this.caption = this.add.container(24, 20, [panel, badge, txt]).setAlpha(0);
    this.fade(this.objective, 0, 200);
    this.fade(this.caption, 1, 500);
    this.time.delayedCall(9000, () => this.hideCaption(0));
  }

  private hideCaption(delay: number): void {
    const c = this.caption;
    if (!c) return;
    this.caption = undefined;
    this.tweens.add({
      targets: c,
      alpha: 0,
      duration: 600,
      delay,
      ease: 'Sine.easeIn',
      onComplete: () => {
        c.destroy();
        if (!this.pauseLayer) this.fade(this.objective, 1, 500);
      },
    });
  }

  private fade(target: Phaser.GameObjects.Container, alpha: number, duration: number): void {
    this.tweens.killTweensOf(target);
    this.tweens.add({ targets: target, alpha, duration, ease: 'Sine.easeInOut' });
  }

  private togglePause(): void {
    const world = this.scene.get('Bloodstream');
    if (this.pauseLayer) {
      this.pauseLayer.destroy();
      this.pauseLayer = undefined;
      this.scene.resume('Bloodstream');
      world.events.emit('resumed');
      // Panelleri geri getir; kontrol ipuçları yeniden kısa bir süre görünür kalır.
      this.objective.setVisible(true).setAlpha(1);
      this.progress.setVisible(true);
      this.hints.setVisible(true).setAlpha(1);
      this.hintTimer?.remove();
      this.hintTimer = this.time.delayedCall(HINT_LINGER, () => this.fade(this.hints, 0, 600));
      return;
    }
    this.scene.pause('Bloodstream');
    // Karartma altında krem paneller morumsu görünür; duraklatmada HUD'u tamamen gizle.
    this.caption?.destroy();
    this.caption = undefined;
    this.objective.setVisible(false);
    this.progress.setVisible(false);
    this.hints.setVisible(false);

    const dim = this.add.rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, COLORS.maroon, 0.55).setOrigin(0, 0);
    dim.setInteractive(); // Arkadaki tıklamaları yut.
    const w = 720;
    const h = 470;
    const px = (GAME_WIDTH - w) / 2;
    const py = (GAME_HEIGHT - h) / 2;
    const panel = createPanel(this, px, py, w, h).setOrigin(0, 0);
    const title = this.add
      .text(GAME_WIDTH / 2, py + 80, 'Oyun Duraklatıldı', textStyle(56, '800'))
      .setOrigin(0.5);
    const tip = this.add
      .text(GAME_WIDTH / 2, py + 138, 'WASD / Oklar: hareket · Boşluk: tara · E: etkileşim', captionStyle(24, '400', '#5a4c3d'))
      .setOrigin(0.5);
    const resume = this.button(GAME_WIDTH / 2, py + 250, 'Devam Et', () => this.togglePause());
    const restart = this.button(GAME_WIDTH / 2, py + 365, 'Baştan Başla', () => {
      this.pauseLayer?.destroy();
      this.pauseLayer = undefined;
      this.scene.stop('Bloodstream');
      this.scene.start('Bloodstream');
    });
    this.pauseLayer = this.add.container(0, 0, [dim, panel, title, tip, resume, restart]).setDepth(100);
  }

  private button(x: number, y: number, label: string, onClick: () => void): Phaser.GameObjects.Container {
    const w = 380;
    const h = 86;
    const bg = this.add.graphics();
    const draw = (hover: boolean): void => {
      bg.clear();
      bg.fillStyle(0x7e1626, 1).fillRoundedRect(-w / 2, -h / 2 + 7, w, h, 30);
      bg.fillStyle(hover ? 0xe0405a : COLORS.accent, 1).fillRoundedRect(-w / 2, -h / 2, w, h, 30);
      bg.lineStyle(4, COLORS.panelEdge, 1).strokeRoundedRect(-w / 2, -h / 2, w, h + 7, 30);
    };
    draw(false);
    const txt = this.add.text(0, -2, label, textStyle(38, '800', '#fbefdc')).setOrigin(0.5);
    const c = this.add.container(x, y, [bg, txt]).setSize(w, h);
    c.setInteractive({ useHandCursor: true })
      .on('pointerover', () => draw(true))
      .on('pointerout', () => draw(false))
      .on('pointerup', onClick);
    return c;
  }
}
