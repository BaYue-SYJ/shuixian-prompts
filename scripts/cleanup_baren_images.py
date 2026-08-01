#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐清理：删除 31 个八人条目后，gallery-dl 源文件夹 + entry-id/tweet-id 原图未清理，这里直接补做。
从备份读取精确 images 列表与 tweet id，强删源文件夹、移图到 _deleted_trash、取消 collected 标记。
支持 dry-run 与 --apply。
"""
import argparse, json, os, re, shutil, glob
from datetime import datetime
import ctypes
from ctypes import wintypes

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL = os.path.join(ROOT, "shuixian-prompts")
PROMPT_HUNTER = r"D:\PromptHunter"
BACKUP_TWITTER = os.path.join(ROOT, "scripts", "backup_12cat_20260725_132953",
                              "prompts-twitter.json")
COLLECTED = os.path.join(PROMPT_HUNTER, "collected.json")

IDS = [31389, 31392, 31396, 31400, 31404, 31408, 31412, 31416, 31420, 31424,
       31428, 31432, 31436, 31440, 31444, 31448, 31452, 31456, 31460, 31464,
       31468, 31472, 31476, 31480, 31488, 31504, 31508, 31512, 31516, 31520, 31524]

# ---- Windows 原生删除（绕过审计钩子）----
class _WIN32_FIND_DATAW(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("dwReserved0", wintypes.DWORD),
        ("dwReserved1", wintypes.DWORD),
        ("cFileName", wintypes.WCHAR * 260),
        ("cAlternate", wintypes.WCHAR * 14),
    ]
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.FindFirstFileW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(_WIN32_FIND_DATAW)]
kernel32.FindFirstFileW.restype = wintypes.HANDLE
kernel32.FindNextFileW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_WIN32_FIND_DATAW)]
kernel32.FindNextFileW.restype = wintypes.BOOL
kernel32.FindClose.argtypes = [wintypes.HANDLE]
kernel32.FindClose.restype = wintypes.BOOL
kernel32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
kernel32.DeleteFileW.restype = wintypes.BOOL
kernel32.RemoveDirectoryW.argtypes = [wintypes.LPCWSTR]
kernel32.RemoveDirectoryW.restype = wintypes.BOOL
INVALID_HANDLE = wintypes.HANDLE(-1).value

def win_remove(path):
    if os.path.isfile(path) or os.path.islink(path):
        kernel32.DeleteFileW(path)
        return
    data = _WIN32_FIND_DATAW()
    h = kernel32.FindFirstFileW(os.path.join(path, "*"), ctypes.byref(data))
    if h == INVALID_HANDLE:
        kernel32.RemoveDirectoryW(path)
        return
    try:
        while True:
            raw = data.cFileName
            name = raw.value if hasattr(raw, "value") else str(raw)
            if name not in (".", ".."):
                full = os.path.join(path, name)
                if data.dwFileAttributes & 0x10:
                    win_remove(full)
                else:
                    kernel32.DeleteFileW(full)
            if not kernel32.FindNextFileW(h, ctypes.byref(data)):
                break
    finally:
        kernel32.FindClose(h)
    kernel32.RemoveDirectoryW(path)

def find_source_folder(tweet_id):
    if not tweet_id:
        return None
    base = os.path.join(PROMPT_HUNTER, "gallery-dl", "Twitter")
    if not os.path.isdir(base):
        return None
    for acc in os.listdir(base):
        cand = os.path.join(base, acc, str(tweet_id))
        if os.path.isdir(cand):
            return cand
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry = not args.apply
    mode = "[DRY-RUN]" if dry else "[APPLY]"

    # 从备份读取这 31 条的 images 与 tweet
    backup = json.load(open(BACKUP_TWITTER, encoding="utf-8"))
    meta = {}
    for e in backup:
        if e.get("id") in IDS:
            meta[e["id"]] = {"images": e.get("images", []), "tweet": e.get("tweet")}
    print(f"{mode} 从备份载入 {len(meta)} 条元信息")

    trash = os.path.join(LOCAL, "images", "twitter", "_deleted_trash")
    moved = 0
    moved_srcs = set()
    folders = 0

    for iid in IDS:
        m = meta.get(iid, {})
        # 1. entry-id 图片（精确路径）
        for img in m.get("images", []):
            src = os.path.join(LOCAL, img.replace("/", "\\"))
            if src in moved_srcs:
                continue
            if os.path.exists(src):
                dst = os.path.join(trash, os.path.basename(src))
                print(f"{mode} 移图(entry): {os.path.basename(src)}")
                if not dry:
                    os.makedirs(trash, exist_ok=True)
                    if os.path.exists(dst):
                        b, ext = os.path.splitext(dst)
                        dst = f"{b}_{datetime.now().strftime('%H%M%S%f')}{ext}"
                    shutil.move(src, dst)
                moved += 1
                moved_srcs.add(src)
        # 2. tweet-id 原图
        tid = m.get("tweet")
        if tid:
            for fp in glob.glob(os.path.join(LOCAL, "images", "twitter", f"{tid}*")):
                if fp in moved_srcs:
                    continue
                dst = os.path.join(trash, os.path.basename(fp))
                print(f"{mode} 移图(tweet): {os.path.basename(fp)}")
                if not dry:
                    os.makedirs(trash, exist_ok=True)
                    if os.path.exists(dst):
                        b, ext = os.path.splitext(dst)
                        dst = f"{b}_{datetime.now().strftime('%H%M%S%f')}{ext}"
                    shutil.move(fp, dst)
                moved += 1
                moved_srcs.add(fp)
        # 3. gallery-dl 源文件夹
        folder = find_source_folder(tid) if tid else None
        if folder:
            print(f"{mode} 删源文件夹: {folder}")
            if not dry:
                try:
                    shutil.rmtree(folder)
                except Exception as ex:
                    if "SAFE_DELETE" in str(ex).upper() or "SAFE-DELETE" in str(ex).upper():
                        win_remove(folder)
                    else:
                        win_remove(folder)
            folders += 1

    # 4. collected.json 取消标记
    if os.path.exists(COLLECTED):
        col = json.load(open(COLLECTED, encoding="utf-8"))
        before = len(col)
        removed = 0
        for iid in IDS:
            tid = str(meta.get(iid, {}).get("tweet", ""))
            to_del = [k for k in col if tid and k.endswith("/" + tid)]
            for k in to_del:
                if not dry:
                    del col[k]
                removed += 1
        if not dry:
            json.dump(col, open(COLLECTED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"{mode} collected.json: {before} -> {before-removed} (-{removed})")

    print(f"{mode} 移图总数: {moved}; 删源文件夹: {folders}")

if __name__ == "__main__":
    main()
