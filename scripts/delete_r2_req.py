#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delete objects from Cloudflare R2 by key list (SigV4 DELETE).
Reads keys from a file (one key per line). Credentials from env (not on disk).
Usage:
  python delete_r2_req.py --keys scripts/_delete_keys.txt --workers 32
"""
import os, sys, hashlib, hmac, datetime, argparse, concurrent.futures as cf

try:
    import requests
except ImportError:
    print("缺少 requests"); sys.exit(1)

EMPTY_HASH = hashlib.sha256(b"").hexdigest()

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def sig_key(secret, datestamp, region, service):
    k = sign(("AWS4" + secret).encode("utf-8"), datestamp)
    k = sign(k, region)
    k = sign(k, service)
    k = sign(k, "aws4_request")
    return k

def delete_one(account, bucket, access, secret, endpoint, key):
    t = datetime.datetime.utcnow()
    amz = t.strftime("%Y%m%dT%H%M%SZ")
    ds = t.strftime("%Y%m%d")
    host = f"{account}.r2.cloudflarestorage.com"
    url = f"{endpoint}/{bucket}/{key}"
    ph = EMPTY_HASH
    chead = f"host:{host}\nx-amz-content-sha256:{ph}\nx-amz-date:{amz}\n"
    creq = "DELETE\n" + f"/{bucket}/{key}\n\n" + chead + "\n" + "host;x-amz-content-sha256;x-amz-date\n" + ph
    scope = f"{ds}/auto/s3/aws4_request"
    sts = "AWS4-HMAC-SHA256\n" + amz + "\n" + scope + "\n" + hashlib.sha256(creq.encode()).hexdigest()
    sk = sig_key(secret, ds, "auto", "s3")
    sig = hmac.new(sk, sts.encode(), hashlib.sha256).hexdigest()
    auth = ("AWS4-HMAC-SHA256 Credential=" + access + "/" + scope +
            ", SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=" + sig)
    headers = {"host": host, "x-amz-content-sha256": ph, "x-amz-date": amz, "Authorization": auth}
    r = requests.delete(url, headers=headers, timeout=30)
    return r.status_code

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    account = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET"]
    access = os.environ["R2_ACCESS_KEY"]
    secret = os.environ["R2_SECRET_KEY"]
    endpoint = f"https://{account}.r2.cloudflarestorage.com"
    with open(args.keys, encoding="utf-8") as f:
        keys = [l.strip() for l in f if l.strip()]
    print(f"total keys: {len(keys)}")
    if args.dry_run:
        print("dry-run, no deletion"); return
    ok = 0; miss = 0; err = 0; errs = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(delete_one, account, bucket, access, secret, endpoint, k): k for k in keys}
        done = 0
        for fut in cf.as_completed(futs):
            done += 1
            k = futs[fut]
            try:
                code = fut.result()
                if code in (200, 204, 404):
                    ok += 1
                else:
                    miss += 1
                    errs.append((k, code))
            except Exception as e:
                err += 1
                errs.append((k, str(e)[:80]))
            if done % 200 == 0:
                print(f"  {done}/{len(keys)} ok={ok} miss={miss} err={err}")
    print(f"DONE ok={ok} (含已不存在404) miss={miss} err={err}")
    if errs[:10]:
        print("samples:", errs[:10])

if __name__ == "__main__":
    main()
