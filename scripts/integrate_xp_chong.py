#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrate xp-chong folder into shuixian-prompts project.
Assumption: Excel rows map to image groups (post IDs) sequentially.
Each image file in a group becomes one gallery entry sharing the row's prompt.
"""
import json, os, re, shutil, glob
from pathlib import Path
from PIL import Image
import openpyxl

BASE_DIR = Path(r"C:\Users\lianxiang\Downloads\xp-chong")
PROJECT_DIR = Path(r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts")
DEPLOY_DIR = Path(r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-deploy")

ORIG_DIR = PROJECT_DIR / "images" / "originals"
THUMB_DIR = PROJECT_DIR / "images" / "thumbs"

def load_prompts():
    with open(PROJECT_DIR / "data" / "prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_prompts(data):
    with open(PROJECT_DIR / "data" / "prompts.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

def load_categories():
    with open(PROJECT_DIR / "data" / "categories.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_categories(cats):
    with open(PROJECT_DIR / "data" / "categories.json", "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False, separators=(",", ":"))

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text or "")
    text = re.sub(r"[-\s]+", "-", text).strip("-").lower()
    return text[:80] or "item"

def make_title(prompt, category, idx):
    if not prompt:
        return f"{category} #{idx}"
    lines = [l.strip() for l in str(prompt).splitlines() if l.strip()]
    if not lines:
        return f"{category} #{idx}"
    first = lines[0]
    # Remove common prefixes like "提示词prompt：", "Prompt:", etc.
    first = re.sub(r"^(提示词|prompt|Prompt)[:：]?\s*", "", first, flags=re.I)
    first = first.strip()
    if len(first) > 60:
        first = first[:57] + "..."
    return first or f"{category} #{idx}"

def group_images(image_dir):
    """Group image files by base ID (numeric prefix before first underscore)."""
    files = sorted([f for f in os.listdir(image_dir)
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])
    groups = {}
    for f in files:
        m = re.match(r"^(\d+)_.*$", f)
        gid = m.group(1) if m else f
        groups.setdefault(gid, []).append(f)
    # Sort each group naturally
    for gid in groups:
        groups[gid].sort(key=lambda x: [int(t) if t.isdigit() else t.lower()
                                        for t in re.split(r"(\d+)", x)])
    return groups

def process_subfolder(subfolder, start_id):
    """Process one xp-chong subfolder. Returns (new_entries, next_id, counts)."""
    folder = BASE_DIR / subfolder
    xlsx_files = list(folder.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"No xlsx found in {folder}")
    xlsx = xlsx_files[0]
    image_dir = folder / "images"
    if not image_dir.exists():
        raise FileNotFoundError(f"No images dir in {folder}")

    # Read prompts from Excel column B, skip header
    wb = openpyxl.load_workbook(str(xlsx), read_only=True, data_only=True)
    ws = wb.active
    prompts = []
    for r, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if r == 1:
            continue
        val = row[1] if len(row) > 1 else None
        if val and str(val).strip():
            prompts.append(str(val).strip())
        else:
            prompts.append(None)

    groups = group_images(image_dir)
    sorted_gids = sorted(groups.keys(), key=lambda x: int(x) if x.isdigit() else x)

    entries = []
    current_id = start_id
    for i, gid in enumerate(sorted_gids):
        prompt = prompts[i] if i < len(prompts) else None
        title = make_title(prompt, subfolder, i + 1)
        for fname in groups[gid]:
            src = image_dir / fname
            ext = ".jpg"
            orig_dst = ORIG_DIR / f"{current_id}{ext}"
            thumb_dst = THUMB_DIR / f"{current_id}{ext}"

            # Copy/convert original
            try:
                im = Image.open(src)
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(orig_dst, "JPEG", quality=92)
            except Exception as e:
                print(f"  SKIP {src}: {e}")
                continue

            # Generate thumbnail: 300px width, preserve aspect ratio
            try:
                im = Image.open(orig_dst)
                im.thumbnail((300, 2000), Image.LANCZOS)
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(thumb_dst, "JPEG", quality=85)
            except Exception as e:
                print(f"  THUMB FAIL {orig_dst}: {e}")
                thumb_dst = orig_dst  # fallback

            slug = f"{slugify(subfolder)}-{gid}-{current_id}"
            entries.append({
                "id": current_id,
                "title": title,
                "prompt": prompt or "",
                "thumb": f"images/thumbs/{current_id}{ext}",
                "image": f"images/originals/{current_id}{ext}",
                "author": subfolder,
                "likes": 0,
                "resultsCount": 0,
                "slug": slug,
                "category": subfolder,
            })
            current_id += 1

    return entries, current_id, {"groups": len(groups), "files": sum(len(v) for v in groups.values()), "prompts": len([p for p in prompts if p])}

def update_categories(data, extra_categories):
    cats = {}
    for d in data:
        c = d.get("category", "其他综合")
        cats[c] = cats.get(c, 0) + 1
    total = len(data)
    # Preserve original order then append extras
    existing_order = ["平面设计","人像写真","摄影纪实","动漫二次元","UI与界面","动物自然","风景建筑","游戏影视","插画艺术","3D与产品","科幻未来","文字Logo","美食料理","其他综合"]
    ordered = [c for c in existing_order if c in cats]
    for c in extra_categories:
        if c in cats and c not in ordered:
            ordered.append(c)
    # Also include any other categories not in known order
    for c in sorted(cats.keys()):
        if c not in ordered:
            ordered.append(c)
    categories = [{"category": c, "count": cats[c], "pct": round(cats[c] / total * 100, 1)} for c in ordered]
    return {"total": total, "categories": categories}

def update_html_categories(html_path, new_categories):
    with open(html_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Update CATEGORIES array
    old_arr = 'const CATEGORIES = ["全部","平面设计","人像写真","摄影纪实","动漫二次元","UI与界面","动物自然","风景建筑","游戏影视","插画艺术","3D与产品","科幻未来","文字Logo","美食料理","其他综合"];'
    existing = ["全部","平面设计","人像写真","摄影纪实","动漫二次元","UI与界面","动物自然","风景建筑","游戏影视","插画艺术","3D与产品","科幻未来","文字Logo","美食料理","其他综合"]
    for c in new_categories:
        if c not in existing:
            existing.append(c)
    new_arr = "const CATEGORIES = [" + ",".join(f'"{c}"' for c in existing) + "];"
    if old_arr not in text:
        # Try to find and replace any CATEGORIES line
        text = re.sub(r'const CATEGORIES = \[[^\]]+\];', new_arr, text)
    else:
        text = text.replace(old_arr, new_arr)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(text)

def split_deploy_data(data):
    # Split into 3 parts similar to original build_deploy.py
    n = len(data)
    part_size = (n + 2) // 3
    parts = [data[i:i+part_size] for i in range(0, n, part_size)]
    # Ensure exactly 3 files
    while len(parts) < 3:
        parts.append([])
    return parts[:3]

def main():
    print("Loading existing data...")
    data = load_prompts()
    start_id = max(d["id"] for d in data) + 1
    print(f"Existing entries: {len(data)}, max id: {start_id - 1}, starting new ids at {start_id}")

    ORIG_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    subfolders = sorted([d for d in os.listdir(BASE_DIR) if (BASE_DIR / d).is_dir()])
    print(f"Found subfolders: {subfolders}")

    all_entries = []
    summary = {}
    for sub in subfolders:
        print(f"\nProcessing {sub}...")
        entries, start_id, counts = process_subfolder(sub, start_id)
        all_entries.extend(entries)
        summary[sub] = counts
        print(f"  -> {counts['files']} images / {counts['groups']} groups / {counts['prompts']} prompts mapped to {len(entries)} entries")

    print(f"\nTotal new entries: {len(all_entries)}")
    data.extend(all_entries)
    save_prompts(data)

    cats = update_categories(data, subfolders)
    save_categories(cats)
    print(f"Updated categories.json: total={cats['total']}")
    for c in cats["categories"]:
        print(f"  {c['category']}: {c['count']} ({c['pct']}%)")

    # Update HTML files
    print("\nUpdating HTML category chips...")
    update_html_categories(PROJECT_DIR / "index.html", subfolders)
    update_html_categories(DEPLOY_DIR / "index.html", subfolders)

    # Regenerate deploy data parts
    print("Regenerating deploy data parts...")
    parts = split_deploy_data(data)
    for i, part in enumerate(parts, start=1):
        with open(DEPLOY_DIR / "data" / f"prompts.part{i}.json", "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  prompts.part{i}.json: {len(part)} entries, {os.path.getsize(DEPLOY_DIR / 'data' / f'prompts.part{i}.json') / 1024 / 1024:.2f} MB")

    # Copy categories.json to deploy
    shutil.copy(PROJECT_DIR / "data" / "categories.json", DEPLOY_DIR / "data" / "categories.json")

    print("\nDone. Summary:")
    for sub, counts in summary.items():
        print(f"  {sub}: {counts['files']} files -> {counts['groups']} groups -> entries with prompt {counts['prompts']}")
    print(f"New total entries: {len(data)}")

if __name__ == "__main__":
    main()
