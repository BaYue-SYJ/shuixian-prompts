<div align="center">

<img src="shuixian-unified/images/icon.svg" width="96" alt="水仙的AI提示词">

# 水仙的AI提示词

**6,011 条中文 AI 绘画提示词，检索 / 分类 / 一键复制，全部开源**

13 大类 · 79 细类 · 每条配效果图 · 无需登录

[🖥 在线逛库](https://prompt.qqsrc.com/) ·
[✨ 功能](#-功能) ·
[🚀 部署](#-本地运行与部署) ·
[🕘 更新日志](https://github.com/BaYue-SYJ/shuixian-prompts/releases) ·
[English](README.en.md)

</div>

<img src="docs/screenshots/features/01-home.png" alt="首页" width="100%">

## 这是什么

一个**中文 AI 绘画提示词库**：把散落在各处的提示词整理到一起，配上生成效果图，让人能搜到、能看懂、能直接复制去用。

提示词覆盖 Midjourney、Stable Diffusion、Flux、ChatGPT、Gemini，以及即梦、可灵、豆包、海螺、文心一格等国产模型。
站点是**纯静态页面**，数据与代码全部开源；图片放在 Cloudflare R2，仓库里只有代码和 JSON 数据。

**在线站点：<https://prompt.qqsrc.com/>**

## ✨ 功能

**找**

- 关键词搜索：模糊匹配，`海报设计` 也能命中「设计感海报」，结果里命中词高亮
- 拼音首字母：输入 `sbpk` 直接出「赛博朋克」
- 标签分面：媒介（12 种）/ 风格（16 种）/ 色调（8 种），带实时计数，可多选
- 筛选器：只看有图 / 有备注 / 已收藏 / 用过的
- 命令面板：`Ctrl / ⌘ + K` 一个框搜「功能 + 分类 + 提示词」

**用**

- 一键复制提示词；模板里的 `{参数}` 原样保留，复制后自己替换（经典版另提供变量填空表单，填完直接拿成品）
- 图片下载（文件名自动用标题 + ID）、`#id=` 深链直达、灯箱 ‹ › 上下文翻页
- 备注与「用过」标记：边打边存，只存在本机浏览器

**管理**

- 收藏合集：多合集、拖拽排序、跨合集移动
- 导出 Markdown / JSON / CSV（带 BOM，Excel 直接打开不乱码），也支持导回来

**其他**

- 两套皮肤：现代版（页面级拆分）与经典版（13 大类卡片墙），右上角一键切换
- 中英双语：点 `EN / 中` 整站换语言，含 92 个分类名（13 大类 + 79 小类）；选择会被记住
- PWA：可安装到桌面，离线能浏览外壳与轻量数据；快捷键按 `?` 查看
- 油猴脚本：在 ChatGPT / Claude / Gemini / Midjourney / 即梦 页面召唤侧边栏搜索并复制

## 🚀 本地运行与部署

必须走 HTTP，直接双击 HTML 会被 `fetch` 的跨域限制挡住：

```bash
git clone https://github.com/BaYue-SYJ/shuixian-prompts.git
cd shuixian-prompts
python -m http.server 8094 --directory shuixian-unified
```

打开 <http://localhost:8094/> 即可，点右上角在「现代版 / 经典版」之间切换。

**部署**：`shuixian-unified/` 是自包含的静态目录，整个拖进 Cloudflare Pages 或任意静态空间就能上线。
`_headers` 里已约定缓存策略，改完 CSS / JS 记得同步升 `?v=` 与 `ASSET_VERSION`（共 4 处），然后 Purge Cache。

## 🎨 两套皮肤

同一份数据，两种逛法。切换时会尽量停在同一类页面（首页↔首页、画廊↔画廊、收藏↔收藏）。

| 现代版 — 页面级拆分 | 经典版 — 13 大类卡片墙 |
| --- | --- |
| <img src="docs/screenshots/features/01-home.png" alt="现代版首页"> | <img src="docs/screenshots/unified/home-classic.png" alt="经典版首页"> |

<details>
<summary>更多截图（提示词详情 / 命令面板 / 标签分面 / 收藏合集 / 英文版 / 手机端）</summary>

| 提示词详情 · 复制与收藏 | 命令面板 ⌘K |
| --- | --- |
| <img src="docs/screenshots/features/07-detail.png" alt="提示词详情"> | <img src="docs/screenshots/features/02-command-palette.png" alt="命令面板"> |

| 标签分面 | 收藏合集管理 |
| --- | --- |
| <img src="docs/screenshots/features/03-facets.png" alt="标签分面"> | <img src="docs/screenshots/features/08-collections.png" alt="收藏合集"> |

| 英文版 | 手机端 |
| --- | --- |
| <img src="docs/screenshots/features/10-english-home.png" alt="英文版"> | <img src="docs/screenshots/features/16-mobile-nav.png" alt="手机端"> |

</details>

## 📁 项目结构

```
shuixian-unified/          站点（自包含，可直接部署）
├── index.html  gallery.html  categories.html  detail.html  search.html
├── favorites.html  about.html  sponsor.html  submit.html  404.html
├── classic/               经典版皮肤（与主站共用同一份 data/）
├── components/  css/      两套皮肤的组件与样式
├── js/
│   ├── base.js            数据加载、卡片、灯箱、收藏
│   ├── features.js        变量填空 / 分面 / 搜索 / 命令面板 / 合集 / i18n 装配
│   └── i18n.js            122 组文案 + 92 个分类名
├── data/                  数据集（两套皮肤共用）
├── tools/                 维护脚本（拼音表 / 版本号 / i18n 注入 / 回归测试）
├── userscript/            油猴侧边栏脚本
├── sw.js  manifest.webmanifest   PWA
└── _headers               Cloudflare Pages 缓存策略
docs/                      功能说明 + 界面截图
```

> 历史版本的源码不在本仓库，归档在
> [Awesome-shuixian-prompts-archive](https://github.com/BaYue-SYJ/Awesome-shuixian-prompts-archive)。

## 🗂 数据说明

采用**分层加载**：轻量列表负责首屏，完整数据在打开详情或复制时才按需加载。

| 文件 | 内容 |
| --- | --- |
| `data/list.part1~3.json` | 轻量列表（标题、分类、点赞、图片路径），首屏加载 |
| `data/prompts.part1~3.json` | 完整数据（含 `prompt` 正文），按需加载 |
| `data/meta.json` `data/categories.json` | 分类结构（大类 → 小类树 / 扁平映射） |
| `data/pinyin.json` | 汉字 → 拼音首字母表，供拼音搜索用 |

字段：现代版 `id` `title` `prompt` `image` `category` `likes`；经典版另带 `themes` `styles` `person`。

图片不随仓库分发：原图在 Cloudflare R2，站点通过 `https://r2.qqsrc.com` 加载，
图床地址是 `js/base.js` 里的 `IMG_BASE` 常量。

## 🔗 相关项目

| 项目 | 说明 |
| --- | --- |
| [shuixian-manju-skills](https://github.com/BaYue-SYJ/shuixian-manju-skills) | 短剧漫剧 6 件套：从小说到成片的创作技能 |
| [threads-ai-radar](https://github.com/BaYue-SYJ/threads-ai-radar) | Threads 爆款雷达，按互动量排榜 |
| [zimeiti-workbuddy](https://github.com/BaYue-SYJ/zimeiti-workbuddy) | Creator Buddy：公众号 / 小红书 / 短视频创作工具箱 |
| [web-html-image-skill](https://github.com/BaYue-SYJ/web-html-image-skill) | web-image：用 HTML/CSS 出图，不依赖生图模型 |
| [Awesome-shuixian-prompts-archive](https://github.com/BaYue-SYJ/Awesome-shuixian-prompts-archive) | 本项目的历史版本归档 |

## 📄 许可

采用**署名使用**协议：可自由学习、fork、二次开发、非商业转载，
但请**保留出处并链接回本仓库**；衍生项目需写清来源；商业用途需先联系作者获取授权。详见 [LICENSE](LICENSE)。

仓库内的提示词原文与图片来自公开渠道的整理与收录，**版权归各自原作者**，本项目只做整理、分类与展示。
商用请自行确认权利来源。

## 💬 联系

- 站点：<https://prompt.qqsrc.com/>
- 公众号：**水仙的AI提示词** —— 会经常写一些 AI 工具与提示词相关的东西
- 微信：**Kas2026** —— 公益免费交流群，不收取任何费用，喜欢技术的可以一起交流
- 投稿、纠错、建议：欢迎开 [Issue](https://github.com/BaYue-SYJ/shuixian-prompts/issues)

| 赞赏码 | 微信 | 公众号 |
|:---:|:---:|:---:|
| <img src="docs/reward-qr.jpg" width="180" alt="赞赏码"> | <img src="docs/wechat-qr.jpg" width="180" alt="微信"> | <img src="docs/wechat-mp-qr.jpg" width="180" alt="公众号"> |

## ❤️ 致谢

| 社区 | 说明 |
| --- | --- |
| [Linux.Do](https://linux.do) | 与社区分享、讨论和跟踪发展 —— 认可 LINUX DO 社区 |

---

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=BaYue-SYJ/shuixian-prompts&type=Date)](https://star-history.com/#BaYue-SYJ/shuixian-prompts&Date)

<sub>

**更新记录请看 [Releases](https://github.com/BaYue-SYJ/shuixian-prompts/releases)** —— 本 README 只描述项目本身，不随版本改动。

如果这个库帮到你，点个 ⭐ 就是最大的支持。

</sub>

</div>
