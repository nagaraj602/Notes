# -*- coding: utf-8 -*-
"""Assembler script to generate chunk_5.md from all company modules."""

import os
import sys

from gen_company_0 import get_cyient_markdown
from gen_company_1 import get_mphasis_markdown
from gen_company_2 import get_ltm_markdown
from gen_company_3 import get_feuji_markdown
from gen_company_4 import get_bounteous1_markdown
from gen_company_5 import get_apty_markdown
from gen_company_6 import get_bounteous2_markdown
from gen_company_7 import get_mindteck_markdown
from gen_company_8 import get_virtusa_markdown

def main():
    parts = [
        get_cyient_markdown(),
        get_mphasis_markdown(),
        get_ltm_markdown(),
        get_feuji_markdown(),
        get_bounteous1_markdown(),
        get_apty_markdown(),
        get_bounteous2_markdown(),
        get_mindteck_markdown(),
        get_virtusa_markdown()
    ]

    output_path = os.path.join(os.path.dirname(__file__), "chunk_5.md")
    content = "\n\n".join(parts) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated {output_path} with {len(content)} characters and {len(content.splitlines())} lines.")

if __name__ == "__main__":
    main()
