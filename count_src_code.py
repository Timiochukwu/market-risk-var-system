#!/usr/bin/env python3
"""Count lines of Python code in src/ folder"""

import os
from pathlib import Path

def count_code_lines(file_path):
    """Count lines in a Python file"""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    total_lines = len(lines)
    non_empty = 0
    code_only = 0
    comments = 0
    docstrings = 0

    in_docstring = False
    docstring_char = None

    for line in lines:
        stripped = line.strip()

        # Check for docstring start/end
        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                docstring_char = '"""' if '"""' in stripped else "'''"
                docstrings += 1
            elif (docstring_char == '"""' and '"""' in stripped) or \
                 (docstring_char == "'''" and "'''" in stripped):
                in_docstring = False
                docstrings += 1
                continue
            continue

        if in_docstring:
            docstrings += 1
            continue

        if stripped:  # Non-empty
            non_empty += 1
            if stripped.startswith('#'):
                comments += 1
            else:
                code_only += 1

    return {
        'total': total_lines,
        'non_empty': non_empty,
        'code': code_only,
        'comments': comments,
        'docstrings': docstrings
    }

# Process all Python files
src_dir = Path('src')
file_stats = []
category_stats = {
    'api': {'files': 0, 'code': 0},
    'data': {'files': 0, 'code': 0},
    'models': {'files': 0, 'code': 0},
    'utils': {'files': 0, 'code': 0}
}

for py_file in sorted(src_dir.rglob('*.py')):
    if py_file.name == '__init__.py':
        continue

    stats = count_code_lines(py_file)
    stats['file'] = str(py_file)

    file_stats.append(stats)

    # Categorize
    if 'api/' in str(py_file):
        category_stats['api']['files'] += 1
        category_stats['api']['code'] += stats['code']
    elif 'data/' in str(py_file):
        category_stats['data']['files'] += 1
        category_stats['data']['code'] += stats['code']
    elif 'models/' in str(py_file):
        category_stats['models']['files'] += 1
        category_stats['models']['code'] += stats['code']
    elif 'utils/' in str(py_file):
        category_stats['utils']['files'] += 1
        category_stats['utils']['code'] += stats['code']

# Calculate totals
total_code = sum(f['code'] for f in file_stats)
total_files = len(file_stats)
total_all_lines = sum(f['total'] for f in file_stats)

print("=" * 80)
print("SRC/ BACKEND CODE ANALYSIS")
print("=" * 80)
print(f"\nTotal Python files: {total_files}")
print(f"Total lines (including blanks/comments): {total_all_lines}")
print(f"Code lines (excluding comments/docstrings): {total_code}")

print("\n" + "=" * 80)
print("BREAKDOWN BY CATEGORY")
print("=" * 80)
for category, stats in sorted(category_stats.items()):
    if stats['files'] > 0:
        print(f"{category.upper():10} {stats['files']:2} files, {stats['code']:5} code lines")

print("\n" + "=" * 80)
print("TOP 10 FILES BY CODE VOLUME")
print("=" * 80)

sorted_stats = sorted(file_stats, key=lambda x: x['code'], reverse=True)
for i, stat in enumerate(sorted_stats[:10], 1):
    filename = Path(stat['file']).name
    print(f"{i:2}. {filename:40} {stat['code']:4} code lines")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Backend src/ Python code: ~{total_code:,} lines")
print("=" * 80)
