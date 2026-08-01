# 收集画廊提示词处理报告（2026-07-28 15:23）

## 范围说明
- 本次「更新的提示词」= 你从两个画廊 UI 收集进本地/部署版的条目：**source=promptsref 1506 + source=webtomind 1501 = 3007 条**。（非 twitter 抓取新增，因 1206 基线后无新 twitter 源条目。）
- 原 twitter 源条目（source=None，926 条）不在本次范围，未改动（校验：越界改动 0）。

## 备份
- `backup_twitter_20260728_1523/local/` 与 `/deploy/`（改前整份，含 prompts-twitter*.json / list-twitter*.json / categories.json / twitter_manifest.json）。

## 改动统计（仅范围内 3007 条）
- 实际变更条目：**255** 条
  - 重分类：**181** 条
  - 重拟标题（仅非中文）：**136** 条
  - 清内容（去 Prompt: 包装 / 指令前缀 / URL）：**28** 条
- 本地 == 部署：是；总条目 3933。

## WebToMind 分类修正前后（核心修复：画廊服务器 classify 缺词边界导致 UI/Logo 虚高）
| 分类 | 修正前 | 修正后 |
|---|---|---|
| 3D/游戏/像素/等距 | 34 | 37 |
| Logo/品牌/VI | 117 | 17 |
| UI/App/网页/SaaS | 82 | 43 |
| 产品/电商/包装 | 52 | 43 |
| 信息图/教育图解/图表 | 6 | 6 |
| 其他综合 | 8 | 13 |
| 商业海报/广告/社媒 | 305 | 331 |
| 头像/人像/写真 | 467 | 529 |
| 字体/排版/标题设计 | 28 | 26 |
| 插画/涂鸦/手绘风 | 123 | 124 |
| 摄影/电影感/写实场景 | 267 | 320 |
| 漫画/故事板/分镜 | 12 | 12 |

## 抽样变更（id | 旧分类→新分类 | 旧标题→新标题 | 内容）
- #33776 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'Close-up of a Stunning Redhead'→**'电影感女性'** | ✓
- #33777 `webtomind` 3D/游戏/像素/等距→**3D/游戏/像素/等距** | 'Ultra Realistic 3D Render'→**'3D 渲染'** | ✓
- #33778 `webtomind` UI/App/网页/SaaS→**摄影/电影感/写实场景** | 'RAW'→**'极简女性'** | ✓
- #33779 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'Ultra-photorealistic Live-acti'→**'复古女性'** | ✓
- #33780 `webtomind` UI/App/网页/SaaS→**头像/人像/写真** | 'Smartphone Selfie of a Beautif'→**'棚拍女性'** | ✓
- #33781 `webtomind` 头像/人像/写真→**头像/人像/写真** | 'Live-action Full-body Fashion '→**'电影感女性'** | ✓
- #33782 `webtomind` UI/App/网页/SaaS→**摄影/电影感/写实场景** | 'Good Morning'→**'电影感女性'** | 清
- #33784 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'GPT IMAGE 2 on Chatgpt'→**'电影感女性'** | ✓
- #33785 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'Fierce Fight ~ ONE PIECE Ver'→**'女性摄影作品'** | ✓
- #33786 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'GPT Image 2 on Chatgpt'→**'摄影作品'** | ✓
- #33788 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'オシャンの水着とビキニどっちが好き？'→**'オシャンの水着とビキニどっちが好き？'** | ✓
- #33792 `webtomind` UI/App/网页/SaaS→**摄影/电影感/写实场景** | 'GPT Image 2 on Chatgpt'→**'电影感女性'** | ✓
- #33793 `webtomind` 头像/人像/写真→**头像/人像/写真** | 'Light Showed Up'→**'人像写真'** | ✓
- #33794 `webtomind` Logo/品牌/VI→**头像/人像/写真** | '【推しを少年誌の表紙にするプロンプト】'→**'【推しを少年誌の表紙にするプロンプト】'** | ✓
- #33795 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'Dancing in the Night Club ~ ON'→**'夜景女性'** | ✓
- #33796 `webtomind` 摄影/电影感/写实场景→**头像/人像/写真** | 'Created with GPT Image 2'→**'电影感女性'** | ✓
- #33801 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | '🐋🎀🍋🥤'→**'摄影作品'** | 清
- #33804 `webtomind` 摄影/电影感/写实场景→**头像/人像/写真** | 'Cinematic Portrait of a Beauti'→**'电影感女性'** | 清
- #33805 `webtomind` 头像/人像/写真→**头像/人像/写真** | '3:4 Close-up Smartphone Portra'→**'极简女性'** | ✓
- #33806 `webtomind` UI/App/网页/SaaS→**摄影/电影感/写实场景** | 'Vertical Full-body Image of th'→**'极简女性'** | ✓
- #33807 `webtomind` Logo/品牌/VI→**摄影/电影感/写实场景** | 'Sophie Thatcher'→**'电影感女性'** | ✓
- #33808 `webtomind` 字体/排版/标题设计→**头像/人像/写真** | 'Vertical 9:16'→**'复古女性'** | ✓
- #33810 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'GPT Image 2 on Chatgpt'→**'摄影作品'** | ✓
- #33811 `webtomind` Logo/品牌/VI→**摄影/电影感/写实场景** | 'これめっちゃムズかった…'→**'电影感女性'** | ✓
- #33812 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | '服饰胸前的蝴蝶结和蕾丝边可太好看了～'→**'服饰胸前的蝴蝶结和蕾丝边可太好看了～'** | 清
- #33813 `webtomind` 头像/人像/写真→**头像/人像/写真** | 'High-quality Mixed-style Verti'→**'电影感女性'** | 清
- #33815 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'Two Beautiful Young Women Taki'→**'极简女性'** | ✓
- #33816 `webtomind` 摄影/电影感/写实场景→**头像/人像/写真** | 'Smartphone Photo of a Beautifu'→**'极简女性'** | ✓
- #33817 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'Vertical 9:16'→**'复古女性'** | 清
- #33818 `webtomind` 摄影/电影感/写实场景→**头像/人像/写真** | 'Ultra-photorealistic Beauty Po'→**'电影感女性'** | 清
- #33820 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | '🐋🍉🥤🍋'→**'摄影作品'** | ✓
- #33821 `webtomind` Logo/品牌/VI→**头像/人像/写真** | '女友聊天'→**'女友聊天'** | ✓
- #33823 `webtomind` UI/App/网页/SaaS→**头像/人像/写真** | '0 on @tapnow_ai'→**'温馨女性'** | ✓
- #33824 `webtomind` Logo/品牌/VI→**摄影/电影感/写实场景** | 'Made with Seednace 2'→**'电影感女性'** | ✓
- #33825 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'Made with Seedance 2'→**'复古女性'** | ✓
- #33829 `webtomind` 摄影/电影感/写实场景→**商业海报/广告/社媒** | 'Ultra-stylized High-fashion Ed'→**'电影感女性'** | ✓
- #33830 `webtomind` UI/App/网页/SaaS→**头像/人像/写真** | 'Smartphone Selfie of a Beautif'→**'极简女性'** | ✓
- #33831 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'Vertical 9:16'→**'复古女性'** | ✓
- #33832 `webtomind` Logo/品牌/VI→**头像/人像/写真** | 'Beautiful Young Woman with Tan'→**'极简女性'** | ✓
- #33833 `webtomind` 其他综合→**其他综合** | 'Seedance로 여름 호캉스 브이로그 찍기 with '→**'AI 生成图片'** | ✓
- #33835 `webtomind` Logo/品牌/VI→**摄影/电影感/写实场景** | 'Restaurant Promotion Video (ft'→**'电影感女性'** | ✓
- #33836 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | '国漫女性角色中我的最爱：吹茶仙子宋玉'→**'国漫女性角色中我的最爱：吹茶仙子宋玉'** | 清
- #33837 `webtomind` UI/App/网页/SaaS→**头像/人像/写真** | 'Dusk Evening by the Sea'→**'电影感女性'** | ✓
- #33844 `webtomind` 摄影/电影感/写实场景→**头像/人像/写真** | 'Smartphone Photo of a Beautifu'→**'街拍女性'** | ✓
- #33845 `webtomind` 头像/人像/写真→**头像/人像/写真** | 'Korean Nightlife Fashion Portr'→**'电影感女性'** | 清
- #33849 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'Smartphone Photo'→**'霓虹女性'** | ✓
- #33850 `webtomind` 摄影/电影感/写实场景→**摄影/电影感/写实场景** | 'RAW Photograph'→**'电影感女性'** | ✓
- #33851 `webtomind` 头像/人像/写真→**头像/人像/写真** | '9:16 Full-body Fashion Portrai'→**'极简女性'** | ✓
- #33852 `webtomind` 头像/人像/写真→**头像/人像/写真** | 'Retro CCD Fashion Portrait'→**'电影感女性'** | ✓
- #33853 `webtomind` UI/App/网页/SaaS→**头像/人像/写真** | 'High-quality Ultra-realistic I'→**'高级感女性'** | ✓
- …（其余变更见脚本 scripts/process_collect_20260728.py 重跑可全量查看）

## 待用户侧（不自动做）
- `upload_r2_req.py --only twitter` 推 images/twitter/* 到 R2；重传 shuixian-deploy/ 到 Cloudflare Pages 并 Purge Cache。

## 备注
- 另有 **58 条** source=None 的原 twitter 条目开头仍带 `Prompt:` 装饰前缀（更早抓取遗留，非本轮更新），本轮按范围未动；如需一并清理可告知。