import Phaser from 'phaser';
// Türkçe için yalnızca latin + latin-ext alt kümeleri gerekir (ş, ğ, ı, İ latin-ext'te).
import '@fontsource/baloo-2/latin-500.css';
import '@fontsource/baloo-2/latin-ext-500.css';
import '@fontsource/baloo-2/latin-700.css';
import '@fontsource/baloo-2/latin-ext-700.css';
import '@fontsource/baloo-2/latin-800.css';
import '@fontsource/baloo-2/latin-ext-800.css';
import '@fontsource/arimo/latin-400.css';
import '@fontsource/arimo/latin-ext-400.css';
import '@fontsource/arimo/latin-700.css';
import '@fontsource/arimo/latin-ext-700.css';
import { GAME_HEIGHT, GAME_WIDTH } from './config';
import { BootScene } from './scenes/BootScene';
import { BloodstreamScene } from './scenes/BloodstreamScene';
import { HudScene } from './scenes/HudScene';

/**
 * Yazı tipleri oyun başlamadan yüklenir: yükleme ekranı dahil hiçbir metin yedek yazı tipiyle
 * çizilmesin. Türkçe harfler (ş, ğ, ı, İ) latin-ext alt kümesinde olduğundan örnek metinle istenir.
 */
async function loadFonts(): Promise<void> {
  const sample = 'ŞşĞğİıÇçÖöÜü';
  const faces = ['500 32px "Baloo 2"', '700 32px "Baloo 2"', '800 32px "Baloo 2"', '400 32px "Arimo"', '700 32px "Arimo"'];
  try {
    await Promise.all(faces.map((f) => document.fonts.load(f, sample)));
  } catch {
    // Yazı tipi yüklenemezse yedek yazı tipiyle devam edilir.
  }
}

await loadFonts();

const game = new Phaser.Game({
  type: Phaser.WEBGL,
  parent: 'game',
  width: GAME_WIDTH,
  height: GAME_HEIGHT,
  backgroundColor: '#3a0c14',
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  // Phaser açılışta panicMax kare boyunca zaman adımını 16,6 ms ile sınırlar; varsayılan 120 kare,
  // yavaş cihazlarda ilk saniyelerin ağır çekim oynaması demek. 1000/min = 250 ms'yi aşan kareler
  // (sekme değişimi vb.) Phaser tarafından önceki bir kare süresiyle değiştirilir.
  fps: { target: 60, min: 4, panicMax: 10 },
  render: {
    antialias: true,
    roundPixels: false,
    powerPreference: 'high-performance',
  },
  scene: [BootScene, BloodstreamScene, HudScene],
});

// Otomatik ekran görüntüsü / test araçları için.
(window as unknown as { __game: Phaser.Game }).__game = game;
