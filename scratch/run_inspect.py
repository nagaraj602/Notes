import json

with open("scratch/batch_5_input.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for i, comp in enumerate(data):
    print(f"[{i}] Company: {comp.get('company')}")
    for r in comp.get('rounds', []):
        print(f"    Round: {r.get('round')} | Date: '{r.get('date', '')}' | Items: {len(r.get('items', []))}")
        categories = []
        for item in r.get('items', []):
            cat = item.get('category', 'UNCATEGORIZED')
            if not categories or categories[-1] != cat:
                categories.append(cat)
        print(f"       Categories: {categories}")
