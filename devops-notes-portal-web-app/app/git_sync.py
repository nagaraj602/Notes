import os
import shutil
import git
import time
import logging
from app.config import REPOS, NOTES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitSync")

def _get_active_token(target_dir: str) -> str:
    for env_var in ["GITHUB_TOKEN", "GH_TOKEN", "GIT_PUSH_TOKEN", "GIT_TOKEN"]:
        val = os.getenv(env_var, "").strip()
        if val:
            return val
    token_files = [
        os.path.join(target_dir, ".git_token"),
        os.path.join(target_dir, "devops-notes", ".git_token"),
        os.path.join(os.path.dirname(target_dir), ".git_token"),
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
    git_cred = os.path.expanduser("~/.git-credentials")
    if os.path.exists(git_cred):
        try:
            with open(git_cred, "r", encoding="utf-8") as f:
                txt = f.read()
            import re
            m = re.search(r'https?://[^:]+:([^@]+)@github\.com', txt)
            if m:
                return m.group(1).strip()
        except Exception:
            pass
    return ""

def _get_authenticated_url(url: str, token: str) -> str:
    if not token or "github.com" not in url:
        return url
    import re
    clean_url = re.sub(r'https?://(?:[^@]+@)?github\.com/', 'https://github.com/', url)
    return clean_url.replace("https://github.com/", f"https://{token}@github.com/")

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
        active_token = _get_active_token(self.target_dir)

        # Clean up any legacy loose files/folders that don't match the current repo folders
        try:
            for item in os.listdir(self.target_dir):
                if item.startswith("."):
                    continue  # Protect dotfiles such as .git_token
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
            auth_url = _get_authenticated_url(repo_url, active_token)

            try:
                os.makedirs(dest_dir, exist_ok=True)
                git_folder = os.path.join(dest_dir, ".git")
                
                if not os.path.exists(git_folder):
                    # Clean directory if non-empty and not a git repo
                    if os.path.exists(dest_dir) and len(os.listdir(dest_dir)) > 0:
                        shutil.rmtree(dest_dir, ignore_errors=True)
                        os.makedirs(dest_dir, exist_ok=True)

                    logger.info(f"Cloning {repo_name} from {repo_url} (branch: {branch}) into {dest_dir}...")
                    git.Repo.clone_from(auth_url, dest_dir, branch=branch)
                    status_msg = f"Cloned {repo_name} ({branch})"
                else:
                    logger.info(f"Pulling {repo_name} ({branch})...")
                    repo = git.Repo(dest_dir)

                    # Ensure git author is configured
                    with repo.config_writer() as cw:
                        if not cw.has_option("user", "name") or not cw.get_value("user", "name"):
                            cw.set_value("user", "name", "nagaraj602")
                        if not cw.has_option("user", "email") or not cw.get_value("user", "email"):
                            cw.set_value("user", "email", "nagarajkamath602@outlook.com")

                    # Update remote origin URL with authenticated token if available
                    try:
                        repo.git.remote("set-url", "origin", auth_url)
                    except Exception:
                        pass

                    origin = repo.remotes.origin
                    try:
                        repo.git.pull("origin", branch, "--rebase")
                    except Exception:
                        origin.pull(branch)

                    # If this is devops-notes and token is available, check for unpushed commits and push
                    if folder_name == "devops-notes" and active_token:
                        try:
                            ahead_log = repo.git.log(f"origin/{branch}..{branch}", "--oneline")
                            if ahead_log.strip():
                                logger.info(f"Pushing unpushed commits in {repo_name} to GitHub...")
                                repo.git.push("origin", f"{branch}:{branch}")
                        except Exception as pe:
                            logger.warning(f"Could not push unpushed commits in {repo_name}: {pe}")

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
                # Never wipe out devops-notes repository to prevent losing unpushed interview schedules or user edits!
                if folder_name == "devops-notes":
                    all_success = False
                    self.repo_statuses[repo_name] = {
                        "status": "warning",
                        "url": repo_url,
                        "branch": branch,
                        "folder": folder_name,
                        "message": f"Sync warning (local data preserved): {str(e)}"
                    }
                    messages.append(f"{repo_name} warning: {str(e)}")
                    continue

                # For external read-only repos (e.g. training-materials), retry fresh clone
                try:
                    logger.info(f"Retrying fresh clone for {repo_name}...")
                    shutil.rmtree(dest_dir, ignore_errors=True)
                    os.makedirs(dest_dir, exist_ok=True)
                    git.Repo.clone_from(auth_url, dest_dir, branch=branch)
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

        # Reconcile interview manager files with freshly pulled data
        try:
            from app.interview_hub import interview_manager
            interview_manager._reconcile_schedules_from_questions()
            interview_manager._generate_markdown_docs()
        except Exception as ie:
            logger.warning(f"Interview manager reconciliation after sync warning: {ie}")

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

    def commit_and_push_file(self, file_path: str, commit_message: str, author_name: str = "nagaraj602", author_email: str = "nagarajkamath602@outlook.com", token: Optional[str] = None) -> Dict[str, Any]:
        """
        Stages, commits, and pushes a specific file to the GitHub repository.
        Works across both local dev (root repo) and container deployment (devops-notes repo).
        """
        try:
            repo = git.Repo(os.path.dirname(os.path.abspath(file_path)), search_parent_directories=True)
            
            # Configure author/committer
            try:
                with repo.config_writer() as cw:
                    if not cw.has_option("user", "name") or not cw.get_value("user", "name"):
                        cw.set_value("user", "name", author_name)
                    if not cw.has_option("user", "email") or not cw.get_value("user", "email"):
                        cw.set_value("user", "email", author_email)
            except Exception:
                pass

            # Stage file
            repo.git.add(file_path)

            # Commit
            actor = git.Actor(author_name, author_email)
            commit = repo.index.commit(commit_message, author=actor, committer=actor)
            logger.info(f"Committed {file_path} as {commit.hexsha[:7]}: {commit_message}")

            # Push
            active_token = token or self.active_token or os.getenv("GITHUB_TOKEN", "").strip()
            branch = "main"
            try:
                branch = repo.active_branch.name
            except Exception:
                pass

            if active_token:
                remote_url = f"https://{active_token}@github.com/nagaraj602/Notes.git"
                try:
                    repo.git.push(remote_url, f"{branch}:{branch}")
                    logger.info(f"Pushed commit {commit.hexsha[:7]} to GitHub ({branch})")
                except Exception as pe:
                    logger.warning(f"Could not push to GitHub: {pe}")
                    return {"status": "committed_local", "commit": commit.hexsha[:7], "warning": str(pe)}
            else:
                try:
                    repo.git.push("origin", f"{branch}:{branch}")
                    logger.info(f"Pushed commit {commit.hexsha[:7]} to origin ({branch})")
                except Exception as pe:
                    logger.warning(f"Push to origin skipped/failed: {pe}")
                    return {"status": "committed_local", "commit": commit.hexsha[:7], "warning": str(pe)}

            return {"status": "success", "commit": commit.hexsha[:7], "branch": branch}
        except Exception as e:
            logger.error(f"Failed to commit and push file {file_path}: {e}")
            return {"status": "error", "message": str(e)}

git_manager = GitSyncManager()