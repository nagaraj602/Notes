"""
DevOps Commands & Examples Cheat Sheet - Markdown Parser & Formatter
Parses section-based markdown tables and structured code examples into rich items.
Supports:
- Grouped sections: ## 1. System Navigation, ## 2. File Operations
- Multi-column tables: | Command | Description & AI Explanation | Key Flags / Syntax | Tags |
- Code blocks: ## Title, **Description**: ..., ```lang ... ```
"""

import re
from typing import Dict, Any, List, Optional


def parse_markdown_table_commands(text: str) -> List[Dict[str, Any]]:
    """
    Parses markdown text into structured command items with section awareness.
    Supports both sectioned markdown tables (## Section Name) and legacy flat tables.
    """
    items: List[Dict[str, Any]] = []
    lines = text.splitlines()

    current_section = "General Commands"
    in_table = False
    col_map: Dict[str, int] = {}

    for line in lines:
        trimmed = line.strip()

        # Check for section header (e.g. "## 1. System Navigation & Directory Operations")
        section_match = re.match(r"^#{2,3}\s+(?:(?:\d+[\.\)]\s*)?)(.+)$", trimmed)
        if section_match and not trimmed.startswith("### Key") and not trimmed.startswith("### Core"):
            # Only switch section if it doesn't look like a sub-note
            candidate_section = section_match.group(1).strip()
            # Clean markdown formatting from section title
            candidate_section = re.sub(r"[*_`]", "", candidate_section).strip()
            if candidate_section and not candidate_section.lower().startswith("table of"):
                current_section = candidate_section
                in_table = False
                col_map = {}
                continue

        # Check for table rows
        if trimmed.startswith("|") and trimmed.endswith("|"):
            raw_cells = trimmed.strip("|").split("|")
            cells = [c.strip() for c in raw_cells]

            # Detect Header Row
            if not in_table:
                lower_cells = [c.lower() for c in cells]
                if any("command" in c for c in lower_cells):
                    in_table = True
                    col_map = {}
                    for idx, c in enumerate(lower_cells):
                        if "command" in c:
                            col_map["command"] = idx
                        elif "description" in c or "explanation" in c or "purpose" in c:
                            col_map["explanation"] = idx
                        elif "flag" in c or "syntax" in c or "option" in c:
                            col_map["flags"] = idx
                        elif "tag" in c or "category" in c:
                            col_map["tags"] = idx
                    # If explanation was not explicitly mapped, assign 1
                    if "explanation" not in col_map and len(cells) > 1:
                        col_map["explanation"] = 1
                    continue
            
            # Skip separator line (| :--- | :--- |)
            if re.match(r"^[\s\-:|]+$", trimmed):
                continue

            # Data Row
            if in_table and len(cells) >= 2:
                cmd_idx = col_map.get("command", 0)
                exp_idx = col_map.get("explanation", 1)
                flags_idx = col_map.get("flags")
                tags_idx = col_map.get("tags")

                raw_cmd = cells[cmd_idx] if cmd_idx < len(cells) else ""
                # Strip markdown code formatting
                cmd = raw_cmd.strip("`").strip()

                explanation = cells[exp_idx] if exp_idx < len(cells) else ""
                
                flags = ""
                if flags_idx is not None and flags_idx < len(cells):
                    flags = cells[flags_idx].strip()

                tags = ""
                if tags_idx is not None and tags_idx < len(cells):
                    tags = cells[tags_idx].strip()
                elif flags_idx is None and len(cells) > 2:
                    # 3-column table: Command | Description | Tags
                    tags = cells[2].strip()

                if cmd:
                    items.append({
                        "section": current_section,
                        "command": cmd,
                        "explanation": explanation,
                        "flags": flags,
                        "tags": tags
                    })
        else:
            in_table = False
            col_map = {}

    # Fallback: parse backticks and bullet patterns if no markdown table was detected
    if not items:
        cmd_pattern = re.compile(r"^(?:[\*\-]\s*)?`([^`]+)`(?:\s*[:\-–]\s*(.+))?$", re.MULTILINE)
        for m in cmd_pattern.finditer(text):
            c = m.group(1).strip()
            e = (m.group(2) or "").strip()
            if c:
                items.append({
                    "section": current_section,
                    "command": c,
                    "explanation": e or "DevOps administration command",
                    "flags": "",
                    "tags": ""
                })

    return items


def parse_markdown_code_examples(text: str) -> List[Dict[str, Any]]:
    """
    Parses markdown code examples (## Title, Description, and ```lang code blocks).
    """
    examples: List[Dict[str, Any]] = []

    # Pattern to find ## sections with code blocks
    section_pattern = re.compile(
        r"##\s+(?:(?:\d+\.?\s*)?)(.+?)\n+(.*?)(?:```([a-zA-Z0-9_-]*)\n([\s\S]*?)```)",
        re.MULTILINE
    )

    for m in section_pattern.finditer(text):
        title = m.group(1).strip()
        desc_raw = m.group(2).strip()
        # Clean up **Description**: prefix if present
        desc_clean = re.sub(
            r"^\*\*(?:Description|Overview|AI Explanation)\*\*:\s*",
            "",
            desc_raw,
            flags=re.IGNORECASE
        ).strip()
        lang = m.group(3).strip() or "yaml"
        code = m.group(4).strip()
        if title and code:
            examples.append({
                "title": title,
                "description": desc_clean or "Production DevOps template and configuration example.",
                "language": lang,
                "code": code
            })

    # Fallback: find any code block if no ## sections matched
    if not examples:
        block_pattern = re.compile(r"```([a-zA-Z0-9_-]*)\n([\s\S]*?)```", re.MULTILINE)
        idx = 1
        for m in block_pattern.finditer(text):
            lang = m.group(1).strip() or "text"
            code = m.group(2).strip()
            examples.append({
                "title": f"Example Code Block #{idx}",
                "description": "Configuration example",
                "language": lang,
                "code": code
            })
            idx += 1

    return examples


def format_commands_markdown(category_name: str, items: List[Dict[str, Any]], description: str = "") -> str:
    """
    Serializes a list of command dictionaries into organized, section-based markdown tables.
    """
    desc = description or f"Comprehensive {category_name} reference with production AI explanations."
    output = f"# {category_name} Commands Cheat Sheet\n\n"
    output += f"> {desc}\n\n"

    # Group items by section
    sections: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        sec = it.get("section") or "General Commands"
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(it)

    has_flags = any(bool(it.get("flags")) for it in items)

    for sec_title, sec_items in sections.items():
        output += f"## {sec_title}\n\n"
        if has_flags:
            output += "| Command | Description & AI Explanation | Key Flags / Syntax | Tags |\n"
            output += "| :--- | :--- | :--- | :--- |\n"
        else:
            output += "| Command | Description & AI Explanation | Category / Tags |\n"
            output += "| :--- | :--- | :--- |\n"

        for it in sec_items:
            cmd = it.get("command", "").strip().replace("|", "\\|")
            exp = it.get("explanation", "").strip().replace("|", "\\|").replace("\n", " ")
            flg = it.get("flags", "").strip().replace("|", "\\|").replace("\n", " ")
            tgs = it.get("tags", "").strip().replace("|", "\\|")

            if has_flags:
                output += f"| `{cmd}` | {exp} | {flg} | {tgs} |\n"
            else:
                output += f"| `{cmd}` | {exp} | {tgs} |\n"
        output += "\n"

    return output.rstrip() + "\n"
