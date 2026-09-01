import os
import shutil
import git
import time
import logging
from app.config import REPO_URL, REPO_BRANCH, NOTES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitSync")

class GitSyncManager:
    def __init__(self, repo_url=REPO_URL, branch=REPO_BRANCH, target_dir=NOTES_DIR):
        self.repo_url = repo_url
        self.branch = branch
        self.target_dir = target_dir
        self.last_sync_time = None
        self.sync_status = "Initialized"

    def sync(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            git_folder = os.path.join(self.target_dir, ".git")
            
            if not os.path.exists(git_folder):
                logger.info(f"Cloning {self.repo_url} into {self.target_dir}...")
                git.Repo.clone_from(self.repo_url, self.target_dir, branch=self.branch)
                self.sync_status = "Cloned successfully"
            else:
                logger.info(f"Pulling latest changes from {self.repo_url}...")
                repo = git.Repo(self.target_dir)
                origin = repo.remotes.origin
                origin.pull(self.branch)
                self.sync_status = "Updated successfully"
                
            self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            return {"status": "success", "message": self.sync_status, "time": self.last_sync_time}
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            self.sync_status = f"Error: {str(e)}"
            return {"status": "error", "message": str(e), "time": self.last_sync_time}

    def get_file_tree(self):
        """Recursively discovers all directories and files in the repository."""
        tree = []
        if not os.path.exists(self.target_dir):
            return tree
            
        def scan_dir(current_path, rel_path=""):
            items = []
            try:
                entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
                for entry in entries:
                    if entry.name.startswith("."):
                        continue  # Skip .git and hidden files
                    item_rel = os.path.join(rel_path, entry.name).replace("\\", "/")
                    if entry.is_dir():
                        children = scan_dir(entry.path, item_rel)
                        items.append({
                            "name": entry.name,
                            "type": "folder",
                            "path": item_rel,
                            "children": children
                        })
                    else:
                        ext = os.path.splitext(entry.name)[1].lower()
                        items.append({
                            "name": entry.name,
                            "type": "file",
                            "ext": ext,
                            "path": item_rel
                        })
            except Exception as e:
                logger.error(f"Error scanning directory {current_path}: {e}")
            return items
            
        return scan_dir(self.target_dir)

    def search_files(self, query: str):
        """Searches for files by name or text content inside notes."""
        results = []
        query_lower = query.lower()
        if not os.path.exists(self.target_dir):
            return results
            
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, self.target_dir).replace("\\", "/")
                
                # Check filename match
                if query_lower in f.lower():
                    results.append({
                        "filename": f,
                        "path": rel_path,
                        "match_type": "filename",
                        "snippet": f"Matched file name: {f}"
                    })
                    continue
                    
                # Check content match for text/markdown files
                if f.endswith((".md", ".txt", ".yaml", ".yml", ".json", ".sh", ".py")):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                            content = file_obj.read()
                            if query_lower in content.lower():
                                idx = content.lower().find(query_lower)
                                start = max(0, idx - 40)
                                end = min(len(content), idx + 80)
                                snippet = ("..." if start > 0 else "") + content[start:end].replace("\n", " ") + "..."
                                results.append({
                                    "filename": f,
                                    "path": rel_path,
                                    "match_type": "content",
                                    "snippet": snippet
                                })
                    except Exception:
                        pass
        return results

git_manager = GitSyncManager()