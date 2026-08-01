# 水仙的AI提示词 · Cloudflare Pages 部署说明

本文件夹 `shuixian-deploy/` 是**直接拖拽部署到 Cloudflare Pages** 的包（手动上传方式）。

## 重要前提（为什么图片不在本文件夹里）

Cloudflare Pages 的**拖拽上传**限制：
- 单文件 ≤ 25 MiB
- **文件总数 ≤ 1,000 个**

而本项目的图片有 **26,953 个**（缩略图 13,473 + 原图 13,480），远超 1,000 上限，
所以**所有图片都走 Cloudflare R2 对象存储**，Pages 里只放 HTML + 拆分后的数据（仅 6 个文件）。

> 本部署包内容：`index.html`、`data/prompts.part1~3.json`、`data/categories.json`、`images/wechat-qr.jpg`
> 总计 6 个文件 / 约 25 MB，完全符合拖拽限制。

---

## 部署步骤

### 第 0 步（可选）：本地预览部署包
直接双击 `shuixian-deploy/index.html` 会因 `fetch` 被 CORS 拦截。**仅用于确认页面结构**，
图片需配置 R2 后才显示。建议用本地服务器：
```
cd shuixian-deploy
python -m http.server 8091
# 浏览器打开 http://localhost:8091
```

### 第 1 步：创建 R2 存储桶并开启公共访问
1. 登录 Cloudflare 控制台 → **R2** → 创建桶（例如 `shuixian-images`）。
2. 进入桶 → **Settings** → 开启 **Public access（公共访问）**，拿到公共域名
   形如 `https://shuixian-images.<subdomain>.r2.dev` 或你绑定的自定义域名 `https://cdn.example.com`。
3. 进入桶 → **Manage R2 API tokens** → 创建令牌（读写权限），记下
   **Access Key ID / Secret Access Key**，以及你的**账户 ID**（URL 里 `https://dash.cloudflare.com/<账户ID>/r2`）。

### 第 2 步：上传图片到 R2
方式 A（推荐，快）：用本项目脚本 `scripts/upload_r2.py`
```bash
pip install boto3
export AWS_ACCESS_KEY_ID="你的R2访问Key"
export AWS_SECRET_ACCESS_KEY="你的R2密钥"
export AWS_ENDPOINT_URL="https://<你的账户ID>.r2.cloudflarestorage.com"
python scripts/upload_r2.py --bucket shuixian-images --workers 16
# 只想先让画廊出图，可只传缩略图：--only thumbs
```
方式 B（rclone，最快、可断点续传）：
```
rclone config  # 新建 S3 类型远程，提供商选 Cloudflare R2，填入 endpoint/key/secret
rclone copy "C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts\images" shuxianR2:shuixian-images --progress
```
方式 C（不写命令）：在 R2 桶页面直接「Upload」拖入 `images` 文件夹（支持大量文件）。

图片在 R2 中的 key 形如 `images/thumbs/xxx.jpg`、`images/originals/xxx.jpg`，
与页面 `IMG_BASE + "/" + 路径` 一致。

### 第 3 步：填入 R2 域名（关键）
打开 `shuixian-deploy/index.html`，找到这一行：
```js
const IMG_BASE = "https://<YOUR-BUCKET>.r2.dev";
```
把 `<YOUR-BUCKET>.r2.dev` 改成你第 1 步拿到的真实公共域名（含 `https://`）。
例如：`const IMG_BASE = "https://shuixian-images.ab12cd.r2.dev";`

> 若已绑定自定义域名：`const IMG_BASE = "https://cdn.example.com";`

### 第 4 步：拖拽部署到 Pages
1. Cloudflare 控制台 → **Workers & Pages** → **Create** → **Pages** → **Upload Assets（直接上传）**。
2. 项目名填 `shuixian-prompts`（或你喜欢的名字）。
3. 把本文件夹 `shuixian-deploy/` 整个拖进上传框 → **Save and Deploy**。
4. 部署完成后得到 `https://shuixian-prompts.pages.dev`，即为线上地址。

### 第 5 步（可选）：绑定自定义域名
Pages 项目 → **Custom domains** → 添加你的域名，按提示在 DNS 加 CNAME。

---

## 顺序提示
- 若**先有 R2**：在第 3 步填好域名后直接第 4 步，部署完图片即可见。
- 若**先拖拽**：部署后画廊暂时显示占位图（图片未就绪），等第 2 步上传完 R2、第 3 步改好域名后，
  **重新拖拽一次**即可显示图片。

## 数据更新
提示词数据来自 `shuixian-prompts/data/prompts.json`。重新生成部署包：
```
python scripts/build_deploy.py
```
会重新拆分并覆盖 `shuixian-deploy/`，之后改 `IMG_BASE` 再拖拽即可。
