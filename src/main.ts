import Phaser from 'phaser';
import '@fontsource/baloo-2/500.css';
import '@fontsource/baloo-2/700.css';
import '@fontsource/baloo-2/800.css';
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
  fps: { target: 60 },
  render: {
    antialias: true,
    roundPixels: false,
    powerPreference: 'high-performance',
  },
  scene: [BootScene, BloodstreamScene, HudScene],
});

// Otomatik ekran görüntüsü / test araçları için.
(window as unknown as { __game: Phaser.Game }).__game = game;
