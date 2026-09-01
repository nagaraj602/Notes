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