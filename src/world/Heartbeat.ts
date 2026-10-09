/**
 * Kalp atışı ritmi ("lup-dup"). Duvar nabzı, kan akışı hızlanması ve ışık titreşimi
 * aynı ritme bağlı olsun diye tek bir zamanlayıcıdan okunur.
 */
export class Heartbeat {
  /** Bir atışın süresi, saniye (varsayılan 64 atım/dk). */
  readonly period: number;
  private t = 0;

  constructor(bpm = 64) {
    this.period = 60 / bpm;
  }

  update(dtSeconds: number): void {
    this.t = (this.t + dtSeconds) % this.period;
  }

  /** 0…1 arası nabız şiddeti: güçlü "lup", ardından daha zayıf "dup", sonra dinlenme. */
  get pulse(): number {
    const lub = this.bump(this.t, 0, 0.16);
    const dub = 0.6 * this.bump(this.t, 0.26, 0.14);
    return Math.min(1, lub + dub);
  }

  /** Atıştan sonra yavaşça sönen akış dalgası (kan akışı hızlanması için). */
  get surge(): number {
    const x = this.t / this.period;
    return Math.exp(-x * 4.5);
  }

  /** Yumuşak yükselip inen tek bir vuruş eğrisi. */
  private bump(t: number, start: number, length: number): number {
    const x = (t - start) / length;
    if (x < 0 || x > 1) return 0;
    return Math.sin(Math.PI * x) ** 2;
  }
}
