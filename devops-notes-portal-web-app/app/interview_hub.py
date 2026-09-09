"""
Interview Hub Manager - Schedules, Calendar, Q&A Repository, and Follow-ups
Stores persistent interview schedules and Q&A in the 'Nagaraj_interviews' folder.
Zero dummy data: Starts completely clean and records only real user interviews.
"""
import os
import json
import uuid
import re
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger("InterviewHub")

CATEGORIES = [
    "Linux", "Shell script", "jenkins", "Github", "Build tools",
    "Docker", "AWS", "Kubernetes", "terraform", "Ansible",
    "jira", "scrum", "Agile", "Monitoring tools", "python",
    "Azure", "AI tool"
]

CATEGORY_KEYWORDS = {
    "Linux": [r"\blinux\b", r"\bubuntu\b", r"\brhel\b", r"\bcentos\b", r"\bsystemd\b", r"\bsystemctl\b", r"\bjournalctl\b", r"\biostat\b", r"\bvmstat\b", r"\bgrep\b", r"\bsed\b", r"\bawk\b", r"\bchmod\b", r"\bchown\b", r"\bhtop\b", r"\bcron\b", r"\bssh\b", r"\bkernel\b", r"\bport 22\b"],
    "Shell script": [r"\bbash\b", r"\bshell\b", r"\bscript\b", r"\bsh\b", r"#!/bin/bash", r"\bcrontab\b"],
    "jenkins": [r"\bjenkins\b", r"\bci/cd\b", r"\bci-cd\b", r"\bci pipeline\b", r"\bjenkinsfile\b", r"\bjnlp\b", r"\bjenkins master\b", r"\bjenkins slave\b", r"\bmaster and slave\b", r"\bjenkins agent\b", r"\bmanage nodes\b", r"\bblue ocean\b", r"\bshared library\b"],
    "Github": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bbitbucket\b", r"\bbranch\b", r"\bmerge\b", r"\brebase\b", r"\bconflict\b", r"\bpull request\b", r"\bcommit\b"],
    "Build tools": [r"\bmaven\b", r"\bgradle\b", r"\bpom\.xml\b", r"\bnpm\b", r"\byarn\b", r"\bnexus\b", r"\bjfrog\b", r"\bartifactory\b", r"\bartifact\b", r"\bbuild once\b", r"\bpromote\b"],
    "Docker": [r"\bdocker\b", r"\bdockerfile\b", r"\bcontainer\b", r"\bimages?\b", r"\bmulti-stage\b", r"\bdocker-compose\b", r"\bcgroups\b", r"\bentrypoint\b", r"\bdistroless\b", r"\bgolden image\b", r"\balpine\b", r"\bbase image\b"],
    "AWS": [r"\baws\b", r"\bec2\b", r"\bs3\b", r"\bvpc\b", r"\biam\b", r"\blambda\b", r"\bcloudwatch\b", r"\bcloudtrail\b", r"\broute53\b", r"\balb\b", r"\bnlb\b", r"\bnacl\b", r"\bsecurity groups?\b", r"\bebs\b", r"\brds\b", r"\becs\b", r"\beks\b", r"\bdynamodb\b", r"\btransit gateway\b", r"\bssm\b", r"\bsecrets manager\b", r"\bami\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b", r"\bpod\b", r"\bpods\b", r"\bdeployments?\b", r"\bservice\b", r"\bingress\b", r"\bconfigmap\b", r"\bsecret\b", r"\bsecrets\b", r"\bhelm\b", r"\bhelm hooks?\b", r"\bdaemonset\b", r"\bstatefulset\b", r"\bkubelet\b", r"\bapiserver\b", r"\betcd\b", r"\bpvc\b", r"\bpv\b", r"\bcni\b", r"\bhpa\b", r"\bvpa\b", r"\bcluster autoscaler\b", r"\bhorizontal pod autoscaler\b", r"\bvertical pod autoscaler\b", r"\bautoscaling\b", r"\bautoscaler\b", r"\bkubectl\b", r"\btaints?\b", r"\baffinity\b", r"\breplicas?\b", r"\brolling update\b", r"\bblue-green\b", r"\bcrashloopbackoff\b", r"\boomkilled\b"],
    "terraform": [r"\bterraform\b", r"\btf\b", r"\bhcl\b", r"\btfstate\b", r"\bterraform state\b", r"\bstate lock\b", r"\bstate file\b", r"\bremote state\b", r"\bbackend\b", r"\bterraform plan\b", r"\bterraform apply\b", r"\bterraform import\b", r"\bprovider\b", r"\bmodule\b"],
    "Ansible": [r"\bansible\b", r"\bplaybook\b", r"\brole\b", r"\binventory\b", r"\badhoc\b", r"\bawx\b", r"\btower\b", r"\bjinja\b"],
    "jira": [r"\bjira\b", r"\bticket\b", r"\bissue\b", r"\bbacklog\b", r"\bconfluence\b"],
    "scrum": [r"\bscrum\b", r"\bstandup\b", r"\bretrospective\b", r"\bstory point\b", r"\bscrum master\b"],
    "Agile": [r"\bagile\b", r"\bkanban\b", r"\bwaterfall\b", r"\bvelocity\b", r"\biteration\b", r"\brca\b", r"\broot cause\b", r"\bpre-prod\b", r"\bstaging\b", r"\brollback\b"],
    "Monitoring tools": [r"\bprometheus\b", r"\bgrafana\b", r"\bdatadog\b", r"\bdynatrace\b", r"\belk\b", r"\bsplunk\b", r"\balertmanager\b", r"\bnagios\b", r"\bzabbix\b", r"\bmetrics\b", r"\balerting\b", r"\bdashboards?\b", r"\bobservability\b"],
    "python": [r"\bpython\b", r"\bboto3\b", r"\bfastapi\b", r"\bflask\b", r"\bdjango\b", r"\bpytest\b", r"\bpip\b"],
    "Azure": [r"\bazure\b", r"\baks\b", r"\bblob\b", r"\bvnet\b", r"\barm\b", r"\bbicep\b", r"\bazure devops\b", r"\bentra\b"],
    "AI tool": [r"\bai\b", r"\bllm\b", r"\bcopilot\b", r"\bchatgpt\b", r"\bgemini\b", r"\bclaude\b", r"\bollama\b", r"\bprompt\b"]
}

def detect_categories(text: str, default_cat: str = "") -> List[str]:
    """Auto-detects relevant categories based on question and answer keywords."""
    detected = []
    if default_cat and default_cat in CATEGORIES and default_cat not in detected:
        detected.append(default_cat)
    text_lower = text.lower()
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if cat not in detected:
                    detected.append(cat)
                break
    return detected

def is_noise_or_chatter(line: str) -> bool:
    l = line.strip().lower()
    if not l:
        return True
    if any(l.startswith(p) for p in [
        "hi @", "class was there", "krishna cancelled", "i took leave on",
        "vincent -", "nithin -", "chethan -", "nagaraj -", "kumar-", "kumar -"
    ]):
        return True
    if re.match(r'^\d{1,2}-[a-z]{3}-\d{4}', l): # date like 16-Feb-2026
        return True
    return False

def is_category_header(line: str) -> str:
    l = line.strip()
    # Matches [Linux]: or [Linux] or [Shell Script]: or [Git]: or [AWS]:
    m = re.match(r'^\[\s*([a-zA-Z\s\-_/]+)\s*\]\s*:?$', l)
    if m:
        cat_raw = m.group(1).strip()
        for cat in CATEGORIES:
            if cat.lower() == cat_raw.lower() or cat_raw.lower() in cat.lower():
                return cat
        return cat_raw
    if l.lower().startswith("interview questions"):
        return "General"
    return ""

def is_question_line(line: str) -> bool:
    l = line.strip()
    if not l or len(l) < 3:
        return False
    # Explicit prefix
    if re.match(r'^(?:Question\s*\d*|Q\d*|\d+[\.\)])\s*[:\.\-]?\s+', l, re.IGNORECASE):
        return True
    # Ends with question mark
    if l.endswith("?"):
        return True
    # Starts with common question / command prompt patterns (and not in code)
    q_starts = [
        "what is", "what are", "what does", "what do", "how do", "how to", "how can", "how does", "how is",
        "why do", "why is", "why should", "why does", "explain ", "difference between", "differentiate ",
        "command to", "command used", "commands to", "list the", "list all", "which command", "which is",
        "write a script", "write a shell", "write a ci/cd", "create a ", "suppose you", "considering ",
        "say you", "your linux", "your team", "your company", "you have", "you deployed", "you deploy",
        "when you", "if you", "if a ", "in what", "can you", "have you", "is it", "where do", "who and",
        "give me the cmd", "give me the comparison"
    ]
    l_lower = l.lower()
    if any(l_lower.startswith(qs) for qs in q_starts) and len(l.split()) >= 3 and not l.startswith("→") and not l.startswith("👉") and not l.startswith("#"):
        return True
    return False

def parse_interview_qa_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Universally parses bulk interview text across all formats:
    - Explicit questions ('Question 1:', 'Q:', '1.')
    - Section & category headers ('[Linux]:', '[Jenkins]', 'Kubernetes Troubleshooting...')
    - Implicit questions ('What is LVM', 'How do you divide learning vs practice?')
    - Answers with multi-line code, ASCII diagrams, and bullet points ('Ans:', 'Answer:', 'Instructor Suggestion:')
    - Sub-questions & follow-ups ('Sub-question: ...')
    - Cleans out non-technical chatter, leaves, and attendance logs.
    """
    lines = raw_text.split("\n")
    items = []
    current_cat = ""
    current_q = None
    current_subquestions = []
    current_answers = []
    current_actions = []
    mode = "none" # "q", "subq", "ans", "action"

    def flush_current():
        nonlocal current_q, current_subquestions, current_answers, current_actions, current_cat, mode
        if current_q:
            q_clean = current_q.strip().strip('"').strip("'").strip()
            # If question has embedded Ans:
            if " Ans:" in q_clean or " ans:" in q_clean:
                parts = re.split(r'\s+ans:\s*', q_clean, flags=re.IGNORECASE)
                q_clean = parts[0].strip()
                if len(parts) > 1:
                    current_answers.insert(0, parts[1].strip())

            ans_parts = []
            if current_subquestions:
                sub_md = "**Follow-up / Sub-questions:**\n" + "\n".join([f"- {sq}" for sq in current_subquestions])
                ans_parts.append(sub_md)
            if current_answers:
                ans_parts.append("**Answer / Solution:**\n" + "\n".join(current_answers))
            if current_actions:
                ans_parts.append("**Action Items / Takeaways:**\n" + "\n".join(current_actions))
            
            final_answer = "\n\n".join(ans_parts).strip() if ans_parts else "To be reviewed / prepared."
            
            # Detect categories from question, answers and active section category
            full_text = f"{current_cat} {q_clean} {' '.join(current_subquestions)} {final_answer}"
            cats = detect_categories(full_text, default_cat=current_cat)
            
            items.append({
                "question": q_clean,
                "answer": final_answer,
                "categories": cats
            })
            current_q = None
            current_subquestions = []
            current_answers = []
            current_actions = []
            mode = "none"

    q_pattern = re.compile(r'^(?:Question\s*\d*|Q\d*|\d+[\.\)])\s*[:\.\-]\s*(.*)$', re.IGNORECASE)
    sub_pattern = re.compile(r'^(?:Sub-question|Sub\s*Question|Follow-up|Follow\s*up)\s*[:\.\-]\s*(.*)$', re.IGNORECASE)
    ans_pattern = re.compile(r'^(?:Instructor[’\']?s?\s*Answer(?:/Suggestion)?|Instructor[’\']?s?\s*Suggestion|Instructor[’\']?s?\s*Answer|Answer|Ans|A)\s*[:\.\-]?\s*(.*)$', re.IGNORECASE)
    action_pattern = re.compile(r'^(?:Action\s*Item|Takeaway|Assignment|Instructor[’\']?s?\s*Final\s*Assignment.*)\s*[:\.\-]?\s*(.*)$', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if mode in ["ans", "action"]:
                # Preserve blank lines inside multiline code/answers
                current_answers.append("")
            continue

        # 1. Skip non-technical chatter / attendance
        if is_noise_or_chatter(stripped):
            continue

        # 2. Check for category header (e.g. "[Linux]:", "[Jenkins]")
        header_cat = is_category_header(stripped)
        if header_cat:
            flush_current()
            current_cat = header_cat
            continue

        # 3. Check for student marker (e.g. "Nithin:", "Kumar:", "Nagaraj:")
        if re.match(r'^[A-Z][a-z]+\s*:\s*$', stripped):
            continue

        # 4. Check explicit regex matches
        q_match = q_pattern.match(stripped)
        sub_match = sub_pattern.match(stripped)
        ans_match = ans_pattern.match(stripped)
        action_match = action_pattern.match(stripped)

        if q_match:
            flush_current()
            current_q = q_match.group(1).strip()
            mode = "q"
        elif ans_match and current_q:
            mode = "ans"
            a_text = ans_match.group(1).strip()
            if a_text:
                current_answers.append(a_text)
        elif sub_match and current_q:
            mode = "subq"
            sq_text = sub_match.group(1).strip().strip('"').strip("'").strip()
            current_subquestions.append(sq_text)
        elif action_match and current_q:
            mode = "action"
            act_text = action_match.group(1).strip()
            if act_text:
                current_actions.append(act_text)
        elif is_question_line(stripped):
            # Consecutive or new implicit question
            flush_current()
            current_q = stripped
            mode = "q"
        else:
            if not current_q:
                # Might be a heading or first question
                if is_question_line(stripped):
                    current_q = stripped
                    mode = "q"
            elif mode == "action":
                current_actions.append(stripped)
            elif mode == "ans":
                current_answers.append(stripped)
            elif mode == "subq":
                current_subquestions.append(stripped)
            elif mode == "q":
                # Check if it has embedded Ans:
                if " Ans:" in stripped or " ans:" in stripped or stripped.startswith("Ans:"):
                    parts = re.split(r'\s*Ans:\s*', stripped, flags=re.IGNORECASE)
                    if parts[0]:
                        current_q += " " + parts[0]
                    mode = "ans"
                    if len(parts) > 1 and parts[1]:
                        current_answers.append(parts[1])
                else:
                    current_q += " " + stripped

    flush_current()
    return items

DEFAULT_ROUNDS = [
    "Technical Round 1",
    "Technical Round 2",
    "Managerial / Tech Lead Round",
    "System Design / Architecture Round",
    "Live Coding / Hands-on Round",
    "DevSecOps & Cloud Scenario Round",
    "HR / Cultural Fit Round",
    "Client / Final Director Round"
]

class InterviewManager:
    def __init__(self):
        self.storage_dir = self._resolve_storage_dir()
        os.makedirs(self.storage_dir, exist_ok=True)
        self.schedules_file = os.path.join(self.storage_dir, "schedules.json")
        self.questions_file = os.path.join(self.storage_dir, "questions.json")
        self.rounds_file = os.path.join(self.storage_dir, "rounds.json")
        self.last_push_status = {"status": "none", "time": "", "message": ""}
        self._init_files()

    def _resolve_storage_dir(self) -> str:
        # 1. Container path
        container_path = "/app/data/notes/devops-notes/Nagaraj_interviews"
        if os.path.exists(os.path.dirname(container_path)):
            return container_path
        
        # 2. Local notes repo path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        notes_path = os.path.join(base_dir, "Nagaraj_interviews")
        if os.path.exists(notes_path):
            return notes_path
        
        # 3. Fallback within app directory
        app_local = os.path.join(os.path.dirname(__file__), "data", "Nagaraj_interviews")
        return app_local

    def _init_files(self):
        # Clean initialization: starts completely empty with NO dummy records
        if not os.path.exists(self.schedules_file):
            self._save_json(self.schedules_file, [])
        if not os.path.exists(self.questions_file):
            self._save_json(self.questions_file, [])
        if not os.path.exists(self.rounds_file):
            self._save_json(self.rounds_file, [])
        self._reconcile_schedules_from_questions()
        self._generate_markdown_docs()

    def _reconcile_schedules_from_questions(self):
        """
        Auto-reconciles schedules.json from questions.json.
        If questions were uploaded for a company & round on a date, but no schedule
        entry exists in schedules.json, automatically creates the completed schedule record.
        """
        questions = self._read_json(self.questions_file)
        if not questions:
            return
        
        schedules = self._read_json(self.schedules_file)
        modified = False

        grouped = {}
        for q in questions:
            comp = (q.get("company") or "").strip()
            rnd = (q.get("round") or "Technical Round 1").strip()
            dt = (q.get("date") or date.today().isoformat()).strip()
            if not comp:
                continue
            key = (comp.lower(), rnd.lower(), dt)
            if key not in grouped:
                grouped[key] = {
                    "company": comp,
                    "round": rnd,
                    "date": dt,
                    "experience": q.get("experience", ""),
                    "notes": q.get("notes", ""),
                    "difficulty": q.get("difficulty", "Moderate"),
                    "created_at": q.get("created_at", datetime.utcnow().isoformat())
                }

        for (comp_lower, rnd_lower, dt), info in grouped.items():
            matched = False
            for s in schedules:
                s_comp = (s.get("company") or "").strip().lower()
                s_rnd = (s.get("round") or "").strip().lower()
                s_date = (s.get("date") or "").strip()
                if s_comp == comp_lower and (s_rnd == rnd_lower or not s_rnd) and (s_date == dt or not s_date):
                    s["questions_uploaded"] = True
                    s["status"] = "completed"
                    if info.get("experience") and not s.get("experience"):
                        s["experience"] = info["experience"]
                    if info.get("notes") and not s.get("notes"):
                        s["notes"] = info["notes"]
                    if info.get("difficulty") and not s.get("difficulty"):
                        s["difficulty"] = info["difficulty"]
                    matched = True
                    break

            if not matched:
                new_sched = {
                    "id": f"sched-{uuid.uuid4().hex[:8]}",
                    "company": info["company"],
                    "role": "DevOps Engineer",
                    "round": info["round"],
                    "date": info["date"],
                    "time": "10:00",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "status": "completed",
                    "questions_uploaded": True,
                    "experience": info.get("experience", ""),
                    "notes": info.get("notes", ""),
                    "difficulty": info.get("difficulty", "Moderate"),
                    "created_at": info.get("created_at")
                }
                schedules.append(new_sched)
                modified = True

        if modified:
            self._save_json(self.schedules_file, schedules, commit_msg="Auto-reconcile completed interview schedules from questions bank")

    # --- ROUNDS API ---
    def get_rounds(self) -> List[Dict[str, Any]]:
        custom_list = self._read_json(self.rounds_file)
        result = []
        for r in DEFAULT_ROUNDS:
            result.append({
                "id": f"def-{r.lower().replace(' ', '-').replace('/', '-')}",
                "name": r,
                "is_default": True,
                "can_delete": False,
                "can_rename": False
            })
        for cr in custom_list:
            result.append({
                "id": cr.get("id"),
                "name": cr.get("name"),
                "is_default": False,
                "can_delete": True,
                "can_rename": True
            })
        return result

    def add_custom_round(self, name: str) -> Dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Round name cannot be empty")
        custom_list = self._read_json(self.rounds_file)
        # Check if already exists in default or custom
        for r in DEFAULT_ROUNDS:
            if r.lower() == clean_name.lower():
                return {"id": f"def-{r.lower().replace(' ', '-')}", "name": r, "is_default": True, "can_delete": False, "can_rename": False}
        for cr in custom_list:
            if cr.get("name", "").lower() == clean_name.lower():
                return {"id": cr["id"], "name": cr["name"], "is_default": False, "can_delete": True, "can_rename": True}

        new_round = {
            "id": f"round-{uuid.uuid4().hex[:8]}",
            "name": clean_name,
            "created_at": datetime.utcnow().isoformat()
        }
        custom_list.append(new_round)
        self._save_json(self.rounds_file, custom_list, commit_msg=f"Add custom interview round: {clean_name}")
        return {
            "id": new_round["id"],
            "name": new_round["name"],
            "is_default": False,
            "can_delete": True,
            "can_rename": True
        }

    def rename_custom_round(self, round_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("Round name cannot be empty")
        custom_list = self._read_json(self.rounds_file)
        target = None
        old_name = ""
        for r in custom_list:
            if r.get("id") == round_id:
                target = r
                old_name = r.get("name", "")
                r["name"] = clean_name
                break
        if not target:
            return None
        self._save_json(self.rounds_file, custom_list, commit_msg=f"Rename custom round '{old_name}' to '{clean_name}'")
        
        # Update any schedules with old round name
        if old_name and old_name != clean_name:
            schedules = self._read_json(self.schedules_file)
            updated_sched = False
            for s in schedules:
                if s.get("round") == old_name:
                    s["round"] = clean_name
                    updated_sched = True
            if updated_sched:
                self._save_json(self.schedules_file, schedules, commit_msg=f"Update schedules round name to '{clean_name}'")

        return {
            "id": target["id"],
            "name": target["name"],
            "is_default": False,
            "can_delete": True,
            "can_rename": True
        }

    def delete_custom_round(self, round_id: str) -> bool:
        custom_list = self._read_json(self.rounds_file)
        filtered = [r for r in custom_list if r.get("id") != round_id]
        if len(filtered) == len(custom_list):
            return False
        self._save_json(self.rounds_file, filtered, commit_msg=f"Delete custom interview round ID: {round_id}")
        return True

    def _read_json(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_json(self, filepath: str, data: List[Dict[str, Any]], commit_msg: str = "Update Nagaraj interviews tracker"):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._generate_markdown_docs()
            self._auto_git_sync(commit_msg)
        except Exception as e:
            logger.error(f"Error saving to {filepath}: {e}")

    def _generate_markdown_docs(self):
        """
        Generates human-readable Markdown files directly in 'Nagaraj_interviews/':
        1. README.md - High-level summary dashboard, interview schedules table & question bank index
        2. <Company>.md - Individual company interview records with full Q&A, follow-ups, and feedback
        """
        try:
            schedules = self._read_json(self.schedules_file)
            questions = self._read_json(self.questions_file)

            schedules.sort(key=lambda s: f"{s.get('date', '')} {s.get('start_time') or s.get('time', '')}", reverse=True)

            # Group questions by company and round
            comp_questions = {}
            for q in questions:
                comp = (q.get("company") or "").strip() or "General"
                rnd = (q.get("round") or "Technical Round 1").strip() or "Technical Round 1"
                if comp not in comp_questions:
                    comp_questions[comp] = {}
                if rnd not in comp_questions[comp]:
                    comp_questions[comp][rnd] = []
                comp_questions[comp][rnd].append(q)

            # Collect all distinct companies across schedules and questions
            all_companies_map = {}
            for s in schedules:
                c = (s.get("company") or "").strip()
                if c:
                    all_companies_map[c.lower()] = c
            for c in comp_questions.keys():
                if c and c.lower() not in all_companies_map:
                    all_companies_map[c.lower()] = c

            all_companies = sorted(list(all_companies_map.values()), key=lambda x: x.lower())

            # 1. Generate README.md
            readme_lines = [
                "# 🎯 Nagaraj DevOps Interview Hub & Schedules",
                "",
                "> **Automated GitHub Persistence:** This folder tracks live interview schedules, technical rounds, candidate experiences, and real interview question banks. All changes made in the DevOps Knowledge Portal are automatically updated and committed here in human-readable format.",
                "",
                "---",
                "",
                "## 📊 Summary Statistics",
                "",
                "| Metric | Count | Description |",
                "| :--- | :--- | :--- |",
                f"| **Total Schedules** | `{len(schedules)}` | Total interview events logged |",
                f"| **Total Companies** | `{len(all_companies)}` | Distinct organizations tracked |",
                f"| **Total Questions Banked** | `{len(questions)}` | Real questions with follow-ups & solutions |",
                f"| **Completed Interviews** | `{len([s for s in schedules if (s.get('status') or '').lower() == 'completed'])}` | Successfully concluded rounds |",
                f"| **Upcoming / Scheduled** | `{len([s for s in schedules if (s.get('status') or '').lower() == 'scheduled'])}` | Upcoming interview rounds |",
                "",
                "---",
                "",
                "## 📅 Interview Schedules & Tracker",
                ""
            ]

            if not schedules:
                readme_lines.append("*No interview schedules recorded yet.*")
            else:
                readme_lines.extend([
                    "| Date | Time (IST) | Company | Role | Round | Status | Difficulty | Notes / Link |",
                    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
                ])
                for s in schedules:
                    dt = s.get("date", "N/A")
                    t_start = s.get("start_time") or s.get("time", "10:00")
                    t_end = s.get("end_time", "")
                    t_str = f"{t_start} - {t_end}" if t_end else t_start
                    comp = s.get("company", "N/A")
                    role = s.get("role", "DevOps Engineer")
                    rnd = s.get("round", "Technical Round")
                    status = (s.get("status") or "scheduled").capitalize()
                    diff = s.get("difficulty", "Moderate")
                    notes = (s.get("notes") or "").replace("\n", " ").strip()
                    link = (s.get("meeting_link") or "").strip()
                    extra = []
                    if link:
                        extra.append(f"[Meeting Link]({link})")
                    if notes:
                        extra.append(notes)
                    extra_str = " • ".join(extra) if extra else "-"
                    
                    if status.lower() == "completed":
                        status_str = "✅ Completed"
                    elif status.lower() == "scheduled":
                        status_str = "⏳ Scheduled"
                    elif status.lower() == "cancelled":
                        status_str = "❌ Cancelled"
                    else:
                        status_str = status

                    safe_fname = re.sub(r'[\\/*?:"<>|]', '_', comp) + ".md"
                    comp_display = f"[{comp}](./{safe_fname})"

                    readme_lines.append(f"| {dt} | {t_str} | {comp_display} | {role} | {rnd} | {status_str} | {diff} | {extra_str} |")

            readme_lines.extend([
                "",
                "---",
                "",
                "## 🏢 Question Banks & Interview Details by Company",
                "",
                "Detailed schedules, notes, job descriptions, and interviewer question banks are maintained in dedicated Markdown documents:",
                ""
            ])

            if not all_companies:
                readme_lines.append("*No interview companies recorded yet.*")
            else:
                for comp in all_companies:
                    safe_fname = re.sub(r'[\\/*?:"<>|]', '_', comp) + ".md"
                    rounds = comp_questions.get(comp, {})
                    total_comp_q = sum(len(qs) for qs in rounds.values())
                    comp_scheds = [s for s in schedules if (s.get("company") or "").strip().lower() == comp.lower()]
                    sched_count = len(comp_scheds)
                    
                    if rounds:
                        rounds_str = ", ".join([f"`{r}` ({len(qs)} Qs)" for r, qs in rounds.items()])
                        readme_lines.append(f"- 🏢 **[{comp}](./{safe_fname})** — {total_comp_q} questions logged ({rounds_str}) • {sched_count} schedule(s)")
                    else:
                        readme_lines.append(f"- 🏢 **[{comp}](./{safe_fname})** — {sched_count} interview round(s) scheduled")

            readme_lines.append("")
            readme_path = os.path.join(self.storage_dir, "README.md")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("\n".join(readme_lines) + "\n")

            # 2. Generate Individual Company Markdown Files
            active_company_files = set()
            for comp in all_companies:
                safe_fname = re.sub(r'[\\/*?:"<>|]', '_', comp) + ".md"
                active_company_files.add(safe_fname)
                comp_file = os.path.join(self.storage_dir, safe_fname)
                
                comp_scheds = [s for s in schedules if (s.get("company") or "").strip().lower() == comp.lower()]
                rounds = comp_questions.get(comp, {})

                lines = [
                    f"# 🏢 {comp} - Interview Experience & Question Bank",
                    "",
                    "> Real DevOps interview questions, technical follow-up questions, and production-tested solutions recorded from actual interview rounds.",
                    "",
                    "---",
                    "",
                    "## 📋 Interview Schedules & Metadata",
                    ""
                ]

                if comp_scheds:
                    lines.extend([
                        "| Round | Date | Time (IST) | Status | Difficulty | Role | Meeting Link |",
                        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
                    ])
                    for cs in comp_scheds:
                        c_rnd = cs.get("round", "Technical Round")
                        c_dt = cs.get("date", "N/A")
                        c_start = cs.get("start_time") or cs.get("time", "10:00")
                        c_end = cs.get("end_time", "")
                        c_t = f"{c_start} - {c_end}" if c_end else c_start
                        c_st = (cs.get("status") or "scheduled").capitalize()
                        c_diff = cs.get("difficulty", "Moderate")
                        c_role = cs.get("role", "DevOps Engineer")
                        c_link = cs.get("meeting_link", "")
                        c_link_str = f"[Link]({c_link})" if c_link else "-"
                        lines.append(f"| {c_rnd} | {c_dt} | {c_t} | {c_st} | {c_diff} | {c_role} | {c_link_str} |")

                    lines.append("")

                    # Check for compensation or notes across schedules
                    ctc_list = [cs.get("salary_ctc") for cs in comp_scheds if cs.get("salary_ctc")]
                    if ctc_list:
                        lines.extend([
                            f"- **Compensation / CTC:** {', '.join(set(ctc_list))}",
                            ""
                        ])

                    jds = [cs.get("job_description") for cs in comp_scheds if cs.get("job_description")]
                    if jds:
                        lines.extend([
                            "### 📄 Job Description / Role Requirements",
                            f"```\n{jds[0]}\n```",
                            ""
                        ])

                    notes_list = [cs.get("notes") for cs in comp_scheds if cs.get("notes")]
                    if notes_list:
                        lines.extend([
                            "### 📝 Candidate Notes & Interview Observations",
                            "\n\n".join(notes_list),
                            ""
                        ])
                else:
                    lines.extend([
                        f"- **Company:** {comp}",
                        ""
                    ])

                lines.extend([
                    "---",
                    "",
                    "## ❓ Technical Questions & Answers",
                    ""
                ])

                if not rounds:
                    lines.append("*No technical questions recorded yet for this company. Questions can be added via the DevOps Knowledge Portal Interview Hub.*")
                    lines.append("")
                else:
                    q_counter = 1
                    for rnd_name, q_list in rounds.items():
                        lines.append(f"### 🎯 Round: {rnd_name}")
                        lines.append("")

                        for q in q_list:
                            q_text = (q.get("question") or "").strip()
                            ans_text = (q.get("answer") or "").strip()
                            cats = q.get("categories", [])
                            diff = q.get("difficulty", "Moderate")
                            
                            cats_str = " ".join([f"`{c}`" for c in cats]) if cats else "`General`"

                            lines.append(f"#### Q{q_counter}: {q_text}")
                            lines.append(f"**Tags:** {cats_str} | **Difficulty:** `{diff}`")
                            lines.append("")

                            if ans_text:
                                lines.append("<details open>")
                                lines.append("<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>")
                                lines.append("")
                                lines.append(ans_text)
                                lines.append("")
                                lines.append("</details>")
                            else:
                                lines.append("*Answer not recorded.*")

                            lines.append("")
                            lines.append("---")
                            lines.append("")
                            q_counter += 1

                with open(comp_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")

            # Clean up obsolete company markdown files if any company was deleted
            for item in os.listdir(self.storage_dir):
                if item.endswith(".md") and item != "README.md":
                    if item not in active_company_files:
                        try:
                            os.remove(os.path.join(self.storage_dir, item))
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Error generating human-readable markdown docs: {e}")

    def _get_github_token(self, repo_dir: str) -> str:
        for env_var in ["GITHUB_TOKEN", "GH_TOKEN", "GIT_PUSH_TOKEN", "GIT_TOKEN"]:
            val = os.getenv(env_var, "").strip()
            if val:
                return val
        token_files = [
            os.path.join(repo_dir, ".git_token"),
            os.path.join(self.storage_dir, ".git_token"),
            os.path.join(os.path.dirname(self.storage_dir), ".git_token"),
            "/app/data/notes/.git_token"
        ]
        for tf in token_files:
            if os.path.exists(tf):
                try:
                    with open(tf, "r", encoding="utf-8") as f:
                        tok = f.read().strip()
                        if tok:
                            return tok
                except Exception:
                    pass
        # Fallback: check ~/.git-credentials on host
        git_cred_file = os.path.expanduser("~/.git-credentials")
        if os.path.exists(git_cred_file):
            try:
                with open(git_cred_file, "r", encoding="utf-8") as f:
                    txt = f.read()
                m = re.search(r'https?://[^:]+:([^@]+)@github\.com', txt)
                if m:
                    return m.group(1).strip()
            except Exception:
                pass
        return ""

    def _run_git_cli(self, repo_dir: str, args: List[str]):
        import subprocess
        try:
            res = subprocess.run(
                ["git", "-C", repo_dir] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def _auto_git_sync(self, commit_msg: str = "Update Nagaraj interviews tracker"):
        try:
            repo_dir = os.path.dirname(self.storage_dir)
            if not os.path.exists(os.path.join(repo_dir, ".git")):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                if os.path.exists(os.path.join(base_dir, ".git")):
                    repo_dir = base_dir
                else:
                    logger.warning(f"No .git directory found at {repo_dir} or {base_dir}")
                    return

            # Ensure git author and committer are configured
            self._run_git_cli(repo_dir, ["config", "user.name", "nagaraj602"])
            self._run_git_cli(repo_dir, ["config", "user.email", "nagarajkamath602@outlook.com"])

            rel_storage = os.path.relpath(self.storage_dir, repo_dir).replace("\\", "/")
            self._run_git_cli(repo_dir, ["add", rel_storage])

            # Check if there are changes to commit
            ret_code, status_out, _ = self._run_git_cli(repo_dir, ["status", "--porcelain", rel_storage])
            committed_now = False
            if status_out:
                c_ret, c_out, c_err = self._run_git_cli(repo_dir, ["commit", "-m", commit_msg])
                if c_ret == 0:
                    logger.info(f"Committed changes in {rel_storage}: '{commit_msg}'")
                    committed_now = True
                else:
                    logger.warning(f"Git commit returned code {c_ret}: {c_err}")

            # Get current active branch
            _, branch, _ = self._run_git_cli(repo_dir, ["rev-parse", "--abbrev-ref", "HEAD"])
            if not branch:
                branch = "main"

            # Check if there are unpushed commits
            _, ahead_log, _ = self._run_git_cli(repo_dir, ["log", f"origin/{branch}..{branch}", "--oneline"])
            needs_push = committed_now or bool(ahead_log.strip())

            if needs_push:
                token = self._get_github_token(repo_dir)
                _, origin_url, _ = self._run_git_cli(repo_dir, ["config", "--get", "remote.origin.url"])

                push_target = "origin"
                if token and "github.com" in origin_url:
                    clean_url = re.sub(r'https?://(?:[^@]+@)?github\.com/', 'https://github.com/', origin_url)
                    push_target = clean_url.replace("https://github.com/", f"https://{token}@github.com/")

                # Rebase pull before push
                self._run_git_cli(repo_dir, ["pull", push_target, branch, "--rebase"])

                # Push to remote
                p_code, p_out, p_err = self._run_git_cli(repo_dir, ["push", push_target, f"{branch}:{branch}"])
                if p_code == 0:
                    logger.info(f"Successfully pushed interviews update to GitHub ({origin_url})!")
                    self.last_push_status = {
                        "status": "success",
                        "time": datetime.utcnow().isoformat(),
                        "message": f"Successfully pushed: {commit_msg}"
                    }
                else:
                    err_msg = p_err or p_out or "Push failed"
                    logger.error(f"Failed to push to GitHub: {err_msg}")
                    self.last_push_status = {
                        "status": "error",
                        "time": datetime.utcnow().isoformat(),
                        "message": err_msg
                    }
            else:
                self.last_push_status = {
                    "status": "success",
                    "time": datetime.utcnow().isoformat(),
                    "message": "Repository up to date with remote."
                }
        except Exception as e:
            logger.error(f"Auto git sync failed: {e}")
            self.last_push_status = {
                "status": "error",
                "time": datetime.utcnow().isoformat(),
                "message": str(e)
            }

    def get_token_status(self) -> Dict[str, Any]:
        repo_dir = os.path.dirname(self.storage_dir)
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if os.path.exists(os.path.join(base_dir, ".git")):
                repo_dir = base_dir

        token = self._get_github_token(repo_dir)
        source = "None"
        if os.getenv("GITHUB_TOKEN"):
            source = "Environment Variable (GITHUB_TOKEN)"
        elif os.getenv("GH_TOKEN") or os.getenv("GIT_PUSH_TOKEN") or os.getenv("GIT_TOKEN"):
            source = "Environment Variable"
        else:
            token_files = [
                "/app/data/notes/.git_token",
                os.path.join(repo_dir, ".git_token"),
                os.path.join(self.storage_dir, ".git_token")
            ]
            for tf in token_files:
                if os.path.exists(tf):
                    source = f"Saved Token File ({os.path.basename(tf)})"
                    break
            if source == "None" and os.path.exists(os.path.expanduser("~/.git-credentials")):
                source = "Host Credentials (~/.git-credentials)"

        masked = ""
        if token:
            if len(token) > 8:
                masked = f"{token[:4]}...{token[-4:]}"
            else:
                masked = "****"

        return {
            "has_token": bool(token),
            "token_masked": masked,
            "source": source,
            "last_push": getattr(self, "last_push_status", None)
        }

    def save_github_token(self, token: str) -> Dict[str, Any]:
        clean_token = token.strip()
        if not clean_token:
            raise ValueError("Token cannot be empty")
        
        target_paths = [
            "/app/data/notes/.git_token",
            os.path.join(self.storage_dir, ".git_token")
        ]
        repo_dir = os.path.dirname(self.storage_dir)
        if os.path.exists(os.path.join(repo_dir, ".git")):
            target_paths.append(os.path.join(repo_dir, ".git_token"))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if os.path.exists(os.path.join(base_dir, ".git")):
            target_paths.append(os.path.join(base_dir, ".git_token"))

        for p in target_paths:
            try:
                parent = os.path.dirname(p)
                if os.path.exists(parent):
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(clean_token)
            except Exception as e:
                logger.warning(f"Could not save token to {p}: {e}")

        # Now test git push immediately
        return self.test_git_push()

    def delete_github_token(self) -> bool:
        target_paths = [
            "/app/data/notes/.git_token",
            os.path.join(self.storage_dir, ".git_token")
        ]
        repo_dir = os.path.dirname(self.storage_dir)
        if os.path.exists(repo_dir):
            target_paths.append(os.path.join(repo_dir, ".git_token"))
        deleted = False
        for p in target_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    deleted = True
                except Exception:
                    pass
        return deleted

    def test_git_push(self) -> Dict[str, Any]:
        self._generate_markdown_docs()
        self._auto_git_sync(commit_msg="Test sync & verify human-readable Nagaraj interviews tracker")
        status = getattr(self, "last_push_status", None)
        if status and status.get("status") == "success":
            return {
                "status": "success",
                "message": "Git sync & push succeeded! Markdown files and schedules are synced to GitHub.",
                "details": status
            }
        else:
            err = status.get("message") if status else "Unknown error during push"
            return {
                "status": "error",
                "message": f"Git push failed: {err}",
                "details": status
            }

    # --- SCHEDULES API ---
    def get_schedules(self) -> List[Dict[str, Any]]:
        self._reconcile_schedules_from_questions()
        schedules = self._read_json(self.schedules_file)
        schedules.sort(key=lambda x: f"{x.get('date', '')} {x.get('start_time') or x.get('time', '')}", reverse=True)
        return schedules

    def add_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        schedules = self._read_json(self.schedules_file)
        start_t = data.get("start_time") or data.get("time", "10:00")
        end_t = data.get("end_time", "")
        new_item = {
            "id": f"sched-{uuid.uuid4().hex[:8]}",
            "company": data.get("company", "").strip(),
            "role": data.get("role", "DevOps Engineer").strip(),
            "round": data.get("round", "Technical Round").strip(),
            "date": data.get("date", date.today().isoformat()),
            "time": start_t,
            "start_time": start_t,
            "end_time": end_t,
            "status": data.get("status", "scheduled"), # scheduled, completed, cancelled, rescheduled
            "meeting_link": data.get("meeting_link", "").strip(),
            "about_company": data.get("about_company", "").strip(),
            "role_info": data.get("role_info", "").strip(),
            "job_description": data.get("job_description", "").strip(),
            "salary_ctc": data.get("salary_ctc", "").strip(),
            "monthly_salary": data.get("monthly_salary", "").strip(),
            "notes": data.get("notes", "").strip(),
            "questions_uploaded": False,
            "created_at": datetime.utcnow().isoformat()
        }
        schedules.append(new_item)
        self._save_json(self.schedules_file, schedules)
        return new_item

    def update_schedule(self, sched_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        schedules = self._read_json(self.schedules_file)
        for s in schedules:
            if s.get("id") == sched_id:
                for k, v in updates.items():
                    if v is not None:
                        s[k] = v
                if "start_time" in updates and "time" not in updates:
                    s["time"] = updates["start_time"]
                elif "time" in updates and "start_time" not in updates:
                    s["start_time"] = updates["time"]
                self._save_json(self.schedules_file, schedules)
                return s
        return None

    def delete_schedule(self, sched_id: str) -> bool:
        schedules = self._read_json(self.schedules_file)
        initial_len = len(schedules)
        schedules = [s for s in schedules if s.get("id") != sched_id]
        if len(schedules) < initial_len:
            self._save_json(self.schedules_file, schedules)
            return True
        return False

    def delete_company(self, company: str) -> Dict[str, Any]:
        comp_target = (company or "").strip().lower()
        if not comp_target:
            return {"status": "error", "message": "Company name required"}

        # Delete from schedules
        schedules = self._read_json(self.schedules_file)
        sched_before = len(schedules)
        schedules = [s for s in schedules if (s.get("company") or "").strip().lower() != comp_target]
        deleted_scheds = sched_before - len(schedules)
        if deleted_scheds > 0:
            self._save_json(self.schedules_file, schedules)

        # Delete from questions
        questions = self._read_json(self.questions_file)
        q_before = len(questions)
        questions = [q for q in questions if (q.get("company") or "").strip().lower() != comp_target]
        deleted_questions = q_before - len(questions)
        if deleted_questions > 0:
            self._save_json(self.questions_file, questions)

        return {
            "status": "deleted",
            "company": company,
            "deleted_schedules": deleted_scheds,
            "deleted_questions": deleted_questions
        }

    def delete_company_round(self, company: str, round_name: str) -> Dict[str, Any]:
        comp_target = (company or "").strip().lower()
        round_target = (round_name or "").strip().lower()
        if not comp_target or not round_target:
            return {"status": "error", "message": "Company and round name required"}

        # Delete from schedules
        schedules = self._read_json(self.schedules_file)
        sched_before = len(schedules)
        schedules = [s for s in schedules if not ((s.get("company") or "").strip().lower() == comp_target and (s.get("round") or "").strip().lower() == round_target)]
        deleted_scheds = sched_before - len(schedules)
        if deleted_scheds > 0:
            self._save_json(self.schedules_file, schedules)

        # Delete from questions
        questions = self._read_json(self.questions_file)
        q_before = len(questions)
        questions = [q for q in questions if not ((q.get("company") or "").strip().lower() == comp_target and (q.get("round") or "").strip().lower() == round_target)]
        deleted_questions = q_before - len(questions)
        if deleted_questions > 0:
            self._save_json(self.questions_file, questions)

        return {
            "status": "deleted",
            "company": company,
            "round": round_name,
            "deleted_schedules": deleted_scheds,
            "deleted_questions": deleted_questions
        }

    # --- QUESTIONS API ---
    def get_questions(self, query: str = "", category: str = "", company: str = "") -> List[Dict[str, Any]]:
        questions = self._read_json(self.questions_file)
        filtered = []
        q_lower = query.lower().strip()
        cat_lower = category.lower().strip()
        comp_lower = company.lower().strip()

        for q in questions:
            # Query match
            if q_lower:
                text_match = (
                    q_lower in q.get("question", "").lower() or
                    q_lower in q.get("answer", "").lower() or
                    q_lower in q.get("company", "").lower() or
                    q_lower in q.get("round", "").lower()
                )
                if not text_match:
                    continue

            # Category filter
            if cat_lower and cat_lower != "all":
                q_cats = [c.lower() for c in q.get("categories", [])]
                if cat_lower not in q_cats:
                    continue

            # Company filter
            if comp_lower and comp_lower != "all":
                if comp_lower not in q.get("company", "").lower():
                    continue

            filtered.append(q)

        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return filtered

    def add_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        questions = self._read_json(self.questions_file)
        cats = data.get("categories", [])
        if not cats:
            # Auto-detect if user left empty
            cats = detect_categories(data.get("question", "") + " " + data.get("answer", ""))
            
        company_name = data.get("company", "").strip()
        round_name = data.get("round", "").strip() or "Technical Round 1"
        interview_date = data.get("date", date.today().isoformat())

        new_q = {
            "id": f"q-{uuid.uuid4().hex[:8]}",
            "company": company_name,
            "round": round_name,
            "date": interview_date,
            "question": data.get("question", "").strip(),
            "answer": data.get("answer", "").strip(),
            "categories": cats,
            "created_at": datetime.utcnow().isoformat()
        }
        questions.append(new_q)
        self._save_json(self.questions_file, questions)

        # Mark corresponding schedule as completed & uploaded, or auto-create if missing
        schedules = self._read_json(self.schedules_file)
        matched = False
        for s in schedules:
            if s.get("company", "").strip().lower() == company_name.lower():
                s["questions_uploaded"] = True
                s["status"] = "completed"
                matched = True
                break

        if not matched and company_name:
            new_sched = {
                "id": f"sched-{uuid.uuid4().hex[:8]}",
                "company": company_name,
                "role": "DevOps Engineer",
                "round": round_name,
                "date": interview_date,
                "time": "10:00",
                "start_time": "10:00",
                "end_time": "11:00",
                "status": "completed",
                "questions_uploaded": True,
                "created_at": datetime.utcnow().isoformat()
            }
            schedules.append(new_sched)

        self._save_json(self.schedules_file, schedules)
        return new_q

    def update_question(self, q_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        questions = self._read_json(self.questions_file)
        for q in questions:
            if q.get("id") == q_id:
                for k, v in updates.items():
                    if v is not None:
                        q[k] = v
                self._save_json(self.questions_file, questions)
                return q
        return None

    def delete_question(self, q_id: str) -> bool:
        questions = self._read_json(self.questions_file)
        initial_len = len(questions)
        questions = [q for q in questions if q.get("id") != q_id]
        if len(questions) < initial_len:
            self._save_json(self.questions_file, questions)
            return True
        return False

    def add_bulk_questions(self, company: str, round_name: str, interview_date: str, qa_items: List[Dict[str, Any]], experience: str = "", notes: str = "", difficulty: str = "") -> int:
        questions = self._read_json(self.questions_file)
        added_count = 0
        company_clean = company.strip()
        round_clean = round_name.strip() or "Technical Round 1"
        date_clean = interview_date.strip() or date.today().isoformat()

        for item in qa_items:
            q_text = item.get("question", "").strip()
            if not q_text:
                continue
            
            cats = item.get("categories", [])
            if not cats:
                cats = detect_categories(q_text + " " + item.get("answer", ""))

            new_q = {
                "id": f"q-{uuid.uuid4().hex[:8]}",
                "company": company_clean,
                "round": round_clean,
                "date": date_clean,
                "question": q_text,
                "answer": item.get("answer", "").strip(),
                "categories": cats,
                "experience": experience.strip(),
                "notes": notes.strip(),
                "difficulty": difficulty.strip(),
                "created_at": datetime.utcnow().isoformat()
            }
            questions.append(new_q)
            added_count += 1

        self._save_json(self.questions_file, questions, f"Add {added_count} interview questions for {company_clean}")

        # Update schedule status or auto-create if missing
        schedules = self._read_json(self.schedules_file)
        matched = False
        for s in schedules:
            if s.get("company", "").strip().lower() == company_clean.lower() and (not round_name or s.get("round", "").strip().lower() == round_clean.lower() or not s.get("questions_uploaded")):
                s["questions_uploaded"] = True
                s["status"] = "completed"
                if experience:
                    s["experience"] = experience.strip()
                if notes:
                    s["notes"] = notes.strip()
                if difficulty:
                    s["difficulty"] = difficulty.strip()
                matched = True
                break

        if not matched and company_clean:
            new_sched = {
                "id": f"sched-{uuid.uuid4().hex[:8]}",
                "company": company_clean,
                "role": "DevOps Engineer",
                "round": round_clean,
                "date": date_clean,
                "time": "10:00",
                "start_time": "10:00",
                "end_time": "11:00",
                "status": "completed",
                "questions_uploaded": True,
                "experience": experience.strip(),
                "notes": notes.strip(),
                "difficulty": difficulty.strip(),
                "created_at": datetime.utcnow().isoformat()
            }
            schedules.append(new_sched)

        self._save_json(self.schedules_file, schedules, f"Mark interview schedule completed for {company_clean}")
        return added_count

    # --- STATISTICS & DETAILED LISTS FOR POPUPS ---
    def get_stats(self) -> Dict[str, Any]:
        self._reconcile_schedules_from_questions()
        schedules = self._read_json(self.schedules_file)
        questions = self._read_json(self.questions_file)

        today = date.today()
        today_str = today.isoformat()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Today's interviews sorted chronologically
        today_schedules = [s for s in schedules if s.get("date") == today_str]
        today_schedules.sort(key=lambda x: x.get("start_time") or x.get("time", "00:00"))

        completed_schedules = [s for s in schedules if s.get("status") == "completed"]
        
        # Unique companies map (from all schedules and questions)
        companies_map = {}
        for s in schedules:
            comp = s.get("company", "").strip()
            if comp:
                if comp not in companies_map:
                    companies_map[comp] = []
                companies_map[comp].append(s)

        # Ensure any company in questions is also present
        for q in questions:
            comp = q.get("company", "").strip()
            if comp and comp not in companies_map:
                companies_map[comp] = [{
                    "id": "sched-auto",
                    "company": comp,
                    "role": "DevOps Engineer",
                    "round": q.get("round", "Technical Round 1"),
                    "date": q.get("date", today_str),
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "status": "completed"
                }]

        # Weekly calculations
        weekly_schedules = []
        for s in schedules:
            try:
                s_date = datetime.strptime(s.get("date", ""), "%Y-%m-%d").date()
                if start_of_week <= s_date <= end_of_week:
                    weekly_schedules.append(s)
            except Exception:
                pass

        weekly_companies = set(s.get("company", "").strip() for s in weekly_schedules if s.get("company"))
        upcoming_schedules = [s for s in schedules if s.get("status") == "scheduled"]

        return {
            "total_attended": len(completed_schedules),
            "total_companies": len(companies_map),
            "weekly_interviews": len(weekly_schedules),
            "weekly_companies": len(weekly_companies),
            "upcoming_count": len(upcoming_schedules),
            "total_questions": len(questions),
            "categories": CATEGORIES,
            # Detailed objects for interactive card click modals
            "today_list": today_schedules,
            "attended_list": completed_schedules,
            "companies_list": [{"company": k, "rounds": v} for k, v in companies_map.items()],
            "weekly_list": weekly_schedules,
            "upcoming_list": upcoming_schedules
        }

    # --- PENDING FOLLOW-UPS (SMART POST-INTERVIEW PROMPT) ---
    def get_pending_followups(self) -> List[Dict[str, Any]]:
        schedules = self._read_json(self.schedules_file)
        now = datetime.now()
        pending = []

        for s in schedules:
            if s.get("questions_uploaded"):
                continue
            if s.get("status") in ["cancelled", "dismissed"]:
                continue

            try:
                s_time = s.get("end_time") or s.get("start_time") or s.get("time", "00:00")
                s_datetime_str = f"{s.get('date')} {s_time}"
                s_dt = datetime.strptime(s_datetime_str, "%Y-%m-%d %H:%M")
                if s_dt <= now:
                    pending.append(s)
            except Exception:
                pass

        return pending

interview_manager = InterviewManager()
