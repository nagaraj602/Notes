# -*- coding: utf-8 -*-
"""Verification script for chunk_5.md."""

import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("scratch/batch_5_input.json", "r", encoding="utf-8") as f:
    input_data = json.load(f)

with open("scratch/chunk_5.md", "r", encoding="utf-8") as f:
    chunk_md = f.read()

print("--- 1. Checking Broken Images ---")
broken_images = re.findall(r'!\[.*?\]\(.*?\)', chunk_md)
if broken_images:
    print(f"FAILED: Found broken image syntax: {broken_images}")
else:
    print("PASSED: No broken image syntax found.")

print("\n--- 2. Checking Category Headers ---")
bullet_categories = re.findall(r'^[ \t]*[●*•-]\s*####\s*【', chunk_md, re.MULTILINE)
if bullet_categories:
    print(f"FAILED: Found bullet points before category headers: {bullet_categories}")
else:
    print("PASSED: Category headers have no bullets.")

print("\n--- 3. Checking Details / Tag Balance ---")
open_details = len(re.findall(r'<details\b', chunk_md))
close_details = len(re.findall(r'</details>', chunk_md))
print(f"Open <details>: {open_details} | Close </details>: {close_details}")
if open_details == close_details:
    print("PASSED: All <details> tags are perfectly balanced.")
else:
    print(f"FAILED: Mismatched details tags (Diff: {open_details - close_details})")

print("\n--- 4. Checking All Questions from batch_5_input.json ---")
total_questions = 0
found_questions = 0
missing_questions = []

for comp_idx, comp in enumerate(input_data):
    for r in comp["rounds"]:
        for item in r["items"]:
            total_questions += 1
            text = item["text"]
            clean_text = text.strip("*").strip()
            # check if clean_text appears in chunk_md
            if clean_text in chunk_md:
                found_questions += 1
            else:
                missing_questions.append((comp["company"], r["round"], clean_text))

print(f"Total questions in JSON: {total_questions}")
print(f"Questions found in chunk_5.md: {found_questions}")
if missing_questions:
    print(f"FAILED: {len(missing_questions)} questions not found:")
    for comp_name, round_name, q_text in missing_questions:
        print(f"  [{comp_name} - {round_name}] {q_text[:80]}...")
else:
    print("PASSED: 100% of questions from batch_5_input.json exist in chunk_5.md!")

print("\n--- 5. Checking Company Summaries & Dates ---")
for comp in input_data:
    comp_name = comp["company"]
    # Check company header
    header_pattern = rf'<summary><h2>🏢\s*{re.escape(comp_name)}</h2></summary>'
    if not re.search(header_pattern, chunk_md, re.IGNORECASE):
        print(f"WARNING: Company header not found for {comp_name}")
    else:
        print(f"PASSED: Company header found for {comp_name}")

    for r in comp["rounds"]:
        r_name = r["round"]
        round_pattern = rf'<summary><h3>\s*{re.escape(r_name)}</h3></summary>'
        if not re.search(round_pattern, chunk_md):
            print(f"WARNING: Round header not found for {comp_name} - {r_name}")
        else:
            print(f"PASSED: Round header found for {comp_name} - {r_name}")

        r_date = r.get("date", "").strip()
        if r_date:
            date_pattern = rf'\*Date:\s*{re.escape(r_date)}\*'
            if not re.search(date_pattern, chunk_md):
                print(f"WARNING: Date not found: {r_date} for {comp_name} - {r_name}")
            else:
                print(f"PASSED: Date found: {r_date}")
