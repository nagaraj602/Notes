"""
DevOps Knowledge Hub - Commands Cheat Sheet Manager
Coordinates loading, parsing, banking, and AI-powered ingestion of DevOps commands
and code example files across categories.
Modular design delegating to:
- cheatsheet_categories.py: Category definitions and metadata
- cheatsheet_parser.py: Section-aware markdown table and code example parsing
- cheatsheet_ai.py: Gemini AI-powered note ingestion
"""

import os
import logging
from typing import Dict, Any, List, Optional

from app.cheatsheet_categories import CHEATSHEET_CATEGORIES, get_category_meta
from app.cheatsheet_parser import (
    parse_markdown_table_commands,
    parse_markdown_code_examples,
    format_commands_markdown
)
from app.cheatsheet_ai import ai_parse_cheatsheet_content

logger = logging.getLogger("CheatsheetManager")


class CheatsheetManager:
    def __init__(self, base_dir: Optional[str] = None):
        self.custom_dir = base_dir
        self._cached_data: Optional[Dict[str, Any]] = None

    def get_cheatsheets_dir(self) -> str:
        """Locates or initializes the commands_cheatsheet directory."""
        if self.custom_dir and os.path.exists(self.custom_dir):
            return self.custom_dir

        env_dir = os.getenv("CHEATSHEET_DIR", "").strip()
        if env_dir and os.path.exists(env_dir):
            return env_dir

        # Container standard paths
        container_candidates = [
            "/app/data/notes/commands_cheatsheet",
            "/app/commands_cheatsheet",
            "/app/data/notes/devops-notes/commands_cheatsheet"
        ]
        for c in container_candidates:
            if os.path.exists(c):
                return c

        # Local development paths: look upwards from current file
        cur = os.path.abspath(os.path.dirname(__file__))
        for _ in range(5):
            cand = os.path.join(cur, "commands_cheatsheet")
            if os.path.exists(cand):
                return cand
            cur = os.path.dirname(cur)

        # Fallback to local sibling or root
        fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "commands_cheatsheet"))
        os.makedirs(fallback, exist_ok=True)
        return fallback

    def get_category_meta(self, category_id: str) -> Optional[Dict[str, Any]]:
        return get_category_meta(category_id)

    def parse_markdown_table_commands(self, text: str) -> List[Dict[str, Any]]:
        return parse_markdown_table_commands(text)

    def parse_markdown_code_examples(self, text: str) -> List[Dict[str, Any]]:
        return parse_markdown_code_examples(text)

    def get_category_data(self, category_id: str) -> Dict[str, Any]:
        """Loads and parses a single category file."""
        meta = self.get_category_meta(category_id)
        if not meta:
            return {"error": f"Category '{category_id}' not found", "items": [], "raw": ""}

        base_dir = self.get_cheatsheets_dir()
        file_path = os.path.join(base_dir, meta["filename"])

        if not os.path.exists(file_path):
            return {
                "meta": meta,
                "items": [],
                "sections": [],
                "total_items": 0,
                "raw": "",
                "file_path": file_path
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if meta["type"] == "commands":
                items = parse_markdown_table_commands(content)
            else:
                items = parse_markdown_code_examples(content)

            # Collect unique sections for quick filtering in frontend
            sections = []
            seen_sections = set()
            for it in items:
                sec = it.get("section")
                if sec and sec not in seen_sections:
                    seen_sections.add(sec)
                    sections.append(sec)

            return {
                "meta": meta,
                "items": items,
                "sections": sections,
                "total_items": len(items),
                "raw": content,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error reading cheatsheet file {file_path}: {e}")
            return {
                "meta": meta,
                "items": [],
                "sections": [],
                "total_items": 0,
                "error": str(e),
                "raw": ""
            }

    def get_all_cheatsheets(self) -> Dict[str, Any]:
        """Loads all cheatsheet categories with summary counts, items, and section lists."""
        result = {
            "categories": [],
            "total_commands": 0,
            "total_examples": 0
        }

        for cat in CHEATSHEET_CATEGORIES:
            data = self.get_category_data(cat["id"])
            cat_entry = {
                **cat,
                "total_items": data.get("total_items", 0),
                "sections": data.get("sections", []),
                "items": data.get("items", [])
            }
            if cat["type"] == "commands":
                result["total_commands"] += data.get("total_items", 0)
            else:
                result["total_examples"] += data.get("total_items", 0)
            result["categories"].append(cat_entry)

        return result

    def save_category_content(self, category_id: str, new_content: str) -> bool:
        """Saves raw markdown content directly to category file."""
        meta = self.get_category_meta(category_id)
        if not meta:
            return False

        base_dir = self.get_cheatsheets_dir()
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, meta["filename"])

        target_paths = [file_path]
        cur = os.path.abspath(os.path.dirname(__file__))
        for _ in range(3):
            cand = os.path.join(cur, "commands_cheatsheet")
            if os.path.exists(cand) and cand != base_dir:
                target_paths.append(os.path.join(cand, meta["filename"]))
            cur = os.path.dirname(cur)

        try:
            for p in set(target_paths):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_content)
            self._cached_data = None
            return True
        except Exception as e:
            logger.error(f"Failed to save cheatsheet {file_path}: {e}")
            return False

    def append_items(self, category_id: str, new_items: List[Dict[str, Any]]) -> bool:
        """Appends command or example items to an existing category file in standard format."""
        meta = self.get_category_meta(category_id)
        if not meta:
            return False

        current_data = self.get_category_data(category_id)
        existing_items = current_data.get("items", [])
        combined_items = existing_items + new_items

        if meta["type"] == "commands":
            output = format_commands_markdown(
                meta["name"],
                combined_items,
                meta.get("description", "")
            )
            return self.save_category_content(category_id, output)
        else:
            raw = current_data.get("raw", "").strip()
            if not raw:
                output = f"# {meta['name']} Examples\n\n> Production-grade {meta['name']} reference configurations.\n\n"
            else:
                output = raw + "\n\n"

            existing_count = len(existing_items)
            for idx, item in enumerate(new_items, 1):
                title = item.get("title", f"Example {existing_count + idx}").strip()
                desc = item.get("description", "Production configuration example.").strip()
                lang = item.get("language", "yaml").strip()
                code = item.get("code", "").strip()

                output += f"## {existing_count + idx}. {title}\n"
                output += f"**Description**: {desc}\n\n"
                output += f"```{lang}\n{code}\n```\n\n"

            return self.save_category_content(category_id, output)

    def ai_parse_cheatsheet(
        self,
        raw_text: str,
        target_category: str,
        prompt_override: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calls Gemini to parse raw notes into structured cheatsheet items."""
        meta = self.get_category_meta(target_category)
        if not meta:
            raise ValueError(f"Unknown target category: {target_category}")

        return ai_parse_cheatsheet_content(
            raw_text=raw_text,
            meta=meta,
            prompt_override=prompt_override,
            api_key=api_key
        )


# Singleton instance
cheatsheet_manager = CheatsheetManager()
