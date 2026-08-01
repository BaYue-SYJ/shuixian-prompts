#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feasibility probe: confirm YouMind API responds and `media` originals are downloadable."""
import json, os, time, urllib.request, urllib.error

API_URL = "https://youmind.com/youmarketing-api/prompts"
REFERER = "https://youmind.com/zh-CN/gpt-image-2-prompts/explore?sortBy=views&sortOrder=desc"
OUT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\scripts\probe_out"

os.makedirs(OUT, exist_ok=True)

def post_json(payload):
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': REFERER,
    }
    req = urllib.request.Request(API_URL, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def download(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': REFERER})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    with open(path, 'wb') as f:
        f.write(body)
    return len(body)

payload = {"model": "gpt-image-2", "limit": 5, "locale": "zh-CN", "q": "",
           "categories": "", "campaign": None, "filterMode": None,
           "searchMode": None, "sortBy": "views", "sortOrder": "desc", "page": 1}

print("== POST prompts page 1 (limit=5) ==")
data = post_json(payload)
print("total:", data.get('total'), "| totalPages:", data.get('totalPages'), "| hasMore:", data.get('hasMore'))
print("returned:", len(data.get('prompts', [])))
print()

for i, p in enumerate(data.get('prompts', [])):
    pid = p.get('id')
    media = p.get('media', []) or []
    thumbs = p.get('mediaThumbnails', []) or []
    orig = media[0] if media else ''
    thumb = thumbs[0] if thumbs else ''
    cats = p.get('promptCategories', []) or []
    title = (p.get('title') or '')[:40]
    print(f"[{i}] id={pid}")
    print(f"    title: {title}")
    print(f"    promptCategories: {cats}")
    print(f"    media[0] original: {orig[:120]}")
    print(f"    mediaThumbnails[0]: {thumb[:120]}")
    # Download the ORIGINAL to compare size vs thumbnail
    if orig:
        try:
            op = os.path.join(OUT, f"orig_{pid}.bin")
            sz = download(orig, op)
            print(f"    >>> downloaded ORIGINAL: {sz} bytes -> {os.path.basename(op)}")
        except Exception as e:
            print(f"    >>> ORIGINAL download FAILED: {e}")
    if thumb:
        try:
            tp = os.path.join(OUT, f"thumb_{pid}.bin")
            sz = download(thumb, tp)
            print(f"    >>> downloaded THUMB:    {sz} bytes -> {os.path.basename(tp)}")
        except Exception as e:
            print(f"    >>> THUMB download FAILED: {e}")
    print()

print("== probe done ==")
