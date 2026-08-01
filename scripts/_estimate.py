import os, random, time, concurrent.futures as cf
import requests

BASE = "https://pub-54e40727ca014de0a7fecf608f7b0412.r2.dev"
IMG = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts\images"
SAMPLE = 120

def hit_rate(sub, total_local):
    d = os.path.join(IMG, sub)
    files = os.listdir(d)
    n_local = len(files)
    samp = random.sample(files, min(SAMPLE, n_local))
    urls = [f"{BASE}/images/{sub}/{f}" for f in samp]
    ok = 0
    def probe(u):
        try:
            r = requests.head(u, timeout=15)
            return 1 if r.status_code == 200 else 0
        except Exception:
            return 0
    with cf.ThreadPoolExecutor(max_workers=40) as ex:
        ok = sum(ex.map(probe, urls))
    rate = ok / len(urls)
    est = int(rate * n_local)
    return n_local, ok, len(urls), rate, est

for sub in ("thumbs", "originals"):
    n_local, ok, ns, rate, est = hit_rate(sub, 0)
    print(f"{sub}: local={n_local} sampled={ns} hits={ok} rate={rate*100:.1f}% -> estimated uploaded ≈ {est:,}")
