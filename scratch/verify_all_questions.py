import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_file = "Interview Questions/2. 9-Sep-2026 from discord.md"
with open(target_file, "r", encoding="utf-8") as f:
    full_content = f.read()

total_questions = 0
found_questions = 0
missing = []

for b in range(1, 7):
    batch_file = f"scratch/batch_{b}_input.json"
    with open(batch_file, "r", encoding="utf-8") as bf:
        data = json.load(bf)
    for comp in data:
        for r in comp["rounds"]:
            for item in r["items"]:
                total_questions += 1
                q_text = item.get("text", "").strip()
                # Clean asterisks, markdown backslashes
                clean_q = q_text.replace('\\-', '-').replace('\\*', '*').replace('\\_', '_').strip('*').strip()
                probe = clean_q[:35].strip()
                if probe.lower() in full_content.lower():
                    found_questions += 1
                else:
                    missing.append((comp["company"], r["round"], q_text))

print(f"Total questions evaluated across all 6 batches: {total_questions}")
print(f"Questions found: {found_questions}")
print(f"Missing: {len(missing)}")
if missing:
    for c, r, q in missing[:15]:
        print(f"  Missing: [{c} - {r}] {q[:70]}...")
else:
    print("ALL 100% of questions across all batches verified present!")
