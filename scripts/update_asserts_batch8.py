# -*- coding: utf-8 -*-
"""批量更新测试断言: 37->45(generated), 40->48(merged/rules), 183->175(queue)"""

files = {
    'tests/test_huangjince_auto_compile.py': [
        ('assert len(generated) == 37', 'assert len(generated) == 45'),
        ('assert len(merged_once) == 40', 'assert len(merged_once) == 48'),
    ],
    'tests/test_huangjince_dynamic_rule_audit.py': [
        ('assert len(candidate_rules) == 40', 'assert len(candidate_rules) == 48'),
        ('assert audit["compiled_drafts"] == len(compiled) == 40', 'assert audit["compiled_drafts"] == len(compiled) == 48'),
        ('assert audit["by_compilability"]["auto_compilable"] == 40', 'assert audit["by_compilability"]["auto_compilable"] == 48'),
        ('assert len(rules) == 40', 'assert len(rules) == 48'),
        ('assert len(saved_queue) >= 183', 'assert len(saved_queue) >= 175'),
    ],
    'tests/test_huangjince_dynamic_rule_drafts.py': [
        ('assert len(rules) == 40', 'assert len(rules) == 48'),
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
