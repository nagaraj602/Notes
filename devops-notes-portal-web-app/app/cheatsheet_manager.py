"""
DevOps Knowledge Hub - Commands Cheat Sheet Manager
Handles loading, parsing, banking, and AI-powered ingestion of DevOps commands
and code example files across 16 categories.
Stored in commands_cheatsheet/<category>.md
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CheatsheetManager")

CHEATSHEET_CATEGORIES = [
    {
        "id": "linux",
        "name": "Linux",
        "filename": "linux.md",
        "type": "commands",
        "icon": "fa-brands fa-linux",
        "color": "amber",
        "description": "Essential Linux administration, troubleshooting, networking, and system diagnostics commands."
    },
    {
        "id": "shell_script",
        "name": "Shell Script",
        "filename": "shell_script.md",
        "type": "commands",
        "icon": "fa-solid fa-terminal",
        "color": "emerald",
        "description": "Bash & Shell scripting commands, syntax, expansions, loops, and conditions."
    },
    {
        "id": "github",
        "name": "Github",
        "filename": "github.md",
        "type": "commands",
        "icon": "fa-brands fa-github",
        "color": "slate",
        "description": "Git & GitHub CLI operations, branch management, rebasing, tags, and conflict resolution."
    },
    {
        "id": "build_tools",
        "name": "Build Tools (Maven, Python, C, NodeJS)",
        "filename": "build_tools.md",
        "type": "commands",
        "icon": "fa-solid fa-gears",
        "color": "rose",
        "description": "Build tools, dependencies, and packaging CLI commands across Maven, Python, C, and Node.js."
    },
    {
        "id": "aws",
        "name": "AWS",
        "filename": "aws.md",
        "type": "commands",
        "icon": "fa-brands fa-aws",
        "color": "amber",
        "description": "AWS CLI v2 commands for EC2, S3, IAM, VPC, EKS, CloudWatch, and RDS management."
    },
    {
        "id": "docker",
        "name": "Docker",
        "filename": "docker.md",
        "type": "commands",
        "icon": "fa-brands fa-docker",
        "color": "sky",
        "description": "Docker container lifecycle, image optimization, buildx, networks, and compose commands."
    },
    {
        "id": "kubernetes",
        "name": "Kubernetes",
        "filename": "kubernetes.md",
        "type": "commands",
        "icon": "fa-solid fa-dharmachakra",
        "color": "indigo",
        "description": "Kubectl cluster operations, debugging, rollouts, logs, pod health, and resource configurations."
    },
    {
        "id": "helm",
        "name": "Helm",
        "filename": "helm.md",
        "type": "commands",
        "icon": "fa-solid fa-anchor",
        "color": "blue",
        "description": "Helm chart package manager commands, repositories, value overrides, releases, and rollbacks."
    },
    {
        "id": "terraform",
        "name": "Terraform",
        "filename": "terraform.md",
        "type": "commands",
        "icon": "fa-solid fa-cubes-stacked",
        "color": "violet",
        "description": "Terraform IaC CLI commands, state operations, workspaces, module imports, and plan execution."
    },
    {
        "id": "ansible",
        "name": "Ansible",
        "filename": "ansible.md",
        "type": "commands",
        "icon": "fa-solid fa-network-wired",
        "color": "red",
        "description": "Ansible ad-hoc commands, playbook executions, vault encryption, and inventory checks."
    },
    {
        "id": "monitoring",
        "name": "Monitoring Tools",
        "filename": "monitoring.md",
        "type": "commands",
        "icon": "fa-solid fa-chart-line",
        "color": "teal",
        "description": "PromQL queries, Grafana dashboards, Datadog CLI, cAdvisor, and alert management commands."
    },
    {
        "id": "shell_examples",
        "name": "Shell Script Examples",
        "filename": "shell_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-code",
        "color": "emerald",
        "description": "Production-ready automation shell scripts for backup, log rotation, and server maintenance."
    },
    {
        "id": "k8s_manifests",
        "name": "Kubernetes Manifest Files",
        "filename": "k8s_manifests.md",
        "type": "examples",
        "icon": "fa-solid fa-file-code",
        "color": "indigo",
        "description": "Production Kubernetes YAML manifests including Deployments, Ingress, StatefulSets, and Probes."
    },
    {
        "id": "terraform_examples",
        "name": "Terraform YAML / HCL Examples",
        "filename": "terraform_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-layer-group",
        "color": "violet",
        "description": "Complete Terraform module architectures, remote state lock setups, and cloud-init integrations."
    },
    {
        "id": "ansible_examples",
        "name": "Ansible Example Files",
        "filename": "ansible_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-boxes-packing",
        "color": "rose",
        "description": "Complete Ansible playbooks for multi-tier configurations, server hardening, and rolling restarts."
    },
    {
        "id": "dockerfile_examples",
        "name": "Dockerfile Example Files",
        "filename": "dockerfile_examples.md",
        "type": "examples",
        "icon": "fa-brands fa-docker",
        "color": "sky",
        "description": "Optimized multi-stage and distroless Dockerfiles for Node, Java, Python, and Go applications."
    }
]

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
        for cat in CHEATSHEET_CATEGORIES:
            if cat["id"].lower() == category_id.lower() or cat["filename"].lower() == category_id.lower():
                return cat
        return None

    def parse_markdown_table_commands(self, text: str) -> List[Dict[str, Any]]:
        """Parses markdown table or section lists into structured command items."""
        items = []
        lines = text.splitlines()
        in_table = False
        headers = []

        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("|") and trimmed.endswith("|"):
                cells = [c.strip() for c in trimmed.strip("|").split("|")]
                if not in_table:
                    # Check if header row
                    if any("command" in c.lower() for c in cells):
                        in_table = True
                        headers = [c.lower() for c in cells]
                        continue
                elif re.match(r"^[\s\-:|]+$", trimmed):
                    # Separator row
                    continue
                else:
                    # Data row
                    if len(cells) >= 2:
                        cmd = cells[0].strip("`").strip()
                        explanation = cells[1].strip()
                        tags = cells[2].strip() if len(cells) > 2 else ""
                        if cmd:
                            items.append({
                                "command": cmd,
                                "explanation": explanation,
                                "tags": tags
                            })
            else:
                in_table = False

        # If table format didn't catch, parse backticks and bullet patterns:
        if not items:
            cmd_pattern = re.compile(r"^(?:[\*\-]\s*)?`([^`]+)`(?:\s*[:\-–]\s*(.+))?$", re.MULTILINE)
            for m in cmd_pattern.finditer(text):
                c = m.group(1).strip()
                e = (m.group(2) or "").strip()
                if c:
                    items.append({
                        "command": c,
                        "explanation": e or "DevOps administration command",
                        "tags": ""
                    })

        return items

    def parse_markdown_code_examples(self, text: str) -> List[Dict[str, Any]]:
        """Parses markdown code examples (## Title, Description, and ```lang code blocks)."""
        examples = []
        # Pattern to find ## sections with code blocks
        section_pattern = re.compile(
            r"##\s+(?:(?:\d+\.?\s*)?)(.+?)\n+(.*?)(?:```([a-zA-Z0-9_-]*)\n([\s\S]*?)```)",
            re.MULTILINE
        )

        for m in section_pattern.finditer(text):
            title = m.group(1).strip()
            desc_raw = m.group(2).strip()
            # Clean up **Description**: prefix if present
            desc_clean = re.sub(r"^\*\*(?:Description|Overview|AI Explanation)\*\*:\s*", "", desc_raw, flags=re.IGNORECASE).strip()
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
                "total_items": 0,
                "raw": "",
                "file_path": file_path
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if meta["type"] == "commands":
                items = self.parse_markdown_table_commands(content)
            else:
                items = self.parse_markdown_code_examples(content)

            return {
                "meta": meta,
                "items": items,
                "total_items": len(items),
                "raw": content,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error reading cheatsheet file {file_path}: {e}")
            return {
                "meta": meta,
                "items": [],
                "total_items": 0,
                "error": str(e),
                "raw": ""
            }

    def get_all_cheatsheets(self) -> Dict[str, Any]:
        """Loads all cheatsheet categories with summary counts and items."""
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

        try:
            with open(file_path, "w", encoding="utf-8") as f:
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
        raw = current_data.get("raw", "").strip()

        if meta["type"] == "commands":
            if not raw or "| Command |" not in raw:
                # Initialize new table
                output = f"# {meta['name']} Commands Cheat Sheet\n\n"
                output += f"> Comprehensive {meta['name']} commands reference with AI explanations.\n\n"
                output += "| Command | Description & AI Explanation | Category / Tags |\n"
                output += "| :--- | :--- | :--- |\n"
            else:
                output = raw + "\n"

            for item in new_items:
                cmd = item.get("command", "").strip().replace("|", "\\|")
                exp = item.get("explanation", "").strip().replace("|", "\\|").replace("\n", " ")
                tags = item.get("tags", "").strip().replace("|", "\\|")
                if cmd:
                    output += f"| `{cmd}` | {exp} | {tags} |\n"

            return self.save_category_content(category_id, output)

        else:
            # Examples type
            if not raw:
                output = f"# {meta['name']} Examples\n\n"
                output += f"> Production-grade {meta['name']} reference configurations.\n\n"
            else:
                output = raw + "\n\n"

            existing_count = current_data.get("total_items", 0)
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
        """
        Calls Gemini 3.8 Flash High exclusively to parse raw notes or commands text
        into structured cheatsheet items with detailed AI explanations.
        """
        from app.ai_engine import call_gemini_api, resolve_gemini_api_key, PINNED_MODEL

        meta = self.get_category_meta(target_category)
        if not meta:
            raise ValueError(f"Unknown target category: {target_category}")

        key = resolve_gemini_api_key(api_key)
        if not key:
            raise ValueError("No Gemini API key found on server. Please configure it in Admin Settings.")

        is_example_type = (meta["type"] == "examples")

        default_command_prompt = f"""You are a Principal DevOps Architect.
Analyze the following unstructured notes, commands, or text, and extract all {meta['name']} commands into a clean JSON array.
For every command, provide:
1. "command": The exact, runnable command line or CLI syntax.
2. "explanation": A detailed, professional AI explanation of what the command does, its flags/switches, and real-world production DevOps use cases.
3. "tags": Relevant keywords or subcategories (e.g. "Troubleshooting", "Networking", "Security", "Disk").

Return strictly valid JSON in this structure:
{{
  "category": "{meta['id']}",
  "parsed_items": [
    {{
      "command": "kubectl get pods -n kube-system --show-labels",
      "explanation": "Lists all pods in the kube-system namespace along with their metadata labels, useful for diagnosing core cluster components and verifying node-agent placement.",
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

        # Strictly call gemini-3.8-flash-high with response_json=True
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

# Singleton instance
cheatsheet_manager = CheatsheetManager()
