"""
Repository-Backed Session & State Database
Stores user session, last viewed file, active tab, and navigation state
directly inside the Notes repository so session persists across refreshes and different servers.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SessionManager:
    def __init__(self):
        self.storage_dir = self._resolve_storage_dir()
        os.makedirs(self.storage_dir, exist_ok=True)
        self.state_file = os.path.join(self.storage_dir, "session_state.json")
        self._init_state()

    def _resolve_storage_dir(self) -> str:
        # Container path
        container_path = "/app/data/notes/devops-notes/Nagaraj_interviews"
        if os.path.exists(os.path.dirname(container_path)):
            return container_path
        
        # Local Notes repo path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        notes_path = os.path.join(base_dir, "Nagaraj_interviews")
        if os.path.exists(notes_path):
            return notes_path
        
        # Fallback
        app_local = os.path.join(os.path.dirname(__file__), "data", "Nagaraj_interviews")
        return app_local

    def _init_state(self):
        if not os.path.exists(self.state_file):
            initial_state = {
                "last_active_file": "",
                "last_active_tab": "all",
                "last_page": "/",
                "scroll_position": 0,
                "view_mode": "preview",
                "sidebar_expanded_folders": [],
                "updated_at": datetime.utcnow().isoformat()
            }
            self._save_json(initial_state)

    def get_state(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.state_file):
                self._init_state()
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def update_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_state()
        for k, v in updates.items():
            if v is not None:
                current[k] = v
        current["updated_at"] = datetime.utcnow().isoformat()
        self._save_json(current)
        return current

    def _save_json(self, data: Dict[str, Any]):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._auto_git_sync()
        except Exception as e:
            print(f"Error saving session state: {e}")

    def _auto_git_sync(self):
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
            repo.git.add("Nagaraj_interviews/session_state.json")
            if repo.is_dirty(untracked_files=True):
                repo.index.commit("Update portal session state in Notes repo")
                try:
                    origin = repo.remotes.origin
                    origin.push()
                except Exception:
                    pass
        except Exception:
            pass

session_manager = SessionManager()
