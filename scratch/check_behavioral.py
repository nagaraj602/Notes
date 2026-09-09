import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/batch_5_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for comp in data:
    for r in comp['rounds']:
        print(f"=== {comp['company']} - {r['round']} ===")
        for item in r['items']:
            prefix = item.get('prefix', '●')
            cat = item.get('category', '')
            text = item.get('text', '')
            if cat == 'BEHAVIORAL' or any(w in text.lower() for w in ['introduce', 'background', 'years of experience', 'ctc', 'salary', 'notice', 'current company', 'previous company', 'originally from', 'where are you', 'how many years']):
                print(f"  [{cat}] {prefix} {text}")
