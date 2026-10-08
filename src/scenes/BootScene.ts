import Phaser from 'phaser';
import { BLOODSTREAM_ASSETS } from '../assets';
import { COLORS, FONT_FAMILY, GAME_HEIGHT, GAME_WIDTH } from '../config';

/**
 * Yazı tipini ve SVG varlıklarını yükler, sonra damar sahnesini başlatır.
 * Yükleme hatası olursa sessizce yer tutucu koymak yerine ekranda açıkça gösterir.
 */
export class BootScene extends Phaser.Scene {
  private failed: string[] = [];

  constructor() {
    super('Boot');
  }

  preload(): void {
    const cx = GAME_WIDTH / 2;
    const cy = GAME_HEIGHT / 2;

    const title = this.add
      .text(cx, cy - 90, 'Vücut Macerası', {
        fontFamily: FONT_FAMILY,
        fontSize: '84px',
        fontStyle: '800',
        color: '#f9e9d0',
      })
      .setOrigin(0.5);
    title.setShadow(0, 6, '#1a0609', 0, false, true);

    const barW = 640;
    const barH = 34;
    const frame = this.add.graphics();
    frame.fillStyle(COLORS.panelFill, 1);
    frame.fillRoundedRect(cx - barW / 2 - 8, cy + 10 - 8, barW + 16, barH + 16, 24);
    frame.lineStyle(5, COLORS.panelEdge, 1);
    frame.strokeRoundedRect(cx - barW / 2 - 8, cy + 10 - 8, barW + 16, barH + 16, 24);
    const fill = this.add.graphics();
    const label = this.add
      .text(cx, cy + 100, 'Hazırlanıyor…', {
        fontFamily: FONT_FAMILY,
        fontSize: '34px',
        fontStyle: '700',
        color: '#f3cdb8',
      })
      .setOrigin(0.5);

    this.load.on(Phaser.Loader.Events.PROGRESS, (p: number) => {
      fill.clear();
      fill.fillStyle(COLORS.accent, 1);
      fill.fillRoundedRect(cx - barW / 2, cy + 10, Math.max(barH, barW * p), barH, 17);
      label.setText(`Küçülme cihazı hazırlanıyor… %${Math.round(p * 100)}`);
    });
    this.load.on(Phaser.Loader.Events.FILE_LOAD_ERROR, (file: Phaser.Loader.File) => {
      this.failed.push(file.url as string);
    });

    for (const a of BLOODSTREAM_ASSETS) {
      this.load.svg(a.key, a.url, { width: a.width, height: a.height });
    }
  }

  async create(): Promise<void> {
    if (this.failed.length > 0) {
      this.showError(this.failed);
      return;
    }
    // Türkçe karakterler (ş, ğ, ı, İ) latin-ext alt kümesinde; metin oluşturmadan önce yüklenmeli.
    try {
      await Promise.all([
        document.fonts.load(`500 32px "Baloo 2"`, 'ŞşĞğİıÇçÖöÜü'),
        document.fonts.load(`700 32px "Baloo 2"`, 'ŞşĞğİıÇçÖöÜü'),
        document.fonts.load(`800 32px "Baloo 2"`, 'ŞşĞğİıÇçÖöÜü'),
      ]);
    } catch {
      // Yazı tipi yüklenemezse yedek yazı tipiyle devam edilir.
    }
    this.scene.start('Bloodstream');
  }

  private showError(urls: string[]): void {
    this.children.removeAll(true);
    this.add
      .text(
        GAME_WIDTH / 2,
        GAME_HEIGHT / 2,
        ['Bazı çizimler yüklenemedi:', ...urls].join('\n'),
        { fontFamily: FONT_FAMILY, fontSize: '30px', color: '#f9e9d0', align: 'center' },
      )
      .setOrigin(0.5);
    console.error('Yüklenemeyen varlıklar:', urls);
  }
}
