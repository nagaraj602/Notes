"""
Old IQ Questions Manager - Parses and manages interview questions from 'Interview Questions' folder.
Supports both container deployment (/app/data/notes/devops-notes/Interview Questions)
and local development environments.
Zero interference with 'Nagaraj_interviews'.
"""

import os
import re
from typing import List, Dict, Any, Optional

CATEGORIES_LIST = [
    "Linux", "Shell script", "CI/CD", "Jenkins", "Git / GitHub", "Docker",
    "Kubernetes", "AWS / Cloud", "Terraform / IaC", "Ansible", "Networking",
    "Security", "Monitoring", "System Design", "Behavioral", "General"
]

CATEGORY_NORMALIZE_MAP = {
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "jenkins": "Jenkins",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "linux": "Linux",
    "shell script": "Shell script",
    "shell": "Shell script",
    "bash": "Shell script",
    "cloud": "AWS / Cloud",
    "aws": "AWS / Cloud",
    "iac": "Terraform / IaC",
    "terraform": "Terraform / IaC",
    "security": "Security",
    "networking": "Networking",
    "monitoring": "Monitoring",
    "system design": "System Design",
    "behavioral": "Behavioral",
    "git": "Git / GitHub",
    "github": "Git / GitHub",
    "ansible": "Ansible",
    "build tools": "Build Tools",
    "other": "General"
}

def normalize_category(cat: str) -> str:
    if not cat:
        return "General"
    cleaned = cat.strip().lower()
    return CATEGORY_NORMALIZE_MAP.get(cleaned, cat.strip())

def detect_category_from_text(text: str) -> str:
    tl = text.lower()
    if any(w in tl for w in ["k8s", "kubernetes", "pod", "pods", "ingress", "clusterip", "nodeport", "hpa", "daemonset", "statefulset", "kubelet", "kubectl"]):
        return "Kubernetes"
    if any(w in tl for w in ["jenkins", "jenkinsfile", "pipeline", "ci/cd", "ci pipeline", "sonarqube", "quality gate"]):
        return "Jenkins"
    if any(w in tl for w in ["docker", "dockerfile", "container", "containers", "image", "multistage", "entrypoint", "cmd"]):
        return "Docker"
    if any(w in tl for w in ["terraform", "tfstate", "iac", "hcl", "state lock"]):
        return "Terraform / IaC"
    if any(w in tl for w in ["aws", "ec2", "s3", "vpc", "nacl", "security group", "route 53", "route53", "dynamodb", "cloudwatch", "iam", "eks", "fargate", "ecs"]):
        return "AWS / Cloud"
    if any(w in tl for w in ["ansible", "playbook", "inventory"]):
        return "Ansible"
    if any(w in tl for w in ["linux", "bash", "shell", "script", "grep", "awk", "sed", "systemd", "cpu 100", "top", "htop"]):
        return "Linux"
    if any(w in tl for w in ["git", "github", "gitlab", "branch", "merge", "pull request", "rebase"]):
        return "Git / GitHub"
    if any(w in tl for w in ["database", "rds", "postgres", "mysql", "mongodb"]):
        return "AWS / Cloud"
    if any(w in tl for w in ["prometheus", "grafana", "monitoring", "alert", "datadog", "pagerduty"]):
        return "Monitoring"
    if any(w in tl for w in ["team size", "developer", "hire you", "mistake", "conflict", "behavioral", "candidate introduction", "introduce yourself"]):
        return "Behavioral"
    return "General"

def get_fallback_answer_for_question(q_text: str, c_name: str, r_name: str) -> str:
    ql = q_text.lower()
    if any(w in ql for w in ["introduce yourself", "brief introduction", "walk me through", "tell me about yourself"]):
        return (
            "\"I am a DevOps Engineer with 5 years of practical IT experience, primarily focusing on CI/CD automation, "
            "AWS cloud infrastructure, and containerized deployments with Docker and Kubernetes.\n\n"
            "### 1. Core Technical Skills\n"
            "- **CI/CD & Source Control:** Jenkins (Declarative Pipelines), Git/GitHub (branching strategies, merge conflict resolution), Maven build tool, SonarQube code quality gates.\n"
            "- **Cloud & Networking (AWS):** VPC (public and private subnets, Internet Gateway, NAT Gateway, Route Tables), EC2, Auto Scaling Groups, Application Load Balancer (ALB), S3, IAM, and CloudWatch.\n"
            "- **Containers & Orchestration:** Docker (writing Dockerfiles, multi-stage builds, image optimization), AWS ECR, and Kubernetes (Deployments, Services, ConfigMaps, Secrets, Ingress, and HPA).\n"
            "- **Infrastructure as Code (IaC) & Automation:** Terraform (modular code, remote S3 state backend with DynamoDB locking), Ansible playbooks, and Shell/Bash scripting for routine OS tasks.\n\n"
            "### 2. Day-to-Day Responsibilities\n"
            "- Managing and troubleshooting CI/CD build and deployment pipelines in Jenkins.\n"
            "- Provisioning and updating AWS infrastructure resources using Terraform modules.\n"
            "- Containerizing applications and managing Kubernetes workloads across DEV, QA, UAT, and PROD.\n"
            "- Resolving Jira tickets related to build failures, deployments, Git merges, and infrastructure monitoring.\""
        )
    if "role" in ql and ("responsibility" in ql or "responsibilities" in ql):
        return (
            "\"In my current role as a DevOps Engineer, my primary responsibilities include:\n\n"
            "1. **CI/CD Pipeline Management:** Creating and maintaining declarative Jenkins pipelines for our microservices, automating build, test, SonarQube scans, Docker packaging, and deployment.\n"
            "2. **Cloud Infrastructure (IaC):** Writing and maintaining Terraform configurations to provision AWS resources like VPCs, subnets, EC2 instances, and security groups with S3 and DynamoDB remote state locking.\n"
            "3. **Containerization & Deployment:** Building Docker images using multi-stage builds, pushing to Amazon ECR, and deploying applications onto Kubernetes clusters.\n"
            "4. **Configuration & Scripting:** Writing Bash scripts and Ansible playbooks for system configuration, log rotation, and server maintenance.\n"
            "5. **Production Support & Troubleshooting:** Monitoring application and infrastructure health using CloudWatch, debugging deployment failures, and working closely with development and QA teams.\""
        )
    if any(w in ql for w in ["years of", "total experience", "relevant experience"]):
        return (
            "\"I have 5 years of professional IT experience, with hands-on work across DevOps practices, AWS cloud infrastructure, "
            "CI/CD pipeline automation (Jenkins), Docker containerization, Kubernetes, and Terraform Infrastructure as Code.\""
        )
    if any(w in ql for w in ["domain", "fintech", "e-commerce", "banking", "retail", "healthcare"]):
        return (
            "\"In my projects, I have supported high-availability web applications:\n\n"
            "- **Security & Isolation:** Applications run inside private subnets behind an Application Load Balancer. Database and backend services are never directly exposed to the public internet.\n"
            "- **High Availability & Scalability:** EC2 Auto Scaling Groups and Kubernetes Horizontal Pod Autoscaling (HPA) automatically scale workloads based on CPU and memory metrics.\n"
            "- **Environment Flow:** Strict environment separation across DEV, QA, UAT, and PROD, with automated deployments to lower environments and approval gates for production releases.\""
        )
    if "contribution" in ql or "specific contribution" in ql:
        return (
            "\"My key contributions in the project include:\n\n"
            "1. **End-to-End Pipeline Setup:** Built declarative Jenkins pipelines that automated the build, test, SonarQube quality analysis, and Docker image deployment to Amazon ECR.\n"
            "2. **Docker Image Optimization:** Implemented multi-stage Docker builds for our services, reducing image sizes from ~700MB down to under 150MB, speeding up deployments significantly.\n"
            "3. **Terraform Infrastructure Automation:** Codified manual AWS configurations into reusable Terraform modules with S3 remote state and DynamoDB locking to prevent state conflicts.\n"
            "4. **Deployment Reliability:** Implemented Kubernetes rolling updates with readiness and liveness probes to achieve zero downtime during application releases.\""
        )
    if any(w in ql for w in ["job description", "role requires", "looking for", "understand this role"]):
        return (
            "\"Based on the job description, this role requires a hands-on DevOps Engineer who can independently manage CI/CD pipelines, "
            "maintain cloud infrastructure on AWS, support Docker and Kubernetes container workloads, and collaborate closely with developers "
            "to ensure smooth, automated, and reliable software releases.\""
        )
    if any(w in ql for w in ["notice period", "working day", "offer in hand", "last working day"]):
        return (
            "\"My official notice period is 30 days (negotiable based on company requirements). I am actively interviewing for DevOps Engineer roles.\""
        )
    if any(w in ql for w in ["relocate", "location", "in person", "travel"]):
        return (
            "\"I am open and flexible to relocate or work in hybrid/on-site setups based on the company's requirements.\""
        )
    return (
        f"\"In {c_name} ({r_name}), the interviewer is looking for practical hands-on understanding. "
        "In production, I ensure reliability by following infrastructure best practices, verifying changes in DEV/QA before PROD, "
        "and automating repetitive tasks through CI/CD and scripts.\""
    )

def total_q_count_helper(companies_map: Dict[str, Any]) -> int:
    return sum(c.get("total_questions", 0) for c in companies_map.values())

class OldIQManager:
    def __init__(self, notes_dir: Optional[str] = None):
        self.custom_notes_dir = notes_dir
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cached_mtime: float = 0

    def get_interview_questions_dir(self) -> str:
        """Locates the 'Interview Questions' folder across Docker, K8s, and local dev."""
        if self.custom_notes_dir and os.path.exists(self.custom_notes_dir):
            p = os.path.join(self.custom_notes_dir, "Interview Questions")
            if os.path.exists(p):
                return p

        # 1. Container mount path inside Docker/K3s
        container_path = "/app/data/notes/devops-notes/Interview Questions"
        if os.path.exists(container_path) and os.path.isdir(container_path):
            return container_path

        # 2. Local development: look upwards from current file directory
        cur = os.path.abspath(os.path.dirname(__file__))
        for _ in range(6):
            candidate = os.path.join(cur, "Interview Questions")
            if os.path.exists(candidate) and os.path.isdir(candidate):
                return candidate
            candidate_notes = os.path.join(cur, "devops-notes", "Interview Questions")
            if os.path.exists(candidate_notes) and os.path.isdir(candidate_notes):
                return candidate_notes
            cur = os.path.dirname(cur)

        return ""

    def _get_dir_mtime(self, directory: str) -> float:
        if not os.path.exists(directory):
            return 0
        latest = os.path.getmtime(directory)
        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith(".md"):
                    try:
                        m = os.path.getmtime(os.path.join(root, f))
                        if m > latest:
                            latest = m
                    except Exception:
                        pass
        return latest

    def get_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Loads and parses all interview questions from the 'Interview Questions' folder."""
        iq_dir = self.get_interview_questions_dir()
        if not iq_dir or not os.path.exists(iq_dir):
            return {
                "companies": [],
                "stats": {"total_companies": 0, "total_rounds": 0, "total_questions": 0, "categories": {}},
                "all_categories": []
            }

        mtime = self._get_dir_mtime(iq_dir)
        if not force_refresh and self._cached_data is not None and self._cached_mtime == mtime:
            return self._cached_data

        parsed = self._parse_all_files(iq_dir)
        self._cached_data = parsed
        self._cached_mtime = mtime
        return parsed

    def _parse_all_files(self, directory: str) -> Dict[str, Any]:
        companies_map: Dict[str, Dict[str, Any]] = {}
        category_counts: Dict[str, int] = {}

        # Discover all markdown files
        md_files = []
        for item in sorted(os.listdir(directory)):
            if item.endswith(".md"):
                md_files.append((item, os.path.join(directory, item)))

        for fname, fpath in md_files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
            except Exception:
                continue

            if "2. 9-Sep-2026" in fname or "1. 23-Aug-2026" in fname:
                self._parse_company_interview_file(fname, content, companies_map, category_counts)
            elif "0. Basic" in fname or "0_1. General" in fname:
                self._parse_general_guide_file(fname, content, companies_map, category_counts)

        # Convert rounds to sorted lists for each company
        for c in companies_map.values():
            c["categories"] = sorted(list(c["categories"]))
            if isinstance(c["rounds"], dict):
                r_list = []
                for r_name, r_data in c["rounds"].items():
                    r_data["categories"] = sorted(list(r_data["categories"]))
                    r_list.append(r_data)
                c["rounds"] = r_list

        companies_list = list(companies_map.values())
        companies_list.sort(key=lambda c: c["company_name"].lower())

        total_rounds = sum(len(c["rounds"]) for c in companies_list)
        total_questions = sum(c["total_questions"] for c in companies_list)

        return {
            "companies": companies_list,
            "stats": {
                "total_companies": len(companies_list),
                "total_rounds": total_rounds,
                "total_questions": total_questions,
                "categories": category_counts
            },
            "all_categories": sorted(list(category_counts.keys()))
        }

    def _parse_company_interview_file(self, fname: str, content: str, companies_map: Dict[str, Any], category_counts: Dict[str, int]):
        lines = content.splitlines()
        
        current_company_name = ""
        current_round_name = "Round 1"
        current_category = "General"
        current_q_text = ""
        current_answer_lines = []
        in_answer = False
        is_sub_q = False
        
        def push_question():
            nonlocal current_q_text, current_answer_lines, in_answer, is_sub_q, current_category
            if not current_q_text:
                return
            
            # Clean question display text (remove trailing asterisks and bullet symbols)
            q_clean = re.sub(r'^\*+\s*(.*?)\s*\*+:', r'\1:', current_q_text.strip())
            q_clean = re.sub(r'^\*+|\*+$', '', q_clean).strip()
            q_clean = re.sub(r'^[●↳\s]+', '', q_clean).strip()
            q_clean = q_clean.replace('**', '').strip()
            if not q_clean:
                q_clean = current_q_text.strip()

            ans_clean = "\n".join(current_answer_lines).strip()
            ans_clean = re.sub(r'^(?:\*{0,2}Answer:\*{0,2}\s*)', '', ans_clean).strip()
            
            c_name = current_company_name or "General Company Interviews"
            r_name = current_round_name or "Technical Round"

            # If question has no answer or < 15 chars, supply structured, production-grade DevOps answer
            if not ans_clean or len(ans_clean) < 15:
                ans_clean = get_fallback_answer_for_question(q_clean, c_name, r_name)

            norm_cat = normalize_category(current_category)
            if norm_cat == "General":
                detected = detect_category_from_text(q_clean + " " + ans_clean)
                if detected != "General":
                    norm_cat = detected

            category_counts[norm_cat] = category_counts.get(norm_cat, 0) + 1
            
            if c_name not in companies_map:
                companies_map[c_name] = {
                    "company_name": c_name,
                    "rounds": {},
                    "total_questions": 0,
                    "categories": set()
                }
            
            if r_name not in companies_map[c_name]["rounds"]:
                companies_map[c_name]["rounds"][r_name] = {
                    "round_name": r_name,
                    "questions": [],
                    "categories": set()
                }
                
            q_entry = {
                "id": f"q_{len(category_counts)}_{total_q_count_helper(companies_map)}",
                "question": q_clean,
                "answer": ans_clean,
                "has_answer": bool(ans_clean),
                "is_sub_q": is_sub_q,
                "category": norm_cat,
                "source_file": fname
            }
            
            companies_map[c_name]["rounds"][r_name]["questions"].append(q_entry)
            companies_map[c_name]["rounds"][r_name]["categories"].add(norm_cat)
            companies_map[c_name]["categories"].add(norm_cat)
            companies_map[c_name]["total_questions"] += 1
            
            current_q_text = ""
            current_answer_lines = []
            in_answer = False
            is_sub_q = False

        for line in lines:
            line_str = line.strip()
            if not line_str:
                if in_answer:
                    current_answer_lines.append(line)
                continue

            # Detect company header in details summary: <summary><h2>🏢 Company</h2></summary>
            m_comp_details = re.search(r'<summary>\s*(?:<h2>)?\s*(?:!\[.*?\]\(.*?\))?\s*(?:🏢)?\s*([A-Za-z0-9\s\.\-_/&]+?)(?:</h2>)?\s*</summary>', line_str, re.IGNORECASE)
            if m_comp_details and not re.search(r'<summary>\s*<strong>', line_str):
                push_question()
                raw_c = m_comp_details.group(1).strip()
                if " - " in raw_c or r"\-" in raw_c:
                    parts = re.split(r'\s*(?:\\-|-|–)\s*', raw_c)
                    current_company_name = parts[0].strip()
                    if len(parts) > 1:
                        current_round_name = parts[1].strip()
                else:
                    current_company_name = raw_c
                continue

            # Detect round header in details summary: <summary><h3>Round</h3></summary>
            m_round_details = re.search(r'<summary>\s*(?:<h3>)?\s*([A-Za-z0-9\s\.\-_/&]+?)(?:</h3>)?\s*</summary>', line_str, re.IGNORECASE)
            if m_round_details and not re.search(r'<summary>\s*<strong>', line_str) and not m_comp_details:
                push_question()
                current_round_name = m_round_details.group(1).strip()
                continue

            # Detect markdown company header: * ![🏢]() **Azentio \- HackerRank Assessment**
            # or ## Persistant – L1
            if ("🏢" in line_str and "**" in line_str) or re.match(r'^##\s+[A-Za-z0-9]', line_str):
                push_question()
                clean = line_str.replace("![🏢]()", "").replace("🏢", "").replace("*", "").replace("#", "").strip()
                clean = clean.replace(r"\-", "-").replace("–", "-")
                parts = [p.strip() for p in clean.split("-") if p.strip()]
                if parts:
                    current_company_name = parts[0]
                    current_round_name = " - ".join(parts[1:]) if len(parts) > 1 else "Level 1"
                continue

            # Detect Category Header: #### 【 CI/CD 】 or * **【 CI/CD 】** or 【 CI/CD 】
            m_cat = re.search(r'【\s*(.+?)\s*】', line_str)
            if m_cat:
                push_question()
                current_category = m_cat.group(1).strip()
                continue

            # Detect Question inside <summary><strong>Question</strong></summary>
            m_q_summary = re.search(r'<summary>\s*<strong>\s*(.+?)\s*</strong>\s*</summary>', line_str, re.IGNORECASE)
            if m_q_summary:
                push_question()
                raw_q = m_q_summary.group(1).strip()
                if raw_q.startswith("↳"):
                    is_sub_q = True
                    raw_q = re.sub(r'^↳\s*(?:Follow-up:\s*)?', '', raw_q).strip()
                elif raw_q.startswith("●"):
                    is_sub_q = False
                    raw_q = re.sub(r'^●\s*', '', raw_q).strip()
                current_q_text = raw_q
                in_answer = True
                continue

            # Detect closing tag </details>
            if line_str.startswith("</details>"):
                if in_answer:
                    push_question()
                continue

            # Detect bullet question line: ● Question text or ↳ Follow-up
            if line_str.startswith("●") or line_str.startswith("↳"):
                push_question()
                is_sub = line_str.startswith("↳")
                q_text = line_str[1:].strip()
                q_text = re.sub(r'^\*+|\*+$', '', q_text).strip()
                current_q_text = q_text
                is_sub_q = is_sub
                in_answer = True
                continue

            if in_answer:
                current_answer_lines.append(line)

        push_question()

    def _parse_general_guide_file(self, fname: str, content: str, companies_map: Dict[str, Any], category_counts: Dict[str, int]):
        lines = content.splitlines()
        comp_name = "DevOps Core Fundamentals" if "0. Basic" in fname else "Production Scenarios & Strategic Recovery"
        current_round = "General Architecture & Behavioral"
        current_cat = "General"
        
        current_q_text = ""
        current_answer_lines = []
        in_answer = False
        
        def push_q():
            nonlocal current_q_text, current_answer_lines, in_answer, current_cat
            if not current_q_text:
                return
            ans_clean = "\n".join(current_answer_lines).strip()
            ans_clean = re.sub(r'^(?:\*{0,2}Answer:\*{0,2}\s*)', '', ans_clean).strip()
            
            # Clean question title
            q_clean = re.sub(r'^\*+|\*+$', '', current_q_text.strip()).strip()
            if not ans_clean or len(ans_clean) < 15:
                ans_clean = get_fallback_answer_for_question(q_clean, comp_name, current_round)

            norm_cat = detect_category_from_text(q_clean + " " + ans_clean)
            category_counts[norm_cat] = category_counts.get(norm_cat, 0) + 1
            
            q_entry = {
                "id": f"gen_{len(category_counts)}_{total_q_count_helper(companies_map)}",
                "question": q_clean,
                "answer": ans_clean,
                "has_answer": bool(ans_clean),
                "is_sub_q": False,
                "category": norm_cat,
                "source_file": fname
            }
            
            if comp_name not in companies_map:
                companies_map[comp_name] = {
                    "company_name": comp_name,
                    "rounds": {},
                    "total_questions": 0,
                    "categories": set()
                }
            if current_round not in companies_map[comp_name]["rounds"]:
                companies_map[comp_name]["rounds"][current_round] = {
                    "round_name": current_round,
                    "questions": [],
                    "categories": set()
                }
            companies_map[comp_name]["rounds"][current_round]["questions"].append(q_entry)
            companies_map[comp_name]["rounds"][current_round]["categories"].add(norm_cat)
            companies_map[comp_name]["categories"].add(norm_cat)
            companies_map[comp_name]["total_questions"] += 1
            
            current_q_text = ""
            current_answer_lines = []
            in_answer = False

        for line in lines:
            line_str = line.strip()
            if not line_str:
                if in_answer:
                    current_answer_lines.append(line)
                continue

            if line_str.startswith("## "):
                push_q()
                current_round = line_str[3:].strip()
                continue

            m_sum = re.search(r'<summary>\s*<strong>\s*(.+?)\s*</strong>\s*</summary>', line_str, re.IGNORECASE)
            if m_sum:
                push_q()
                raw_q = m_sum.group(1).strip()
                raw_q = re.sub(r'^\d+[\.\)]\s*', '', raw_q)
                current_q_text = raw_q
                in_answer = True
                continue

            if line_str.startswith("</details>"):
                if in_answer:
                    push_q()
                continue

            if in_answer:
                current_answer_lines.append(line)

        push_q()

old_iq_manager = OldIQManager()
