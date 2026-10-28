/* 线上(线上站) vs 本地(127.0.0.1:8140) 同区域截图 + 元素框选坐标
   输出到 ../../reports/20261028-compare/raw/ 与 rects.json */
const p = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const OUT = path.resolve(__dirname, '..', '..', 'reports', '20261028-compare');
const RAW = path.join(OUT, 'raw');
const SIDES = {
  live: 'https://prompt.qqsrc.com/',
  local: 'http://127.0.0.1:8140/',
};

// marks: 需要在图里画红框的元素选择器（找不到就跳过）
const ITEMS = [
  {
    id: '01-hero-cta', page: 'index.html', pad: 22, minH: 90,
    cropSel: { live: '.hero-cta', local: '.hero-cta' },
    marks: {
      live: ['.hero-cta a[href*="categories.html"]'],
      local: ['.hero-cta a'],
    },
  },
  {
    id: '02-hero-stats', page: 'index.html', pad: 24, minH: 110,
    marks: { live: ['.hero-stats'], local: ['.hero-stats'] },
  },
  {
    id: '03-hero-lead', page: 'index.html', pad: 20, minH: 80,
    marks: { live: ['.hero .lead'], local: ['.hero .lead'] },
  },
  {
    id: '04-footer', page: 'index.html', pad: 22, minH: 120,
    cropSel: { live: '.sx-footer .foot-col', local: '.sx-footer .foot-col' },
    marks: {
      live: ['.sx-footer .foot-col a[href*="categories"]', '.sx-footer .foot-col a[href*="search"]'],
      local: [],
    },
  },
  {
    id: '05-rail', page: 'gallery.html', pad: 18, minH: 160,
    cropSel: { live: '#filterRail', local: '#filterRail' },
    marks: {
      live: ['#filterGroup .maj:nth-child(1)', '#filterGroup .maj:nth-child(2)'],
      local: ['#filterGroup .maj.multi', '#filterGroup .maj.leaf'],
    },
  },
  {
    id: '06-card', page: 'gallery.html', pad: 18, minH: 200,
    // 本地用「多图」分类，保证第一张卡一定带角标；线上没有该分类，用普通画廊首卡
    pageBySide: { local: 'gallery.html?cat=' + encodeURIComponent('多图') },
    cropSel: { live: '#grid .card', local: '#grid .card' },
    marks: { live: [], local: ['.multi-badge'] },
  },
  {
    id: '07-detail', page: 'detail.html?id=30005', pad: 16, minH: 300,
    cropSel: { live: '.detail-panel', local: '.detail-panel' },
    marks: {
      live: ['.detail-body .act-bar', '.detail-body .note-box'],
      local: ['.detail-body .lb-actions', '.detail-body > .lb-prompt'],
    },
  },
  {
    id: '08-categories', page: 'categories.html', pad: 0, minH: 420, viewport: true,
    marks: { live: ['.page-head'], local: ['.err'] },
  },
];

function union(rects) {
  const xs = [], ys = [], xe = [], ye = [];
  rects.forEach(r => { xs.push(r.x); ys.push(r.y); xe.push(r.x + r.w); ye.push(r.y + r.h); });
  return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xe) - Math.min(...xs), h: Math.max(...ye) - Math.min(...ys) };
}

(async () => {
  fs.mkdirSync(RAW, { recursive: true });
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });
  const out = {};

  for (const [side, base] of Object.entries(SIDES)) {
    out[side] = {};
    for (const it of ITEMS) {
      const pg = await b.newPage();
      const errs = [];
      pg.on('pageerror', e => errs.push(String(e)));
      await pg.setViewport({ width: 1440, height: 1000, deviceScaleFactor: 2 });
      const page = (it.pageBySide && it.pageBySide[side]) || it.page;
      const url = base + page;
      let status = 0;
      try {
        const resp = await pg.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
        status = resp ? resp.status() : 0;
      } catch (e) {
        out[side][it.id] = { error: String(e).slice(0, 80) };
        await pg.close();
        continue;
      }
      await new Promise(r => setTimeout(r, 2600));

      const sels = (it.marks[side] || []);
      const rects = await pg.evaluate(sels => sels.map(s => {
        const el = document.querySelector(s);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height };
      }), sels);
      let cropRect = null;
      if (it.cropSel && it.cropSel[side]) {
        cropRect = await pg.evaluate(s => {
          const el = document.querySelector(s); if (!el) return null;
          const r = el.getBoundingClientRect();
          return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height };
        }, it.cropSel[side]);
      }

      let clip;
      const found = cropRect ? [cropRect] : rects.filter(Boolean);
      if (it.viewport) {
        clip = { x: 0, y: 0, width: 1440, height: 520 };
      } else if (found.length) {
        const u = union(found);
        clip = {
          x: Math.max(0, Math.round(u.x - it.pad)),
          y: Math.max(0, Math.round(u.y - it.pad)),
          width: Math.round(u.w + it.pad * 2),
          height: Math.max(it.minH || 0, Math.round(u.h + it.pad * 2)),
        };
      } else {
        clip = { x: 0, y: 0, width: 1440, height: 400 };
      }

      const file = path.join(RAW, it.id + '-' + side + '.png');
      await pg.screenshot({ path: file, clip, captureBeyondViewport: true });
      out[side][it.id] = {
        file: 'raw/' + it.id + '-' + side + '.png',
        status,
        clip,
        marks: rects.map((r, i) => r ? {
          label: sels[i],
          x: Math.round(r.x - clip.x), y: Math.round(r.y - clip.y),
          w: Math.round(r.w), h: Math.round(r.h),
        } : null).filter(Boolean),
        errs: errs.slice(0, 2),
      };
      await pg.close();
      console.log(side, it.id, '→', status, JSON.stringify(clip));
    }
  }

  await b.close();
  fs.writeFileSync(path.join(OUT, 'rects.json'), JSON.stringify(out, null, 1), 'utf8');
  console.log('done');
})();
