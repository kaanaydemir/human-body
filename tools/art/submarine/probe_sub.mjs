// Verification probe for the submarine art (does not change src/): opens the game headless, optionally applies
// the runtime settings this art is authored for, drives the keys and takes a screenshot.
//
//   node tools/art/submarine/probe_sub.mjs --out <png> [--params "x=3000&y=450"] [--keys "ArrowRight:1500"]
//        [--mode current|recommended] [--hud 0|1] [--freeze 1]
//
// --mode current      : the game exactly as src/ is today (light ADD + tint 0xffa848 at 0.8, jet alpha 0.25-0.9,
//                       fx/bubble particles).
// --mode recommended  : what the lead is asked to put into src/objects/Submarine.ts:
//                       light NORMAL blend, no tint, alpha 0.95 (flicker kept); jet alpha 0.5 + 0.45*thrust;
//                       jet bubbles from player/jet_bubble.svg (16-28 px, +-70 px fan, 1.2-2 s, alpha >= 0.8),
//                       emitted in world space (emitter at 0,0; the emit point follows the jet anchor).
import { chromium } from 'playwright';
import { createServer } from 'vite';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, cur, i, arr) => {
    if (cur.startsWith('--')) acc.push([cur.slice(2), arr[i + 1]?.startsWith('--') ? 'true' : arr[i + 1]]);
    return acc;
  }, []),
);
const out = args.out ?? 'tools/out/submarine/probe.png';
const mode = args.mode ?? 'recommended';
const server = await createServer({ logLevel: 'error', server: { port: 0, host: '127.0.0.1' } });
await server.listen();
const url = `http://127.0.0.1:${server.httpServer.address().port}/?${args.params ?? ''}`;
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => {
  if (m.type() === 'error') errors.push(`console: ${m.text()}`);
});
try {
  await page.goto(url);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(Number(args.wait ?? 1200));
  const info = await page.evaluate(async ({ mode, hud }) => {
    const g = window.__game;
    const s = g.scene.getScene('Bloodstream');
    if (hud === '0') g.scene.getScene('Hud').cameras.main.setVisible(false);
    // the 700 ms intro fade crawls at ~6 FPS in headless software WebGL; it is not part of the art
    s.cameras.main.resetFX();
    const sub = s.children.list.find((o) => o.type === 'Container' && o.depth === 50);
    if (!sub) return 'no sub';
    if (mode !== 'recommended') return 'current';
    await new Promise((resolve) => {
      s.load.svg('jet_bubble', 'assets/svg/player/jet_bubble.svg', { width: 32, height: 32 });
      s.load.once('complete', resolve);
      s.load.start();
    });
    // re-set the alphas right after Submarine.step() each frame (the Container renderer itself calls
    // child.setAlpha while drawing, so setAlpha must not be overridden)
    sub.light.setBlendMode(0).clearTint(); // 0 = Phaser.BlendModes.NORMAL
    const step = sub.step.bind(sub);
    sub.step = (dt, input) => {
      step(dt, input);
      sub.light.setAlpha(sub.light.alpha * (0.95 / 0.8)); // LIGHT_ALPHA 0.8 -> 0.95, flicker kept
      sub.jet.setAlpha(0.5 + 0.45 * sub.thrust);
    };
    const em = s.add
      .particles(0, 0, 'jet_bubble', {
        lifespan: { min: 1200, max: 2000 },
        speedX: { min: -150, max: -50 },
        speedY: { min: -60, max: 60 },
        scale: { min: 0.5, max: 0.875 },
        alpha: { start: 1, end: 0, ease: 'Quad.easeIn' },
        rotate: { min: -20, max: 20 },
        gravityY: -15,
        frequency: 45,
        emitting: false,
      })
      .setDepth(49);
    // world-space trail: the emitter stays at (0,0); Submarine.ts moves the emit point, not the emitter
    em.setPosition = (x, y) => {
      em.particleX = x;
      em.particleY = y;
      return em;
    };
    sub.bubbles.stop();
    sub.bubbles.setVisible(false);
    sub.bubbles = em;
    return 'recommended';
  }, { mode, hud: args.hud ?? '1' });
  await page.waitForTimeout(1000); // let a few frames run with the patched step
  for (const step of (args.keys ?? '').split(',').filter(Boolean)) {
    const [key, ms] = step.split(':');
    if (key === 'wait') {
      await page.waitForTimeout(Number(ms));
      continue;
    }
    await page.keyboard.down(key);
    await page.waitForTimeout(Number(ms ?? 300));
    if (args.hold !== key) await page.keyboard.up(key);
  }
  await page.evaluate((freeze) => {
    if (freeze === '1') window.__game.scene.getScene('Bloodstream').scene.pause();
  }, args.freeze ?? '1');
  // let the paused scene render a few frames so the camera and the drawn sub agree with the numbers below
  await page.waitForTimeout(1500);
  const pos = await page.evaluate(() => {
    const s = window.__game.scene.getScene('Bloodstream');
    const sub = s.children.list.find((o) => o.type === 'Container' && o.depth === 50);
    const cam = s.cameras.main;
    return {
      x: sub.x - cam.scrollX,
      y: sub.y - cam.scrollY,
      rot: sub.rotation,
      bubbles: sub.bubbles.getAliveParticleCount(),
      bubbleTex: sub.bubbles.texture.key,
      jetAlpha: sub.jet.alpha,
      thrust: sub.thrust,
      state: sub.subState,
      lightAlpha: sub.light.alpha,
      lightBlend: sub.light.blendMode,
      delta: window.__game.loop.delta,
      fps: window.__game.loop.actualFps,
      subX: sub.x,
      sx: sub.scaleX,
      sy: sub.scaleY,
    };
  });
  await mkdir(path.dirname(out), { recursive: true });
  await page.waitForTimeout(300);
  await page.screenshot({ path: out, timeout: 240000 });
  console.log(JSON.stringify({ out, mode: info, sub: pos, errors }));
} finally {
  await browser.close();
  await server.close();
}
