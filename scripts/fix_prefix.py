# -*- coding: utf-8 -*-
"""修复rule_id前缀：dynamic_huangjince_ -> classic_huangjince_dynamic_"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('rule_id="dynamic_huangjince_', 'rule_id="classic_huangjince_dynamic_')

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed rule_id prefixes")
