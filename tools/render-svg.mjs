// Bir SVG dosyasını Chromium ile PNG'ye rasterize eder.
// Kullanım: node tools/render-svg.mjs <girdi.svg> <çıktı.png> [ölçek=1] [arkaplan=transparent|checker|#rrggbb]
// Sanat varlıklarını oyuna koymadan önce gözle kontrol etmek içindir.
import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const [, , input, output, scaleArg = '1', bg = 'checker'] = process.argv;
if (!input || !output) {
  console.error('Kullanım: node tools/render-svg.mjs <girdi.svg> <çıktı.png> [ölçek] [arkaplan]');
  process.exit(1);
}
const svg = await readFile(input, 'utf8');
const vb = svg.match(/viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"/);
if (!vb) {
  console.error('SVG kök öğesinde viewBox bulunamadı: ' + input);
  process.exit(1);
}
const scale = Number(scaleArg);
const w = Math.round(Number(vb[3]) * scale);
const h = Math.round(Number(vb[4]) * scale);
const background =
  bg === 'transparent'
    ? 'transparent'
    : bg === 'checker'
      ? 'repeating-conic-gradient(#ddd 0% 25%, #fff 0% 50%) 50% / 32px 32px'
      : bg;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: w, height: h } });
const dataUrl = 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
await page.setContent(
  `<html><body style="margin:0;background:${background}"><img id="i" src="${dataUrl}" width="${w}" height="${h}" style="display:block"></body></html>`,
);
await page.waitForFunction(() => document.getElementById('i').complete);
const ok = await page.evaluate(() => document.getElementById('i').naturalWidth > 0);
if (!ok) {
  console.error('SVG yüklenemedi (bozuk XML olabilir): ' + input);
  await browser.close();
  process.exit(2);
}
await page.screenshot({ path: output, omitBackground: bg === 'transparent' });
await browser.close();
console.log(`${path.basename(input)} -> ${output} (${w}x${h})`);
