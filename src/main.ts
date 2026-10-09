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
  // Phaser açılışta 120 kare boyunca zaman adımını 16,6 ms ile sınırlar; yavaş cihazlarda bu, ilk
  // saniyelerin ağır çekim oynaması demek. 200 ms'yi aşan sıçramalar zaten ayrıca kırpılıyor.
  fps: { target: 60, panicMax: 10 },
  render: {
    antialias: true,
    roundPixels: false,
    powerPreference: 'high-performance',
  },
  scene: [BootScene, BloodstreamScene, HudScene],
});

// Otomatik ekran görüntüsü / test araçları için.
(window as unknown as { __game: Phaser.Game }).__game = game;
