import Phaser from 'phaser';

/**
 * WASD / ok tuşları ile hareket, E etkileşim, Boşluk tarama.
 * ESC (duraklatma) HUD sahnesinde dinlenir, çünkü duraklatılan sahnenin update'i çalışmaz.
 */
export class Controls {
  private readonly keys: Record<
    'W' | 'A' | 'S' | 'D' | 'UP' | 'DOWN' | 'LEFT' | 'RIGHT' | 'E' | 'SPACE',
    Phaser.Input.Keyboard.Key
  >;

  constructor(scene: Phaser.Scene) {
    const kb = scene.input.keyboard;
    if (!kb) throw new Error('Klavye girişi kullanılamıyor');
    const K = Phaser.Input.Keyboard.KeyCodes;
    this.keys = kb.addKeys(
      {
        W: K.W,
        A: K.A,
        S: K.S,
        D: K.D,
        UP: K.UP,
        DOWN: K.DOWN,
        LEFT: K.LEFT,
        RIGHT: K.RIGHT,
        E: K.E,
        SPACE: K.SPACE,
      },
      true,
    ) as Controls['keys'];
  }

  /** -1…1 yatay ve dikey yön (ekran koordinatı: aşağı pozitif). */
  get axis(): { x: number; y: number } {
    const k = this.keys;
    const x = (k.D.isDown || k.RIGHT.isDown ? 1 : 0) - (k.A.isDown || k.LEFT.isDown ? 1 : 0);
    const y = (k.S.isDown || k.DOWN.isDown ? 1 : 0) - (k.W.isDown || k.UP.isDown ? 1 : 0);
    return { x, y };
  }

  get interactPressed(): boolean {
    return Phaser.Input.Keyboard.JustDown(this.keys.E);
  }

  get scanPressed(): boolean {
    return Phaser.Input.Keyboard.JustDown(this.keys.SPACE);
  }

  /** Duraklatmadan dönünce takılı kalmış tuş durumlarını temizler. */
  reset(): void {
    for (const key of Object.values(this.keys)) key.reset();
  }
}
