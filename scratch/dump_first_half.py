import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/batch_5_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for comp_idx in range(7):
    comp = data[comp_idx]
    print(f"\n=======================================================")
    print(f"Company [{comp_idx}]: {comp['company']}")
    for r_idx, r in enumerate(comp['rounds']):
        print(f"  Round: {r['round']} | Date: '{r.get('date', '')}'")
        curr_cat = None
        for item_idx, item in enumerate(r['items']):
            cat = item.get('category', 'UNCATEGORIZED')
            if cat != curr_cat:
                curr_cat = cat
                print(f"    #### 【 {curr_cat} 】")
            prefix = item.get('prefix', '●')
            text = item.get('text', '')
            print(f"      {prefix} ({item_idx}) {text}")
