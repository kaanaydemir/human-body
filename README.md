# Vücut Macerası

Çocuklar için Türkçe, 2B bir keşif ve macera oyunu prototipi. Küçültülmüş bir kâşif minyatür
denizaltısıyla hastanın kan damarına girer. Alyuvarlar, akyuvarlar, vitaminler ve trombositlerle
birlikte vücuttaki sorunu araştırır. Klasik Avrupa eğitici çizgi dizilerinden esinlenmiştir. Tüm
karakterler ve çizimler bu proje için özgün olarak tasarlanmıştır.

Görsel yönün tek kaynağı `reference.png` dosyasıdır. Ayrıntılar `ART_DIRECTION.md` ve
`ASSET_MANIFEST.md` dosyalarında.

![Oyun ve referans karşılaştırması](docs/screenshots/stage2_vs_reference.jpg)

## Çalıştırma

```bash
npm install
npm run dev
```

Ardından tarayıcıda terminalde yazan adresi açın (varsayılan: http://localhost:5173).

| Tuş | İşlev |
|---|---|
| WASD / Ok tuşları | Denizaltıyı hareket ettir |
| E | Etkileşim / konuş |
| Boşluk | Tara |
| ESC | Duraklat |
| Fare | Diyalog ve bulmaca etkileşimleri |

Geliştirici parametreleri:
- `?debug=1` adres ekine eklenirse FPS ve konum gösterilir.
- `?x=5000` ile damarın belirli bir noktasından başlanır.

## Teknoloji

- TypeScript
- Phaser 3
- Vite
- 1920×1080 tasarım çözünürlüğü (ekrana göre ölçeklenir)
- Çizimler `public/assets/svg/` altında SVG dosyalarıdır ve yüklenirken rasterize edilir. Her çizim grubu
  `tools/art/<grup>/` altındaki bir Python üretici betiğiyle (yalnızca standart kütüphane) üretilir.
- Yazı tipleri pakete gömülüdür (`@fontsource`). Altyazılarda Arimo, başlık ve düğmelerde Baloo 2 kullanılır.

## Proje yapısı

```
src/
  main.ts                 Phaser oyun yapılandırması
  config.ts               Ölçüler, paralaks katsayıları, derinlikler, renkler
  assets.ts               Yüklenecek SVG listesi (ASSET_MANIFEST.md ile aynı boyutlar)
  scenes/BootScene.ts     Yükleme ekranı
  scenes/BloodstreamScene.ts  Ana damar sahnesi
  scenes/HudScene.ts      Görev paneli, ilerleme, kontrol ipuçları, duraklatma
  objects/Submarine.ts    Denizaltı: hareket, durumlar, animasyon
  world/Vessel.ts         Damar paralaks katmanları
  world/Heartbeat.ts      Kalp ritmi (duvar nabzı, akış dalgası)
  fx/BloodFlow.ts         Plazma zerreleri, akış çizgileri, serbest kan diskleri
  input/Controls.ts       Klavye girişi
  ui/Panel.ts             Krem panel, rozet ve yazı stilleri
tools/
  art/<grup>/             Çizim üreticileri (far, rear, ceiling, floor, foreground-fx, submarine, ui)
  render-svg.mjs          Bir SVG'yi PNG olarak önizler
  screenshot.mjs          Oyunu başsız tarayıcıda açıp ekran görüntüsü alır
  out/                    Geçici çıktılar (git'e girmez)
```

## Geliştirme araçları

```bash
npm run typecheck
npm run build
python3 -I tools/art/floor/gen_floor.py          # bir çizim grubunu yeniden üret
node tools/render-svg.mjs public/assets/svg/player/sub_front.svg tools/out/sub.png 1
node tools/screenshot.mjs --out tools/out/shot.png --params "debug=1" --keys "ArrowRight:1500"
```

`screenshot.mjs`, açılıştaki kamera kararması bitene kadar bekler. Başsız tarayıcı yazılımsal WebGL ile 5–8 FPS
çalışır; bu yalnızca test ortamına özgüdür.

## Ekran görüntüleri

| Başlangıç | Keşif | Zemine iniş |
|---|---|---|
| ![](docs/screenshots/stage2_start.jpg) | ![](docs/screenshots/stage2_hero.jpg) | ![](docs/screenshots/stage2_land.jpg) |

## Yol haritası

1. ☑ Sanat yönü belgesi ve varlık listesi
2. ☑ Ana damar sahnesi: kapalı damar, paralaks, denizaltı, kamera
3. ☐ Canlı hücreler: alyuvarlar, oksijen kapları, vitaminler, akyuvarlar
4. ☐ Diyalog ve alyuvar komutanı
5. ☐ Tıkanıklık bulmacası (tarama + onarım)
6. ☐ Hastane girişi, şırınga sahnesi, görev sonu
7. ☐ Cila ve tam test
