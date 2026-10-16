/* ===== Home Page v10 ===== */
(function(){
  const state = App.state;

  /* ---------- 热门搜索：从 5000+ 真实提示词中随机抽样的 ≤4 字标签 ---------- */
  const HOT_SEARCHES = [
    "极简女性","复古女性","女性写实","人像动漫",
    "极简人物","人像温柔","人像复古","人像写真",
    "食物海报","极简美食","字体设计","3D动物",
    "动物手绘","猫头像","3D角色","角色漫画",
    "纹理背景","海报产品","极简汽车","车写实",
    "3D建筑","极简建筑","机器人","角色插画"
  ];

  function renderHotTags(){
    const el = document.getElementById('hotTags'); if(!el) return;
    el.innerHTML = "";
    HOT_SEARCHES.forEach(text => {
      const b = document.createElement('span');
      b.className = "hot-tag"; b.textContent = text;
      b.onclick = () => {
        const input = document.getElementById('heroSearch');
        if(input){ input.value = text; state.q = text; }
        // 跳转到画廊页搜索
        window.location.href = "gallery.html?q=" + encodeURIComponent(text);
      };
      el.appendChild(b);
    });
  }

  /* ---------- 精选预览：真实 R2 图片 + 渐变遮罩 + 换一批 ---------- */
  const GRADIENTS = [
    "linear-gradient(180deg,transparent 40%,rgba(26,107,107,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(94,75,139,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(184,105,42,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(166,61,91,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(138,122,10,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(26,96,128,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(42,128,80,.55) 100%)",
    "linear-gradient(180deg,transparent 40%,rgba(90,75,160,.55) 100%)",
  ];
  const FEATURED_COUNT = 8;

  function pickRandom(n){
    const list = App.ALL.filter(d => (d.category||"其他/未归类") !== "其他/未归类");
    if(list.length === 0) return [];
    const shuffled = list.slice().sort(() => Math.random() - 0.5);
    return shuffled.slice(0, Math.min(n, shuffled.length));
  }

  function makeFeaturedCard(d, idx){
    const card = document.createElement('div'); card.className = "feat-card";
    // 图片区域（真实 R2 图片 + 渐变遮罩）
    const thumb = document.createElement('div'); thumb.className = "feat-thumb";
    const firstImg = (d.image && d.image.trim()) || (d.thumb && d.thumb.trim()) || "";
    if(firstImg){
      const img = document.createElement('img');
      img.src = App.imgUrl(firstImg);
      img.alt = d.title || "";
      img.loading = "lazy";
      img.onerror = function(){ this.style.opacity = "0.3"; this.style.background = "#eef2f4"; };
      thumb.appendChild(img);
      // 渐变遮罩叠加
      const overlay = document.createElement('div'); overlay.className = "gradient-overlay";
      overlay.style.background = GRADIENTS[idx % GRADIENTS.length];
      thumb.appendChild(overlay);
    } else {
      // 无图片时用纯渐变底色
      const gradDiv = document.createElement('div');
      gradDiv.style.cssText = "position:absolute;inset:0;background:" +
        ["linear-gradient(135deg,#1a6b6b,#2a9d8f)","linear-gradient(135deg,#5e4b8b,#7c5dba)",
         "linear-gradient(135deg,#b8692a,#d4953a)","linear-gradient(135deg,#a63d5b,#c85a78)"][idx % 4];
      thumb.appendChild(gradDiv);
    }
    // 分类 pill
    const catName = d.category || "其他";
    const pill = document.createElement('span'); pill.className = "cat-pill";
    pill.textContent = catName.length > 10 ? catName.slice(0,9)+"…" : catName;
    thumb.appendChild(pill);
    card.appendChild(thumb);
    // 内容
    const body = document.createElement('div'); body.className = "feat-body";
    const title = document.createElement('div'); title.className = "feat-title";
    title.textContent = d.title || "(未命名)";
    body.appendChild(title);
    // 提示词预览
    const preview = document.createElement('div'); preview.className = "feat-prompt-preview";
    const full = App.fullOf(d);
    const promptText = (full.prompt || d.prompt || "").trim();
    preview.textContent = promptText ? (promptText.length > 50 ? promptText.slice(0,47)+"…" : promptText) : "提示词";
    body.appendChild(preview);
    // meta: 收藏
    const meta = document.createElement('div'); meta.className = "feat-meta";
    const collect = document.createElement('span'); collect.className = "feat-collect";
    const isFav = App.isFav(d.id);
    collect.innerHTML = '<svg viewBox="0 0 24 24" fill="'+(isFav?'currentColor':'none')+'" stroke="currentColor" stroke-width="2"><path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.18L12 21z"/></svg>' + (isFav?"已收藏":"收藏");
    collect.onclick = (e) => { e.stopPropagation(); App.toggleFavFromCard(d, null); renderFeatured(); };
    meta.appendChild(collect);
    body.appendChild(meta);
    card.appendChild(body);
    card.onclick = () => App.openLightbox(d);
    return card;
  }

  function renderFeatured(){
    const grid = document.getElementById('featuredGrid'); if(!grid) return;
    grid.innerHTML = "";
    const items = pickRandom(FEATURED_COUNT);
    if(items.length === 0){
      grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray)">暂无数据</div>';
      return;
    }
    items.forEach((d,i) => grid.appendChild(makeFeaturedCard(d, i)));
  }

  document.getElementById('refreshFeatured').onclick = () => { renderFeatured(); };

  /* ---------- 全部分类：12 大类桶网格 ---------- */

  // 每个大类的图标、颜色、描述
  const BUCKET_META = {
    "动漫二次元": {icon:"🌟", color:"#9B5BC4", desc:"二次元角色、立绘、日漫风，还有各种动漫插画。"},
    "海报广告":   {icon:"📢", color:"#E0892F", desc:"海报、banner、封面和社媒配图，拿来就能用。"},
    "人物写真":   {icon:"👤", color:"#2C8CAB", desc:"真人写真、人像摄影、合照证件照，写实风都在这。", feature:true},
    "随手拍":     {icon:"📸", color:"#4FA3C7", desc:"生活里随手一拍那种松弛感的照片。"},
    "插画艺术":   {icon:"🎨", color:"#D6607A", desc:"手绘、治愈、剪纸、油画水彩，各种画风的插画。"},
    "其他/未归类":{icon:"📦", color:"#888888", desc:"还没想好归哪类的，先搁这了。"},
    "产品电商":   {icon:"🛍", color:"#E6A23C", desc:"产品摄影、电商详情、包装和美食图。"},
    "车辆机械3D": {icon:"🚗", color:"#607D8B", desc:"汽车、机械、3D 渲染和工业设计。"},
    "游戏":       {icon:"🎮", color:"#673AB7", desc:"游戏角色、场景、卡牌，还有像素风。"},
    "建筑空间场景":{icon:"🏛", color:"#795548", desc:"建筑、室内、景观和各种空间场景。"},
    "晓兰":       {icon:"🌸", color:"#EC407A", desc:"晓兰主题专属的一批。"},
    "（大凶）":   {icon:"💋", color:"#E91E63", desc:"大凶系列主题，懂的都懂。"}
  };

  // 从数据中动态计算每个大类的子类和条数
  function buildBucketData(){
    const buckets = {};
    // 初始化所有大类
    Object.keys(BUCKET_META).forEach(k => {
      buckets[k] = {key:k, subs:[], count:0, ...BUCKET_META[k]};
    });
    // 遍历数据聚合子类
    App.ALL.forEach(d => {
      const subCat = d.category || "其他/未归类";
      const majorCat = App.SUB_TO_MAJOR[subCat] || "其他/未归类";
      if(buckets[majorCat]){
        buckets[majorCat].count++;
        // 查找或创建子类条目
        let found = null;
        for(const s of buckets[majorCat].subs){
          if(s.n === subCat){ found = s; break; }
        }
        if(!found){
          found = {n:subCat, c:0, d:majorCat};
          buckets[majorCat].subs.push(found);
        }
        found.c++;
      }
    });
    // 转为数组，按条数降序，（大凶）置底
    let arr = Object.values(buckets).filter(b => b.key !== "（大凶）");
    arr.sort((a,b) => b.count - a.count);
    const daXiong = buckets["（大凶）"];
    if(daXiong) arr.push(daXiong);
    return arr;
  }

  function renderCategoryGrid(){
    const grid = document.getElementById('bucketGrid');
    const statsRow = document.getElementById('statsRow');
    const metaEl = document.getElementById('catMeta');
    if(!grid) return;

    const data = buildBucketData();
    const totalPrompts = data.reduce((s,b) => s + b.count, 0);
    const totalSubs = data.reduce((s,b) => s + b.subs.length, 0);
    const maxBucket = data.length ? data.reduce((a,b) => b.count > a.count ? b : a) : null;

    // 统计行
    if(statsRow){
      statsRow.innerHTML = "";
      [
        {label:"总提示词", value:totalPrompts.toLocaleString(), cls:"teal"},
        {label:"大类桶", value:data.length, cls:"purple"},
        {label:"细分类", value:totalSubs, cls:"orange"},
        {label:"最大桶", value:maxBucket ? maxBucket.count.toLocaleString() : "0", cls:"rose"}
      ].forEach(s => {
        const sc = document.createElement('div'); sc.className = "stat-card";
        sc.innerHTML = '<div class="sl">'+s.label+'</div><div class="sv '+s.cls+'">'+s.value+'</div>';
        statsRow.appendChild(sc);
      });
    }

    // 元信息
    if(metaEl) metaEl.textContent = totalPrompts.toLocaleString()+" 条 · "+data.length+" 桶 / "+totalSubs+" 细类";

    // 渲染折叠桶卡片（手风琴）
    grid.innerHTML = "";
    data.forEach((bkt, idx) => {
      const card = document.createElement('div');
      card.className = "bucket";
      card.style.setProperty("--bc", bkt.color);
      card.style.setProperty("--bt", bkt.color + "14");

      // ===== 盖子（lid）=====
      const lid = document.createElement('div'); lid.className = "bkt-lid";

      // 图标
      const ico = document.createElement('span'); ico.className = "bkt-ico"; ico.textContent = bkt.icon;
      lid.appendChild(ico);

      // 名称
      const h3 = document.createElement('h3'); h3.textContent = bkt.key; lid.appendChild(h3);

      // 提示文字（提醒用户点击展开）
      const hint = document.createElement('span'); hint.className = "bkt-hint";
      hint.textContent = "里面 " + bkt.subs.length + " 个小类 · 点开看看";
      lid.appendChild(hint);

      // 计数
      const cnt = document.createElement('div'); cnt.className = "cnt";
      cnt.innerHTML = "<b>"+bkt.count.toLocaleString()+"</b><span>条</span>";
      lid.appendChild(cnt);

      // 箭头
      const arrow = document.createElement('span'); arrow.className = "bkt-arrow";
      arrow.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';
      lid.appendChild(arrow);

      card.appendChild(lid);

      // ===== 展开内容区（body）=====
      const body = document.createElement('div'); body.className = "bkt-body";
      const inner = document.createElement('div'); inner.className = "bkt-inner";

      // 子类标签行
      const sub = document.createElement('div'); sub.className = "sub";
      bkt.subs.forEach(s => {
        const sp = document.createElement('span');
        sp.innerHTML = s.n + (s.c > 0 ? " <b>"+s.c+"</b>" : "");
        sp.onclick = (e) => {
          e.stopPropagation();
          window.location.href = "gallery.html?cat=" + encodeURIComponent(s.n);
        };
        sub.appendChild(sp);
      });
      inner.appendChild(sub);

      // 底部占比条
      const bottom = document.createElement('div'); bottom.className = "bottom";
      const track = document.createElement('div'); track.className = "bar-track";
      const fill = document.createElement('div'); fill.className = "bar-fill";
      const pct = totalPrompts > 0 ? Math.round(bkt.count / totalPrompts * 100) : 0;
      fill.style.width = pct + "%";
      track.appendChild(fill);
      bottom.appendChild(track);
      const pctLabel = document.createElement('span'); pctLabel.className = "pct";
      pctLabel.textContent = "占比 " + pct + "% · 共 " + bkt.subs.length + " 个细分类";
      bottom.appendChild(pctLabel);
      inner.appendChild(bottom);

      body.appendChild(inner);
      card.appendChild(body);

      // 点击盖子切换展开/收起
      lid.onclick = (e) => {
        e.stopPropagation();
        const isOpen = card.classList.contains("open");
        // 关闭其他已打开的桶（手风琴互斥）
        grid.querySelectorAll(".bucket.open").forEach(b => { if(b !== card) b.classList.remove("open"); });
        card.classList.toggle("open", !isOpen);
      };

      grid.appendChild(card);
    });
  }

  // 明细面板
  function showDetail(bkt){
    const panel = document.getElementById('catDetail');
    if(!panel) return;
    panel.classList.add("show");

    document.getElementById('dIco').textContent = bkt.icon;
    document.getElementById('dIco').style.background = bkt.color + "18";
    document.getElementById('dTitle').textContent = bkt.key;
    document.getElementById('dTitle').style.color = bkt.color;
    document.getElementById('dSub').textContent = bkt.desc;

    const sg = document.getElementById('dSubgrid');
    sg.innerHTML = "";
    bkt.subs.forEach(s => {
      const sc = document.createElement('div'); sc.className = "subcard";
      sc.innerHTML = '<div class="st">'+s.n+'</div><div class="sn">'+s.c+'</div><div class="sd">条提示词</div>';
      sc.style.cursor = "pointer";
      sc.onclick = () => { window.location.href = "gallery.html?cat=" + encodeURIComponent(s.n); };
      sg.appendChild(sc);
    });

    document.getElementById('dClose').onclick = () => panel.classList.remove("show");
  }

  /* ---------- 搜索跳转画廊 ---------- */
  const heroSearchBtn = document.getElementById('heroSearchBtn');
  const heroSearch = document.getElementById('heroSearch');
  if(heroSearchBtn) heroSearchBtn.onclick = doHeroSearch;
  if(heroSearch) heroSearch.addEventListener('keydown', (e) => {
    if(e.key === 'Enter'){ e.preventDefault(); doHeroSearch(); }
  });

  function doHeroSearch(){
    const input = document.getElementById('heroSearch');
    if(input && input.value.trim()){
      window.location.href = "gallery.html?q=" + encodeURIComponent(input.value.trim());
    }
  }

  /* ---------- 初始化 ---------- */
  App.init({
    page: 'index',
    onSearch: (q) => {
      // 首页搜索：跳转到画廊页面，携带搜索词（跨全部分类搜索 title + prompt）
      if(q && q.trim()) window.location.href = "gallery.html?q=" + encodeURIComponent(q.trim());
    },
    onReady: () => {
      renderHotTags();
      renderFeatured();
      renderCategoryGrid();
    }
  });
})();
