import Phaser from 'phaser';
import { COLORS, GAME_HEIGHT, GAME_WIDTH } from '../config';
import { createBadge, createPanel, textStyle } from '../ui/Panel';

/**
 * Oyun dünyasının üstünde sabit duran arayüz: görev paneli, ilerleme şeridi, kontrol ipuçları,
 * giriş altyazısı ve ESC duraklatma menüsü. Damar sahnesinden bağımsız çalışır ki duraklatmada da canlı kalsın.
 */
export class HudScene extends Phaser.Scene {
  private pauseLayer?: Phaser.GameObjects.Container;
  private caption?: Phaser.GameObjects.Container;
  private progressSub?: Phaser.GameObjects.Container;
  private readonly progressBar = { x: 0, width: 0 };

  constructor() {
    super('Hud');
  }

  create(): void {
    this.createObjective();
    this.createProgress();
    this.createControlsHint();
    this.showCaption('3', 'Kan damarının içindesin! Alyuvarlar oksijeni\ntüm vücuda taşıyor. İleri doğru ilerle ve keşfet.');

    this.input.keyboard?.on('keydown-ESC', () => this.togglePause());
    this.registry.events.on('changedata-moved', () => this.hideCaption(), this);
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.registry.events.off('changedata-moved', undefined, this);
    });
  }

  update(): void {
    const p = (this.registry.get('progress') as number | undefined) ?? 0;
    if (this.progressSub) {
      this.progressSub.x = this.progressBar.x + p * this.progressBar.width;
    }
  }

  private createObjective(): void {
    const x = 36;
    const y = 30;
    const w = 700;
    const h = 112;
    createPanel(this, x, y, w, h).setOrigin(0, 0);
    this.add.image(x + 62, y + h / 2, 'icon_objective').setDisplaySize(78, 78);
    this.add.text(x + 112, y + 18, 'GÖREV', textStyle(24, '800', '#a3283a'));
    this.add.text(x + 112, y + 46, 'Kan damarında ilerle ve çevreni keşfet.', textStyle(32, '700'));
  }

  private createProgress(): void {
    const w = 460;
    const x = GAME_WIDTH - 36 - w;
    const y = 30;
    createPanel(this, x, y, w, 112).setOrigin(0, 0);
    this.add.text(x + 32, y + 16, 'Damar yolculuğu', textStyle(26, '800', '#a3283a'));
    const trackX = x + 40;
    const trackW = w - 80;
    const trackY = y + 78;
    const g = this.add.graphics();
    g.fillStyle(0xecddc7, 1).fillRoundedRect(trackX - 6, trackY - 9, trackW + 12, 18, 9);
    g.lineStyle(4, COLORS.panelEdge, 1).strokeRoundedRect(trackX - 6, trackY - 9, trackW + 12, 18, 9);
    this.progressBar.x = trackX;
    this.progressBar.width = trackW;
    this.progressSub = this.add
      .container(trackX, trackY - 6, [
        this.add.image(0, 0, 'sub_back'),
        this.add.image(0, 0, 'explorer'),
        this.add.image(0, 0, 'sub_front'),
      ])
      .setScale(0.14);
  }

  private createControlsHint(): void {
    const w = 940;
    const h = 92;
    const x = 36;
    const y = GAME_HEIGHT - 30 - h;
    createPanel(this, x, y, w, h).setOrigin(0, 0);
    const cy = y + h / 2;
    let cx = x + 34;
    const label = (t: string): void => {
      const txt = this.add.text(cx, cy, t, textStyle(26, '700')).setOrigin(0, 0.5);
      cx += txt.width + 30;
    };
    this.add.text(cx, cy, 'WASD / Oklar', textStyle(26, '800', '#a3283a')).setOrigin(0, 0.5);
    cx += 182;
    label('Hareket');
    this.add.image(cx + 52, cy, 'key_space').setDisplaySize(104, 46);
    this.add.text(cx + 52, cy - 1, 'Boşluk', textStyle(20, '800')).setOrigin(0.5);
    cx += 116;
    label('Tara');
    this.add.image(cx + 24, cy, 'key_e').setDisplaySize(48, 48);
    cx += 58;
    label('Etkileşim');
    this.add.text(cx, cy, 'ESC', textStyle(26, '800', '#a3283a')).setOrigin(0, 0.5);
    cx += 62;
    label('Duraklat');
  }

  /** Referanstaki numaralı altyazılar gibi: rozet + krem panel. Oyuncu hareket edince solar. */
  showCaption(number: string, text: string): void {
    this.caption?.destroy();
    const w = 980;
    const h = 150;
    const x = (GAME_WIDTH - w) / 2;
    const y = 170;
    const panel = createPanel(this, 0, 0, w, h).setOrigin(0, 0);
    const badge = createBadge(this, 70, h / 2, number, 76);
    const txt = this.add.text(130, h / 2, text, textStyle(34, '700')).setOrigin(0, 0.5).setLineSpacing(4);
    this.caption = this.add.container(x, y, [panel, badge, txt]).setAlpha(0);
    this.tweens.add({ targets: this.caption, alpha: 1, y: y + 10, duration: 500, ease: 'Sine.easeOut' });
    this.time.delayedCall(9000, () => this.hideCaption());
  }

  private hideCaption(): void {
    const c = this.caption;
    if (!c || c.getData('hiding')) return;
    c.setData('hiding', true);
    this.tweens.add({
      targets: c,
      alpha: 0,
      y: c.y - 12,
      duration: 600,
      delay: 1800,
      ease: 'Sine.easeIn',
      onComplete: () => c.destroy(),
    });
    this.caption = undefined;
  }

  private togglePause(): void {
    const world = this.scene.get('Bloodstream');
    if (this.pauseLayer) {
      this.pauseLayer.destroy();
      this.pauseLayer = undefined;
      this.scene.resume('Bloodstream');
      world.events.emit('resumed');
      return;
    }
    this.scene.pause('Bloodstream');
    const dim = this.add.rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, COLORS.maroon, 0.6).setOrigin(0, 0);
    dim.setInteractive(); // Arkadaki tıklamaları yut.
    const w = 720;
    const h = 420;
    const px = (GAME_WIDTH - w) / 2;
    const py = (GAME_HEIGHT - h) / 2;
    const panel = createPanel(this, px, py, w, h).setOrigin(0, 0);
    const title = this.add
      .text(GAME_WIDTH / 2, py + 84, 'Oyun Duraklatıldı', textStyle(56, '800'))
      .setOrigin(0.5);
    const resume = this.button(GAME_WIDTH / 2, py + 210, 'Devam Et', () => this.togglePause());
    const restart = this.button(GAME_WIDTH / 2, py + 320, 'Baştan Başla', () => {
      this.pauseLayer?.destroy();
      this.pauseLayer = undefined;
      this.scene.stop('Bloodstream');
      this.scene.start('Bloodstream');
    });
    this.pauseLayer = this.add.container(0, 0, [dim, panel, title, resume, restart]).setDepth(100);
  }

  private button(x: number, y: number, label: string, onClick: () => void): Phaser.GameObjects.Container {
    const w = 380;
    const h = 86;
    const bg = this.add.graphics();
    const draw = (hover: boolean): void => {
      bg.clear();
      bg.fillStyle(0x7e1626, 1).fillRoundedRect(-w / 2, -h / 2 + 7, w, h, 30);
      bg.fillStyle(hover ? 0xe0405a : COLORS.accent, 1).fillRoundedRect(-w / 2, -h / 2, w, h, 30);
      bg.lineStyle(5, COLORS.panelEdge, 1).strokeRoundedRect(-w / 2, -h / 2, w, h + 7, 30);
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
