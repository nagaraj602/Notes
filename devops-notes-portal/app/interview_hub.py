"""
Interview Hub Manager - Schedules, Calendar, Q&A Repository, and Follow-ups
Stores persistent interview schedules and Q&A in the 'Nagaraj_interviews' folder.
Zero dummy data: Starts completely clean and records only real user interviews.
"""
import os
import json
import uuid
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

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

def detect_categories(text: str) -> List[str]:
    """Auto-detects relevant categories based on question and answer keywords."""
    detected = []
    text_lower = text.lower()
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if cat not in detected:
                    detected.append(cat)
                break
    return detected

def parse_interview_qa_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Intelligently parses bulk interview text into structured Question & Answer items.
    Handles headings, 'Question N:', sub-questions, 'Instructor's Answer/Suggestion:', etc.
    """
    lines = raw_text.strip().split("\n")
    items = []
    current_topic = ""
    current_q = None
    current_subquestions = []
    current_answers = []
    current_actions = []
    mode = "none" # "q", "subq", "ans", "action"

    def flush_current():
        nonlocal current_q, current_subquestions, current_answers, current_actions, current_topic, mode
        if current_q:
            # Build answer markdown
            ans_parts = []
            if current_subquestions:
                sub_md = "**Follow-up / Sub-questions:**\n" + "\n".join([f"- {sq}" for sq in current_subquestions])
                ans_parts.append(sub_md)
            if current_answers:
                ans_parts.append("**Answer / Instructor Suggestion:**\n" + "\n".join(current_answers))
            if current_actions:
                ans_parts.append("**Action Items / Takeaways:**\n" + "\n".join(current_actions))
            
            final_answer = "\n\n".join(ans_parts).strip() if ans_parts else "To be reviewed / prepared."
            
            # Auto detect categories from topic + question + subquestions + answer
            full_text = f"{current_topic} {current_q} {' '.join(current_subquestions)} {final_answer}"
            cats = detect_categories(full_text)
            
            items.append({
                "question": current_q,
                "answer": final_answer,
                "categories": cats
            })
            current_q = None
            current_subquestions = []
            current_answers = []
            current_actions = []
            mode = "none"

    q_pattern = re.compile(r'^(?:Question\s*\d+|Q\d+|Q|\d+)\s*[:\.\-]\s*(.*)$', re.IGNORECASE)
    sub_pattern = re.compile(r'^(?:Sub-question|Sub\s*Question|Follow-up|Follow\s*up)\s*[:\.\-]\s*(.*)$', re.IGNORECASE)
    ans_pattern = re.compile(r'^(?:Instructor[’\']?s?\s*Answer(?:/Suggestion)?|Instructor[’\']?s?\s*Suggestion|Instructor[’\']?s?\s*Answer|Answer|Ans|A)\s*[:\.\-]?\s*(.*)$', re.IGNORECASE)
    action_pattern = re.compile(r'^(?:Action\s*Item|Takeaway|Assignment|Instructor[’\']?s?\s*Final\s*Assignment.*)\s*[:\.\-]?\s*(.*)$', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        q_match = q_pattern.match(stripped)
        sub_match = sub_pattern.match(stripped)
        ans_match = ans_pattern.match(stripped)
        action_match = action_pattern.match(stripped)

        # Check if line is a domain section header (e.g. "Kubernetes Troubleshooting", "Docker Images & Security")
        is_section_header = (
            not stripped.startswith('"') 
            and not stripped.startswith("'") 
            and not stripped.startswith("-") 
            and not stripped.startswith("*")
            and not re.match(r'^\d+\.', stripped)
            and not (q_match or sub_match or ans_match or action_match)
            and any(k.lower() in stripped.lower() for k in ["kubernetes", "docker", "aws", "jenkins", "ci/cd", "helm", "monitoring", "environments", "linux", "terraform", "ansible", "security", "infrastructure"])
            and len(stripped.split()) <= 8
        )

        if q_match:
            flush_current()
            q_text = q_match.group(1).strip().strip('"').strip("'").strip()
            current_q = q_text
            mode = "q"
        elif is_section_header:
            flush_current()
            current_topic = stripped
        elif sub_match and current_q:
            sq_text = sub_match.group(1).strip().strip('"').strip("'").strip()
            current_subquestions.append(sq_text)
            mode = "subq"
        elif ans_match and current_q:
            mode = "ans"
            a_text = ans_match.group(1).strip()
            if a_text:
                current_answers.append(a_text)
        elif action_match and current_q:
            mode = "action"
            act_text = action_match.group(1).strip()
            if act_text:
                current_actions.append(act_text)
        else:
            if not current_q:
                current_topic = stripped
            elif mode == "action":
                current_actions.append(stripped)
            elif mode == "ans":
                current_answers.append(stripped)
            elif mode == "subq":
                current_subquestions.append(stripped)
            elif mode == "q":
                current_q += " " + stripped

    flush_current()
    return items

class InterviewManager:
    def __init__(self):
        self.storage_dir = self._resolve_storage_dir()
        os.makedirs(self.storage_dir, exist_ok=True)
        self.schedules_file = os.path.join(self.storage_dir, "schedules.json")
        self.questions_file = os.path.join(self.storage_dir, "questions.json")
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
            self._auto_git_sync(commit_msg)
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")

    def _auto_git_sync(self, commit_msg: str = "Update Nagaraj interviews tracker"):
        try:
            repo_dir = os.path.dirname(self.storage_dir)
            if not os.path.exists(os.path.join(repo_dir, ".git")):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                if os.path.exists(os.path.join(base_dir, ".git")):
                    repo_dir = base_dir
                else:
                    return

            import git
            repo = git.Repo(repo_dir)
            repo.git.add("Nagaraj_interviews")
            if repo.is_dirty(untracked_files=True):
                repo.index.commit(commit_msg)
                try:
                    origin = repo.remotes.origin
                    origin.push()
                except Exception:
                    pass
        except Exception:
            pass

    # --- SCHEDULES API ---
    def get_schedules(self) -> List[Dict[str, Any]]:
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
            
        new_q = {
            "id": f"q-{uuid.uuid4().hex[:8]}",
            "company": data.get("company", "").strip(),
            "round": data.get("round", "").strip(),
            "date": data.get("date", date.today().isoformat()),
            "question": data.get("question", "").strip(),
            "answer": data.get("answer", "").strip(),
            "categories": cats,
            "created_at": datetime.utcnow().isoformat()
        }
        questions.append(new_q)
        self._save_json(self.questions_file, questions)

        # Mark corresponding schedule as completed & uploaded
        schedules = self._read_json(self.schedules_file)
        for s in schedules:
            if s.get("company", "").lower() == new_q["company"].lower():
                s["questions_uploaded"] = True
                s["status"] = "completed"
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
        for item in qa_items:
            q_text = item.get("question", "").strip()
            if not q_text:
                continue
            
            cats = item.get("categories", [])
            if not cats:
                cats = detect_categories(q_text + " " + item.get("answer", ""))

            new_q = {
                "id": f"q-{uuid.uuid4().hex[:8]}",
                "company": company.strip(),
                "round": round_name.strip(),
                "date": interview_date.strip() or date.today().isoformat(),
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

        self._save_json(self.questions_file, questions, f"Add {added_count} interview questions for {company}")

        # Update schedule status and attach experience & notes
        schedules = self._read_json(self.schedules_file)
        for s in schedules:
            if s.get("company", "").lower() == company.lower() and (not round_name or s.get("round", "").lower() == round_name.lower() or not s.get("questions_uploaded")):
                s["questions_uploaded"] = True
                s["status"] = "completed"
                if experience:
                    s["experience"] = experience.strip()
                if notes:
                    s["notes"] = notes.strip()
                if difficulty:
                    s["difficulty"] = difficulty.strip()
        self._save_json(self.schedules_file, schedules, f"Mark interview schedule completed for {company}")

        return added_count

    # --- STATISTICS & DETAILED LISTS FOR POPUPS ---
    def get_stats(self) -> Dict[str, Any]:
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
        
        # Unique companies map
        companies_map = {}
        for s in completed_schedules:
            comp = s.get("company", "").strip()
            if comp:
                if comp not in companies_map:
                    companies_map[comp] = []
                companies_map[comp].append(s)

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
