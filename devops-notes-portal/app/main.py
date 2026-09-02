import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import (
    REPOS, AUTO_SYNC_INTERVAL_MINUTES,
    NOTES_DIR
)
from app.git_sync import git_manager
from app.markdown_engine import render_markdown
from app.database import (
    init_db, get_or_create_user, save_calculation_history,
    get_user_history, clear_user_history, save_vpc_project,
    get_user_vpc_projects, delete_vpc_project
)
from app.cidr_engine import (
    calculate_cidr_details, find_next_available_subnet,
    split_subnet, merge_subnets, validate_network,
    get_cloud_comparison, generate_terraform_hcl, get_generated_subnets, CLOUD_SPECS
)
from app.interview_hub import interview_manager, CATEGORIES

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
    # Initialize SQLite Database
    init_db()
    # Initial sync on container boot
    git_manager.sync()
    # Start periodic sync worker
    asyncio.create_task(auto_sync_worker())
    yield

app = FastAPI(title="DevOps Knowledge Hub", lifespan=lifespan)

# Templates & Static Files
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon():
    fav_path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404)

# --- WEB ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    repo_trees = git_manager.get_file_tree()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "repo_trees": repo_trees,
            "tree": repo_trees,
            "repos": git_manager.repos,
            "last_sync": git_manager.last_sync_time,
            "sync_status": git_manager.sync_status
        }
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "repos": git_manager.repos,
            "repo_statuses": git_manager.repo_statuses,
            "sync_interval": AUTO_SYNC_INTERVAL_MINUTES,
            "last_sync": git_manager.last_sync_time,
            "sync_status": git_manager.sync_status
        }
    )

@app.get("/interviews", response_class=HTMLResponse)
async def interviews_page(request: Request):
    stats = interview_manager.get_stats()
    return templates.TemplateResponse(
        request=request,
        name="interviews.html",
        context={
            "stats": stats,
            "categories": CATEGORIES,
            "last_sync": git_manager.last_sync_time,
            "sync_status": git_manager.sync_status
        }
    )

# --- API ENDPOINTS ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "last_sync": git_manager.last_sync_time}

@app.post("/api/sync")
async def trigger_sync():
    result = git_manager.sync()
    return JSONResponse(content=result)

from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse, RedirectResponse

@app.get("/raw/{file_path:path}")
async def get_raw_asset(file_path: str):
    """Serves images, diagrams, and binary assets from the notes repositories."""
    normalized = os.path.normpath(file_path).lstrip("/\\")
    safe_path = os.path.abspath(os.path.join(NOTES_DIR, normalized))
    if not safe_path.startswith(os.path.abspath(NOTES_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(safe_path)

@app.get("/api/tree")
async def get_tree():
    return JSONResponse(content=git_manager.get_file_tree())

@app.get("/api/file")
async def get_file_content(path: str):
    normalized = os.path.normpath(path).lstrip("/\\").replace("\\", "/")
    safe_path = os.path.abspath(os.path.join(NOTES_DIR, normalized))
    
    # If not found directly, search across repo folders
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        for repo_info in git_manager.repos:
            candidate = os.path.abspath(os.path.join(NOTES_DIR, repo_info["folder"], normalized))
            if os.path.exists(candidate) and os.path.isfile(candidate):
                safe_path = candidate
                normalized = os.path.relpath(candidate, NOTES_DIR).replace("\\", "/")
                break

    if not safe_path.startswith(os.path.abspath(NOTES_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    try:
        with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    ext = os.path.splitext(safe_path)[1].lower()
    is_markdown = ext in [".md", ".markdown"]
    rendered_html = render_markdown(raw_content, file_rel_path=normalized) if is_markdown else f"<pre><code>{raw_content}</code></pre>"

    return JSONResponse({
        "path": normalized,
        "filename": os.path.basename(normalized),
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

@app.post("/api/save-note")
async def save_note(
    filename: str = Form(...),
    folder: str = Form(""),
    content: str = Form(...)
):
    """Allows saving custom notes directly into the notes directory."""
    if not filename.endswith(".md"):
        filename += ".md"
    target_folder = os.path.abspath(os.path.join(NOTES_DIR, folder))
    if not target_folder.startswith(os.path.abspath(NOTES_DIR)):
        raise HTTPException(status_code=403, detail="Invalid folder path")
        
    return JSONResponse({"status": "success", "path": os.path.relpath(file_path, NOTES_DIR)})

# ==============================================================================
# CLOUD CIDR & NETWORK ARCHITECT ROUTES & API
# ==============================================================================

@app.get("/cidr", response_class=HTMLResponse)
async def cidr_planner_page(request: Request):
    """Renders the Production-Grade Stateful Cloud CIDR Visual Planner."""
    return templates.TemplateResponse(
        request=request,
        name="cidr.html",
        context={
            "cloud_specs": CLOUD_SPECS,
            "default_cloud": "aws"
        }
    )

class CalculateRequest(BaseModel):
    cidr: str
    cloud_provider: str = "aws"
    username: Optional[str] = "default"
    save_history: bool = False

class AutoSubnetRequest(BaseModel):
    parent_cidr: str
    existing_subnets: List[str] = []
    target_prefix: int

class SplitSubnetRequest(BaseModel):
    cidr: str
    target_prefix: Optional[int] = None

class MergeSubnetRequest(BaseModel):
    subnets: List[str]

class ValidateRequest(BaseModel):
    vpc_cidr: str
    subnets: List[Dict[str, Any]] = []
    cloud_provider: str = "aws"

class SaveProjectRequest(BaseModel):
    username: str
    project_name: str
    vpc_cidr: str
    cloud_provider: str
    subnets: List[Dict[str, Any]]

class UserLoginRequest(BaseModel):
    username: str

@app.post("/api/cidr/calculate")
async def api_calculate_cidr(req: CalculateRequest):
    try:
        details = calculate_cidr_details(req.cidr, req.cloud_provider)
        if req.save_history and req.username:
            save_calculation_history(
                username=req.username,
                cidr=details["cidr"],
                cloud_provider=req.cloud_provider,
                total_ips=details["total_ips"],
                usable_ips=details["usable_ips"],
                subnet_mask=details["netmask"]
            )
        return JSONResponse(details)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class GenerateSubnetsRequest(BaseModel):
    parent_cidr: str
    target_prefix: int
    cloud_provider: str = "aws"
    limit: int = 100

@app.post("/api/cidr/generate-subnets")
async def api_generate_subnets(req: GenerateSubnetsRequest):
    try:
        data = get_generated_subnets(req.parent_cidr, req.target_prefix, req.cloud_provider, req.limit)
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cidr/auto-subnet")
async def api_auto_subnet(req: AutoSubnetRequest):
    try:
        suggestion = find_next_available_subnet(req.parent_cidr, req.existing_subnets, req.target_prefix)
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"No available /{req.target_prefix} subnet remaining in {req.parent_cidr}")
        return JSONResponse(suggestion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cidr/split")
async def api_split_subnet(req: SplitSubnetRequest):
    try:
        subnets = split_subnet(req.cidr, req.target_prefix)
        return JSONResponse(subnets)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cidr/merge")
async def api_merge_subnets(req: MergeSubnetRequest):
    try:
        result = merge_subnets(req.subnets)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cidr/validate")
async def api_validate_network(req: ValidateRequest):
    try:
        issues = validate_network(req.vpc_cidr, req.subnets, req.cloud_provider)
        return JSONResponse({"valid": len([i for i in issues if i["level"] == "error"]) == 0, "issues": issues})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/cidr/comparison")
async def api_cloud_comparison(cidr: str = "10.0.0.0/16"):
    try:
        comp = get_cloud_comparison(cidr)
        return JSONResponse(comp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cidr/terraform")
async def api_generate_terraform(req: SaveProjectRequest):
    try:
        hcl = generate_terraform_hcl(req.project_name, req.vpc_cidr, req.subnets, req.cloud_provider)
        return PlainTextResponse(hcl)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User & State Persistence APIs
@app.post("/api/user/login")
async def api_user_login(req: UserLoginRequest):
    try:
        user = get_or_create_user(req.username)
        history = get_user_history(req.username)
        projects = get_user_vpc_projects(req.username)
        return JSONResponse({"user": user, "history": history, "projects": projects})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/history")
async def api_get_history(username: str):
    history = get_user_history(username)
    return JSONResponse(history)

@app.delete("/api/user/history")
async def api_clear_history(username: str):
    clear_user_history(username)
    return JSONResponse({"status": "cleared"})

@app.post("/api/vpc/project")
async def api_save_vpc_project(req: SaveProjectRequest):
    try:
        subnets_json = json.dumps(req.subnets)
        proj_id = save_vpc_project(req.username, req.project_name, req.vpc_cidr, req.cloud_provider, subnets_json)
        return JSONResponse({"status": "saved", "project_id": proj_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vpc/projects")
async def api_get_vpc_projects(username: str):
    projects = get_user_vpc_projects(username)
    # Parse subnets_json
    for p in projects:
        try:
            p["subnets"] = json.loads(p["subnets_json"])
        except Exception:
            p["subnets"] = []
    return JSONResponse(projects)

@app.delete("/api/vpc/project/{project_id}")
async def api_delete_vpc_project(project_id: int, username: str):
    delete_vpc_project(project_id, username)
    return JSONResponse({"status": "deleted"})

# --- INTERVIEW HUB APIS ---

class ScheduleCreateRequest(BaseModel):
    company: str
    role: Optional[str] = "DevOps Engineer"
    round: Optional[str] = "Technical Round"
    date: str
    time: Optional[str] = "10:00"
    start_time: Optional[str] = "10:00"
    end_time: Optional[str] = "11:00"
    status: Optional[str] = "scheduled"
    meeting_link: Optional[str] = ""
    notes: Optional[str] = ""

class ScheduleUpdateRequest(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    round: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    questions_uploaded: Optional[bool] = None

class QuestionCreateRequest(BaseModel):
    company: str
    round: Optional[str] = ""
    date: Optional[str] = ""
    question: str
    answer: str
    categories: Optional[List[str]] = []

class QuestionUpdateRequest(BaseModel):
    company: Optional[str] = None
    round: Optional[str] = None
    date: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    categories: Optional[List[str]] = None

class DetectCategoriesRequest(BaseModel):
    text: str

class BulkQuestionItem(BaseModel):
    question: str
    answer: str
    categories: Optional[List[str]] = []

class BulkQuestionsRequest(BaseModel):
    company: str
    round: Optional[str] = ""
    date: Optional[str] = ""
    questions: List[BulkQuestionItem]

class FollowupActionRequest(BaseModel):
    schedule_id: str
    action: str # "skip", "cancel", "reschedule"
    new_date: Optional[str] = None
    new_time: Optional[str] = None

@app.get("/api/interviews/stats")
async def api_interview_stats():
    return JSONResponse(interview_manager.get_stats())

@app.get("/api/interviews/schedules")
async def api_get_schedules():
    return JSONResponse(interview_manager.get_schedules())

@app.post("/api/interviews/schedules")
async def api_add_schedule(req: ScheduleCreateRequest):
    item = interview_manager.add_schedule(req.dict())
    return JSONResponse({"status": "success", "schedule": item})

@app.put("/api/interviews/schedules/{sched_id}")
async def api_update_schedule(sched_id: str, req: ScheduleUpdateRequest):
    updated = interview_manager.update_schedule(sched_id, req.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return JSONResponse({"status": "success", "schedule": updated})

@app.delete("/api/interviews/schedules/{sched_id}")
async def api_delete_schedule(sched_id: str):
    success = interview_manager.delete_schedule(sched_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return JSONResponse({"status": "deleted"})

@app.get("/api/interviews/questions")
async def api_get_questions(q: Optional[str] = "", category: Optional[str] = "", company: Optional[str] = ""):
    questions = interview_manager.get_questions(query=q, category=category, company=company)
    return JSONResponse(questions)

@app.post("/api/interviews/questions")
async def api_add_question(req: QuestionCreateRequest):
    new_q = interview_manager.add_question(req.dict())
    return JSONResponse({"status": "success", "question": new_q})

@app.put("/api/interviews/questions/{q_id}")
async def api_update_question(q_id: str, req: QuestionUpdateRequest):
    updated = interview_manager.update_question(q_id, req.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Question not found")
    return JSONResponse({"status": "success", "question": updated})

@app.delete("/api/interviews/questions/{q_id}")
async def api_delete_question(q_id: str):
    success = interview_manager.delete_question(q_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return JSONResponse({"status": "deleted"})

@app.post("/api/interviews/autodetect-categories")
async def api_detect_categories(req: DetectCategoriesRequest):
    from app.interview_hub import detect_categories
    cats = detect_categories(req.text)
    return JSONResponse({"categories": cats})

@app.post("/api/interviews/questions/bulk")
async def api_add_bulk_questions(req: BulkQuestionsRequest):
    qa_list = [item.dict() for item in req.questions]
    count = interview_manager.add_bulk_questions(req.company, req.round or "", req.date or "", qa_list)
    return JSONResponse({"status": "success", "count": count})

@app.get("/api/interviews/pending-followups")
async def api_get_pending_followups():
    return JSONResponse(interview_manager.get_pending_followups())

@app.post("/api/interviews/dismiss-followup")
async def api_dismiss_followup(req: FollowupActionRequest):
    if req.action == "cancel":
        interview_manager.update_schedule(req.schedule_id, {"status": "cancelled"})
    elif req.action == "reschedule":
        interview_manager.update_schedule(req.schedule_id, {
            "status": "scheduled",
            "date": req.new_date or date.today().isoformat(),
            "time": req.new_time or "10:00"
        })
    elif req.action == "skip":
        interview_manager.update_schedule(req.schedule_id, {"status": "dismissed"})
    return JSONResponse({"status": "success", "action": req.action})