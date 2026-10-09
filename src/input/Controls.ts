import Phaser from 'phaser';

/**
 * WASD / ok tuşları ile hareket, E etkileşim, Boşluk tarama.
 * ESC (duraklatma) HUD sahnesinde dinlenir, çünkü duraklatılan sahnenin update'i çalışmaz.
 *
 * E ve Boşluk olay dinleyicisiyle kuyruğa alınır: kare başına JustDown yoklaması, basma ve
 * bırakma aynı karede işlendiğinde (yavaş cihazda kısa bir dokunuş) basışı kaçırır.
 */
export class Controls {
  private interactQueued = false;
  private scanQueued = false;

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
    this.keys.E.on('down', () => (this.interactQueued = true));
    this.keys.SPACE.on('down', () => (this.scanQueued = true));
  }

  /** -1…1 yatay ve dikey yön (ekran koordinatı: aşağı pozitif). */
  get axis(): { x: number; y: number } {
    const k = this.keys;
    const x = (k.D.isDown || k.RIGHT.isDown ? 1 : 0) - (k.A.isDown || k.LEFT.isDown ? 1 : 0);
    const y = (k.S.isDown || k.DOWN.isDown ? 1 : 0) - (k.W.isDown || k.UP.isDown ? 1 : 0);
    return { x, y };
  }

  /** Son okumadan beri E'ye basıldı mı? (Okuyunca sıfırlanır.) */
  consumeInteract(): boolean {
    const v = this.interactQueued;
    this.interactQueued = false;
    return v;
  }

  /** Son okumadan beri Boşluk'a basıldı mı? (Okuyunca sıfırlanır.) */
  consumeScan(): boolean {
    const v = this.scanQueued;
    this.scanQueued = false;
    return v;
  }

  /** Duraklatmadan dönünce takılı kalmış tuş durumlarını ve bekleyen basışları temizler. */
  reset(): void {
    for (const key of Object.values(this.keys)) key.reset();
    this.interactQueued = false;
    this.scanQueued = false;
  }
}
