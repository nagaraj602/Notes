import os
import json

DEFAULT_REPOS = [
    {
        "id": "training-materials",
        "name": "ArtisanTek Training Materials",
        "short_name": "Training Materials",
        "icon": "fa-graduation-cap",
        "url": "https://github.com/artisantek/training-materials.git",
        "branch": "master",
        "folder": "training-materials"
    },
    {
        "id": "devops-notes",
        "name": "DevOps Notes (nagaraj602)",
        "short_name": "DevOps Notes",
        "icon": "fa-book-bookmark",
        "url": "https://github.com/nagaraj602/Notes.git",
        "branch": "main",
        "folder": "devops-notes"
    }
]

REPOS_JSON = os.getenv("REPOS_JSON", "")
if REPOS_JSON:
    try:
        REPOS = json.loads(REPOS_JSON)
    except Exception:
        REPOS = DEFAULT_REPOS
else:
    REPOS = DEFAULT_REPOS

# Allow individual overrides via REPO_URL and REPO_BRANCH if specified
custom_repo_url = os.getenv("REPO_URL", "").strip()
custom_repo_branch = os.getenv("REPO_BRANCH", "").strip()
if custom_repo_url:
    for r in REPOS:
        if r["id"] == "devops-notes":
            r["url"] = custom_repo_url
            if custom_repo_branch:
                r["branch"] = custom_repo_branch

AUTO_SYNC_INTERVAL_MINUTES = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "5"))
NOTES_DIR = os.getenv("NOTES_DIR", "/app/data/notes")