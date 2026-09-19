"""
DevOps Commands & Examples Cheat Sheet - Gemini AI Parser Module
Calls Gemini 3.8 Flash High exclusively to parse raw notes or scripts into structured items.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("CheatsheetAI")


def ai_parse_cheatsheet_content(
    raw_text: str,
    meta: Dict[str, Any],
    prompt_override: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calls Gemini 3.8 Flash High exclusively to parse raw notes or commands text
    into structured cheatsheet items with detailed AI explanations.
    """
    from app.ai_engine import call_gemini_api, resolve_gemini_api_key, PINNED_MODEL

    key = resolve_gemini_api_key(api_key)
    if not key:
        raise ValueError("No Gemini API key found on server. Please configure it in Admin Settings.")

    is_example_type = (meta.get("type") == "examples")

    default_command_prompt = f"""You are a Principal DevOps Architect.
Analyze the following unstructured notes, commands, or text, and extract all {meta['name']} commands into a clean JSON array.
Group commands into logical sections (e.g. "Navigation", "Process Management", "Networking", "Storage").
For every command, provide:
1. "section": The section/category name (e.g. "1. System Diagnostics").
2. "command": The exact, runnable command line or CLI syntax.
3. "explanation": A detailed, professional AI explanation of what the command does and real-world production DevOps use cases.
4. "flags": Key flags or options explained (e.g. "-p (port), -v (volume)").
5. "tags": Relevant keywords or subcategories (e.g. "Troubleshooting", "Networking", "Security").

Return strictly valid JSON in this structure:
{{
  "category": "{meta['id']}",
  "parsed_items": [
    {{
      "section": "1. Pod Diagnostics",
      "command": "kubectl get pods -n kube-system --show-labels",
      "explanation": "Lists all pods in the kube-system namespace along with their metadata labels, useful for diagnosing core cluster components and verifying node-agent placement.",
      "flags": "-n (namespace), --show-labels (prints labels as column)",
      "tags": "Kubernetes, Pods, Diagnostics"
    }}
  ]
}}
"""

    default_example_prompt = f"""You are a Principal DevOps Architect.
Analyze the following unstructured notes or script text, and extract production-grade {meta['name']} code examples into a clean JSON array.
For every code block, provide:
1. "title": Clear, descriptive title of the configuration or script.
2. "description": Detailed explanation of the architecture, key settings, and security/reliability considerations.
3. "language": Code language syntax (e.g. "bash", "yaml", "hcl", "dockerfile").
4. "code": Complete, runnable code content with comments and best practices.

Return strictly valid JSON in this structure:
{{
  "category": "{meta['id']}",
  "parsed_items": [
    {{
      "title": "High-Availability Deployment with Rolling Update and Probes",
      "description": "Production Kubernetes deployment with resource requests/limits, readiness/liveness probes, and rolling update strategy.",
      "language": "yaml",
      "code": "apiVersion: apps/v1\\nkind: Deployment\\n..."
    }}
  ]
}}
"""

    system_prompt = prompt_override.strip() if prompt_override and prompt_override.strip() else (
        default_example_prompt if is_example_type else default_command_prompt
    )

    user_content = f"Target Category: {meta['name']} ({meta['id']})\n\nInput Content To Process:\n{raw_text[:25000]}"

    contents = [
        {"parts": [{"text": user_content}]}
    ]

    raw_response = call_gemini_api(
        contents=contents,
        api_key=key,
        model=PINNED_MODEL,
        system_instruction=system_prompt,
        response_json=True
    )

    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        parsed = json.loads(clean_json.strip())
        items = parsed.get("parsed_items", [])
        return {
            "status": "success",
            "model": PINNED_MODEL,
            "category": meta["id"],
            "category_name": meta["name"],
            "type": meta["type"],
            "count": len(items),
            "items": items,
            "raw_response": raw_response
        }
    except Exception as e:
        logger.error(f"Failed to parse Gemini JSON output: {e}\nRaw output: {raw_response}")
        raise ValueError(f"AI returned non-JSON output: {str(e)}")
