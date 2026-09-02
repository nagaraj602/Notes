"""
Interview Hub Manager - Schedules, Calendar, Q&A Repository, and Follow-ups
Stores persistent interview schedules and Q&A in the 'Nagaraj_interviews' folder.
"""
import os
import json
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

CATEGORIES = [
    "Linux", "Shell script", "jenkins", "Github", "Build tools",
    "Docker", "AWS", "Kubernetes", "terraform", "Ansible",
    "jira", "scrum", "Agile", "Monitoring tools", "python",
    "Azure", "AI tool"
]

class InterviewManager:
    def __init__(self):
        self.storage_dir = self._resolve_storage_dir()
        os.makedirs(self.storage_dir, exist_ok=True)
        self.schedules_file = os.path.join(self.storage_dir, "schedules.json")
        self.questions_file = os.path.join(self.storage_dir, "questions.json")
        self._init_files()

    def _resolve_storage_dir(self) -> str:
        # Check container path
        container_path = "/app/data/notes/devops-notes/Nagaraj_interviews"
        if os.path.exists(os.path.dirname(container_path)):
            return container_path
        
        # Check local notes repo path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        notes_path = os.path.join(base_dir, "Nagaraj_interviews")
        if os.path.exists(notes_path):
            return notes_path
        
        # Fallback within app directory
        app_local = os.path.join(os.path.dirname(__file__), "data", "Nagaraj_interviews")
        return app_local

    def _init_files(self):
        if not os.path.exists(self.schedules_file):
            # Seed initial sample past and upcoming interview schedules
            initial_schedules = [
                {
                    "id": "sched-sample-1",
                    "company": "Persistant Systems",
                    "role": "Senior DevOps Engineer",
                    "round": "L1 Technical Discussion",
                    "date": "2026-08-23",
                    "time": "11:00",
                    "status": "completed",
                    "meeting_link": "https://teams.microsoft.com",
                    "notes": "Asked in-depth questions on AWS VPC Endpoints, Kubernetes Ingress, Terraform import, and Docker multi-stage builds.",
                    "questions_uploaded": True,
                    "created_at": "2026-08-20T10:00:00Z"
                },
                {
                    "id": "sched-sample-2",
                    "company": "Altemrik",
                    "role": "DevOps / SRE Specialist",
                    "round": "Technical Discussion 1",
                    "date": "2026-08-28",
                    "time": "14:30",
                    "status": "completed",
                    "meeting_link": "https://meet.google.com",
                    "notes": "Focused on Java/FastAPI microservices deployment on EKS, Jenkins Shared Libraries, and Inter-Region VPC Peering.",
                    "questions_uploaded": True,
                    "created_at": "2026-08-25T12:00:00Z"
                },
                {
                    "id": "sched-sample-3",
                    "company": "Cognizant / Tech Mahindra",
                    "role": "Lead Cloud DevOps Engineer",
                    "round": "Client Technical Round",
                    "date": (date.today() + timedelta(days=2)).isoformat(),
                    "time": "15:00",
                    "status": "scheduled",
                    "meeting_link": "https://zoom.us/j/1234567890",
                    "notes": "Focus on Kubernetes cluster migration, Terraform modules, and CI/CD zero-downtime deployments.",
                    "questions_uploaded": False,
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            self._save_json(self.schedules_file, initial_schedules)

        if not os.path.exists(self.questions_file):
            initial_questions = [
                {
                    "id": "q-sample-1",
                    "company": "Persistant Systems",
                    "round": "L1 Technical Discussion",
                    "date": "2026-08-23",
                    "question": "Difference between NACL and Security Group in AWS VPC?",
                    "answer": "**Security Group (SG):** Operates at the instance/ENI level, is **stateful** (return traffic is automatically allowed), and supports **allow rules only**.\n\n**Network ACL (NACL):** Operates at the subnet level as a firewall, is **stateless** (return traffic must be explicitly permitted), and supports both **allow and deny rules** evaluated in strict numerical order.",
                    "categories": ["AWS"],
                    "created_at": "2026-08-23T12:00:00Z"
                },
                {
                    "id": "q-sample-2",
                    "company": "Persistant Systems",
                    "round": "L1 Technical Discussion",
                    "date": "2026-08-23",
                    "question": "How do you patch an EC2 instance located in a private subnet without exposing it to the internet?",
                    "answer": "1. **Outbound Connectivity:** Deploy a **NAT Gateway** in a public subnet and route `0.0.0.0/0` to it, allowing outbound package updates (`yum update`).\n2. **AWS Systems Manager (SSM) Patch Manager:** Configure **VPC Endpoints (PrivateLink)** for SSM (`ssm`, `ssmmessages`, `ec2messages`) and attach `AmazonSSMManagedInstanceCore` IAM role. Patching runs automatically through scheduled maintenance baselines with zero public internet exposure.",
                    "categories": ["AWS", "Linux"],
                    "created_at": "2026-08-23T12:05:00Z"
                },
                {
                    "id": "q-sample-3",
                    "company": "Altemrik",
                    "round": "Technical Discussion 1",
                    "date": "2026-08-28",
                    "question": "How do you share reusable pipeline code across 100+ microservices in Jenkins?",
                    "answer": "Using **Jenkins Shared Libraries**:\n* Store standardized stages, build patterns, and notifications in a central Git repo.\n* Import into any microservice `Jenkinsfile` via `@Library('my-shared-library') _`.\n* Individual service pipelines only need ~10 lines of declarative config calling standard functions.",
                    "categories": ["jenkins", "Github"],
                    "created_at": "2026-08-28T16:00:00Z"
                },
                {
                    "id": "q-sample-4",
                    "company": "Altemrik",
                    "round": "Technical Discussion 1",
                    "date": "2026-08-28",
                    "question": "How do you establish interconnectivity between EC2 instances in us-east-1 (N. Virginia) and us-east-2 (Ohio)?",
                    "answer": "Using **AWS Inter-Region VPC Peering** (or AWS Transit Gateway with peering):\n* Create peering connection between the two VPCs and accept the handshake.\n* Update Route Tables in both subnets to target the peering connection (`pcx-xxxx`).\n* Update Security Groups to allow private inbound traffic on application ports from the remote CIDR.\n* All traffic travels privately on AWS's redundant global fiber backbone.",
                    "categories": ["AWS"],
                    "created_at": "2026-08-28T16:15:00Z"
                }
            ]
            self._save_json(self.questions_file, initial_questions)

    def _read_json(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_json(self, filepath: str, data: List[Dict[str, Any]]):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")

    # --- SCHEDULES API ---
    def get_schedules(self) -> List[Dict[str, Any]]:
        schedules = self._read_json(self.schedules_file)
        # Sort by date and time
        schedules.sort(key=lambda x: f"{x.get('date', '')} {x.get('time', '')}", reverse=True)
        return schedules

    def add_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        schedules = self._read_json(self.schedules_file)
        new_item = {
            "id": f"sched-{uuid.uuid4().hex[:8]}",
            "company": data.get("company", "").strip(),
            "role": data.get("role", "DevOps Engineer").strip(),
            "round": data.get("round", "Technical Round").strip(),
            "date": data.get("date", date.today().isoformat()),
            "time": data.get("time", "10:00"),
            "status": data.get("status", "scheduled"), # scheduled, completed, cancelled, rescheduled
            "meeting_link": data.get("meeting_link", "").strip(),
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
        new_q = {
            "id": f"q-{uuid.uuid4().hex[:8]}",
            "company": data.get("company", "").strip(),
            "round": data.get("round", "").strip(),
            "date": data.get("date", date.today().isoformat()),
            "question": data.get("question", "").strip(),
            "answer": data.get("answer", "").strip(),
            "categories": data.get("categories", []),
            "created_at": datetime.utcnow().isoformat()
        }
        questions.append(new_q)
        self._save_json(self.questions_file, questions)

        # Mark corresponding schedule as having questions uploaded if match exists
        schedules = self._read_json(self.schedules_file)
        for s in schedules:
            if s.get("company", "").lower() == new_q["company"].lower():
                s["questions_uploaded"] = True
                s["status"] = "completed"
        self._save_json(self.schedules_file, schedules)

        return new_q

    def add_bulk_questions(self, company: str, round_name: str, interview_date: str, qa_items: List[Dict[str, Any]]) -> int:
        questions = self._read_json(self.questions_file)
        added_count = 0
        for item in qa_items:
            q_text = item.get("question", "").strip()
            if not q_text:
                continue
            new_q = {
                "id": f"q-{uuid.uuid4().hex[:8]}",
                "company": company.strip(),
                "round": round_name.strip(),
                "date": interview_date.strip() or date.today().isoformat(),
                "question": q_text,
                "answer": item.get("answer", "").strip(),
                "categories": item.get("categories", []),
                "created_at": datetime.utcnow().isoformat()
            }
            questions.append(new_q)
            added_count += 1

        self._save_json(self.questions_file, questions)

        # Update schedule flag
        schedules = self._read_json(self.schedules_file)
        for s in schedules:
            if s.get("company", "").lower() == company.lower():
                s["questions_uploaded"] = True
                s["status"] = "completed"
        self._save_json(self.schedules_file, schedules)

        return added_count

    # --- STATISTICS & SUMMARY METRICS ---
    def get_stats(self) -> Dict[str, Any]:
        schedules = self._read_json(self.schedules_file)
        questions = self._read_json(self.questions_file)

        today = date.today()
        # Start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        completed_schedules = [s for s in schedules if s.get("status") == "completed"]
        all_companies = set(s.get("company", "").strip() for s in completed_schedules if s.get("company"))

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
            "total_companies": len(all_companies),
            "weekly_interviews": len(weekly_schedules),
            "weekly_companies": len(weekly_companies),
            "upcoming_count": len(upcoming_schedules),
            "total_questions": len(questions),
            "categories": CATEGORIES
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
                s_datetime_str = f"{s.get('date')} {s.get('time', '00:00')}"
                s_dt = datetime.strptime(s_datetime_str, "%Y-%m-%d %H:%M")
                if s_dt <= now:
                    pending.append(s)
            except Exception:
                pass

        return pending

interview_manager = InterviewManager()
