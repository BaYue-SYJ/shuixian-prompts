/* i18n 一致性校验：
   ① 所有页面 data-i18n / data-i18n-placeholder / data-i18n-title 的 key 必须在 zh 和 en 里都存在
   ② features.js / base.js 里用到的 t('x') / tf('x') key 也要存在
   ③ 分类英文映射必须覆盖 meta.json 里全部 13 大类 + 79 小类
   退出码非 0 表示有问题 */
const fs = require('fs'), path = require('path'), vm = require('vm'), glob = require('fs');

const ROOT = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(p, 'utf8');

// ---- 载入字典 ----
const ctx = { window: {}, console };
vm.createContext(ctx);
vm.runInContext(read(path.join(ROOT, 'js', 'i18n.js')), ctx, { filename: 'i18n.js' });
const I18N = ctx.window.SX_I18N;
const zh = I18N.ui.zh, en = I18N.ui.en, cat = I18N.cat;

let bad = 0;
const fail = m => { bad++; console.log('  FAIL ' + m); };
const ok = m => console.log('  OK   ' + m);

// ---- ① 页面属性 key ----
const pages = fs.readdirSync(ROOT).filter(f => f.endsWith('.html'));
const comps = fs.readdirSync(path.join(ROOT, 'components')).filter(f => f.endsWith('.html')).map(f => 'components/' + f);
const files = pages.concat(comps);
const keysInHtml = new Set();
files.forEach(f => {
  const s = read(path.join(ROOT, f));
  for (const m of s.matchAll(/data-i18n(?:-placeholder|-title)?="([^"]+)"/g)) keysInHtml.add(m[1]);
});
console.log('页面共用到 ' + keysInHtml.size + ' 个 i18n key');
[...keysInHtml].sort().forEach(k => {
  if (!(k in zh)) fail('zh 缺少 ' + k);
  if (!(k in en)) fail('en 缺少 ' + k);
});
if (!bad) ok('页面 data-i18n 的 key 在 zh/en 均存在');

// ---- ② 代码里的 t()/tf() key（features.js + base.js） ----
const jsFiles = ['js/features.js', 'js/base.js'];
const used = new Set();
jsFiles.forEach(f => {
  const s = read(path.join(ROOT, f));
  for (const m of s.matchAll(/\b(?:t|tf)\(\s*'([a-z0-9_]+)'/gi)) used.add(m[1]);
});
console.log('\n代码里用到 ' + used.size + ' 个 key');
[...used].sort().forEach(k => {
  if (!(k in zh)) fail('zh 缺少(代码) ' + k);
  if (!(k in en)) fail('en 缺少(代码) ' + k);
});
ok('代码 t()/tf() 的 key 在 zh/en 均存在');

// ---- ③ 分类英文覆盖 ----
const meta = JSON.parse(read(path.join(ROOT, 'data', 'meta.json')));
const names = new Set();
meta.majors.forEach(m => { names.add(m.name); m.subs.forEach(s => names.add(s.name)); });
console.log('\n分类名共 ' + names.size + ' 个（13 大类 + 79 小类去重）');
const missing = [...names].filter(n => !cat[n]);
missing.forEach(n => fail('分类缺少英文：' + n));
if (!missing.length) ok('全部 ' + names.size + ' 个分类都有英文名');

// ---- ④ zh / en key 数量应一致（结构对齐） ----
const zk = Object.keys(zh).sort(), ek = Object.keys(en).sort();
const onlyZh = zk.filter(k => !(k in en));
const onlyEn = ek.filter(k => !(k in zh));
if (onlyZh.length) fail('只有 zh 的 key：' + onlyZh.join(','));
if (onlyEn.length) fail('只有 en 的 key：' + onlyEn.join(','));
console.log('\nzh ' + zk.length + ' 个 key / en ' + ek.length + ' 个 key');
if (!onlyZh.length && !onlyEn.length) ok('zh / en key 完全对齐');

console.log('\n' + (bad ? '发现 ' + bad + ' 个问题' : '全部通过'));
process.exit(bad ? 1 : 0);
