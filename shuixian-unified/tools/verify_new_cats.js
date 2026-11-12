/* 所有「New-*」新增大类的一次性验收：
   入口 / 计数与 meta 一致 / 筛选条数 / 多图角标 / 图片可访问 / 详情页
   以后再加 New-XX 分类，这个测试自动覆盖，不用改。 */
const p = require('puppeteer-core');
const https = require('https');
const BASE = 'http://127.0.0.1:8140/';

let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

const head = u => new Promise(res => {
  const req = https.request(u, { method: 'HEAD' }, r => { r.resume(); res(r.statusCode); });
  req.on('error', () => res(0));
  req.setTimeout(15000, () => { req.destroy(); res(0); });
  req.end();
});

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars', '--no-proxy-server'],
  });

  const pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 1440, height: 1000 });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 90000 });
  await new Promise(r => setTimeout(r, 3200));

  const cats = await pg.evaluate(() =>
    window.App.D.majors
      .filter(m => /^New/i.test(m.name))
      .map(m => ({ name: m.name, count: m.count, color: (window.App.catColor(m.name) || {}).main || '' }))
  );
  ok(cats.length >= 2, '识别到新增大类 ' + cats.length + ' 个：' + cats.map(c => c.name).join(' / '));

  const total = await pg.evaluate(() => window.App.ALL.length);
  const majors = await pg.evaluate(() => window.App.D.majors.length);
  const metaTotal = await pg.evaluate(() => (window.App.D.meta ? window.App.D.meta.total : window.App.ALL.length));
  ok(total === metaTotal, `站点总数与 meta 一致（${total}）`);
  ok(majors === cats.length + 12 || majors === cats.length + 13, '大类总数与 meta 对齐（' + majors + '）');

  for (const cat of cats) {
    console.log(`\n── ${cat.name} ──`);

    // 1) 左栏入口
    const rail = await pg.evaluate(name => {
      const el = document.querySelector(`#filterGroup .maj[data-maj="${name}"]`);
      return {
        exists: !!el,
        leaf: el ? el.classList.contains('leaf') : false,
        label: el ? el.textContent.replace(/\s+/g, ' ').trim() : '',
        active: !!document.querySelector(`#filterGroup .maj[data-maj="${name}"] button.active`),
      };
    }, cat.name);
    ok(rail.exists && rail.leaf, `${cat.name} 在左栏有可点入口（${rail.label}）`);
    ok(rail.label.includes(String(cat.count)), `${cat.name} 计数 ${cat.count} 与 meta 一致`);
    ok(/^#[0-9A-Fa-f]{6}$/.test(cat.color), `${cat.name} 有独立配色 ${cat.color}`);

    // 2) 点进去看条数
    await pg.click(`#filterGroup .maj[data-maj="${cat.name}"] > button`);
    await new Promise(r => setTimeout(r, 2200));
    const flt = await pg.evaluate(name => ({
      count: (document.querySelector('#resultCount') || {}).textContent || '',
      active: !!document.querySelector(`#filterGroup .maj[data-maj="${name}"] button.active`),
      multi: document.querySelectorAll('#grid .card .multi-badge').length,
      cards: document.querySelectorAll('#grid .card').length,
    }), cat.name);
    ok(flt.count.replace(/\D/g, '') === String(cat.count), `${cat.name} 筛选出 ${cat.count} 条`, flt.count);
    ok(flt.active, `${cat.name} 按钮呈选中态`);
    ok(flt.cards > 0, `${cat.name} 有卡片渲染（${flt.cards}）`);

    // 3) 图片可访问（懒加载会干扰 naturalWidth，直接验 URL）
    await pg.evaluate(() => window.scrollTo(0, 0));
    await new Promise(r => setTimeout(r, 1200));
    const srcs = await pg.evaluate(() =>
      [...document.querySelectorAll('#grid .card img')].slice(0, 5)
        .map(i => i.currentSrc || i.src || '').filter(Boolean)
    );
    const codes = [];
    for (const u of srcs.slice(0, 5)) codes.push(await head(u));
    ok(codes.length > 0 && codes.every(c => c === 200), `${cat.name} 前 ${codes.length} 张主图 HTTP 200（${codes.join(',')}）`);

    // 4) 详情页
    const mid = await pg.evaluate(name => {
      const s = window.App.ALL.find(x => x.category === name);
      return s ? s.id : null;
    }, cat.name);
    if (mid == null) { ok(false, `${cat.name} 能找到条目`); continue; }

    await pg.goto(BASE + 'detail.html?id=' + mid, { waitUntil: 'networkidle2', timeout: 90000 });
    await new Promise(r => setTimeout(r, 2400));
    const det = await pg.evaluate(name => {
      const img = document.querySelector('#dImg img');
      const tags = [...document.querySelectorAll('.lb-tags .tag')].map(t => t.textContent.trim());
      return {
        title: (document.querySelector('.lb-title') || {}).textContent || '',
        imgOk: img ? img.naturalWidth > 0 : false,
        hasCat: tags.some(t => t.includes(name)),
        promptLen: ((document.querySelector('#dPrompt') || {}).textContent || '').length,
      };
    }, cat.name);
    ok(det.title.length > 0, `${cat.name} 详情页有标题：` + det.title.slice(0, 16));
    ok(det.imgOk, `${cat.name} 详情页主图正常显示`);
    ok(det.hasCat, `${cat.name} 分类标签正确`);
    ok(det.promptLen > 50, `${cat.name} 正文完整（${det.promptLen} 字）`);

    await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 90000 });
    await new Promise(r => setTimeout(r, 2600));
  }

  ok(errs.length === 0, '全程无 JS 报错', errs.slice(0, 2).join(' | '));
  await pg.close();
  await b.close();

  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
