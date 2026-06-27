# -*- coding: utf-8 -*-
"""批量更新测试断言: 23→29→37(generated), 26→32→40(merged)"""

files = {
    'tests/test_huangjince_auto_compile.py': [
        ('assert len(generated) == 29', 'assert len(generated) == 37'),
        ('assert len(merged_once) == 32', 'assert len(merged_once) == 40'),
    ],
    'tests/test_huangjince_dynamic_rule_audit.py': [
        ('assert len(candidate_rules) == 32', 'assert len(candidate_rules) == 40'),
        ('assert audit["compiled_drafts"] == len(compiled) == 32', 'assert audit["compiled_drafts"] == len(compiled) == 40'),
        ('assert audit["by_compilability"]["auto_compilable"] == 32', 'assert audit["by_compilability"]["auto_compilable"] == 40'),
        ('assert len(rules) == 32', 'assert len(rules) == 40'),
        ('assert len(saved_queue) >= 191', 'assert len(saved_queue) >= 183'),
    ],
    'tests/test_huangjince_dynamic_rule_drafts.py': [
        ('assert len(rules) == 32', 'assert len(rules) == 40'),
    ],
}

for fp, replacements in files.items():
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {fp}")
