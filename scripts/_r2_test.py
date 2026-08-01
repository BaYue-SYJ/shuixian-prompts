import os, sys, time
sys.path.insert(0, r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\scripts")
import upload_r2_req as m

account = os.environ["R2_ACCOUNT_ID"]
bucket = os.environ["R2_BUCKET"]
access = os.environ["R2_ACCESS_KEY"]
secret = os.environ["R2_SECRET_KEY"]
endpoint = f"https://{account}.r2.cloudflarestorage.com"

# 1) plain connectivity probe (no auth) -> should reach Cloudflare (403/400 expected)
print("== probe connectivity ==")
try:
    import requests
    r = requests.get(endpoint, timeout=20)
    print("probe status:", r.status_code, "len:", len(r.text))
except Exception as e:
    print("probe ERROR:", repr(e))

# 2) upload ONE thumbnail to verify SigV4
print("== upload 1 file ==")
items = m.collect("thumbs")
fp, key = items[0]
print("first:", key, os.path.getsize(fp), "bytes; total thumbs:", len(items))
t0 = time.time()
res = m.upload_one(account, bucket, access, secret, endpoint, fp, key, True)
print("upload result:", res, "in", round(time.time()-t0, 2), "s")
