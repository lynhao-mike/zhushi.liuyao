# -*- coding: utf-8 -*-
"""检查自动编译生成的规则"""
from pathlib import Path
import json

judgements_path = Path("data/classic_judgements.jsonl")
with open(judgements_path, 'r', encoding='utf-8') as f:
    judgements = [json.loads(line) for line in f]

# 检查第四批的3个judgement ID是否存在
batch4_ids = [
    "classic_huangjince_e22183be6692",
    "classic_huangjince_902d8f46b5d2",
    "classic_huangjince_315234a45a5b",
]

judgement_map = {j['id']: j for j in judgements}

print(f"Total judgements: {len(judgements)}")
print(f"\nChecking batch 4 judgement IDs:")
for jid in batch4_ids:
    if jid in judgement_map:
        j = judgement_map[jid]
        print(f"  [OK] {jid}")
        print(f"    Text: {j['raw_text'][:50]}...")
    else:
        print(f"  [MISSING] {jid}")

# 检查生成的候选规则
rules_path = Path("data/huangjince_candidate_rules.jsonl")
with open(rules_path, 'r', encoding='utf-8') as f:
    rules = [json.loads(line) for line in f]

print(f"\nTotal candidate rules: {len(rules)}")
print("\nLast 5 rule IDs:")
for r in rules[-5:]:
    print(f"  {r['id']}")
