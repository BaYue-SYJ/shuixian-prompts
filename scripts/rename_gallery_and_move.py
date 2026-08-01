#!/usr/bin/env python3
"""
把 "画图展示" 改名为 "画廊"，并把标题含 "AI 人像生成分享" 的条目归类为 "画廊"。
处理本地 + 部署两端数据，重新生成 categories.json 与部署分片。
"""
import json, re, shutil
from pathlib import Path
from collections import Counter

BASE = Path('C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54')
LOCAL = BASE / 'shuixian-prompts/data'
DEPLOY = BASE / 'shuixian-deploy/data'

TITLE_PAT = re.compile(r'AI\s*人像\s*生成\s*分享')
OLD_CAT = '画图展示'
NEW_CAT = '画廊'


def update_categories(data):
    changed = 0
    for e in data:
        cat = e.get('category', '')
        title = e.get('title', '')
        if cat == OLD_CAT:
            e['category'] = NEW_CAT
            changed += 1
        if TITLE_PAT.search(title):
            if e.get('category') != NEW_CAT:
                e['category'] = NEW_CAT
                changed += 1
    return changed


def regen_categories(data_list, out_path):
    total = 0
    c = Counter()
    for data in data_list:
        total += len(data)
        for e in data:
            c[e.get('category', '')] += 1
    categories = [{'category': cat, 'count': n, 'pct': round(n / total * 100, 2)} for cat, n in c.most_common()]
    out = {'total': total, 'categories': categories}
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    return out


def split_prompts(data, out_dir, prefix='prompts.part', n_parts=3):
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(data)
    base = total // n_parts
    rem = total % n_parts
    sizes = [base + (1 if i < rem else 0) for i in range(n_parts)]
    idx = 0
    for i, size in enumerate(sizes, 1):
        part = data[idx:idx + size]
        out_path = out_dir / f'{prefix}{i}.json'
        out_path.write_text(json.dumps(part, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        idx += size
    return sizes


def main():
    # 1. 读取本地数据
    local_files = {
        'prompts.json': LOCAL / 'prompts.json',
        'prompts-twitter.json': LOCAL / 'prompts-twitter.json',
        'prompts-twitter-cat1.json': LOCAL / 'prompts-twitter-cat1.json',
        'prompts-twitter-cat2.json': LOCAL / 'prompts-twitter-cat2.json',
    }
    local_data = {k: json.load(open(v, 'r', encoding='utf-8')) for k, v in local_files.items()}

    # 2. 修改分类
    total_changed = 0
    for name, data in local_data.items():
        n = update_categories(data)
        total_changed += n
        print(f'本地 {name}: 改动 {n} 条')

    # 3. 写回本地 JSON
    for name, data in local_data.items():
        local_files[name].write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # 4. 重新生成本地 categories.json
    local_cat = regen_categories(local_data.values(), LOCAL / 'categories.json')
    print(f'\n本地 categories.json: total={local_cat["total"]}')
    for item in local_cat['categories']:
        print(f'  {item["category"]}: {item["count"]} ({item["pct"]}%)')

    # 5. 同步到部署版
    DEPLOY.mkdir(parents=True, exist_ok=True)
    # 复制 twitter 文件
    for name in ['prompts-twitter.json', 'prompts-twitter-cat1.json', 'prompts-twitter-cat2.json']:
        shutil.copy2(local_files[name], DEPLOY / name)
    # 拆分 prompts.json
    sizes = split_prompts(local_data['prompts.json'], DEPLOY)
    print(f'\n部署 prompts.json 拆分: {sizes}')

    # 6. 重新生成部署版 categories.json（含 part 文件 + twitter 文件）
    deploy_all = [
        json.load(open(DEPLOY / 'prompts.part1.json', 'r', encoding='utf-8')),
        json.load(open(DEPLOY / 'prompts.part2.json', 'r', encoding='utf-8')),
        json.load(open(DEPLOY / 'prompts.part3.json', 'r', encoding='utf-8')),
        json.load(open(DEPLOY / 'prompts-twitter.json', 'r', encoding='utf-8')),
        json.load(open(DEPLOY / 'prompts-twitter-cat1.json', 'r', encoding='utf-8')),
        json.load(open(DEPLOY / 'prompts-twitter-cat2.json', 'r', encoding='utf-8')),
    ]
    deploy_cat = regen_categories(deploy_all, DEPLOY / 'categories.json')
    print(f'\n部署 categories.json: total={deploy_cat["total"]}')
    for item in deploy_cat['categories']:
        print(f'  {item["category"]}: {item["count"]} ({item["pct"]}%)')

    print(f'\n总计改动条目数: {total_changed}')


if __name__ == '__main__':
    main()
