/* 品牌 logo 回归：顶栏与页脚都用图片 logo（不再是内联 SVG），图片能真正加载 */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  for (const vp of [{ w: 1440, h: 900, name: '桌面' }, { w: 390, h: 844, name: '手机' }]) {
    const pg = await b.newPage();
    const errs = [];
    pg.on('pageerror', e => errs.push(String(e)));
    await pg.setViewport({ width: vp.w, height: vp.h, isMobile: vp.w < 600, hasTouch: vp.w < 600 });
    await pg.goto(BASE + 'index.html', { waitUntil: 'networkidle2', timeout: 60000 });
    await new Promise(r => setTimeout(r, 2200));

    const d = await pg.evaluate(() => {
      const navMark = document.querySelector('#sx-nav .brand .mark');
      const footMark = document.querySelector('#sx-footer .brand .mark');
      const img = navMark ? navMark.querySelector('img') : null;
      const r = navMark ? navMark.getBoundingClientRect() : null;
      return {
        hasNavMark: !!navMark, hasFootMark: !!footMark,
        navSvg: navMark ? navMark.querySelectorAll('svg').length : -1,
        footSvg: footMark ? footMark.querySelectorAll('svg').length : -1,
        imgSrc: img ? img.getAttribute('src') : '',
        loaded: img ? img.naturalWidth > 0 : false,
        natW: img ? img.naturalWidth : 0,
        boxW: r ? Math.round(r.width) : 0,
        boxH: r ? Math.round(r.height) : 0,
        radius: navMark ? getComputedStyle(navMark).borderRadius : '',
        fit: img ? getComputedStyle(img).objectFit : '',
        fit: img ? getComputedStyle(img).objectFit : '',
      };
    });

    ok(d.hasNavMark && d.hasFootMark, `${vp.name}: 顶栏与页脚都有品牌标记`);
    ok(d.navSvg === 0 && d.footSvg === 0, `${vp.name}: 内联 SVG 已全部替换为图片`, `nav=${d.navSvg} foot=${d.footSvg}`);
    ok(/images\/1水仙_02\.jpg/.test(d.imgSrc), `${vp.name}: 引用原图 1水仙_02.jpg（${d.imgSrc}）`);
    ok(d.loaded && d.natW >= 100, `${vp.name}: 图片加载成功（原始宽 ${d.natW}px）`);
    ok(d.boxW >= 28 && d.boxW <= 38 && d.boxW === d.boxH, `${vp.name}: 显示尺寸约 30–36px 方形（${d.boxW}×${d.boxH}）`);
    ok(d.fit === 'contain', `${vp.name}: 原图等比缩放、不裁剪（object-fit=${d.fit}）`);
    ok(errs.length === 0, `${vp.name}: 无 JS 报错`, errs.slice(0, 2).join(' | '));
    await pg.close();
  }

  /* 其他页面也要有（组件是注入的，别只测首页） */
  const pages = ['gallery.html', 'detail.html?id=1', 'about.html', 'favorites.html'];
  for (const url of pages) {
    const pg = await b.newPage();
    await pg.setViewport({ width: 1440, height: 900 });
    await pg.goto(BASE + url, { waitUntil: 'networkidle2', timeout: 60000 });
    await new Promise(r => setTimeout(r, 1600));
    const okImg = await pg.evaluate(() => {
      const img = document.querySelector('#sx-nav .brand .mark img');
      return !!img && img.naturalWidth > 0;
    });
    ok(okImg, url + ' 顶栏 logo 正常');
    await pg.close();
  }

  /* 标签页图标 / 主屏图标：link 存在且资源可访问，manifest 指向新 png */
  const pg = await b.newPage();
  await pg.goto(BASE + 'index.html', { waitUntil: 'networkidle2', timeout: 60000 });
  const iconInfo = await pg.evaluate(async () => {
    const links = [...document.querySelectorAll('link[rel="icon"], link[rel="apple-touch-icon"]')]
      .map(l => ({ rel: l.rel, href: l.getAttribute('href') }));
    const status = [];
    for (const l of links) {
      try { const r = await fetch(l.href); status.push({ href: l.href, ok: r.ok, type: r.headers.get('content-type') }); }
      catch (e) { status.push({ href: l.href, ok: false, type: 'ERR' }); }
    }
    let man = null;
    try {
      const r = await fetch('manifest.webmanifest');
      man = await r.json();
    } catch (e) { man = null; }
    return { links, status, icons: man ? man.icons : null };
  });
  ok(iconInfo.links.length >= 3, '页面声明了 favicon / png 图标 / apple-touch-icon（' + iconInfo.links.length + ' 条）');
  ok(iconInfo.status.every(s => s.ok), '所有图标资源可访问', JSON.stringify(iconInfo.status.filter(s => !s.ok)));
  ok((iconInfo.status.find(s => /favicon\.ico/.test(s.href)) || {}).ok === true, 'favicon.ico 可访问');
  const ic = iconInfo.icons || [];
  ok(ic.length >= 2 && ic.every(i => /\.png$/.test(i.src)), 'manifest 图标全部指向 png（' + ic.map(i => i.sizes).join('/') + '）');
  ok(ic.some(i => i.purpose === 'maskable'), 'manifest 含 maskable 图标');
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
