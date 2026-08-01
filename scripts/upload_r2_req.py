#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 requests + AWS SigV4 把 images/ 上传到 Cloudflare R2（无需 boto3）。
凭证从环境变量读取（不落盘）：
  R2_ACCOUNT_ID  账户ID
  R2_BUCKET      桶名
  R2_ACCESS_KEY  R2 API 令牌 Access Key ID
  R2_SECRET_KEY  R2 API 令牌 Secret Access Key

用法：
  python upload_r2_req.py --workers 16
  python upload_r2_req.py --only thumbs
  python upload_r2_req.py --dry-run
"""
import os, sys, re, json, hashlib, hmac, datetime, argparse, concurrent.futures as cf, urllib.parse

try:
    import requests
except ImportError:
    print("缺少 requests，请先: pip install requests")
    sys.exit(1)

IMG_DIR = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts\images"

CT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
      ".webp": "image/webp", ".gif": "image/gif"}


def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def sig_key(secret, datestamp, region, service):
    k = sign(("AWS4" + secret).encode("utf-8"), datestamp)
    k = sign(k, region)
    k = sign(k, service)
    k = sign(k, "aws4_request")
    return k


def list_objects_v2(account, bucket, access, secret, prefix):
    """ListObjectsV2，返回指定前缀下的所有 Key 列表。"""
    keys = []
    token = None
    host = f"{account}.r2.cloudflarestorage.com"
    uri = f"/{bucket}/"
    empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    while True:
        qs = [("list-type", "2"), ("prefix", prefix), ("max-keys", "1000")]
        if token:
            qs.append(("continuation-token", token))
        qs.sort(key=lambda x: x[0])
        qstr = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
            for k, v in qs
        )
        t = datetime.datetime.now(datetime.timezone.utc)
        amz = t.strftime("%Y%m%dT%H%M%SZ")
        ds = t.strftime("%Y%m%d")
        chead = f"host:{host}\nx-amz-content-sha256:{empty}\nx-amz-date:{amz}\n"
        creq = f"GET\n{uri}\n{qstr}\n{chead}\nhost;x-amz-content-sha256;x-amz-date\n{empty}"
        scope = f"{ds}/auto/s3/aws4_request"
        sts = "AWS4-HMAC-SHA256\n" + amz + "\n" + scope + "\n" + hashlib.sha256(creq.encode()).hexdigest()
        sk = sig_key(secret, ds, "auto", "s3")
        sig = hmac.new(sk, sts.encode("utf-8"), hashlib.sha256).hexdigest()
        auth = ("AWS4-HMAC-SHA256 Credential=" + access + "/" + scope +
                ", SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=" + sig)
        url = f"https://{host}{uri}?{qstr}"
        r = requests.get(url, headers={
            "host": host, "x-amz-content-sha256": empty, "x-amz-date": amz,
            "Authorization": auth
        }, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"ListObjectsV2 failed {r.status_code}: {r.text[:200]}")
        body = r.text
        keys.extend(re.findall(r"<Key>([^<]+)</Key>", body))
        if "<IsTruncated>true</IsTruncated>" in body:
            m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", body)
            token = m.group(1) if m else None
        else:
            break
    return keys


def collect(only=None, pattern=None):
    rx = re.compile(pattern) if pattern else None
    items = []
    subs = []
    for sub in ("thumbs", "originals", "twitter"):
        if only and sub not in only:
            continue
        subs.append(sub)
    # twitter 扩展文件夹：images/twitter-<slug>/ 也归入 twitter 范畴（新分类独立文件夹）
    if only is None or "twitter" in only:
        for name in sorted(os.listdir(IMG_DIR)):
            if name != "twitter" and name.startswith("twitter") and os.path.isdir(os.path.join(IMG_DIR, name)):
                subs.append(name)
    for sub in subs:
        d = os.path.join(IMG_DIR, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.lower().endswith(tuple(CT)):
                if rx and not rx.search(fn):
                    continue
                items.append((os.path.join(d, fn), f"images/{sub}/{fn}"))
    return items


def upload_one(account, bucket, access, secret, endpoint, fp, key, force):
    with open(fp, "rb") as f:
        data = f.read()
    t = datetime.datetime.utcnow()
    amz = t.strftime("%Y%m%dT%H%M%SZ")
    ds = t.strftime("%Y%m%d")
    ph = hashlib.sha256(data).hexdigest()
    host = f"{account}.r2.cloudflarestorage.com"
    url = f"{endpoint}/{bucket}/{key}"
    chead = f"host:{host}\nx-amz-content-sha256:{ph}\nx-amz-date:{amz}\n"
    creq = "PUT\n" + f"/{bucket}/{key}\n\n" + chead + "\n" + "host;x-amz-content-sha256;x-amz-date\n" + ph
    scope = f"{ds}/auto/s3/aws4_request"
    sts = "AWS4-HMAC-SHA256\n" + amz + "\n" + scope + "\n" + hashlib.sha256(creq.encode()).hexdigest()
    sk = sig_key(secret, ds, "auto", "s3")
    sig = hmac.new(sk, sts.encode(), hashlib.sha256).hexdigest()
    auth = ("AWS4-HMAC-SHA256 Credential=" + access + "/" + scope +
            ", SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=" + sig)
    headers = {"host": host, "x-amz-content-sha256": ph, "x-amz-date": amz,
               "Authorization": auth, "Content-Type": CT.get(os.path.splitext(fp)[1].lower(), "application/octet-stream")}
    r = requests.put(url, data=data, headers=headers, timeout=120)
    if r.status_code >= 400:
        return f"ERR {r.status_code} {r.text[:120]}"
    return "put"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--only", choices=["thumbs", "originals", "twitter"], default=None)
    ap.add_argument("--pattern", default=None, help="仅上传文件名匹配此正则的图片（如 '29[4-9][0-9][0-9]\\.jpg'）")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-existing", action="store_true",
                    help="先列出 R2 上已存在的 key，跳过已存在的文件（真正的增量上传）")
    args = ap.parse_args()

    account = os.environ.get("R2_ACCOUNT_ID")
    bucket = os.environ.get("R2_BUCKET")
    access = os.environ.get("R2_ACCESS_KEY")
    secret = os.environ.get("R2_SECRET_KEY")
    need_cred = (not args.dry_run) or args.skip_existing
    if need_cred and not (account and bucket and access and secret):
        print("缺少环境变量 R2_ACCOUNT_ID / R2_BUCKET / R2_ACCESS_KEY / R2_SECRET_KEY")
        sys.exit(1)
    endpoint = f"https://{account}.r2.cloudflarestorage.com" if account else ""

    items = collect(args.only, args.pattern)

    # ---- 真正的增量：跳过 R2 上已存在的 key ----
    if args.skip_existing:
        prefixes = set()
        for _, key in items:
            # key 形如 images/twitter/xxx.jpg 或 images/twitter-cat1/xxx.jpg
            prefix = key[:key.rfind("/") + 1]
            prefixes.add(prefix)
        existing = set()
        print(f"🔍 正在扫描 R2 已存在对象（{len(prefixes)} 个前缀）...")
        for prefix in sorted(prefixes):
            ks = list_objects_v2(account, bucket, access, secret, prefix)
            existing.update(ks)
            print(f"   {prefix}: {len(ks)} 个已存在")
        before = len(items)
        items = [(fp, key) for fp, key in items if key not in existing]
        skipped = before - len(items)
        print(f"⏭ 跳过已存在: {skipped} 个")

    total = len(items)
    gb = sum(os.path.getsize(fp) for fp, _ in items) / 1024 / 1024 / 1024
    print(f"待上传: {total:,} 个, {gb:.2f} GB" + ("  [dry-run]" if args.dry_run else ""))
    if args.dry_run:
        return

    done = {"put": 0, "err": 0}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(upload_one, account, bucket, access, secret, endpoint, fp, key, args.force) for fp, key in items]
        for i, f in enumerate(futs, 1):
            try:
                res = f.result()
            except Exception as e:
                done["err"] += 1
                if done["err"] <= 5:
                    print("ERR", e)
                res = "err"
            if res != "put":
                done["err"] += 1
                if done["err"] <= 5:
                    print(res)
            else:
                done["put"] += 1
            if i % 1000 == 0:
                print(f"进度 {i:,}/{total:,} put={done['put']} err={done['err']}")
    print(f"\n完成: put={done['put']} err={done['err']}")


if __name__ == "__main__":
    main()
