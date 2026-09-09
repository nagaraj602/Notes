import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('devops-notes-portal-web-app'))

from app.old_iq_manager import old_iq_manager

data = old_iq_manager.get_data(force_refresh=True)
stats = data['stats']
print("Portal Old IQ Stats:")
print(f"  Total Companies: {stats['total_companies']}")
print(f"  Total Rounds: {stats['total_rounds']}")
print(f"  Total Questions: {stats['total_questions']}")
print(f"  Categories count: {len(stats['categories'])}")

print(f"\nSample of parsed companies ({len(data['companies'])} total):")
for c in data['companies'][:10]:
    total_q = sum(len(r['questions']) for r in c['rounds'])
    print(f"  - {c['company_name']} ({len(c['rounds'])} rounds, {total_q} questions)")
