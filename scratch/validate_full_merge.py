# -*- coding: utf-8 -*-
"""Comprehensive verification for 2. 9-Sep-2026 from discord.md"""
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

target_file = "Interview Questions/2. 9-Sep-2026 from discord.md"
if not os.path.exists(target_file):
    print(f"ERROR: {target_file} does not exist!")
    sys.exit(1)

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Total characters: {len(content)}")
print(f"Total lines: {len(content.splitlines())}")

# 1. Broken images
broken_images = re.findall(r'!\[.*?\]\(.*?\)', content)
if broken_images:
    print(f"[FAIL] Found broken images: {broken_images[:10]}")
else:
    print("[PASS] Zero broken image syntax found.")

# 2. Bullets before categories
bad_cats = re.findall(r'^[ \t]*[●*•-]\s*####\s*【', content, re.MULTILINE)
if bad_cats:
    print(f"[FAIL] Bullets before category headers found: {len(bad_cats)}")
else:
    print("[PASS] No bullets before category headers.")

# 3. Markers
markers = re.findall(r'<!--\s*NEXT_[A-Z_]+\s*-->', content)
if markers:
    print(f"[FAIL] Leftover markers found: {markers}")
else:
    print("[PASS] No leftover comment markers.")

# 4. Details balance
open_d = len(re.findall(r'<details\b', content))
close_d = len(re.findall(r'</details>', content))
print(f"Open <details>: {open_d} | Close </details>: {close_d}")
if open_d == close_d:
    print("[PASS] Details tags perfectly balanced.")
else:
    print(f"[FAIL] Details tag mismatch: {open_d - close_d}")

# 5. Check candidate intro without answers
bad_candidate = re.findall(r'<details>\s*<summary><strong>[●↳]\s*\*\*Candidate Introduction:\*\*', content)
if bad_candidate:
    print(f"[FAIL] Found answers for Candidate Introduction: {len(bad_candidate)}")
else:
    print("[PASS] Candidate introductions have no answer collapses.")

print("\n--- Summary Verification Complete ---")
