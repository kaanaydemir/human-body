// Oyunu başsız Chromium'da açar, isteğe bağlı tuşlara basar ve ekran görüntüsü alır.
// Konsol hatalarını da raporlar ("çalışma zamanı hatası yok" kontrolü için).
//
// Kullanım:
//   node tools/screenshot.mjs --out tools/out/shot.png [--params "x=3000&debug=1"]
//        [--keys "ArrowRight:1500,ArrowUp:400"] [--wait 1500] [--shots 3 --interval 700]
//        [--width 1920 --height 1080]
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
const out = args.out ?? 'tools/out/shot.png';
const width = Number(args.width ?? 1920);
const height = Number(args.height ?? 1080);
const shots = Number(args.shots ?? 1);
const interval = Number(args.interval ?? 600);
const wait = Number(args.wait ?? 1200);

const server = await createServer({ logLevel: 'error', server: { port: 0, host: '127.0.0.1' } });
await server.listen();
const address = server.httpServer.address();
const url = `http://127.0.0.1:${address.port}/?${args.params ?? ''}`;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width, height } });
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => {
  if (m.type() === 'error' || m.type() === 'warning') errors.push(`${m.type()}: ${m.text()}`);
});

try {
  await page.goto(url);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(wait);

  for (const step of (args.keys ?? '').split(',').filter(Boolean)) {
    const [key, ms] = step.split(':');
    if (key === 'wait') {
      await page.waitForTimeout(Number(ms));
      continue;
    }
    await page.keyboard.down(key);
    await page.waitForTimeout(Number(ms ?? 300));
    await page.keyboard.up(key);
  }

  await mkdir(path.dirname(out), { recursive: true });
  for (let i = 0; i < shots; i++) {
    const file = shots === 1 ? out : out.replace(/\.png$/, `_${i + 1}.png`);
    await page.screenshot({ path: file });
    console.log('ekran görüntüsü:', file);
    if (i < shots - 1) await page.waitForTimeout(interval);
  }
  const fps = await page.evaluate(() => Math.round(window.__game?.loop?.actualFps ?? 0));
  console.log('FPS (başsız, yazılımsal WebGL):', fps);
} finally {
  if (errors.length) {
    console.log('KONSOL HATALARI/UYARILARI:');
    for (const e of errors) console.log('  ' + e);
  } else {
    console.log('Konsol hatası yok.');
  }
  await browser.close();
  await server.close();
}
