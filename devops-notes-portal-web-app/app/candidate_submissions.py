"""
Candidate Submissions Manager - Secret Instructor Dashboard Backend
Tracks interviews and questions submitted by candidates:
- Candidate / User Name
- Company Name
- Date and Time of the schedule
- Salary CTC & Monthly
- Round Name
- Recording Link (YouTube)
- Questions & Answers added by the user
STRICT PRIVACY: NEVER accepts, requires, or stores any PAT of candidates.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("CandidateSubmissions")

class CandidateSubmissionsManager:
    def __init__(self):
        self.file_path = self._resolve_file_path()
        self._init_file()

    def _resolve_file_path(self) -> str:
        hidden_filename = ".candidate_submissions.json"
        try:
            from app.config import NOTES_DIR
            if NOTES_DIR and os.path.exists(NOTES_DIR):
                dn = os.path.join(NOTES_DIR, "devops-notes")
                if os.path.exists(dn):
                    return os.path.join(dn, hidden_filename)
                return os.path.join(NOTES_DIR, hidden_filename)
        except Exception:
            pass

        container_path = f"/app/data/notes/devops-notes/{hidden_filename}"
        if os.path.exists(os.path.dirname(container_path)):
            return container_path

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        notes_path = os.path.join(base_dir, hidden_filename)
        if os.path.exists(base_dir):
            return notes_path

        app_local = os.path.join(os.path.dirname(__file__), "data", hidden_filename)
        os.makedirs(os.path.dirname(app_local), exist_ok=True)
        return app_local

    def _init_file(self):
        # Migrate old unhidden file if present
        try:
            old_unhidden = self.file_path.replace(".candidate_submissions.json", "candidate_submissions.json")
            if os.path.exists(old_unhidden) and not os.path.exists(self.file_path):
                with open(old_unhidden, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                self._save_json(old_data)
                os.remove(old_unhidden)
            elif os.path.exists(old_unhidden) and os.path.exists(self.file_path):
                os.remove(old_unhidden)
        except Exception:
            pass

        if not os.path.exists(self.file_path):
            self._save_json([])

    def _read_json(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.file_path):
                return []
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error reading candidate submissions: {e}")
            return []

    def _save_json(self, data: List[Dict[str, Any]]):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving candidate submissions: {e}")

    def add_submission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        submissions = self._read_json()

        cand_name = (data.get("candidate_name") or data.get("user_name") or "").strip()
        if not cand_name:
            cand_name = "Candidate"

        company = (data.get("company") or "").strip()
        if not company:
            raise ValueError("Company name is required")

        round_name = (data.get("round") or "Technical Round 1").strip()
        sched_date = (data.get("date") or datetime.utcnow().strftime("%Y-%m-%d")).strip()
        start_t = (data.get("start_time") or data.get("time") or "10:00").strip()
        end_t = (data.get("end_time") or "").strip()
        salary_ctc = (data.get("salary_ctc") or "").strip()
        monthly_sal = (data.get("monthly_salary") or "").strip()
        rec_link = (data.get("recording_link") or "").strip()
        exp = (data.get("experience") or "").strip()
        notes = (data.get("notes") or "").strip()
        transcript = (data.get("transcript") or "").strip()
        has_transcript = bool(transcript) or bool(data.get("has_transcript"))
        original_raw_text = (data.get("original_raw_text") or "").strip()
        source_type = (data.get("source_type") or ("youtube" if rec_link else "manual")).strip()

        raw_questions = data.get("questions") or []
        clean_questions = []
        for q in raw_questions:
            q_text = (q.get("question") or "").strip()
            if not q_text:
                continue
            sub_qs = q.get("sub_questions") or []
            if isinstance(sub_qs, str):
                sub_qs = [s.strip() for s in sub_qs.split("\n") if s.strip()]
            suggestions = (q.get("suggestions") or q.get("instructor_suggestions") or "").strip()
            clean_questions.append({
                "id": f"cq-{uuid.uuid4().hex[:8]}",
                "question": q_text,
                "sub_questions": sub_qs,
                "answer": (q.get("answer") or "").strip(),
                "suggestions": suggestions,
                "categories": q.get("categories") or ["General"],
                "difficulty": q.get("difficulty") or "Moderate",
                "recording_link": (q.get("recording_link") or rec_link or "").strip()
            })

        # Check if matching submission exists for this candidate, company, round, and date
        existing = next(
            (s for s in submissions if 
             (s.get("candidate_name", "").lower() == cand_name.lower()) and 
             (s.get("company", "").lower() == company.lower()) and 
             (s.get("round", "").lower() == round_name.lower()) and
             (s.get("date", "") == sched_date)), 
            None
        )

        if existing:
            if start_t:
                existing["start_time"] = start_t
                existing["time"] = start_t
            if end_t:
                existing["end_time"] = end_t
            if salary_ctc:
                existing["salary_ctc"] = salary_ctc
            if monthly_sal:
                existing["monthly_salary"] = monthly_sal
            if rec_link:
                existing["recording_link"] = rec_link
            if notes:
                existing["notes"] = notes
            if exp:
                existing["experience"] = exp
            if transcript:
                existing["transcript"] = transcript
                existing["has_transcript"] = True
            if original_raw_text:
                existing["original_raw_text"] = original_raw_text
            if source_type:
                existing["source_type"] = source_type

            existing_q_texts = {q.get("question", "").lower().strip() for q in existing.get("questions", [])}
            for q in clean_questions:
                if q.get("question", "").lower().strip() not in existing_q_texts:
                    existing.setdefault("questions", []).append(q)
                    existing_q_texts.add(q.get("question", "").lower().strip())

            existing["question_count"] = len(existing.get("questions", []))
            existing["updated_at"] = datetime.utcnow().isoformat()
            self._save_json(submissions)
            return existing

        new_submission = {
            "id": f"sub-{uuid.uuid4().hex[:8]}",
            "candidate_name": cand_name,
            "company": company,
            "round": round_name,
            "date": sched_date,
            "time": start_t,
            "start_time": start_t,
            "end_time": end_t,
            "salary_ctc": salary_ctc,
            "monthly_salary": monthly_sal,
            "recording_link": rec_link,
            "experience": exp,
            "notes": notes,
            "transcript": transcript,
            "has_transcript": has_transcript,
            "original_raw_text": original_raw_text,
            "source_type": source_type,
            "questions": clean_questions,
            "question_count": len(clean_questions),
            "created_at": datetime.utcnow().isoformat(),
            "status": "new"
        }

        submissions.insert(0, new_submission)
        self._save_json(submissions)
        return new_submission

    def get_submissions(self, candidate: str = "", company: str = "", q: str = "") -> List[Dict[str, Any]]:
        submissions = self._read_json()
        filtered = submissions

        if candidate and candidate != "All":
            c_low = candidate.lower().strip()
            filtered = [s for s in filtered if (s.get("candidate_name") or "").lower().strip() == c_low]

        if company and company != "All":
            comp_low = company.lower().strip()
            filtered = [s for s in filtered if (s.get("company") or "").lower().strip() == comp_low]

        if q:
            q_low = q.lower().strip()
            def matches(s):
                if q_low in (s.get("candidate_name") or "").lower():
                    return True
                if q_low in (s.get("company") or "").lower():
                    return True
                if q_low in (s.get("round") or "").lower():
                    return True
                for question in s.get("questions", []):
                    if q_low in (question.get("question") or "").lower():
                        return True
                    if q_low in (question.get("answer") or "").lower():
                        return True
                return False
            filtered = [s for s in filtered if matches(s)]

        return filtered

    def delete_submission(self, sub_id: str) -> bool:
        submissions = self._read_json()
        initial_len = len(submissions)
        submissions = [s for s in submissions if s.get("id") != sub_id]
        if len(submissions) < initial_len:
            self._save_json(submissions)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        submissions = self._read_json()
        candidates = set()
        companies = set()
        total_questions = 0
        total_videos = 0
        total_transcripts = 0

        for s in submissions:
            c = (s.get("candidate_name") or "").strip()
            if c:
                candidates.add(c)
            comp = (s.get("company") or "").strip()
            if comp:
                companies.add(comp)
            total_questions += len(s.get("questions") or [])
            if s.get("recording_link"):
                total_videos += 1
            if s.get("transcript"):
                total_transcripts += 1

        return {
            "total_submissions": len(submissions),
            "total_candidates": len(candidates),
            "total_companies": len(companies),
            "total_questions": total_questions,
            "total_recordings": total_videos,
            "total_transcripts": total_transcripts,
            "candidates_list": sorted(list(candidates)),
            "companies_list": sorted(list(companies))
        }

    def import_to_hub(self, sub_id: str) -> Dict[str, Any]:
        submissions = self._read_json()
        target = next((s for s in submissions if s.get("id") == sub_id), None)
        if not target:
            raise ValueError("Submission not found")

        from app.interview_hub import interview_manager

        new_sched = interview_manager.add_schedule({
            "company": target.get("company"),
            "role": "DevOps Engineer",
            "round": target.get("round") or "Technical Round 1",
            "date": target.get("date"),
            "start_time": target.get("start_time") or target.get("time") or "10:00",
            "end_time": target.get("end_time") or "",
            "salary_ctc": target.get("salary_ctc") or "",
            "monthly_salary": target.get("monthly_salary") or "",
            "recording_link": target.get("recording_link") or "",
            "transcript": target.get("transcript") or "",
            "has_transcript": bool(target.get("transcript")),
            "original_raw_text": target.get("original_raw_text") or "",
            "source_type": target.get("source_type") or "manual",
            "notes": f"Candidate Submission by: {target.get('candidate_name')}. {target.get('notes', '')}".strip(),
            "experience": target.get("experience") or "",
            "status": "completed"
        })

        q_count = 0
        if target.get("questions"):
            q_count = interview_manager.add_bulk_questions(
                company=target.get("company"),
                round_name=target.get("round") or "Technical Round 1",
                interview_date=target.get("date"),
                qa_items=target.get("questions"),
                experience=target.get("experience") or "",
                notes=f"Candidate: {target.get('candidate_name')}",
                difficulty="Moderate",
                recording_link=target.get("recording_link") or "",
                transcript=target.get("transcript") or "",
                original_raw_text=target.get("original_raw_text") or "",
                source_type=target.get("source_type") or "manual"
            )

        target["status"] = "approved"
        self._save_json(submissions)

        return {
            "status": "success",
            "schedule_id": new_sched.get("id"),
            "questions_added": q_count,
            "message": f"Successfully approved {target.get('candidate_name')}'s interview with {q_count} questions into Nagaraj's Interview Hub!"
        }

candidate_manager = CandidateSubmissionsManager()
