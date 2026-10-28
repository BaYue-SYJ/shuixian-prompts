/* =========================================================
   tools/test_mobile_nav.js
   验证「手机端顶栏只留 语言 / 版本 / 主题，其余进汉堡菜单」
   用最小 DOM 桩件加载真实 features.js，断言装配结果与可见性规则。
   运行： node tools/test_mobile_nav.js
   ========================================================= */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log('  OK   ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  → ' + extra : '')); }
};

/* ---------- 极简 DOM ---------- */
function El(tag) {
  const e = {
    tagName: tag.toUpperCase(), children: [], parentNode: null,
    attrs: {}, dataset: {}, _cls: new Set(), style: {}, value: '',
    textContent: '', innerHTML: '', type: '', id: '', href: '',
    listeners: {},
  };
  Object.defineProperty(e, 'className', {
    get() { return [...e._cls].join(' '); },
    set(v) { e._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
  });
  Object.defineProperty(e, 'classList', {
    get() {
      return {
        add: (...c) => c.forEach(x => e._cls.add(x)),
        remove: (...c) => c.forEach(x => e._cls.delete(x)),
        contains: c => e._cls.has(c),
        toggle: (c, f) => (f === undefined ? (e._cls.has(c) ? e._cls.delete(c) : e._cls.add(c)) : (f ? e._cls.add(c) : e._cls.delete(c))),
      };
    },
  });
  e.appendChild = c => { c.parentNode = e; e.children.push(c); return c; };
  e.insertBefore = (c, ref) => {
    c.parentNode = e;
    const i = ref ? e.children.indexOf(ref) : -1;
    if (i < 0) e.children.push(c); else e.children.splice(i, 0, c);
    return c;
  };
  e.removeChild = c => { const i = e.children.indexOf(c); if (i >= 0) e.children.splice(i, 1); return c; };
  e.remove = () => { if (e.parentNode) e.parentNode.removeChild(e); };
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); };
  e.getAttribute = k => (e.attrs[k] !== undefined ? e.attrs[k] : null);
  e.addEventListener = (t, fn) => { (e.listeners[t] = e.listeners[t] || []).push(fn); };
  e.dispatch = (t, ev) => (e.listeners[t] || []).forEach(fn => fn(ev || {}));
  e.closest = sel => {
    const isId = sel.startsWith('#'), isCls = sel.startsWith('.');
    const key = sel.replace(/^[.#]/, '');
    let n = e;
    while (n) {
      if (isId) { if (n.id === key) return n; }
      else if (isCls) { if (n._cls && n._cls.has(key)) return n; }
      else if (n.tagName === sel.toUpperCase()) return n;
      n = n.parentNode;
    }
    return null;
  };
  e.querySelector = sel => {
    const cls = sel.replace(/^\./, '').replace(/^#/, '');
    const isId = sel.startsWith('#');
    return tree(e).find(n => (isId ? n.id === cls : (n._cls && n._cls.has(cls)))) || null;
  };
  e.querySelectorAll = sel => {
    const cls = sel.replace(/^\./, '').replace(/^#/, '');
    const isId = sel.startsWith('#');
    return tree(e).filter(n => (isId ? n.id === cls : (n._cls && n._cls.has(cls))));
  };
  return e;
}
const tree = root => { const out = []; (function walk(n) { n.children.forEach(c => { out.push(c); walk(c); }); })(root); return out; };
const byId = (root, id) => tree(root).find(n => n.id === id);
const byClass = (root, c) => tree(root).filter(n => n._cls && n._cls.has(c));

/* ---------- 搭建导航（与 components/header.html 一致） ---------- */
function buildNav() {
  const header = El('header'); header.id = 'sx-nav';
  const inner = El('div'); inner.className = 'sx-nav-inner'; header.appendChild(inner);

  const navLinks = El('nav'); navLinks.id = 'navLinks'; navLinks.className = 'nav-links';
  ['index', 'gallery', 'favorites', 'about'].forEach(p => {
    const a = El('a'); a.className = 'nav-link'; a.dataset.page = p; a.textContent = p;
    navLinks.appendChild(a);
  });
  inner.appendChild(navLinks);

  const actions = El('div'); actions.className = 'nav-actions';

  const theme = El('button'); theme.id = 'themeBtn'; theme.className = 'icon-btn';
  actions.appendChild(theme);

  const fav = El('a'); fav.className = 'icon-btn only-desktop'; fav.href = 'favorites.html';
  actions.appendChild(fav);

  const submit = El('a'); submit.className = 'btn btn-amber only-desktop';
  submit.href = 'submit.html'; submit.textContent = '投稿'; actions.appendChild(submit);

  const toggle = El('button'); toggle.id = 'navToggle'; toggle.className = 'icon-btn nav-toggle';
  actions.appendChild(toggle);

  inner.appendChild(actions);
  return { header, inner, navLinks, actions, theme, fav, submit, toggle };
}

/* ---------- 加载真实 features.js ---------- */
const doc = {
  documentElement: El('html'),
  body: (() => { const b = El('body'); b.dataset.page = 'index'; return b; })(),
  title: '',
  querySelector: () => null,
  querySelectorAll: () => [],
  createElement: El,
  addEventListener: () => { },
};
const vm0 = require('vm');
const i18nSandbox = { window: {} };
vm0.createContext(i18nSandbox);
vm0.runInContext(fs.readFileSync(path.join(ROOT, 'js', 'i18n.js'), 'utf8'), i18nSandbox, { filename: 'i18n.js' });

const win = {
  addEventListener: () => { },
  dispatchEvent: () => { },
  matchMedia: () => ({ matches: false, addEventListener() { }, addListener() { } }),
  localStorage: (() => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => m[k] = String(v), removeItem: k => delete m[k] }; })(),
  SX_I18N: i18nSandbox.window.SX_I18N,
  location: { href: '', reload: () => { } },
};

const ctx = { document: doc, window: win, localStorage: win.localStorage, navigator: { language: 'zh-CN' }, location: win.location, console };

/* 真实 features.js 需要 App 与 sx:ready；这里只取 wireHeader 相关行为，
   靠替换内部 $ 查询来源来驱动。做法：把导航树挂成可被 querySelector 命中。 */
const nodes = buildNav();
doc.body.appendChild(nodes.header);

// 让 querySelector / querySelectorAll 走真实树
doc.querySelector = sel => {
  if (sel.startsWith('#')) return byId(doc.body, sel.slice(1));
  if (sel.startsWith('.')) return byClass(doc.body, sel.slice(1))[0] || null;
  return null;
};
doc.querySelectorAll = sel => {
  if (sel.startsWith('.')) return byClass(doc.body, sel.slice(1));
  if (sel.startsWith('#')) { const n = byId(doc.body, sel.slice(1)); return n ? [n] : []; }
  return tree(doc.body).filter(n => n.tagName === sel.toUpperCase());
};

let src = fs.readFileSync(path.join(ROOT, 'js', 'features.js'), 'utf8');
// 把内部函数暴露到 window，供测试断言（注入在 IIFE 内部、结尾 })(); 之前）
const PROBE = "\n  try{ window.__FX_TEST__ = { wireHeader: wireHeader, applyI18n: applyI18n, FX: FX }; }catch(e){ window.__FX_TEST__ = { error: String(e) }; }\n";
const closeIdx = src.lastIndexOf('})();');
if (closeIdx < 0) throw new Error('features.js 尾部结构变化，找不到 IIFE 收尾');
src = src.slice(0, closeIdx) + PROBE + src.slice(closeIdx);

const vm = require('vm');
const sandbox = Object.assign(Object.create(null), ctx, {
  window: win, document: doc, localStorage: win.localStorage,
  setTimeout: (fn) => { try { fn(); } catch (e) { } return 0; },
  clearTimeout: () => { },
  setInterval: () => 0, clearInterval: () => { },
  requestAnimationFrame: (fn) => { try { fn(0); } catch (e) { } return 0; },
  cancelAnimationFrame: () => { },
  fetch: () => Promise.reject(new Error('no fetch in test')),
  CustomEvent: class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } },
  Event: class { constructor(t) { this.type = t; } },
  IntersectionObserver: class { observe() { } unobserve() { } disconnect() { } },
  MutationObserver: class { observe() { } disconnect() { } takeRecords() { return []; } },
  matchMedia: win.matchMedia,
  performance: { now: () => Date.now() },
});
vm.createContext(sandbox);
let loadErr = null;
try { vm.runInContext(src, sandbox, { filename: 'features.js' }); } catch (e) { loadErr = e; }

console.log('== 0. 加载 ==');
ok('features.js 可加载', !loadErr, loadErr && loadErr.message);

console.log('== 1. 顶栏常驻按钮（语言 / 主题）==');
const T = win.__FX_TEST__ || {};
ok('内部函数已暴露', typeof T.wireHeader === 'function', JSON.stringify(T.error || ''));
if (typeof T.wireHeader !== 'function') { console.log(`\n通过 ${pass} / 失败 ${fail}`); process.exit(1); }

T.wireHeader();

const actions = nodes.actions;
const langBtn = byId(doc.body, 'langBtn');
ok('语言按钮已注入 (#langBtn)', !!langBtn);
ok('语言按钮带 lang-btn 类', !!langBtn && langBtn._cls.has('lang-btn'));
ok('语言按钮是 icon-only 圆形', !!langBtn && langBtn._cls.has('icon-only'));
ok('语言按钮文案为 EN', !!langBtn && langBtn.textContent === 'EN');

ok('主题按钮存在 (#themeBtn)', !!byId(doc.body, 'themeBtn'));

console.log('== 2. 桌面端的投稿 / 收藏打上 only-desktop ==');
ok('投稿链接带 only-desktop', nodes.submit._cls.has('only-desktop'));
ok('收藏链接带 only-desktop', nodes.fav._cls.has('only-desktop'));
ok('主题按钮没有 only-desktop（移动端要留）', !nodes.theme._cls.has('only-desktop'));
ok('语言按钮没有 only-desktop（移动端要留）', !!langBtn && !langBtn._cls.has('only-desktop'));

console.log('== 3. 汉堡菜单里的两项（命令面板 + 投稿） ==');
const mb = byId(doc.body, 'mobilePaletteBtn');
const ms = byId(doc.body, 'mobileSubmitLink');
ok('菜单含命令面板入口', !!mb);
ok('菜单含投稿', !!ms, ms ? ms.textContent : 'null');
ok('菜单不再重复添加「收藏」（导航里已有）', !byId(doc.body, 'mobileFavLink'));
ok('两项都在 #navLinks 内', !!mb && mb.parentNode === nodes.navLinks
  && !!ms && ms.parentNode === nodes.navLinks);
ok('两项都带 only-mobile 类',
  !!mb && mb._cls.has('only-mobile') && !!ms && ms._cls.has('only-mobile'));
ok('投稿指向 submit.html', !!ms && ms.href === 'submit.html');
ok('命令面板是 button 不是链接', !!mb && mb.tagName === 'BUTTON');
ok('导航里恰有一条「收藏」(data-page=favorites)',
  nodes.navLinks.children.filter(a => a.dataset.page === 'favorites').length === 1);

console.log('== 4. 菜单项顺序（命令面板 → 投稿） ==');
const kids = nodes.navLinks.children;
const iMb = kids.indexOf(mb), iMs = kids.indexOf(ms);
ok('命令面板在投稿之前', iMb >= 0 && iMs > iMb, `${iMb} vs ${iMs}`);
const origLinks = kids.filter(k => k._cls && k._cls.has('nav-link') && !k._cls.has('only-mobile'));
const lastOrigIdx = origLinks.reduce((m, k) => Math.max(m, kids.indexOf(k)), -1);
ok('两项都在原有导航链接之后', iMb > lastOrigIdx, `${iMb} > ${lastOrigIdx}`);

console.log('== 5. 点击菜单项后收起菜单 ==');
nodes.navLinks._cls.add('open');
nodes.toggle._cls.add('open');
nodes.navLinks.dispatch('click', { target: ms });
ok('点投稿后菜单移除 open', !nodes.navLinks._cls.has('open'));
ok('burger 图标恢复非激活态', !nodes.toggle._cls.has('open'));
ok('aria-expanded 置 false', nodes.toggle.getAttribute('aria-expanded') === 'false');

console.log('== 6. 幂等（二次装配不重复注入） ==');
const before = nodes.navLinks.children.length;
T.wireHeader();
ok('再次 wireHeader 不新增菜单项', nodes.navLinks.children.length === before,
  `${before} → ${nodes.navLinks.children.length}`);
ok('语言按钮只有一个', byClass(doc.body, 'lang-btn').length === 1);

console.log('== 7. 英文态文案 ==');
T.FX.setLang('en');
T.FX.applyI18n();
ok('英文下语言按钮显示「中」', langBtn.textContent === '中', langBtn.textContent);
ok('英文下菜单投稿为 Submit', ms.textContent === T.FX.t('nav_submit'), ms.textContent);
ok('英文下命令面板入口非空', !!mb.textContent && mb.textContent.length > 0, mb.textContent);
T.FX.setLang('zh');
T.FX.applyI18n();
ok('切回中文后语言按钮显示 EN', langBtn.textContent === 'EN', langBtn.textContent);

console.log(`\n通过 ${pass} / 失败 ${fail}`);
process.exit(fail ? 1 : 0);
