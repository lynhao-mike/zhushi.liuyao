# -*- coding: utf-8 -*-
"""临时脚本：修复中文引号为英文引号"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换中文引号为英文引号
content = content.replace('"', '"').replace('"', '"')

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Chinese quotes to English quotes")
