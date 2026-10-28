/* =========================================================
   水仙 · 提示词花园 — features.js 回归自测
   在 Node 里用 DOM 桩件加载 js/features.js，对真实数据跑核心纯逻辑。
   用法：node tools/test_features.js      （退出码 0 = 全部通过）
   ========================================================= */
const fs = require('fs'), path = require('path'), vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const prompts = [];
for (const i of [1, 2, 3]) prompts.push(...JSON.parse(fs.readFileSync(path.join(ROOT, 'data', `prompts.part${i}.json`), 'utf8')));
const pinyin = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'pinyin.json'), 'utf8'));

const noop = () => { };
const lsData = {};
const localStorageStub = {
  getItem: k => (k in lsData ? lsData[k] : null),
  setItem: (k, v) => { lsData[k] = String(v); },
  removeItem: k => { delete lsData[k]; },
};
function el() {
  return {
    classList: { add: noop, remove: noop, toggle: noop, contains: () => false },
    addEventListener: noop, appendChild: noop, insertBefore: noop, remove: noop,
    querySelector: () => null, querySelectorAll: () => [],
    setAttribute: noop, removeAttribute: noop,
    style: {}, dataset: {}, innerHTML: '', textContent: '',
  };
}
const bodyEl = el(); bodyEl.dataset = { page: 'gallery' };
const documentStub = {
  documentElement: el(), body: bodyEl, head: el(),
  addEventListener: noop, createElement: () => el(),
  querySelector: () => null, querySelectorAll: () => [], getElementById: () => null,
};
const windowStub = {
  addEventListener: noop, dispatchEvent: noop, open: noop, innerWidth: 1280, innerHeight: 900,
  location: { href: '', origin: 'http://localhost', pathname: '/gallery.html', hash: '' },
  localStorage: localStorageStub, document: documentStub,
};
const AppStub = {
  getBoards: () => ({ boards: [{ id: 'default', name: '我的收藏', items: [] }], active: 'default' }),
  saveBoards: noop, findSample: id => prompts.find(p => p.id == id),
  ALL: prompts, D: { samples: prompts }, toast: noop, copyText: noop, isFav: () => false,
  imgUrl: p => 'https://r2.qqsrc.com/' + p, ensureFull: () => Promise.resolve(),
  openLightbox: noop, renderCards: noop,
};
windowStub.App = AppStub;

const ctx = vm.createContext({
  window: windowStub, document: documentStub, localStorage: localStorageStub, App: AppStub,
  console, JSON, Math, Date, Object, Array, String, Number, RegExp, Set, Map, Promise, Boolean,
  Blob: function () { }, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: noop },
  FileReader: function () { }, MutationObserver: function () { this.observe = noop; },
  CustomEvent: function () { }, navigator: {}, setTimeout: noop, clearTimeout: noop,
  fetch: u => Promise.resolve({ json: () => Promise.resolve(String(u).includes('pinyin') ? pinyin : {}) }),
});
ctx.location = windowStub.location;

vm.runInContext(fs.readFileSync(path.join(ROOT, 'js', 'features.js'), 'utf8'), ctx, { filename: 'features.js' });
const FX = ctx.window.FX;

let pass = 0, fail = 0;
function check(name, cond, extra) {
  if (cond) { pass++; console.log('  OK   ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  → ' + extra : '')); }
}

(async () => {
  const withVar = prompts.find(p => /\{argument\s+name=/.test(p.prompt || ''));
  const noVar = prompts.find(p => !/\{argument\s+name=/.test(p.prompt || '') && (p.prompt || '').length > 30);

  console.log('== 1. 拼音首字母 ==');
  await FX.loadPinyin();
  const ini = FX.initials('赛博朋克');
  check('赛博朋克 → sbpk', ini === 'sbpk', '实际: ' + ini);
  check('分类「高端女性杂志」首字母非空', FX.initials('高端女性杂志').length >= 6, FX.initials('高端女性杂志'));

  console.log('== 2. 智能搜索 ==');
  const hits = FX.smartSearch(prompts, 'sbpk').slice(0, 8);
  console.log('  "sbpk" 前 4 条: ' + JSON.stringify(hits.slice(0, 4).map(x => x.title)));
  check('拼音缩写能召回结果', hits.length > 0);
  check('召回结果含「赛博朋克」相关', hits.some(x => /赛博|朋克|cyber/i.test(x.title + x.category + (x.prompt || ''))));
  check('中文关键词可搜到', FX.smartSearch(prompts, '海报').length > 0);
  check('标题命中优先于正文命中', FX.smartScore({ title: '海报设计' }, '海报') > FX.smartScore({ title: '无关标题', prompt: '海报' }, '海报'));
  check('完全无关返回 0 分', FX.smartScore({ title: 'zzz', category: 'yyy', prompt: 'xxx' }, 'qqqq') === 0);
  check('高亮输出含 mark 标签', /<mark class="hl">赛博<\/mark>/.test(FX.highlight('赛博朋克城市', '赛博')));
  check('高亮对 HTML 转义', FX.highlight('<script>', '').includes('&lt;'));

  console.log('== 3. 标签分面 ==');
  const poster = prompts.find(p => /海报/.test(p.title + p.category));
  const tg = FX.tagsFor(poster);
  console.log('  #' + poster.id + ' ' + poster.title + ' → ' + JSON.stringify(tg));
  check('海报类命中「媒介:海报」', (tg['媒介'] || []).includes('海报'));
  check('至少一个分面有标签', Object.values(tg).some(a => a.length));
  const anime = prompts.find(p => /动漫|二次元/.test(p.category));
  check('动漫类有风格标签', (FX.tagsFor(anime)['风格'] || []).length > 0);

  console.log('== 4. 筛选器 ==');
  FX.filters.facets = { '媒介': ['海报'] };
  const f1 = FX.applyFilters(prompts);
  check('按分面筛选后数量变少且全部命中', f1.length > 0 && f1.length < prompts.length && f1.every(x => (FX.tagsFor(x)['媒介'] || []).includes('海报')), f1.length + '/' + prompts.length);
  FX.filters.facets = {};
  FX.filters.hasImage = true;
  const f2 = FX.applyFilters(prompts);
  check('「只看有图」过滤生效', f2.length > 0 && f2.every(x => !!x.image), f2.length + '/' + prompts.length);
  FX.filters.hasImage = false;
  check('重置后恢复全量', FX.applyFilters(prompts).length === prompts.length);

  console.log('== 5. 导出 ==');
  AppStub.getBoards = () => ({ boards: [{ id: 'default', name: '测试合集', items: [withVar.id, noVar.id] }], active: 'default' });
  const B = FX.loadBoards();
  const board = FX.activeBoard(B);
  const md = FX.boardToMD(B, board);
  const csv = FX.boardToCSV(board);
  const js = FX.boardToJSON(board);
  check('Markdown 含合集名与代码块', md.includes('测试合集') && md.includes('```') && md.includes(withVar.title));
  check('CSV 带 BOM 与表头', csv.charCodeAt(0) === 0xFEFF && csv.split('\r\n')[0].includes('prompt'));
  const parsed = JSON.parse(js);
  check('JSON 可解析且条目数正确', parsed.count === 2 && parsed.items.length === 2);
  check('JSON 含 prompt 正文', parsed.items[0].prompt.length > 0);
  check('单条 Markdown 含 ID 与图片地址', FX.itemToMD(withVar).includes('#' + withVar.id) && FX.itemToMD(withVar).includes('r2.qqsrc.com'));
  check('CSV 行数 = 表头 + 2 条', csv.split('\r\n').length === 3);
  prompts.push({ id: 999999, title: 'A"B\nC', category: '测试', image: '', prompt: 'line1\nline2 "quoted"', likes: 0 });
  const csv2 = FX.boardToCSV({ items: [999999] });
  const row2 = csv2.split('\r\n')[1] || '';
  check('CSV 引号转义为双引号', csv2.includes('""'), row2.slice(0, 80));
  check('CSV 单行字段数 = 6', (row2.match(/","/g) || []).length === 5, row2.slice(0, 80));

  console.log('\n通过 ' + pass + ' / 失败 ' + fail + '   （数据 ' + prompts.length + ' 条，汉字表 ' + pinyin.count + '）');
  process.exit(fail ? 1 : 0);
})();
