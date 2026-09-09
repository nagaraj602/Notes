import os
import shutil
import git
import time
import logging
from app.config import REPOS, NOTES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitSync")

class GitSyncManager:
    def __init__(self, repos=REPOS, target_dir=NOTES_DIR):
        self.repos = repos
        self.target_dir = target_dir
        self.last_sync_time = None
        self.sync_status = "Initialized"
        self.repo_statuses = {}

    def sync(self):
        os.makedirs(self.target_dir, exist_ok=True)
        all_success = True
        messages = []
        valid_folders = [r["folder"] for r in self.repos]

        # Clean up any legacy loose files/folders that don't match the current repo folders
        try:
            for item in os.listdir(self.target_dir):
                item_path = os.path.join(self.target_dir, item)
                if item not in valid_folders:
                    logger.info(f"Removing legacy/stale item at root: {item_path}")
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

        # Sync each repository into its designated clean folder
        for repo_info in self.repos:
            repo_name = repo_info["name"]
            repo_url = repo_info["url"]
            branch = repo_info.get("branch", "main")
            folder_name = repo_info["folder"]
            dest_dir = os.path.join(self.target_dir, folder_name)

            try:
                os.makedirs(dest_dir, exist_ok=True)
                git_folder = os.path.join(dest_dir, ".git")
                
                if not os.path.exists(git_folder):
                    # Clean directory if non-empty and not a git repo
                    if os.path.exists(dest_dir) and len(os.listdir(dest_dir)) > 0:
                        shutil.rmtree(dest_dir, ignore_errors=True)
                        os.makedirs(dest_dir, exist_ok=True)

                    logger.info(f"Cloning {repo_name} from {repo_url} (branch: {branch}) into {dest_dir}...")
                    git.Repo.clone_from(repo_url, dest_dir, branch=branch)
                    status_msg = f"Cloned {repo_name} ({branch})"
                else:
                    logger.info(f"Pulling {repo_name} ({branch})...")
                    repo = git.Repo(dest_dir)
                    origin = repo.remotes.origin
                    origin.pull(branch)
                    status_msg = f"Updated {repo_name} ({branch})"
                    
                self.repo_statuses[repo_name] = {
                    "status": "success",
                    "url": repo_url,
                    "branch": branch,
                    "folder": folder_name,
                    "message": status_msg
                }
                messages.append(status_msg)
            except Exception as e:
                logger.error(f"Sync failed for {repo_name}: {str(e)}")
                # If pull failed due to branch mismatch or dirty tree, try fresh clone
                try:
                    logger.info(f"Retrying fresh clone for {repo_name}...")
                    shutil.rmtree(dest_dir, ignore_errors=True)
                    os.makedirs(dest_dir, exist_ok=True)
                    git.Repo.clone_from(repo_url, dest_dir, branch=branch)
                    status_msg = f"Freshly cloned {repo_name} ({branch})"
                    self.repo_statuses[repo_name] = {
                        "status": "success",
                        "url": repo_url,
                        "branch": branch,
                        "folder": folder_name,
                        "message": status_msg
                    }
                    messages.append(status_msg)
                except Exception as retry_err:
                    all_success = False
                    self.repo_statuses[repo_name] = {
                        "status": "error",
                        "url": repo_url,
                        "branch": branch,
                        "folder": folder_name,
                        "message": str(retry_err)
                    }
                    messages.append(f"{repo_name} error: {str(retry_err)}")

        self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        self.sync_status = "All Synced" if all_success else "Partial Sync Error"
        return {
            "status": "success" if all_success else "error",
            "message": " | ".join(messages),
            "time": self.last_sync_time,
            "repos": self.repo_statuses
        }

    def get_file_tree(self):
        """Returns the file trees for each repository separately and sequentially."""
        repo_trees = []
        if not os.path.exists(self.target_dir):
            return repo_trees
            
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
            
        # Group sequentially by repository
        for repo_info in self.repos:
            folder = repo_info["folder"]
            repo_path = os.path.join(self.target_dir, folder)
            children = scan_dir(repo_path, folder) if os.path.exists(repo_path) else []
            repo_trees.append({
                "id": repo_info.get("id", folder),
                "name": repo_info["name"],
                "short_name": repo_info.get("short_name", repo_info["name"]),
                "icon": repo_info.get("icon", "fa-folder"),
                "folder": folder,
                "url": repo_info["url"],
                "branch": repo_info["branch"],
                "children": children
            })
        return repo_trees

    def search_files(self, query: str):
        """Searches for files by name or text content inside all notes across repos."""
        results = []
        query_lower = query.lower()
        if not os.path.exists(self.target_dir):
            return results
            
        for repo_info in self.repos:
            folder = repo_info["folder"]
            repo_path = os.path.join(self.target_dir, folder)
            if not os.path.exists(repo_path):
                continue
                
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if f.startswith("."):
                        continue
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, self.target_dir).replace("\\", "/")
                    
                    # Check filename match
                    if query_lower in f.lower():
                        results.append({
                            "repo_name": repo_info["short_name"],
                            "repo_id": repo_info.get("id", folder),
                            "filename": f,
                            "path": rel_path,
                            "match_type": "filename",
                            "snippet": f"Matched file name: {f}"
                        })
                        continue
                        
                    # Check content match for text/markdown/yaml/code files
                    if f.endswith((".md", ".txt", ".yaml", ".yml", ".json", ".sh", ".py", ".tf", ".conf", ".sql")):
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                                content = file_obj.read()
                                if query_lower in content.lower():
                                    idx = content.lower().find(query_lower)
                                    start = max(0, idx - 40)
                                    end = min(len(content), idx + 80)
                                    snippet = ("..." if start > 0 else "") + content[start:end].replace("\n", " ") + "..."
                                    results.append({
                                        "repo_name": repo_info["short_name"],
                                        "repo_id": repo_info.get("id", folder),
                                        "filename": f,
                                        "path": rel_path,
                                        "match_type": "content",
                                        "snippet": snippet
                                    })
                        except Exception:
                            pass
        return results

git_manager = GitSyncManager()