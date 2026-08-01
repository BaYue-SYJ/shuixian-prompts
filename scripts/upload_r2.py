#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 shuixian-prompts/images/ 下所有图片上传到 Cloudflare R2。
图片在 R2 中的 key 与本地相对路径一致（images/thumbs/xxx.jpg、images/originals/xxx.jpg），
对应部署页 IMG_BASE + "/" + 该路径。

依赖：pip install boto3

环境变量（来自 R2 API 令牌）：
  AWS_ACCESS_KEY_ID      R2 令牌 Access Key ID
  AWS_SECRET_ACCESS_KEY  R2 令牌 Secret Access Key
  AWS_ENDPOINT_URL       https://<你的账户ID>.r2.cloudflarestorage.com

用法：
  # 仅统计（不联网），确认要上传的文件
  python upload_r2.py --bucket shuixian-images --dry-run

  # 正式上传（自动跳过已存在的对象，可用 --force 强制覆盖）
  python upload_r2.py --bucket shuixian-images --workers 16

  # 只上传缩略图（更快先让画廊出图）
  python upload_r2.py --bucket shuixian-images --only thumbs
"""
import os, sys, argparse, concurrent.futures as cf

IMG_DIR = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts\images"


def collect(only=None):
    items = []
    for sub in ("thumbs", "originals"):
        if only and sub not in only:
            continue
        d = os.path.join(IMG_DIR, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                fp = os.path.join(d, fn)
                key = f"images/{sub}/{fn}"
                items.append((fp, key))
    return items


def upload_one(s3, bucket, fp, key, force):
    if not force:
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return "skip"
        except Exception:
            pass
    s3.upload_file(fp, bucket, key)
    return "put"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--endpoint", default=os.environ.get("AWS_ENDPOINT_URL", ""))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--only", choices=["thumbs", "originals"], default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = collect(args.only)
    total = len(items)
    total_bytes = sum(os.path.getsize(fp) for fp, _ in items)
    print(f"待上传文件: {total:,} 个, 总体积: {total_bytes/1024/1024/1024:.2f} GB")
    if args.dry_run:
        print("（dry-run 结束，未联网）")
        return

    if not args.endpoint:
        print("缺少 AWS_ENDPOINT_URL（R2 账户端点），请设置环境变量后重试。")
        sys.exit(1)

    try:
        import boto3
    except ImportError:
        print("未安装 boto3，请先执行: pip install boto3")
        sys.exit(1)

    s3 = boto3.client("s3", endpoint_url=args.endpoint)
    done = {"put": 0, "skip": 0, "err": 0}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(upload_one, s3, args.bucket, fp, key, args.force) for fp, key in items]
        for i, f in enumerate(futs, 1):
            try:
                r = f.result()
            except Exception as e:
                done["err"] += 1
                if done["err"] <= 5:
                    print("ERR", e)
            else:
                done[r] = done.get(r, 0) + 1
            if i % 1000 == 0:
                print(f"进度 {i:,}/{total:,}  put={done['put']} skip={done['skip']} err={done['err']}")
    print(f"\n完成: put={done['put']} skip={done['skip']} err={done['err']}")
    if done["err"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
