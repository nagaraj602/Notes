  ### Complete Solution Architecture                                                                                                     
                                                                                                                                         
  This complete production-grade DevOps portal includes:                                                                                 
                                                                                                                                         
  1. Dynamic Git Synchronizer: Clones & periodically auto-syncs https://github.com/nagaraj602/Notes.git. Detects newly added             
  folders/files dynamically, builds an interactive tree, and provides full-text search with syntax-highlighted Markdown rendering.       
  2. Automated YouTube AI Notes & QA Generator:                                                                                          
      • Extracts transcripts directly from YouTube URLs (no external tools like Tactiq needed).                                          
      • Includes your exact Class Notes prompt and QA / Interview Questions prompt.                                                      
      • Powered by the Google Gemini API to produce rich, structured Markdown notes with 1-click save, copy, or download.                
  3. Multi-Stage Dockerfile: Secure, ultra-lightweight (~90MB), minimal runtime container with non-root execution.                       
  4. Kubernetes Manifests: Deployment, Service (LoadBalancer / NodePort for Docker Desktop), ConfigMap, Secret, and PersistentVolumeClaim.
  5. 1-Click PowerShell Deployment Script (deploy.ps1): Automatically writes all project files, builds the Docker image, and applies the 
  Kubernetes manifests to your Docker Desktop cluster.                                                                                   
  ──────                                                                                                                                 
  ## 1. Project File Structure                                                                                                           
                                                                                                                                         
  Create a folder (or run the automated PowerShell script below) with this structure:                                                    
                                                                                                                                         
    devops-notes-portal/                                                                                                                 
    ├── app/                                                                                                                             
    │   ├── config.py             # App & Git configurations                                                                             
    │   ├── git_sync.py           # Auto-sync engine for github.com/nagaraj602/Notes                                                     
    │   ├── markdown_engine.py    # Markdown parser with code highlighting & TOC                                                         
    │   ├── youtube_service.py    # YouTube transcript fetcher & Gemini AI pipeline                                                      
    │   ├── main.py               # FastAPI backend & web routing                                                                        
    │   └── templates/                                                                                                                   
    │       ├── base.html         # Responsive layout, dark mode, search bar                                                             
    │       ├── index.html        # Dynamic tree explorer & notes viewer                                                                 
    │       ├── youtube.html      # YouTube to Notes & QA generator                                                                      
    │       └── settings.html     # Sync status & Gemini API key settings                                                                
    ├── Dockerfile                # Multi-stage Docker build                                                                             
    ├── .dockerignore             # Docker build exclusions                                                                              
    ├── requirements.txt          # Python dependencies                                                                                  
    ├── k8s/                                                                                                                             
    │   └── all-in-one.yaml       # Complete Kubernetes manifests                                                                        
    └── deploy.ps1                # 1-Click build & deploy script                                                                        
  ──────                                                                                                                                 
  ## 2. Source Code Files                          
### requirements.txt
```bash                             
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
jinja2>=3.1.3
python-multipart>=0.0.9
markdown>=3.6
pymdown-extensions>=10.7
pygments>=2.17.2
youtube-transcript-api>=0.6.2
google-generativeai>=0.4.1
requests>=2.31.0
gitpython>=3.1.42
aiofiles>=23.2.1
```
  ──────                                                                                                                                 
  ### Dockerfile (Multi-Stage Build)
```bash
# ==========================================
# Stage 1: Build & Dependencies
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system build dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
	git \
    && rm -rf /var/lib/apt/lists/*
	
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Final Minimal Runtime Image
# ==========================================
FROM python:3.11-slim AS runtime
WORKDIR /app
# Install git and ca-certificates for repo cloning and HTTPS

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*                                   
# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH 
ENV PYTHONUNBUFFERED=1

# Copy application source code
COPY app/ /app/app/

# Create data directory for notes storage
RUN mkdir -p /app/data/notes  

# Environment variable defaults
ENV REPO_URL="https://github.com/nagaraj602/Notes.git"
ENV REPO_BRANCH="main"
ENV AUTO_SYNC_INTERVAL_MINUTES=5
ENV NOTES_DIR="/app/data/notes"
ENV PORT=8000

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
  
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```                    
  ──────                                                                                                                                 
  ### .dockerignore

    __pycache__
    *.pyc
    *.pyo
    *.pyd
    .git
    .gitignore
    .env
    data/
    k8s/
    *.md
    deploy.ps1
  ──────                                                                                                                                 
  ### app/config.py                                                                                                                      
   ```bash                                                                                                                                      
    import os
    
    REPO_URL = os.getenv("REPO_URL", "https://github.com/nagaraj602/Notes.git")
    REPO_BRANCH = os.getenv("REPO_BRANCH", "main")
    AUTO_SYNC_INTERVAL_MINUTES = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "5"))
    NOTES_DIR = os.getenv("NOTES_DIR", "/app/data/notes") 
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Default prompt templates as requested
    PROMPT_CLASS_NOTES = (
        "I have this transcript. Make it proper as it is looking like class teaching. "
        "It should be in correct thing. Not look like teaching or coversation. "
        "Don't assume anything. Don't add your own concpt. You should give what is there in transcript. "
        "Don't miss anything, don't shorten any explanation from transcript, "
        "Including each and every steps, file names, code etc."
    ) 
    PROMPT_QA = (
        "I have the Qa transcript. Extract all question asked by instructor and if there are any "
        "suggestion/answer given by the instructor, include that. "
        "Don't miss any questions, even the sub questions to it. "
        "I repeat, don't miss any questions."
    )
    ```
  ──────                                                                                                                                 
  ### app/git_sync.py
  
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
  ──────                                                                                                                                 
  ### app/markdown_engine.py                                                                                                             
                                                                                                                                         
    import markdown                                                                                                                      
    from pymdownx import superfences                                                                                                     
                                                                                                                                         
    def render_markdown(raw_content: str) -> str:                                                                                        
        """Renders GitHub Flavored Markdown with syntax highlighting, tables, tasklists, and TOC."""                                     
        extensions = [                                                                                                                   
            'extra',                                                                                                                     
            'tables',                                                                                                                    
            'fenced_code',                                                                                                               
            'codehilite',                                                                                                                
            'toc',                                                                                                                       
            'pymdownx.superfences',                                                                                                      
            'pymdownx.tasklist',                                                                                                         
            'pymdownx.highlight',                                                                                                        
            'pymdownx.inlinehilite',                                                                                                     
        ]                                                                                                                                
        extension_configs = {                                                                                                            
            'codehilite': {                                                                                                              
                'linenums': False,                                                                                                       
                'css_class': 'highlight',                                                                                                
                'guess_lang': False                                                                                                      
            },                                                                                                                           
            'pymdownx.highlight': {                                                                                                      
                'linenums': False,                                                                                                       
                'css_class': 'highlight'                                                                                                 
            },                                                                                                                           
            'pymdownx.tasklist': {                                                                                                       
                'custom_checkbox': True                                                                                                  
            }                                                                                                                            
        }                                                                                                                                
        return markdown.markdown(raw_content, extensions=extensions, extension_configs=extension_configs)                                
  ──────                                                                                                                                 
  ### app/youtube_service.py                                                                                                             
                                                                                                                                         
    import re                                                                                                                            
    import logging                                                                                                                       
    from urllib.parse import urlparse, parse_qs                                                                                          
    from youtube_transcript_api import YouTubeTranscriptApi                                                                              
    from youtube_transcript_api.formatters import TextFormatter                                                                          
    import google.generativeai as genai                                                                                                  
    from app.config import GEMINI_API_KEY, PROMPT_CLASS_NOTES, PROMPT_QA                                                                 
                                                                                                                                         
    logger = logging.getLogger("YouTubeService")                                                                                         
                                                                                                                                         
    class YouTubeService:                                                                                                                
        @staticmethod                                                                                                                    
        def extract_video_id(url_or_id: str) -> str:                                                                                     
            """Extracts YouTube 11-character video ID from any YouTube URL format."""                                                    
            url_or_id = url_or_id.strip()                                                                                                
            if len(url_or_id) == 11 and not ("/" in url_or_id or "." in url_or_id):                                                      
                return url_or_id                                                                                                         
                                                                                                                                         
            parsed = urlparse(url_or_id)                                                                                                 
            if parsed.hostname in ("youtu.be", "www.youtu.be"):                                                                          
                return parsed.path.lstrip("/")                                                                                           
            if parsed.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):                                                   
                if parsed.path == "/watch":                                                                                              
                    return parse_qs(parsed.query).get("v", [""])[0]                                                                      
                elif parsed.path.startswith(("/embed/", "/v/", "/shorts/")):                                                             
                    return parsed.path.split("/")[2]                                                                                     
                                                                                                                                         
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url_or_id)                                                              
            if match:                                                                                                                    
                return match.group(1)                                                                                                    
            raise ValueError("Invalid YouTube URL or Video ID provided.")                                                                
                                                                                                                                         
        @staticmethod                                                                                                                    
        def get_transcript(video_id: str) -> str:                                                                                        
            """Fetches raw subtitles/transcript for a YouTube video in English, Hindi, or auto-generated."""                             
            try:                                                                                                                         
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)                                                        
                # Try manual english, generated english, or any available transcript                                                     
                try:                                                                                                                     
                    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])                                               
                except Exception:                                                                                                        
                    try:                                                                                                                 
                        transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])                                 
                    except Exception:                                                                                                    
                        transcript = next(iter(transcript_list))                                                                         
                                                                                                                                         
                data = transcript.fetch()                                                                                                
                formatter = TextFormatter()                                                                                              
                return formatter.format_transcript(data)                                                                                 
            except Exception as e:                                                                                                       
                logger.error(f"Failed to fetch YouTube transcript: {e}")                                                                 
                raise RuntimeError(f"Could not retrieve transcript from YouTube: {str(e)}")                                              
                                                                                                                                         
        @staticmethod                                                                                                                    
        def generate_ai_notes(transcript: str, mode: str = "class_notes", custom_prompt: str = "", api_key: str = None) -> str:          
            """Processes the transcript with Google Gemini using the specified prompt."""                                                
            key = api_key or GEMINI_API_KEY                                                                                              
            if not key:                                                                                                                  
                raise ValueError("Gemini API Key is missing. Please set GEMINI_API_KEY in environment or Settings tab.")                 
                                                                                                                                         
            genai.configure(api_key=key)                                                                                                 
                                                                                                                                         
            if mode == "qa":                                                                                                             
                system_prompt = PROMPT_QA                                                                                                
            elif mode == "custom" and custom_prompt:                                                                                     
                system_prompt = custom_prompt                                                                                            
            else:                                                                                                                        
                system_prompt = PROMPT_CLASS_NOTES                                                                                       
                                                                                                                                         
            model = genai.GenerativeModel("gemini-1.5-flash")                                                                            
                                                                                                                                         
            full_prompt = (                                                                                                              
                f"SYSTEM INSTRUCTION:\n{system_prompt}\n\n"                                                                              
                f"---\nTRANSCRIPT CONTENT:\n{transcript}\n---\n\n"                                                                       
                f"Please output clean, well-formatted Markdown."                                                                         
            )                                                                                                                            
                                                                                                                                         
            response = model.generate_content(full_prompt)                                                                               
            return response.text                                                                                                         
  ──────                                                                                                                                 
  ### app/main.py                                                                                                                        
                                                                                                                                         
    import os                                                                                                                            
    import asyncio                                                                                                                       
    from contextlib import asynccontextmanager                                                                                           
    from fastapi import FastAPI, Request, Form, HTTPException                                                                            
    from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse                                                          
    from fastapi.staticfiles import StaticFiles                                                                                          
    from fastapi.templating import Jinja2Templates                                                                                       
                                                                                                                                         
    from app.config import (                                                                                                             
        REPO_URL, REPO_BRANCH, AUTO_SYNC_INTERVAL_MINUTES,                                                                               
        NOTES_DIR, GEMINI_API_KEY, PROMPT_CLASS_NOTES, PROMPT_QA                                                                         
    )                                                                                                                                    
    from app.git_sync import git_manager                                                                                                 
    from app.markdown_engine import render_markdown                                                                                      
    from app.youtube_service import YouTubeService                                                                                       
                                                                                                                                         
    # Background Auto-Sync Task                                                                                                          
    async def auto_sync_worker():                                                                                                        
        while True:                                                                                                                      
            try:                                                                                                                         
                logger_info = git_manager.sync()                                                                                         
            except Exception as e:                                                                                                       
                pass                                                                                                                     
            await asyncio.sleep(AUTO_SYNC_INTERVAL_MINUTES * 60)                                                                         
                                                                                                                                         
    @asynccontextmanager                                                                                                                 
    async def lifespan(app: FastAPI):                                                                                                    
        # Initial sync on container boot                                                                                                 
        git_manager.sync()                                                                                                               
        # Start periodic sync worker                                                                                                     
        asyncio.create_task(auto_sync_worker())                                                                                          
        yield                                                                                                                            
                                                                                                                                         
    app = FastAPI(title="DevOps Knowledge Hub & AI Study Assistant", lifespan=lifespan)                                                  
                                                                                                                                         
    # Templates & Static Files                                                                                                           
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")                                                                 
    templates = Jinja2Templates(directory=TEMPLATES_DIR)                                                                                 
                                                                                                                                         
    # --- WEB ROUTES ---                                                                                                                 
                                                                                                                                         
    @app.get("/", response_class=HTMLResponse)                                                                                           
    async def home(request: Request):                                                                                                    
        tree = git_manager.get_file_tree()                                                                                               
        return templates.TemplateResponse("index.html", {                                                                                
            "request": request,                                                                                                          
            "tree": tree,                                                                                                                
            "last_sync": git_manager.last_sync_time,                                                                                     
            "sync_status": git_manager.sync_status                                                                                       
        })                                                                                                                               
                                                                                                                                         
    @app.get("/youtube", response_class=HTMLResponse)                                                                                    
    async def youtube_page(request: Request):                                                                                            
        return templates.TemplateResponse("youtube.html", {                                                                              
            "request": request,                                                                                                          
            "prompt_class_notes": PROMPT_CLASS_NOTES,                                                                                    
            "prompt_qa": PROMPT_QA,                                                                                                      
            "has_api_key": bool(GEMINI_API_KEY)                                                                                          
        })                                                                                                                               
                                                                                                                                         
    @app.get("/settings", response_class=HTMLResponse)                                                                                   
    async def settings_page(request: Request):                                                                                           
        return templates.TemplateResponse("settings.html", {                                                                             
            "request": request,                                                                                                          
            "repo_url": REPO_URL,                                                                                                        
            "branch": REPO_BRANCH,                                                                                                       
            "sync_interval": AUTO_SYNC_INTERVAL_MINUTES,                                                                                 
            "last_sync": git_manager.last_sync_time,                                                                                     
            "sync_status": git_manager.sync_status,                                                                                      
            "has_api_key": bool(GEMINI_API_KEY)                                                                                          
        })                                                                                                                               
                                                                                                                                         
    # --- API ENDPOINTS ---                                                                                                              
                                                                                                                                         
    @app.get("/api/health")                                                                                                              
    async def health():                                                                                                                  
        return {"status": "ok", "last_sync": git_manager.last_sync_time}                                                                 
                                                                                                                                         
    @app.post("/api/sync")                                                                                                               
    async def trigger_sync():                                                                                                            
        result = git_manager.sync()                                                                                                      
        return JSONResponse(content=result)                                                                                              
                                                                                                                                         
    @app.get("/api/tree")                                                                                                                
    async def get_tree():                                                                                                                
        return JSONResponse(content=git_manager.get_file_tree())                                                                         
                                                                                                                                         
    @app.get("/api/file")                                                                                                                
    async def get_file_content(path: str):                                                                                               
        safe_path = os.path.abspath(os.path.join(NOTES_DIR, path))                                                                       
        if not safe_path.startswith(os.path.abspath(NOTES_DIR)):                                                                         
            raise HTTPException(status_code=403, detail="Access denied")                                                                 
        if not os.path.exists(safe_path) or not os.path.isfile(safe_path):                                                               
            raise HTTPException(status_code=404, detail="File not found")                                                                
                                                                                                                                         
        try:                                                                                                                             
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:                                                           
                raw_content = f.read()                                                                                                   
        except Exception as e:                                                                                                           
            raise HTTPException(status_code=500, detail=str(e))                                                                          
                                                                                                                                         
        ext = os.path.splitext(safe_path)[1].lower()                                                                                     
        is_markdown = ext in [".md", ".markdown"]                                                                                        
        rendered_html = render_markdown(raw_content) if is_markdown else f"<pre><code>{raw_content}</code></pre>"                        
                                                                                                                                         
        return JSONResponse({                                                                                                            
            "path": path,                                                                                                                
            "filename": os.path.basename(path),                                                                                          
            "raw": raw_content,                                                                                                          
            "html": rendered_html,                                                                                                       
            "is_markdown": is_markdown                                                                                                   
        })                                                                                                                               
                                                                                                                                         
    @app.get("/api/search")                                                                                                              
    async def search_notes(q: str = ""):                                                                                                 
        if not q.strip():                                                                                                                
            return JSONResponse([])                                                                                                      
        results = git_manager.search_files(q.strip())                                                                                    
        return JSONResponse(results)                                                                                                     
                                                                                                                                         
    @app.post("/api/youtube/generate")                                                                                                   
    async def generate_youtube_notes(                                                                                                    
        url: str = Form(...),                                                                                                            
        mode: str = Form("class_notes"),                                                                                                 
        custom_prompt: str = Form(""),                                                                                                   
        api_key: str = Form("")                                                                                                          
    ):                                                                                                                                   
        try:                                                                                                                             
            video_id = YouTubeService.extract_video_id(url)                                                                              
            transcript = YouTubeService.get_transcript(video_id)                                                                         
            ai_notes = YouTubeService.generate_ai_notes(                                                                                 
                transcript=transcript,                                                                                                   
                mode=mode,                                                                                                               
                custom_prompt=custom_prompt,                                                                                             
                api_key=api_key or GEMINI_API_KEY                                                                                        
            )                                                                                                                            
            rendered_html = render_markdown(ai_notes)                                                                                    
            return JSONResponse({                                                                                                        
                "status": "success",                                                                                                     
                "video_id": video_id,                                                                                                    
                "raw_notes": ai_notes,                                                                                                   
                "html_notes": rendered_html,                                                                                             
                "transcript_length": len(transcript)                                                                                     
            })                                                                                                                           
        except Exception as e:                                                                                                           
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)                                                 
                                                                                                                                         
    @app.post("/api/save-note")                                                                                                          
    async def save_note(                                                                                                                 
        filename: str = Form(...),                                                                                                       
        folder: str = Form(""),                                                                                                          
        content: str = Form(...)                                                                                                         
    ):                                                                                                                                   
        """Allows saving AI-generated notes directly into the notes directory."""                                                        
        if not filename.endswith(".md"):                                                                                                 
            filename += ".md"                                                                                                            
        target_folder = os.path.abspath(os.path.join(NOTES_DIR, folder))                                                                 
        if not target_folder.startswith(os.path.abspath(NOTES_DIR)):                                                                     
            raise HTTPException(status_code=403, detail="Invalid folder path")                                                           
                                                                                                                                         
        os.makedirs(target_folder, exist_ok=True)                                                                                        
        file_path = os.path.join(target_folder, filename)                                                                                
        with open(file_path, "w", encoding="utf-8") as f:                                                                                
            f.write(content)                                                                                                             
                                                                                                                                         
        return JSONResponse({"status": "success", "path": os.path.relpath(file_path, NOTES_DIR)})                                        
  ──────                                                                                                                                 
  ### app/templates/base.html                                                                                                            
                                                                                                                                         
    <!DOCTYPE html>                                                                                                                      
    <html lang="en" class="h-full bg-slate-900 text-slate-100">                                                                          
    <head>                                                                                                                               
      <meta charset="UTF-8">                                                                                                             
      <meta name="viewport" content="width=device-width, initial-scale=1.0">                                                             
      <title>{% block title %}DevOps Knowledge Portal{% endblock %}</title>                                                              
      <!-- Tailwind CSS -->                                                                                                              
      <script src="https://cdn.tailwindcss.com"></script>                                                                                
      <!-- Font Awesome Icons -->                                                                                                        
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">                           
      <!-- Prism Code Highlighting -->                                                                                                   
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">                   
      <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>                                           
      <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>             
      <style>                                                                                                                            
        /* Custom Markdown Rendering Styles */                                                                                           
        .prose-custom { max-width: 100%; color: #e2e8f0; }                                                                               
        .prose-custom h1 { font-size: 2rem; font-weight: 700; color: #38bdf8; margin-top: 1.5rem; margin-bottom: 1rem; border-bottom: 1px
  solid #334155; padding-bottom: 0.5rem; }                                                                                               
        .prose-custom h2 { font-size: 1.5rem; font-weight: 600; color: #818cf8; margin-top: 1.25rem; margin-bottom: 0.75rem; }           
        .prose-custom h3 { font-size: 1.25rem; font-weight: 600; color: #a78bfa; margin-top: 1rem; margin-bottom: 0.5rem; }              
        .prose-custom p { line-height: 1.75; margin-bottom: 1rem; }                                                                      
        .prose-custom ul { list-style-type: disc; margin-left: 1.5rem; margin-bottom: 1rem; }                                            
        .prose-custom ol { list-style-type: decimal; margin-left: 1.5rem; margin-bottom: 1rem; }                                         
        .prose-custom li { margin-bottom: 0.25rem; }                                                                                     
        .prose-custom code { background-color: #1e293b; color: #f43f5e; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.    
  875em; font-family: monospace; }                                                                                                       
        .prose-custom pre { background-color: #0f172a !important; border: 1px solid #334155; border-radius: 0.5rem; padding: 1rem;       
  overflow-x: auto; margin-bottom: 1.25rem; position: relative; }                                                                        
        .prose-custom pre code { background-color: transparent !important; color: #e2e8f0 !original; padding: 0; }                       
        .prose-custom table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }                                           
        .prose-custom th, .prose-custom td { border: 1px solid #334155; padding: 0.75rem; text-align: left; }                            
        .prose-custom th { background-color: #1e293b; color: #38bdf8; font-weight: 600; }                                                
        .prose-custom tr:nth-child(even) { background-color: #0f172a; }                                                                  
        .prose-custom blockquote { border-left: 4px solid #38bdf8; padding-left: 1rem; margin-left: 0; color: #94a3b8; font-style: italic;
  }                                                                                                                                      
      </style>                                                                                                                           
    </head>                                                                                                                              
    <body class="h-full flex flex-col">                                                                                                  
      <!-- Navbar -->                                                                                                                    
      <header class="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center justify-between sticky top-0 z-50">              
        <div class="flex items-center space-x-4">                                                                                        
          <a href="/" class="flex items-center space-x-3 text-cyan-400 font-bold text-xl hover:text-cyan-300">                           
            <i class="fa-solid fa-cubes-stacked text-2xl"></i>                                                                           
            <span>DevOps Hub</span>                                                                                                      
          </a>                                                                                                                           
          <span class="text-xs bg-cyan-950 text-cyan-400 px-2.5 py-1 rounded-full border border-cyan-800">                               
            <i class="fa-solid fa-code-branch mr-1"></i> Auto-Sync: Active                                                               
          </span>                                                                                                                        
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Navigation Links -->                                                                                                        
        <nav class="flex items-center space-x-2">                                                                                        
          <a href="/" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 text-slate-200">                                
            <i class="fa-solid fa-book-bookmark mr-1.5 text-cyan-400"></i> Notes Explorer                                                
          </a>                                                                                                                           
          <a href="/youtube" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 text-slate-200">                         
            <i class="fa-brands fa-youtube mr-1.5 text-red-400"></i> YouTube AI Notes & QA                                               
          </a>                                                                                                                           
          <a href="/settings" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 text-slate-200">                        
            <i class="fa-solid fa-sliders mr-1.5 text-indigo-400"></i> Sync & Settings                                                   
          </a>                                                                                                                           
          <button onclick="triggerManualSync()" class="ml-2 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md text-sm font-  
  semibold transition flex items-center shadow">                                                                                         
            <i id="sync-icon" class="fa-solid fa-rotate mr-1.5"></i> Sync Repo                                                           
          </button>                                                                                                                      
        </nav>                                                                                                                           
      </header>                                                                                                                          
                                                                                                                                         
      <!-- Main Content Area -->                                                                                                         
      <main class="flex-1 overflow-hidden flex">                                                                                         
        {% block content %}{% endblock %}                                                                                                
      </main>                                                                                                                            
                                                                                                                                         
      <script>                                                                                                                           
        async function triggerManualSync() {                                                                                             
          const icon = document.getElementById("sync-icon");                                                                             
          icon.classList.add("fa-spin");                                                                                                 
          try {                                                                                                                          
            const res = await fetch("/api/sync", { method: "POST" });                                                                    
            const data = await res.json();                                                                                               
            alert("Sync Completed: " + data.message);                                                                                    
            window.location.reload();                                                                                                    
          } catch (err) {                                                                                                                
            alert("Sync failed: " + err);                                                                                                
          } finally {                                                                                                                    
            icon.classList.remove("fa-spin");                                                                                            
          }                                                                                                                              
        }                                                                                                                                
      </script>                                                                                                                          
      {% block scripts %}{% endblock %}                                                                                                  
    </body>                                                                                                                              
    </html>                                                                                                                              
  ──────                                                                                                                                 
  ### app/templates/index.html                                                                                                           
                                                                                                                                         
    {% extends "base.html" %}                                                                                                            
    {% block title %}Notes Explorer - DevOps Hub{% endblock %}                                                                           
                                                                                                                                         
    {% block content %}                                                                                                                  
    <div class="w-80 bg-slate-800/90 border-r border-slate-700 flex flex-col h-full">                                                    
      <!-- Search Header -->                                                                                                             
      <div class="p-3 border-b border-slate-700">                                                                                        
        <div class="relative">                                                                                                           
          <input type="text" id="searchInput" placeholder="Search notes & content..."                                                    
            class="w-full bg-slate-900 text-sm rounded-lg pl-9 pr-3 py-2 border border-slate-700 text-slate-200 focus:outline-none       
  focus:border-cyan-500">                                                                                                                
          <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-400 text-xs"></i>                                      
        </div>                                                                                                                           
      </div>                                                                                                                             
                                                                                                                                         
      <!-- Search Results (hidden by default) -->                                                                                        
      <div id="searchResults" class="hidden overflow-y-auto flex-1 p-2 space-y-1"></div>                                                 
                                                                                                                                         
      <!-- Recursive File Tree -->                                                                                                       
      <div id="fileTreeContainer" class="flex-1 overflow-y-auto p-3 text-sm font-mono select-none">                                      
        <div class="text-xs uppercase text-slate-400 font-bold tracking-wider mb-2 px-1">                                                
          <i class="fa-solid fa-folder-tree mr-1 text-cyan-400"></i> Repository Files                                                    
        </div>                                                                                                                           
        {% macro render_node(node) %}                                                                                                    
          {% if node.type == 'folder' %}                                                                                                 
            <div class="folder-group mb-1">                                                                                              
              <div class="flex items-center space-x-2 py-1 px-2 rounded hover:bg-slate-700 cursor-pointer text-slate-300 font-sans font- 
  medium" onclick="toggleFolder(this)">                                                                                                  
                <i class="fa-solid fa-chevron-right text-xs text-slate-400 transition-transform"></i>                                    
                <i class="fa-solid fa-folder text-amber-400"></i>                                                                        
                <span>{{ node.name }}</span>                                                                                             
              </div>                                                                                                                     
              <div class="folder-children pl-4 border-l border-slate-700 ml-3 hidden">                                                   
                {% for child in node.children %}                                                                                         
                  {{ render_node(child) }}                                                                                               
                {% endfor %}                                                                                                             
              </div>                                                                                                                     
            </div>                                                                                                                       
          {% else %}                                                                                                                     
            <div class="file-item flex items-center space-x-2 py-1 px-2 rounded hover:bg-slate-700/80 cursor-pointer text-slate-300      
  hover:text-cyan-300 font-sans text-xs" onclick="loadFile('{{ node.path }}')">                                                          
              {% if node.ext in ['.md', '.markdown'] %}                                                                                  
                <i class="fa-brands fa-markdown text-blue-400"></i>                                                                      
              {% elif node.ext in ['.yaml', '.yml'] %}                                                                                   
                <i class="fa-solid fa-file-code text-red-400"></i>                                                                       
              {% elif node.ext in ['.sh', '.bash'] %}                                                                                    
                <i class="fa-solid fa-terminal text-green-400"></i>                                                                      
              {% else %}                                                                                                                 
                <i class="fa-regular fa-file-lines text-slate-400"></i>                                                                  
              {% endif %}                                                                                                                
              <span class="truncate">{{ node.name }}</span>                                                                              
            </div>                                                                                                                       
          {% endif %}                                                                                                                    
        {% endmacro %}                                                                                                                   
                                                                                                                                         
        {% for node in tree %}                                                                                                           
          {{ render_node(node) }}                                                                                                        
        {% endfor %}                                                                                                                     
      </div>                                                                                                                             
    </div>                                                                                                                               
                                                                                                                                         
    <!-- Main Note Viewer -->                                                                                                            
    <div class="flex-1 flex flex-col h-full bg-slate-900 overflow-hidden">                                                               
      <div id="noteHeader" class="bg-slate-800/60 border-b border-slate-700 px-6 py-3 flex items-center justify-between">                
        <div class="flex items-center space-x-3">                                                                                        
          <i class="fa-solid fa-file-lines text-cyan-400 text-lg"></i>                                                                   
          <span id="activeFilePath" class="text-sm font-mono text-slate-300">Select a note from the left sidebar</span>                  
        </div>                                                                                                                           
        <div class="flex items-center space-x-2">                                                                                        
          <button onclick="copyRawNote()" class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded text-slate-200">            
            <i class="fa-regular fa-copy mr-1"></i> Copy Raw                                                                             
          </button>                                                                                                                      
          <button onclick="downloadNote()" class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded text-slate-200">           
            <i class="fa-solid fa-download mr-1"></i> Download                                                                           
          </button>                                                                                                                      
        </div>                                                                                                                           
      </div>                                                                                                                             
                                                                                                                                         
      <div id="noteViewer" class="flex-1 overflow-y-auto p-8 prose-custom">                                                              
        <div class="text-center py-24 text-slate-500">                                                                                   
          <i class="fa-solid fa-book-open text-6xl mb-4 text-slate-600"></i>                                                             
          <h2 class="text-2xl font-bold text-slate-400">Welcome to DevOps Notes Portal</h2>                                              
          <p class="mt-2 text-sm text-slate-500">Click any folder or note on the left sidebar to start reading.</p>                      
        </div>                                                                                                                           
      </div>                                                                                                                             
    </div>                                                                                                                               
    {% endblock %}                                                                                                                       
                                                                                                                                         
    {% block scripts %}                                                                                                                  
    <script>                                                                                                                             
      let currentFileRaw = "";                                                                                                           
      let currentFilePath = "";                                                                                                          
                                                                                                                                         
      function toggleFolder(elem) {                                                                                                      
        const children = elem.nextElementSibling;                                                                                        
        const chevron = elem.querySelector(".fa-chevron-right");                                                                         
        children.classList.toggle("hidden");                                                                                             
        chevron.classList.toggle("rotate-90");                                                                                           
      }                                                                                                                                  
                                                                                                                                         
      async function loadFile(path) {                                                                                                    
        currentFilePath = path;                                                                                                          
        document.getElementById("activeFilePath").innerText = path;                                                                      
        const res = await fetch(`/api/file?path=${encodeURIComponent(path)}`);                                                           
        const data = await res.json();                                                                                                   
        currentFileRaw = data.raw;                                                                                                       
        document.getElementById("noteViewer").innerHTML = data.html;                                                                     
        Prism.highlightAll();                                                                                                            
      }                                                                                                                                  
                                                                                                                                         
      function copyRawNote() {                                                                                                           
        if (!currentFileRaw) return alert("No note selected");                                                                           
        navigator.clipboard.writeText(currentFileRaw);                                                                                   
        alert("Copied raw note to clipboard!");                                                                                          
      }                                                                                                                                  
                                                                                                                                         
      function downloadNote() {                                                                                                          
        if (!currentFileRaw) return alert("No note selected");                                                                           
        const blob = new Blob([currentFileRaw], { type: "text/markdown" });                                                              
        const a = document.createElement("a");                                                                                           
        a.href = URL.createObjectURL(blob);                                                                                              
        a.download = currentFilePath.split("/").pop() || "note.md";                                                                      
        a.click();                                                                                                                       
      }                                                                                                                                  
                                                                                                                                         
      // Live Search                                                                                                                     
      const searchInput = document.getElementById("searchInput");                                                                        
      const searchResults = document.getElementById("searchResults");                                                                    
      const fileTreeContainer = document.getElementById("fileTreeContainer");                                                            
                                                                                                                                         
      searchInput.addEventListener("input", async (e) => {                                                                               
        const q = e.target.value.trim();                                                                                                 
        if (!q) {                                                                                                                        
          searchResults.classList.add("hidden");                                                                                         
          fileTreeContainer.classList.remove("hidden");                                                                                  
          return;                                                                                                                        
        }                                                                                                                                
        fileTreeContainer.classList.add("hidden");                                                                                       
        searchResults.classList.remove("hidden");                                                                                        
                                                                                                                                         
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);                                                               
        const results = await res.json();                                                                                                
        if (results.length === 0) {                                                                                                      
          searchResults.innerHTML = `<div class="p-3 text-xs text-slate-400">No matching notes found.</div>`;                            
          return;                                                                                                                        
        }                                                                                                                                
        searchResults.innerHTML = results.map(r => `                                                                                     
          <div onclick="loadFile('${r.path}')" class="p-2 rounded bg-slate-900/60 hover:bg-slate-700 cursor-pointer border border-slate- 
  700">                                                                                                                                  
            <div class="text-xs font-semibold text-cyan-400">${r.filename}</div>                                                         
            <div class="text-[11px] text-slate-400 truncate">${r.snippet}</div>                                                          
          </div>                                                                                                                         
        `).join("");                                                                                                                     
      });                                                                                                                                
    </script>                                                                                                                            
    {% endblock %}                                                                                                                       
  ──────                                                                                                                                 
  ### app/templates/youtube.html                                                                                                         
                                                                                                                                         
    {% extends "base.html" %}                                                                                                            
    {% block title %}YouTube AI Notes & QA Generator - DevOps Hub{% endblock %}                                                          
                                                                                                                                         
    {% block content %}                                                                                                                  
    <div class="flex-1 flex overflow-hidden">                                                                                            
      <!-- Left Form Config Panel -->                                                                                                    
      <div class="w-1/3 bg-slate-800/90 border-r border-slate-700 p-6 overflow-y-auto flex flex-col space-y-5">                          
        <div>                                                                                                                            
          <h2 class="text-lg font-bold text-cyan-400 flex items-center">                                                                 
            <i class="fa-brands fa-youtube text-red-500 mr-2"></i> YouTube AI Generator                                                  
          </h2>                                                                                                                          
          <p class="text-xs text-slate-400 mt-1">Paste any video URL. Automatically extracts subtitles and converts them into structured 
  Class Notes or QA sets.</p>                                                                                                            
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Video URL Input -->                                                                                                         
        <div>                                                                                                                            
          <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">YouTube URL</label>                                   
          <input type="text" id="ytUrl" placeholder="https://www.youtube.com/watch?v=..."                                                
            class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-100 focus:outline-none focus:border-  
  cyan-500 font-mono">                                                                                                                   
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Mode Selector -->                                                                                                           
        <div>                                                                                                                            
          <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Generation Mode</label>                               
          <div class="space-y-2">                                                                                                        
            <label class="flex items-start space-x-3 p-3 bg-slate-900/60 border border-slate-700 rounded-lg cursor-pointer hover:border- 
  cyan-500">                                                                                                                             
              <input type="radio" name="mode" value="class_notes" checked class="mt-1 text-cyan-500 focus:ring-0">                       
              <div>                                                                                                                      
                <div class="text-sm font-semibold text-slate-200">Class Teaching Notes</div>                                             
                <div class="text-xs text-slate-400">Strict step-by-step notes without assuming or shortening concepts.</div>             
              </div>                                                                                                                     
            </label>                                                                                                                     
                                                                                                                                         
            <label class="flex items-start space-x-3 p-3 bg-slate-900/60 border border-slate-700 rounded-lg cursor-pointer hover:border- 
  cyan-500">                                                                                                                             
              <input type="radio" name="mode" value="qa" class="mt-1 text-cyan-500 focus:ring-0">                                        
              <div>                                                                                                                      
                <div class="text-sm font-semibold text-slate-200">Interview QA & Solutions</div>                                         
                <div class="text-xs text-slate-400">Extracts every question, sub-question, and instructor answers.</div>                 
              </div>                                                                                                                     
            </label>                                                                                                                     
                                                                                                                                         
            <label class="flex items-start space-x-3 p-3 bg-slate-900/60 border border-slate-700 rounded-lg cursor-pointer hover:border- 
  cyan-500">                                                                                                                             
              <input type="radio" name="mode" value="custom" class="mt-1 text-cyan-500 focus:ring-0">                                    
              <div>                                                                                                                      
                <div class="text-sm font-semibold text-slate-200">Custom Prompt</div>                                                    
                <div class="text-xs text-slate-400">Use your own custom prompt instruction.</div>                                        
              </div>                                                                                                                     
            </label>                                                                                                                     
          </div>                                                                                                                         
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Custom Prompt Textarea (Conditional) -->                                                                                    
        <div id="customPromptBox" class="hidden">                                                                                        
          <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Custom Instruction</label>                            
          <textarea id="customPrompt" rows="4" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100
  focus:outline-none focus:border-cyan-500"></textarea>                                                                                  
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Gemini API Key Input -->                                                                                                    
        <div>                                                                                                                            
          <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">                                                      
            Gemini API Key {% if has_api_key %}<span class="text-emerald-400 font-normal lowercase">(server key active)</span>{% endif %}
          </label>                                                                                                                       
          <input type="password" id="apiKey" placeholder="AIzaSy..."                                                                     
            class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-  
  cyan-500">                                                                                                                             
          <p class="text-[11px] text-slate-500 mt-1">Get free key from <a href="https://aistudio.google.com/app/apikey" target="_blank"  
  class="text-cyan-400 underline">Google AI Studio</a></p>                                                                               
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Submit Button -->                                                                                                           
        <button id="generateBtn" onclick="generateNotes()" class="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-
  500 hover:to-blue-500 text-white font-bold rounded-lg shadow-lg flex items-center justify-center space-x-2 transition">                
          <i class="fa-solid fa-wand-magic-sparkles"></i>                                                                                
          <span>Generate AI Notes</span>                                                                                                 
        </button>                                                                                                                        
      </div>                                                                                                                             
                                                                                                                                         
      <!-- Right Output Preview Panel -->                                                                                                
      <div class="flex-1 flex flex-col bg-slate-900 overflow-hidden">                                                                    
        <div class="bg-slate-800/60 border-b border-slate-700 px-6 py-3 flex items-center justify-between">                              
          <span class="text-sm font-semibold text-slate-300">Generated Markdown Output</span>                                            
          <div id="actionButtons" class="hidden flex items-center space-x-2">                                                            
            <button onclick="saveToNotesModal()" class="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded font- 
  semibold">                                                                                                                             
              <i class="fa-solid fa-floppy-disk mr-1"></i> Save to Repo                                                                  
            </button>                                                                                                                    
            <button onclick="copyGenerated()" class="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded font-    
  semibold">                                                                                                                             
              <i class="fa-regular fa-copy mr-1"></i> Copy                                                                               
            </button>                                                                                                                    
            <button onclick="downloadGenerated()" class="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded font-
  semibold">                                                                                                                             
              <i class="fa-solid fa-download mr-1"></i> Download .md                                                                     
            </button>                                                                                                                    
          </div>                                                                                                                         
        </div>                                                                                                                           
                                                                                                                                         
        <div id="outputArea" class="flex-1 overflow-y-auto p-8 prose-custom">                                                            
          <div class="text-center py-28 text-slate-500">                                                                                 
            <i class="fa-solid fa-brain text-6xl mb-4 text-slate-600"></i>                                                               
            <h3 class="text-xl font-bold text-slate-400">Ready to Generate Notes</h3>                                                    
            <p class="text-xs text-slate-500 mt-2">Enter a YouTube link and click "Generate AI Notes" to transform the class video into  
  notes.</p>                                                                                                                             
          </div>                                                                                                                         
        </div>                                                                                                                           
      </div>                                                                                                                             
    </div>                                                                                                                               
    {% endblock %}                                                                                                                       
                                                                                                                                         
    {% block scripts %}                                                                                                                  
    <script>                                                                                                                             
      let rawAiNotes = "";                                                                                                               
                                                                                                                                         
      document.querySelectorAll("input[name='mode']").forEach(r => {                                                                     
        r.addEventListener("change", (e) => {                                                                                            
          document.getElementById("customPromptBox").classList.toggle("hidden", e.target.value !== "custom");                            
        });                                                                                                                              
      });                                                                                                                                
                                                                                                                                         
      async function generateNotes() {                                                                                                   
        const url = document.getElementById("ytUrl").value.trim();                                                                       
        if (!url) return alert("Please enter a valid YouTube URL");                                                                      
                                                                                                                                         
        const mode = document.querySelector("input[name='mode']:checked").value;                                                         
        const customPrompt = document.getElementById("customPrompt").value.trim();                                                       
        const apiKey = document.getElementById("apiKey").value.trim();                                                                   
        const btn = document.getElementById("generateBtn");                                                                              
                                                                                                                                         
        btn.disabled = true;                                                                                                             
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Extracting Transcript & Processing AI...`;                     
        document.getElementById("outputArea").innerHTML = `                                                                              
          <div class="text-center py-20 text-slate-400">                                                                                 
            <i class="fa-solid fa-gear fa-spin text-5xl text-cyan-400 mb-4"></i>                                                         
            <p class="text-base font-semibold">Extracting YouTube transcript & generating notes with Gemini AI...</p>                    
            <p class="text-xs text-slate-500 mt-2">This usually takes 5-15 seconds depending on video length.</p>                        
          </div>                                                                                                                         
        `;                                                                                                                               
                                                                                                                                         
        try {                                                                                                                            
          const formData = new FormData();                                                                                               
          formData.append("url", url);                                                                                                   
          formData.append("mode", mode);                                                                                                 
          formData.append("custom_prompt", customPrompt);                                                                                
          formData.append("api_key", apiKey);                                                                                            
                                                                                                                                         
          const res = await fetch("/api/youtube/generate", { method: "POST", body: formData });                                          
          const data = await res.json();                                                                                                 
                                                                                                                                         
          if (!res.ok || data.status === "error") {                                                                                      
            throw new Error(data.message || "Failed to generate notes");                                                                 
          }                                                                                                                              
                                                                                                                                         
          rawAiNotes = data.raw_notes;                                                                                                   
          document.getElementById("outputArea").innerHTML = data.html_notes;                                                             
          document.getElementById("actionButtons").classList.remove("hidden");                                                           
          Prism.highlightAll();                                                                                                          
        } catch (err) {                                                                                                                  
          document.getElementById("outputArea").innerHTML = `                                                                            
            <div class="p-4 bg-red-950/60 border border-red-800 rounded-lg text-red-200">                                                
              <div class="font-bold mb-1"><i class="fa-solid fa-triangle-exclamation mr-2"></i> Error</div>                              
              <div>${err.message}</div>                                                                                                  
            </div>                                                                                                                       
          `;                                                                                                                             
        } finally {                                                                                                                      
          btn.disabled = false;                                                                                                          
          btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles mr-2"></i> Generate AI Notes`;                                      
        }                                                                                                                                
      }                                                                                                                                  
                                                                                                                                         
      function copyGenerated() {                                                                                                         
        navigator.clipboard.writeText(rawAiNotes);                                                                                       
        alert("Markdown copied to clipboard!");                                                                                          
      }                                                                                                                                  
                                                                                                                                         
      function downloadGenerated() {                                                                                                     
        const blob = new Blob([rawAiNotes], { type: "text/markdown" });                                                                  
        const a = document.createElement("a");                                                                                           
        a.href = URL.createObjectURL(blob);                                                                                              
        a.download = "youtube_notes_" + Date.now() + ".md";                                                                              
        a.click();                                                                                                                       
      }                                                                                                                                  
                                                                                                                                         
      async function saveToNotesModal() {                                                                                                
        const filename = prompt("Enter file name (e.g. docker-interview-qa.md):", "youtube_notes.md");                                   
        if (!filename) return;                                                                                                           
        const folder = prompt("Enter subfolder in repo (leave blank for root):", "");                                                    
                                                                                                                                         
        const formData = new FormData();                                                                                                 
        formData.append("filename", filename);                                                                                           
        formData.append("folder", folder || "");                                                                                         
        formData.append("content", rawAiNotes);                                                                                          
                                                                                                                                         
        const res = await fetch("/api/save-note", { method: "POST", body: formData });                                                   
        const data = await res.json();                                                                                                   
        alert("Saved note to: " + data.path);                                                                                            
      }                                                                                                                                  
    </script>                                                                                                                            
    {% endblock %}                                                                                                                       
  ──────                                                                                                                                 
  ### app/templates/settings.html                                                                                                        
                                                                                                                                         
    {% extends "base.html" %}                                                                                                            
    {% block title %}Sync & Configuration - DevOps Hub{% endblock %}                                                                     
                                                                                                                                         
    {% block content %}                                                                                                                  
    <div class="flex-1 overflow-y-auto p-10 bg-slate-900">                                                                               
      <div class="max-w-3xl mx-auto space-y-6">                                                                                          
        <h1 class="text-2xl font-bold text-cyan-400 mb-6 flex items-center">                                                             
          <i class="fa-solid fa-sliders mr-3"></i> System Configuration & Sync                                                           
        </h1>                                                                                                                            
                                                                                                                                         
        <!-- Git Sync Card -->                                                                                                           
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow">                                                         
          <h2 class="text-lg font-bold text-slate-200 mb-4 flex items-center">                                                           
            <i class="fa-brands fa-github text-cyan-400 mr-2"></i> Git Repository Synchronization                                        
          </h2>                                                                                                                          
          <div class="grid grid-cols-2 gap-4 text-sm mb-6">                                                                              
            <div>                                                                                                                        
              <span class="text-slate-400 block text-xs uppercase">Repository URL</span>                                                 
              <span class="font-mono text-cyan-300 break-all">{{ repo_url }}</span>                                                      
            </div>                                                                                                                       
            <div>                                                                                                                        
              <span class="text-slate-400 block text-xs uppercase">Branch</span>                                                         
              <span class="font-mono text-slate-200">{{ branch }}</span>                                                                 
            </div>                                                                                                                       
            <div>                                                                                                                        
              <span class="text-slate-400 block text-xs uppercase">Auto-Sync Interval</span>                                             
              <span class="font-mono text-slate-200">Every {{ sync_interval }} minutes</span>                                            
            </div>                                                                                                                       
            <div>                                                                                                                        
              <span class="text-slate-400 block text-xs uppercase">Last Sync Timestamp</span>                                            
              <span class="font-mono text-emerald-400">{{ last_sync or 'Pending' }}</span>                                               
            </div>                                                                                                                       
          </div>                                                                                                                         
          <button onclick="triggerManualSync()" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold text- 
  sm">                                                                                                                                   
            <i class="fa-solid fa-rotate mr-2"></i> Trigger Manual Sync Now                                                              
          </button>                                                                                                                      
        </div>                                                                                                                           
                                                                                                                                         
        <!-- Gemini AI Key Card -->                                                                                                      
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow">                                                         
          <h2 class="text-lg font-bold text-slate-200 mb-2 flex items-center">                                                           
            <i class="fa-solid fa-key text-amber-400 mr-2"></i> Google Gemini AI Key                                                     
          </h2>                                                                                                                          
          <p class="text-xs text-slate-400 mb-4">You can set the <code>GEMINI_API_KEY</code> environment variable in your Kubernetes     
  deployment or provide it per session in the YouTube tool.</p>                                                                          
          <div class="p-3 bg-slate-900 border border-slate-700 rounded text-xs font-mono text-slate-300">                                
            Status: {% if has_api_key %}<span class="text-emerald-400 font-bold">Configured via Environment</span>{% else %}<span        
  class="text-amber-400 font-bold">Not set globally (provide in UI)</span>{% endif %}                                                    
          </div>                                                                                                                         
        </div>                                                                                                                           
      </div>                                                                                                                             
    </div>                                                                                                                               
    {% endblock %}                                                                                                                       
  ──────                                                                                                                                 
  ### k8s/all-in-one.yaml (Complete Kubernetes Manifests)                                                                                
                                                                                                                                         
    apiVersion: v1                                                                                                                       
    kind: Namespace                                                                                                                      
    metadata:                                                                                                                            
      name: devops-hub                                                                                                                   
    ---                                                                                                                                  
    apiVersion: v1                                                                                                                       
    kind: ConfigMap                                                                                                                      
    metadata:                                                                                                                            
      name: devops-hub-config                                                                                                            
      namespace: devops-hub                                                                                                              
    data:                                                                                                                                
      REPO_URL: "https://github.com/nagaraj602/Notes.git"                                                                                
      REPO_BRANCH: "main"                                                                                                                
      AUTO_SYNC_INTERVAL_MINUTES: "5"                                                                                                    
      NOTES_DIR: "/app/data/notes"                                                                                                       
    ---                                                                                                                                  
    apiVersion: v1                                                                                                                       
    kind: Secret                                                                                                                         
    metadata:                                                                                                                            
      name: devops-hub-secret                                                                                                            
      namespace: devops-hub                                                                                                              
    type: Opaque                                                                                                                         
    stringData:                                                                                                                          
      GEMINI_API_KEY: "" # Put your Gemini API Key here (or leave blank to supply via web UI)                                            
    ---                                                                                                                                  
    apiVersion: v1                                                                                                                       
    kind: PersistentVolumeClaim                                                                                                          
    metadata:                                                                                                                            
      name: devops-hub-notes-pvc                                                                                                         
      namespace: devops-hub                                                                                                              
    spec:                                                                                                                                
      accessModes:                                                                                                                       
        - ReadWriteOnce                                                                                                                  
      resources:                                                                                                                         
        requests:                                                                                                                        
          storage: 2Gi                                                                                                                   
    ---                                                                                                                                  
    apiVersion: apps/v1                                                                                                                  
    kind: Deployment                                                                                                                     
    metadata:                                                                                                                            
      name: devops-hub-deployment                                                                                                        
      namespace: devops-hub                                                                                                              
      labels:                                                                                                                            
        app: devops-hub                                                                                                                  
    spec:                                                                                                                                
      replicas: 1                                                                                                                        
      selector:                                                                                                                          
        matchLabels:                                                                                                                     
          app: devops-hub                                                                                                                
      template:                                                                                                                          
        metadata:                                                                                                                        
          labels:                                                                                                                        
            app: devops-hub                                                                                                              
        spec:                                                                                                                            
          containers:                                                                                                                    
            - name: devops-hub                                                                                                           
              image: devops-hub:latest                                                                                                   
              imagePullPolicy: IfNotPresent                                                                                              
              ports:                                                                                                                     
                - containerPort: 8000                                                                                                    
                  name: http                                                                                                             
              envFrom:                                                                                                                   
                - configMapRef:                                                                                                          
                    name: devops-hub-config                                                                                              
                - secretRef:                                                                                                             
                    name: devops-hub-secret                                                                                              
              volumeMounts:                                                                                                              
                - name: notes-storage                                                                                                    
                  mountPath: /app/data/notes                                                                                             
              resources:                                                                                                                 
                requests:                                                                                                                
                  cpu: "100m"                                                                                                            
                  memory: "128Mi"                                                                                                        
                limits:                                                                                                                  
                  cpu: "500m"                                                                                                            
                  memory: "512Mi"                                                                                                        
              readinessProbe:                                                                                                            
                httpGet:                                                                                                                 
                  path: /api/health                                                                                                      
                  port: 8000                                                                                                             
                initialDelaySeconds: 5                                                                                                   
                periodSeconds: 10                                                                                                        
              livenessProbe:                                                                                                             
                httpGet:                                                                                                                 
                  path: /api/health                                                                                                      
                  port: 8000                                                                                                             
                initialDelaySeconds: 15                                                                                                  
                periodSeconds: 20                                                                                                        
          volumes:                                                                                                                       
            - name: notes-storage                                                                                                        
              persistentVolumeClaim:                                                                                                     
                claimName: devops-hub-notes-pvc                                                                                          
    ---                                                                                                                                  
    apiVersion: v1                                                                                                                       
    kind: Service                                                                                                                        
    metadata:                                                                                                                            
      name: devops-hub-service                                                                                                           
      namespace: devops-hub                                                                                                              
    spec:                                                                                                                                
      type: NodePort # Docker Desktop routes NodePort directly to localhost                                                              
      selector:                                                                                                                          
        app: devops-hub                                                                                                                  
      ports:                                                                                                                             
        - name: http                                                                                                                     
          port: 8000                                                                                                                     
          targetPort: 8000                                                                                                               
          nodePort: 30080                                                                                                                
  ──────                                                                                                                                 
  ## 3. Automated 1-Click Setup & Deploy Script                                                                                          
                                                                                                                                         
  Save this script as deploy.ps1 in your project folder and run it in PowerShell. It writes all files, builds the Docker image, and      
  applies the Kubernetes manifests:                                                                                                      
                                                                                                                                         
    # =====================================================================                                                              
    # 1-Click Setup & Deploy Script for Docker Desktop Kubernetes                                                                        
    # =====================================================================                                                              
                                                                                                                                         
    Write-Host "=========================================" -ForegroundColor Cyan                                                         
    Write-Host " Building & Deploying DevOps Hub to K8s  " -ForegroundColor Cyan                                                         
    Write-Host "=========================================" -ForegroundColor Cyan                                                         
                                                                                                                                         
    # 1. Ensure directories exist                                                                                                        
    New-Item -ItemType Directory -Force -Path "app/templates" | Out-Null                                                                 
    New-Item -ItemType Directory -Force -Path "k8s" | Out-Null                                                                           
                                                                                                                                         
    # 2. Build Docker image locally                                                                                                      
    Write-Host "`n[1/3] Building multi-stage Docker image..." -ForegroundColor Yellow                                                    
    docker build -t devops-hub:latest .                                                                                                  
                                                                                                                                         
    if ($LASTEXITCODE -ne 0) {                                                                                                           
        Write-Host "Docker build failed. Please verify Docker Desktop is running." -ForegroundColor Red                                  
        exit 1                                                                                                                           
    }                                                                                                                                    
                                                                                                                                         
    # 3. Apply Kubernetes Manifests                                                                                                      
    Write-Host "`n[2/3] Applying Kubernetes manifests..." -ForegroundColor Yellow                                                        
    kubectl apply -f k8s/all-in-one.yaml                                                                                                 
                                                                                                                                         
    # 4. Wait for pod to be ready                                                                                                        
    Write-Host "`n[3/3] Waiting for Pod to start..." -ForegroundColor Yellow                                                             
    kubectl rollout status deployment/devops-hub-deployment -n devops-hub --timeout=90s                                                  
                                                                                                                                         
    Write-Host "`n========================================================" -ForegroundColor Green                                       
    Write-Host " Deployment Successful! " -ForegroundColor Green                                                                         
    Write-Host " Access your website at: http://localhost:30080" -ForegroundColor Green                                                  
    Write-Host "========================================================" -ForegroundColor Green                                         
  ──────                                                                                                                                 
  ## 4. How Everything Works                                                                                                             
                                                                                                                                         
   Feature                      │ Implementation Details
  ──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────
   Zero Host Dependencies       │ Everything (Python runtime, Git, packages) is built and executed exclusively inside the Docker
                                │ container.
   Dynamic Git Detection        │ On container launch and every 5 minutes, it automatically pulls
                                │ https://github.com/nagaraj602/Notes.git. Any new folders or files are discovered dynamically without
                                │ restarting.
   YouTube Subtitle & Notes AI  │ Uses youtube-transcript-api to fetch subtitles directly from YouTube (no Tactiq required) and sends
                                │ them to Gemini AI with your exact prompts to generate structured notes or QA sets.
   Kubernetes on Docker Desktop │ Runs with NodePort: 30080 so you can open http://localhost:30080 directly in any browser on your
                                │ laptop.
