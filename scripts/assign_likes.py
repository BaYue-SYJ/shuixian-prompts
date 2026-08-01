#!/usr/bin/env python3
"""
给所有数据写入 likes 热度分，并同步到部署版；同时生成热度统计。
热度规则：图片数*5 + 人物热词 + 视觉热词 + 标题长度适中 + 基础随机。
"""
import json, re, random, shutil
from pathlib import Path
from collections import Counter

random.seed(42)
BASE = Path('C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54')
LOCAL = BASE / 'shuixian-prompts/data'
DEPLOY = BASE / 'shuixian-deploy/data'

HOT_PERSON = re.compile(r'美女|帅哥|人像|少女|写真|头像|自拍|女性|女神|男神|woman|girl|portrait|selfie|人物|角色|cosplay')
HOT_VISUAL = re.compile(r'电影感|霓虹|胶片|8K|超写实|高清|真实|细腻|精致|氛围|光影|cinematic|realistic|photo')


def heat(e):
    s = 0
    imgs = list(e.get('images', []))
    if e.get('thumb') and e.get('thumb') not in imgs:
        imgs = [e.get('thumb')] + imgs
    s += min(len(imgs), 6) * 5
    text = (e.get('title', '') + ' ' + e.get('prompt', '')).lower()
    if HOT_PERSON.search(text):
        s += 20
    if HOT_VISUAL.search(text):
        s += 10
    tl = len(e.get('title', ''))
    if 10 <= tl <= 30:
        s += 5
    s += random.randint(0, 40)
    return int(s)


def main():
    files = ['prompts.json', 'prompts-twitter.json', 'prompts-twitter-cat1.json', 'prompts-twitter-cat2.json']
    all_data = []
    for fn in files:
        data = json.load(open(LOCAL / fn, 'r', encoding='utf-8'))
        for e in data:
            e['likes'] = heat(e)
        (LOCAL / fn).write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        all_data.extend(data)
        c = Counter(e['likes'] for e in data)
        print(f'{fn}: {len(data)} 条, likes 范围 {min(c)}-{max(c)}, 常见 {c.most_common(3)}')

    # 同步到部署版
    DEPLOY.mkdir(parents=True, exist_ok=True)
    for fn in ['prompts-twitter.json', 'prompts-twitter-cat1.json', 'prompts-twitter-cat2.json']:
        shutil.copy2(LOCAL / fn, DEPLOY / fn)

    # 拆分 prompts.json
    main_data = json.load(open(LOCAL / 'prompts.json', 'r', encoding='utf-8'))
    n_parts = 3
    total = len(main_data)
    base = total // n_parts
    rem = total % n_parts
    sizes = [base + (1 if i < rem else 0) for i in range(n_parts)]
    idx = 0
    for i, size in enumerate(sizes, 1):
        part = main_data[idx:idx + size]
        (DEPLOY / f'prompts.part{i}.json').write_text(
            json.dumps(part, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        idx += size
    print(f'部署 prompts.json 拆分: {sizes}')

    # 生成总体热度统计
    total_likes = sum(e['likes'] for e in all_data)
    top10 = sorted(all_data, key=lambda x: x['likes'], reverse=True)[:10]
    print(f'\n总热度分: {total_likes}, 平均: {total_likes / len(all_data):.1f}')
    print('Top 10 热度条目:')
    for e in top10:
        print(f'  likes={e["likes"]} id={e["id"]} title={e.get("title","")[:30]}')


if __name__ == '__main__':
    main()
