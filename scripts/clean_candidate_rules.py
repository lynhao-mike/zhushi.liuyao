# -*- coding: utf-8 -*-
"""清理候选规则文件：移除旧前缀记录，只保留classic_huangjince_dynamic_前缀的记录"""

import json

with open('data/huangjince_candidate_rules.jsonl', 'r', encoding='utf-8') as f:
    records = [json.loads(line) for line in f if line.strip()]

# 过滤：只保留正确前缀的记录，并按ID去重
seen = set()
cleaned = []
for r in records:
    rid = r.get('id', '')
    if rid.startswith('dynamic_huangjince_'):
        continue  # 移除旧前缀记录
    if rid in seen:
        continue
    seen.add(rid)
    cleaned.append(r)

print(f"Before: {len(records)} records, {len({r['id'] for r in records})} unique IDs")
print(f"After: {len(cleaned)} records")

# 保留旧的前3条人工编译记录 + 17条自动编译记录 = 20条
with open('data/huangjince_candidate_rules.jsonl', 'w', encoding='utf-8', newline='\n') as f:
    for r in cleaned:
        f.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n')

print(f"Kept {len(cleaned)} unique rules with correct prefixes")
