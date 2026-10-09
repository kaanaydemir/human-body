import Phaser from 'phaser';

/** Dokunmatik yönlendirmede, parmak denizaltıya bu kadar yakınsa hareket yok (px). */
const TOUCH_DEADZONE = 40;
/** Parmak bu uzaklıkta olunca tam güç (px). */
const TOUCH_FULL = { x: 220, y: 160 };
/** Bu süreden kısa ve az kayan dokunuş "tara" sayılır. */
const TAP_MS = 250;
const TAP_SLOP = 24;

/**
 * WASD / ok tuşları ile hareket, E etkileşim, Boşluk tarama.
 * Dokunmatik ekranda: parmağı sürüklemek denizaltıyı o yöne götürür, kısa dokunuş tarar.
 * ESC (duraklatma) HUD sahnesinde dinlenir, çünkü duraklatılan sahnenin update'i çalışmaz.
 *
 * E ve Boşluk olay dinleyicisiyle kuyruğa alınır: kare başına JustDown yoklaması, basma ve
 * bırakma aynı karede işlendiğinde (yavaş cihazda kısa bir dokunuş) basışı kaçırır.
 */
export class Controls {
  private interactQueued = false;
  private scanQueued = false;
  private touch?: Phaser.Input.Pointer;
  private touchStart = { x: 0, y: 0 };

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

    scene.input.on(Phaser.Input.Events.POINTER_DOWN, (p: Phaser.Input.Pointer) => {
      if (!p.wasTouch) return;
      this.touch = p;
      this.touchStart = { x: p.x, y: p.y };
    });
    scene.input.on(Phaser.Input.Events.POINTER_UP, (p: Phaser.Input.Pointer) => {
      if (p !== this.touch) return;
      const moved = Phaser.Math.Distance.Between(p.x, p.y, this.touchStart.x, this.touchStart.y);
      // Süre oyun saatinden değil dokunuşun kendi zaman damgalarından ölçülür (yavaş karede de doğru).
      if (p.upTime - p.downTime < TAP_MS && moved < TAP_SLOP) this.scanQueued = true;
      this.touch = undefined;
    });
  }

  /**
   * -1…1 yatay ve dikey yön (ekran koordinatı: aşağı pozitif). Klavye basılıysa o geçerlidir;
   * değilse ve ekrana dokunuluyorsa parmağın denizaltıya göre yönü (uzaklığa göre kademeli).
   * @param subScreen denizaltının ekrandaki konumu
   */
  axis(subScreen: { x: number; y: number }): { x: number; y: number } {
    const k = this.keys;
    const x = (k.D.isDown || k.RIGHT.isDown ? 1 : 0) - (k.A.isDown || k.LEFT.isDown ? 1 : 0);
    const y = (k.S.isDown || k.DOWN.isDown ? 1 : 0) - (k.W.isDown || k.UP.isDown ? 1 : 0);
    if (x !== 0 || y !== 0 || !this.touch?.isDown) return { x, y };
    const dx = this.touch.x - subScreen.x;
    const dy = this.touch.y - subScreen.y;
    if (Math.hypot(dx, dy) < TOUCH_DEADZONE) return { x: 0, y: 0 };
    return {
      x: Phaser.Math.Clamp(dx / TOUCH_FULL.x, -1, 1),
      y: Phaser.Math.Clamp(dy / TOUCH_FULL.y, -1, 1),
    };
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
    this.touch = undefined;
    this.interactQueued = false;
    this.scanQueued = false;
  }
}
