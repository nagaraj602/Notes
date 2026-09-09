import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('Interview Questions/2. 9-Sep-2026 from discord.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for lno in [3, 6, 1025, 1869, 3745]:
    print(f'=== Around line {lno} ===')
    start = max(0, lno - 3)
    end = min(len(lines), lno + 5)
    for i in range(start, end):
        print(f'{i+1}: {lines[i].rstrip()}')
