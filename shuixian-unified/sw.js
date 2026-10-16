/* =========================================================
   水仙 · 提示词花园 — service worker
   策略：
     · 安装时预缓存「应用外壳」+ 轻量数据（list/meta/categories/pinyin）
     · 数据 JSON：network-first（在线取最新，离线回落缓存）
     · css/js/components/images：cache-first（资源都带 ?v=，可安全长缓存）
     · 导航请求：network-first，离线回落 index.html
     · R2 图片：cache-first 并按条数修剪，避免无限膨胀
   更新：改动静态资源后递增 CACHE 版本号即可触发换新
   ========================================================= */
const VERSION = 'sx-v17';
const SHELL = VERSION + '-shell';
const DATA = VERSION + '-data';
const IMG = VERSION + '-img';
const IMG_MAX = 320;

const PRECACHE = [
  './',
  './index.html',
  './gallery.html',
  './categories.html',
  './search.html',
  './detail.html',
  './favorites.html',
  './about.html',
  './sponsor.html',
  './submit.html',
  './404.html',
  './manifest.webmanifest',
  './images/icon.svg',
  './images/wechat-qr.jpg',
  './css/base.css?v=17',
  './css/features.css?v=17',
  './js/i18n.js?v=17',
  './js/base.js?v=17',
  './js/features.js?v=17',
  './components/header.html?v=17',
  './components/footer.html?v=17',
  './components/lightbox.html?v=17',
  './components/modals.html?v=17',
  './data/meta.json',
  './data/categories.json',
  './data/pinyin.json',
  './data/list.part1.json',
  './data/list.part2.json',
  './data/list.part3.json'
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    // 逐条容错：个别文件失败不影响整体安装
    await Promise.all(PRECACHE.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => null)));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => ![SHELL, DATA, IMG].includes(k)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', e => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
});

async function trim(cacheName, max) {
  const c = await caches.open(cacheName);
  const keys = await c.keys();
  if (keys.length <= max) return;
  for (const k of keys.slice(0, keys.length - max)) await c.delete(k);
}

async function networkFirst(req, cacheName) {
  const c = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res && res.ok) c.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await c.match(req, { ignoreSearch: false });
    if (hit) return hit;
    const loose = await c.match(req, { ignoreSearch: true });
    if (loose) return loose;
    throw err;
  }
}

async function cacheFirst(req, cacheName, trimMax) {
  const c = await caches.open(cacheName);
  const hit = await c.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res && (res.ok || res.type === 'opaque')) {
    c.put(req, res.clone()).then(() => { if (trimMax) trim(cacheName, trimMax); }).catch(() => {});
  }
  return res;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 导航请求：优先网络，离线回落首页
  if (req.mode === 'navigate') {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        const c = await caches.open(SHELL);
        c.put(req, res.clone()).catch(() => {});
        return res;
      } catch (err) {
        const c = await caches.open(SHELL);
        return (await c.match(req)) || (await c.match('./index.html')) || Response.error();
      }
    })());
    return;
  }

  // R2 图床
  if (url.hostname === 'r2.qqsrc.com') {
    e.respondWith(cacheFirst(req, IMG, IMG_MAX).catch(() => Response.error()));
    return;
  }

  // 站内资源
  if (url.origin === location.origin) {
    if (/\/data\/.*\.json$/.test(url.pathname)) {
      e.respondWith(networkFirst(req, DATA).catch(() => Response.error()));
      return;
    }
    if (/\.(css|js|png|jpe?g|webp|gif|svg|woff2?|ttf|ico)$/.test(url.pathname) || /\/components\//.test(url.pathname)) {
      e.respondWith(cacheFirst(req, SHELL).catch(() => Response.error()));
      return;
    }
  }
});
