# 水仙的AI提示词

AI 提示词画廊的源码仓库：本地开发版 + 部署版，单一源头管理。

## 目录结构
- `shuixian-prompts/` —— 本地开发版（完整 prompts 数据、分类/重分类脚本、本地预览）
- `shuixian-deploy/` —— 部署版静态站点（直接托管到静态空间即可上线）


## 重要：图片不在 git 中
原图 `images/originals`（2.8G）与 twitter 图 `images/twitter`（5.7G）已托管在 **R2 对象存储**，
画廊通过 R2 域名加载，不依赖本地文件。因此 `shuixian-prompts/images/` 整体被 `.gitignore` 排除；
部署版 `shuixian-deploy/images/` 仅含 2 张页脚微信二维码图。



## 分类体系
当前为 **17 类单标签**（人物优先，非人类主题零泄漏），详见 `reclassify_17cat_strict_report.md`。
- 人物：真人/写实人物、动漫/二次元人物
- 非人 15 类：字体/排版/标题、Logo/品牌/VI、UI/App/网页/SaaS、产品/电商/包装、海报/广告/社媒、
  插画/艺术/概念、漫画/分镜/故事板、信息图/教育图解、3D/游戏/像素/等距、建筑/室内/空间、风景/自然、
  动物/宠物、车辆/机械/科幻、抽象/纹理/背景、其他/未归类



## 本地预览
- 部署版预览：`python -m http.server 8091 --directory shuixian-deploy`
- 本地版预览：`python -m http.server 8090 --directory shuixian-prompts`
