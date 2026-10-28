/* =========================================================
   水仙 · 提示词花园  —  base.js
   架构对齐 shuixian-deploy-2：
     · 图片走 Cloudflare R2（IMG_BASE + imgUrl）
     · 数据通过 fetch 拆分 JSON 加载（list.part* 首屏 / prompts.part* 按需）
     · 组件（header/footer/lightbox/modals）通过 fetch 注入
     · App.init({page, onReady}) 页面初始化模式
     · IntersectionObserver 懒加载 + localStorage 收藏画板
   视觉沿用 v2（design-system.css / base.css）
   ========================================================= */
const App = (() => {
  // ---------- 配置 ----------
  const ASSET_VERSION = '27';                        // 每次更新静态资源请 +1，并同步 HTML 里的 ?v=
  const IMG_BASE = "https://r2.qqsrc.com";          // Cloudflare R2 公共图床
  const FAV_KEY = 'sx-boards-v2';
  const REC_KEY = 'sx-recent-v2';

  // ---------- 工具 ----------
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => (s == null ? '' : String(s)).replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const imgUrl = p => (p ? IMG_BASE + '/' + p : p);

  // ---------- 语言钩子（features.js 提供实现；未加载时回退中文） ----------
  // 只影响「显示」；数据的 category、URL 的 ?cat= 一律保持中文原名。
  const T = (k, d) => (window.FX && typeof FX.t === 'function') ? FX.t(k) : (d != null ? d : k);
  const catLabel = c => {
    if (c === '其他/未归类') return '杂项';   // 显示名改「杂项」，数据 key 不变（URL/筛选/数据引用不受影响）
    return (window.FX && typeof FX.catName === 'function') ? FX.catName(c) : c;
  };

  function heartSvg(filled){
    return `<svg viewBox="0 0 24 24" fill="${filled?'currentColor':'none'}" stroke="currentColor" stroke-width="2"><path d="M12 21s-7.5-4.6-10-9.3C.3 8.4 2 5 5.3 5c2 0 3.4 1.2 4.7 3 1.3-1.8 2.7-3 4.7-3C18 5 19.7 8.4 22 11.7 19.5 16.4 12 21 12 21z"/></svg>`;
  }

  // ---------- 主题 ----------
  const html = document.documentElement;
  function applyTheme(t){ html.setAttribute('data-theme', t); }
  function toggleTheme(){ const n = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'; localStorage.setItem('sx-theme', n); applyTheme(n); }

  // ---------- 分类配色 ----------
  function catColor(name){
    const c = (META && META.colors && META.colors[name]) || {};
    return { bg: c.bg || '#E3F4F8', main: c.main || '#2C8CAB' };
  }

  // ---------- 状态 / 数据 ----------
  let META = null;            // { total, subCount, hot, majors, colors }
  let SAMPLES = [];           // 轻量列表（无 prompt）
  const DETAIL = {};          // id -> 完整条目（含 prompt，按需填充）
  let fullLoaded = false, fullPromise = null;
  let options = { page: null, onReady: null };
  const LIST_PARTS  = ["data/list.part1.json",  "data/list.part2.json",  "data/list.part3.json"];
  const FULL_PARTS  = ["data/prompts.part1.json","data/prompts.part2.json","data/prompts.part3.json"];

  function findSample(id){ return DETAIL[id] || SAMPLES.find(s => s.id == id); }

  async function loadData(){
    const meta = await (await fetch('data/meta.json')).json();
    META = meta;
    const parts = await Promise.all(LIST_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));
    SAMPLES = [].concat(...parts);
    SAMPLES.forEach(s => { DETAIL[s.id] = s; });
  }
  // 按需加载完整数据（含 prompt），供灯箱 / 详情 / 全文搜索使用
  function ensureFull(){
    if (fullLoaded) return Promise.resolve();
    if (fullPromise) return fullPromise;
    fullPromise = (async () => {
      const parts = await Promise.all(FULL_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));
      [].concat(...parts).forEach(e => {
        DETAIL[e.id] = e;
        const orig = SAMPLES.find(s => s.id == e.id);   // 把 prompt 回填进轻量列表，供搜索/画廊正文命中
        if (orig) orig.prompt = e.prompt;
      });
      fullLoaded = true;
      if (typeof window.__onFullLoaded === 'function') window.__onFullLoaded();
    })();
    return fullPromise;
  }

  // ---------- 组件注入 ----------
  async function injectComponent(url, selector, position = 'beforeend'){
    const sep = url.includes('?') ? '&' : '?';
    const res = await fetch(url + sep + 'v=' + ASSET_VERSION);
    if (!res.ok) throw new Error('组件加载失败 ' + url);
    const htmlText = await res.text();
    const el = document.querySelector(selector);
    if (el) el.insertAdjacentHTML(position, htmlText);
  }
  async function loadComponents(){
    await Promise.all([
      injectComponent('components/header.html',   'body', 'afterbegin'),
      injectComponent('components/footer.html',   'main', 'afterend'),
      injectComponent('components/lightbox.html', 'body', 'beforeend'),
      injectComponent('components/modals.html',   'body', 'beforeend')
    ]);
  }

  function highlightNav(){
    const page = options.page;
    $$('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.page === page));
  }
  function initMobileNav(){
    const toggle = $('#navToggle'); const nav = $('#navLinks');
    if (!toggle || !nav) return;
    const setOpen = open => { toggle.classList.toggle('open', open); nav.classList.toggle('open', open); };
    toggle.addEventListener('click', e => { e.stopPropagation(); setOpen(!nav.classList.contains('open')); });
    nav.addEventListener('click', e => { const t = e.target.closest('a, button'); if (t) setOpen(false); });
    document.addEventListener('click', e => { if (nav.classList.contains('open') && !toggle.contains(e.target) && !nav.contains(e.target)) setOpen(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 920) setOpen(false); });
  }
  function wireCommon(){
    highlightNav();
    initMobileNav();
    const themeBtn = $('#themeBtn'); if (themeBtn) themeBtn.addEventListener('click', toggleTheme);
    const ns = $('#navSearchInput');
    if (ns) ns.addEventListener('keydown', e => { if (e.key === 'Enter' && ns.value.trim()) location.href = 'search.html?q=' + encodeURIComponent(ns.value.trim()); });
    // 灯箱全局事件
    const lb = $('#sx-lightbox');
    if (lb){
      lb.addEventListener('click', e => { if (e.target.hasAttribute('data-close')) closeLightbox(); });
    }
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
  }

  // ---------- 收藏画板（localStorage） ----------
  function getBoards(){ try { return JSON.parse(localStorage.getItem(FAV_KEY)) || { boards:[{id:'default',name:'我的收藏',items:[]}], active:'default' }; } catch(e){ return { boards:[{id:'default',name:'我的收藏',items:[]}], active:'default' }; } }
  function saveBoards(b){ localStorage.setItem(FAV_KEY, JSON.stringify(b)); }
  function isFav(id){ const b = getBoards(); return b.boards.some(x => x.items.includes(id)); }
  function toggleFav(id){
    const b = getBoards(); const board = b.boards.find(x => x.id === b.active) || b.boards[0];
    const i = board.items.indexOf(id);
    if (i >= 0) board.items.splice(i, 1); else board.items.push(id);
    saveBoards(b); toast(i >= 0 ? T('toast_unfaved', '已从画板移除') : T('toast_faved', '已加入收藏画板')); updateFavButtons(); return i < 0;
  }
  function updateFavButtons(){ $$('.act.fav').forEach(btn => { const id = +btn.dataset.id; const on = isFav(id); btn.classList.toggle('on', on); btn.innerHTML = heartSvg(on); }); }

  // ---------- Toast & Copy ----------
  let toastEl;
  function toast(msg){ if (!toastEl){ toastEl = document.createElement('div'); toastEl.className = 'toast'; document.body.appendChild(toastEl); } toastEl.textContent = msg; toastEl.classList.add('show'); clearTimeout(toastEl._t); toastEl._t = setTimeout(() => toastEl.classList.remove('show'), 1800); }
  function copyText(t){ if (navigator.clipboard){ navigator.clipboard.writeText(t).then(() => toast(T('toast_copied', '提示词已复制'))).catch(() => fallbackCopy(t)); } else fallbackCopy(t); }
  function fallbackCopy(t){ const ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); toast(T('toast_copied', '提示词已复制')); } catch(e){} ta.remove(); }

  // ---------- 卡片渲染 ----------
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting){ const img = e.target; if (img.dataset.src){ img.src = img.dataset.src; img.removeAttribute('data-src'); } io.unobserve(img); } });
  }, { rootMargin: '300px' });

  function observeImages(c){ c.querySelectorAll('img.ph-img[data-src]').forEach(img => io.observe(img)); }

  // 一条提示词可能对应多张图：images 数组为准，缺省回退到 image 单图字段
  const imageList = s => {
    if (!s) return [];
    let arr = Array.isArray(s.images) ? s.images.filter(Boolean).slice() : [];
    if (!arr.length) return s.image ? [s.image] : [];
    if (s.image && arr.indexOf(s.image) < 0) arr.unshift(s.image);
    return arr;
  };
  const isMulti = s => imageList(s).length > 1;

  function thumb(s){
    const category = s.category || '';
    const img = s.image;
    const { bg, main } = catColor(category);
    const wm = (catLabel(category) || '图').slice(0, 1);
    const hint = '<span class="load-hint">' + esc(T('load_hint', '原图加载中，首次打开请稍候…')) + '</span>';
    const inner = img
      ? `${hint}<img class="ph-img" data-src="${esc(imgUrl(img))}" alt="${esc(catLabel(category))}" onload="this.previousElementSibling?.remove()" onerror="this.style.display='none'">`
      : `<span class="wm">${esc(wm)}</span>`;
    return `<div class="ph" style="background:linear-gradient(140deg,${bg} 0%,${main} 135%);">${inner}</div>`;
  }

  function cardHTML(s){
    const { main } = catColor(s.category);
    return `<article class="card" data-id="${s.id}">
      <a class="thumb" href="detail.html?id=${s.id}" style="--cc:${main}">
        ${thumb(s)}
        <span class="cat-pill" style="--cc:${main}">${esc(catLabel(s.category))}</span>
        ${isMulti(s) ? `<span class="multi-badge">${esc(T('multi_tag', '多图'))} · ${imageList(s).length}</span>` : ''}
        <span class="hover-actions">
          <button class="act fav ${isFav(s.id) ? 'on' : ''}" data-id="${s.id}" title="${esc(T('title_fav', '收藏'))}">${heartSvg(isFav(s.id))}</button>
          <button class="act" data-copy="${s.id}" title="${esc(T('copy_prompt', '复制提示词'))}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10" stroke-linecap="round"/></svg></button>
        </span>
      </a>
      <div class="body">
        <a class="title" href="detail.html?id=${s.id}">${esc(s.title)}</a>
        <div class="prompt-line">${esc(s.prompt || '')}</div>
      </div>
    </article>`;
  }

  // 瀑布流列数：与旧 CSS 断点一致（按视口，>1100→4, >760→3, >540→2, 否则 1）
  function colsForWidth(){
    const vw = window.innerWidth;
    if (vw <= 540) return 1;
    if (vw <= 760) return 2;
    if (vw <= 1100) return 3;
    return 4;
  }
  function bindCardEvents(card){
    card.querySelectorAll('.act.fav').forEach(b => b.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); toggleFav(+b.dataset.id); }));
    card.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); const s = findSample(+b.dataset.copy); copyText(s ? s.prompt : ''); }));
  }
  function cardEl(s){
    const tmp = document.createElement('div');
    tmp.innerHTML = cardHTML(s);
    const el = tmp.firstElementChild;
    bindCardEvents(el);
    return el;
  }
  // 卡片轮询均分到各列：缩略图均 3:4、文字块高度接近，轮询即近似最优瀑布流平衡，
  // 且保证「显示更多」时新卡横向铺开（左→右、上→下），杜绝 CSS columns 列优先导致的「只堆右边两列」。
  function layoutCards(list, colEls){
    const n = colEls.length;
    list.forEach((s, k) => colEls[k % n].appendChild(cardEl(s)));
  }
  function renderCards(list, container, opts){
    if (!container) return;
    opts = opts || {};
    if (!list || !list.length){ container.innerHTML = '<div class="empty"><div class="big">🌱</div>' + esc(T('empty_no_match', '没有匹配的提示词，换个关键词或分类试试。')) + '</div>'; container._mz = null; return; }
    const isMasonry = container.classList.contains('masonry') && !container.classList.contains('uniform');
    if (!isMasonry){
      container.innerHTML = list.map(cardHTML).join('');
      container.querySelectorAll('.card').forEach(bindCardEvents);
      observeImages(container);
      container._mz = null;
      return;
    }
    const cols = opts.cols || colsForWidth(container);
    const rebuild = !opts.append || !container._mz || container._mz.cols !== cols;
    if (rebuild){
      container.innerHTML = '';
      const colEls = [];
      for (let i = 0; i < cols; i++){ const d = document.createElement('div'); d.className = 'm-col'; container.appendChild(d); colEls.push(d); }
      layoutCards(list, colEls);
      container._mz = { list: list.slice(), cols: cols };
    } else {
      const colEls = $$('.m-col', container);
      const start = container._mz.list.length;
      layoutCards(list.slice(start), colEls);
      container._mz.list = list.slice();
    }
    observeImages(container);
  }
  function relayoutMasonryAll(){
    $$('.masonry').forEach(c => {
      if (c.classList.contains('uniform')) return;
      if (!c._mz) return;
      const cols = colsForWidth(c);
      if (cols === c._mz.cols) return;
      (App.renderCards || renderCards)(c._mz.list, c, { append: false });
    });
  }
  let _rzT;
  window.addEventListener('resize', () => { clearTimeout(_rzT); _rzT = setTimeout(relayoutMasonryAll, 150); });

  // ---------- 灯箱（完整显示整图 + R2 原图） ----------
  function buildLightbox(){
    let lb = document.getElementById('sx-lightbox');
    if (lb) return lb;
    lb = document.createElement('div'); lb.className = 'lightbox'; lb.id = 'sx-lightbox';
    lb.innerHTML = `<div class="lb-backdrop" data-close></div>
      <div class="lb-panel"><button class="lb-close" data-close aria-label="关闭">✕</button>
        <div class="lb-img" id="lbImg"></div>
        <div class="lb-body" id="lbBody"></div>
      </div>`;
    document.body.appendChild(lb);
    return lb;
  }
  // 多图缩略图条：挂到任意图片容器上（灯箱 / 详情页共用），点哪张换哪张
  function attachThumbs(container, s){
    const imgs = imageList(s);
    if (!container || imgs.length < 2) return null;
    const strip = document.createElement('div');
    strip.className = 'lb-thumbs';
    const setSrc = p => {
      let im = container.querySelector('img.ph-img');
      if (!im){
        container.insertAdjacentHTML('afterbegin', `<img class="ph-img" src="${esc(imgUrl(p))}" alt="">`);
        im = container.querySelector('img.ph-img');
      } else {
        im.src = imgUrl(p);
      }
      const h = container.querySelector('.load-hint'); if (h) h.remove();
    };
    imgs.forEach((p, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'lb-thumb' + (i === 0 ? ' on' : '');
      b.title = (i + 1) + ' / ' + imgs.length;
      b.innerHTML = `<img src="${esc(imgUrl(p))}" alt="" loading="lazy">`;
      b.addEventListener('click', e => {
        e.preventDefault(); e.stopPropagation();
        setSrc(p);
        strip.querySelectorAll('.lb-thumb').forEach(x => x.classList.toggle('on', x === b));
      });
      strip.appendChild(b);
    });
    container.appendChild(strip);
    return strip;
  }

  function openLightbox(id){
    const s = findSample(id); if (!s) return;
    const lb = buildLightbox();
    const { bg, main } = catColor(s.category);
    const lbImg = $('#lbImg');
    const hint = '<span class="load-hint">' + esc(T('load_hint', '原图加载中，首次打开请稍候…')) + '</span>';
    const fallback = `<div class="ph" style="background:linear-gradient(140deg,${bg},${main})"></div><span class="wm">${esc((catLabel(s.category) || '图').slice(0,1))}</span>`;
    if (s.image){
      lbImg.innerHTML = `${hint}<img class="ph-img" src="${esc(imgUrl(s.image))}" alt="${esc(catLabel(s.category))}">`;
      const im = lbImg.querySelector('img');
      im.addEventListener('load', () => { const h = lbImg.querySelector('.load-hint'); if (h) h.remove(); });
      im.addEventListener('error', () => {
        if (im.isConnected) im.remove();
        const h = lbImg.querySelector('.load-hint'); if (h) h.remove();
        if (!lbImg.querySelector('.ph')) lbImg.insertAdjacentHTML('afterbegin', fallback);
      });
      if (im.complete && im.naturalWidth){ const h = lbImg.querySelector('.load-hint'); if (h) h.remove(); }
    } else {
      lbImg.innerHTML = fallback;
    }
    // 多图：图片区左下角缩略图条，点哪张换哪张（不影响左右箭头翻提示词）
    attachThumbs(lbImg, s);
    const tokPrompt = esc(s.prompt || T('loading_dots', '（加载中…）')).replace(/(\{argument[^}]*\})/g, '<span class="tok">$1</span>');
    $('#lbBody').innerHTML = `
      <div class="lb-crumb"><a href="gallery.html">${esc(T('de_crumb_gallery', '画廊'))}</a> › <a href="gallery.html?cat=${encodeURIComponent(s.category)}" style="--cc:${main}">${esc(catLabel(s.category))}</a></div>
      <h2 class="lb-title">${esc(s.title)}</h2>
      <div class="lb-tags"><span class="tag cc" style="--cc:${main};--cc-bg:${bg}">${esc(catLabel(s.category))}</span><span class="tag">ID #${s.id}</span></div>
      <div class="lb-prompt" id="lbPrompt">${tokPrompt}</div>
      <div class="lb-actions">
        <button class="btn btn-primary" id="lbCopy">${esc(T('copy_prompt', '复制提示词'))}</button>
        <button class="btn btn-soft fav-btn ${isFav(s.id) ? 'on' : ''}" data-id="${s.id}">${heartSvg(isFav(s.id))} ${esc(isFav(s.id) ? T('fav_added', '已收藏') : T('fav_add', '收藏'))}</button>
        <button class="btn btn-soft" data-copy="${s.id}">${esc(T('copy_plain', '复制原文'))}</button>
      </div>`;
    $('#lbCopy').addEventListener('click', () => copyText(s.prompt || ''));
    $('#lbBody').querySelector('.fav-btn').addEventListener('click', function(){ const on = toggleFav(s.id); this.classList.toggle('on', on); this.innerHTML = heartSvg(on) + ' ' + esc(on ? T('fav_added', '已收藏') : T('fav_add', '收藏')); updateFavButtons(); });
    $('#lbBody').querySelector('[data-copy]').addEventListener('click', () => copyText(s.prompt || ''));
    // 轻量数据无 prompt：按需补齐
    if (!s.prompt){
      ensureFull().then(() => { const f = findSample(id); if (f && f.prompt && lb.classList.contains('open')){ const tk = esc(f.prompt).replace(/(\{argument[^}]*\})/g, '<span class="tok">$1</span>'); const p = $('#lbPrompt'); if (p) p.innerHTML = tk; } });
    }
    lb.classList.add('open'); document.body.style.overflow = 'hidden';
  }
  function closeLightbox(){ const lb = document.getElementById('sx-lightbox'); if (lb){ lb.classList.remove('open'); document.body.style.overflow = ''; } }

  // ---------- 版本切换按钮：已按需求移除（经典版下线） ----------

  // ---------- 初始化 ----------
  function init(opts){
    options = Object.assign({ page: null, onReady: null }, opts);
    applyTheme(localStorage.getItem('sx-theme') || 'light');
    loadComponents()
      .then(wireCommon)
      .then(loadData)
      .then(() => {
        if (typeof options.onReady === 'function') options.onReady();
        // 通知 features.js（新功能层）可以装配了
        window.dispatchEvent(new CustomEvent('sx:ready', { detail: { page: options.page } }));
      })
      .catch(err => { console.error(err); const l = document.querySelector('.loading'); if (l) l.textContent = '数据加载失败：' + err.message + '（请通过本地服务器或 CF 打开本页）'; });
  }

  // ---------- 暴露 API（同时兼容 v2 的 SX.* 用法） ----------
  return {
    init,
    get D(){ return { majors: META ? META.majors : [], samples: SAMPLES, colors: META ? META.colors : {}, total: META ? META.total : SAMPLES.length, subCount: META ? META.subCount : 0, hot: META ? META.hot : [] }; },
    get ALL(){ return SAMPLES; },
    IMG_BASE, ASSET_VERSION,
    $, $$, imgUrl,
    findSample, catColor, thumb, cardHTML, renderCards, imageList, isMulti, attachThumbs,
    openLightbox, closeLightbox, ensureFull,
    toggleFav, isFav, toast, copyText, getBoards, saveBoards
  };
})();

window.App = App;
window.SX  = App;          // 兼容 v2 页面里 SX.* 的写法
window.$   = App.$;
window.$$  = App.$$;

// 全局：点卡片（非链接/非按钮）唤起灯箱
document.addEventListener('click', e => {
  const card = e.target.closest('.card');
  if (card && !e.target.closest('a') && !e.target.closest('.act')){
    App.openLightbox(+card.dataset.id);
  }
});
