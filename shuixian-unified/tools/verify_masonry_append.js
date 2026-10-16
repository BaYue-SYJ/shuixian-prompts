// 回归：画廊「显示更多」必须横向铺开（新卡分布到全部列，而非只堆右边两列）
// 运行：NODE_PATH=C:/Users/lianxiang/.workbuddy/binaries/node/workspace/node_modules node verify_masonry_append.js
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.SX_URL || 'http://127.0.0.1:8140';

let pass = 0, fail = 0;
const ok = (name, cond, extra) => { if (cond) { pass++; console.log('  ✅', name); } else { fail++; console.log('  ❌', name, extra != null ? '→ ' + JSON.stringify(extra) : ''); } };

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto(BASE + '/gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });

  // 等瀑布流列容器建好
  await page.waitForSelector('#grid .m-col', { timeout: 15000 });
  await page.waitForFunction(() => document.querySelectorAll('#grid .card').length >= 24, { timeout: 15000 });
  await new Promise(r => setTimeout(r, 400));

  const snap = () => page.evaluate(() => {
    const grid = document.querySelector('#grid');
    const g = grid.getBoundingClientRect();
    const cards = [...grid.querySelectorAll('.card')];
    const xs = [...new Set(cards.map(c => Math.round(c.getBoundingClientRect().left - g.left)))].sort((a, b) => a - b);
    return cards.map(c => {
      const r = c.getBoundingClientRect();
      return { id: c.dataset.id, col: xs.indexOf(Math.round(r.left - g.left)), y: Math.round(r.top - g.top) };
    });
  });

  const a = await snap();                 // n=24
  await page.evaluate(() => document.querySelector('#showMore').click());
  await new Promise(r => setTimeout(r, 700));
  const b = await snap();                 // n=48

  const colCount = (list) => [...new Set(list.map(o => o.col))].length;
  const perCol = (list) => { const m = {}; list.forEach(o => m[o.col] = (m[o.col] || 0) + 1); return m; };

  console.log('n=24: cards=%d cols=%d dist=%j', a.length, colCount(a), perCol(a));
  console.log('n=48: cards=%d cols=%d dist=%j', b.length, colCount(b), perCol(b));

  const added = b.filter(o => !new Set(a.map(x => x.id)).has(o.id));
  const addedPerCol = perCol(added);
  console.log('新增 %d 张 → 各列新增：%j', added.length, addedPerCol);

  console.log('\n断言：');
  ok('n=24 卡片数 = 24', a.length === 24, a.length);
  ok('n=48 卡片数 = 48', b.length === 48, b.length);
  ok('列数 = 4（1440 视口）', colCount(b) === 4, colCount(b));
  ok('24→48 实际新增 24 张', added.length === 24, added.length);
  ok('新增卡遍布全部 4 列', Object.keys(addedPerCol).length === 4, addedPerCol);
  // 核心回归：旧 bug 是新增只落 col2/col3；这里要求每列都新增 ≥1
  const cols = [0, 1, 2, 3];
  ok('最左列(col0)也有新增卡', (addedPerCol[0] || 0) >= 1, addedPerCol);
  ok('每列新增均 ≥1（非只堆右边两列）', cols.every(c => (addedPerCol[c] || 0) >= 1), addedPerCol);
  ok('无控制台/页面错误', errors.length === 0, errors.slice(0, 3));

  await browser.close();
  console.log('\n结果：%d PASS / %d FAIL', pass, fail);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('ERR', e); process.exit(2); });
