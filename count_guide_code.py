#!/usr/bin/env python3
"""Count lines of Python code in tutorial guides"""

import os
import re
from pathlib import Path

def extract_python_code(markdown_content):
    """Extract Python code blocks from markdown"""
    # Pattern to match ```python ... ``` blocks
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, markdown_content, re.DOTALL)

    code_lines = []
    for match in matches:
        code_lines.extend(match.split('\n'))

    return code_lines

def count_code_lines(lines):
    """Count non-empty, non-comment lines"""
    total = 0
    code_only = 0

    for line in lines:
        stripped = line.strip()
        if stripped:  # Non-empty
            total += 1
            if not stripped.startswith('#') and stripped != '"""' and stripped != "'''":
                code_only += 1

    return total, code_only

# Process all guide files
guide_dir = Path('guide')
all_code_lines = []
file_stats = []

for md_file in sorted(guide_dir.glob('DAY_*.md')):
    content = md_file.read_text()
    code_lines = extract_python_code(content)
    all_code_lines.extend(code_lines)

    total, code_only = count_code_lines(code_lines)
    file_stats.append({
        'file': md_file.name,
        'total_lines': total,
        'code_lines': code_only
    })

# Overall stats
total_lines, code_only_lines = count_code_lines(all_code_lines)

print("=" * 80)
print("TUTORIAL GUIDES CODE ANALYSIS")
print("=" * 80)
print(f"\nTotal tutorial files: {len(file_stats)}")
print(f"Total lines in code blocks: {len(all_code_lines)}")
print(f"Non-empty lines: {total_lines}")
print(f"Code lines (excluding comments): {code_only_lines}")

print("\n" + "=" * 80)
print("TOP 10 GUIDES BY CODE VOLUME")
print("=" * 80)

# Sort by total lines
sorted_stats = sorted(file_stats, key=lambda x: x['total_lines'], reverse=True)
for i, stat in enumerate(sorted_stats[:10], 1):
    print(f"{i:2}. {stat['file']:40} {stat['total_lines']:4} lines ({stat['code_lines']:4} code)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Tutorial guides Python code: ~{code_only_lines:,} lines")
print("=" * 80)
