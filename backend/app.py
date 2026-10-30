"""FastAPI backend: serves the evaluation API and the static dashboard."""
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional

# Ensure project root is importable (needed on Vercel)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from evaluator import report, storage
from evaluator.dataset import load_tasks, public_view
from evaluator.runner import evaluate_code

app = FastAPI(title="CodeEval AI", version="1.0.0")
TASKS = load_tasks()
BY_ID = {t["id"]: t for t in TASKS}
FRONTEND_DIR = ROOT / "public"


@contextmanager
def db():
    conn = storage.connect(os.environ.get("CODEEVAL_DB") or None)
    try:
        yield conn
    finally:
        conn.close()


class EvaluateRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(default="", max_length=100)
    task_id: str
    code: str = Field(min_length=1, max_length=50000)
    run_index: int = Field(default=1, ge=1, le=1000)
    manual_review: Optional[Dict[str, float]] = None


@app.get("/api/tasks")
def list_tasks():
    return [public_view(t) for t in TASKS]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in BY_ID:
        raise HTTPException(404, "unknown task")
    return public_view(BY_ID[task_id])


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    if os.environ.get("VERCEL"):  # never run arbitrary submitted code on a public deployment
        raise HTTPException(403, "Evaluation is disabled on the public deployment. Run CodeEval AI locally.")
    task = BY_ID.get(req.task_id)
    if task is None:
        raise HTTPException(404, "unknown task")
    try:
        ev = evaluate_code(task, req.code, req.manual_review)
    except ValueError as e:
        raise HTTPException(422, str(e))
    with db() as conn:
        sid = storage.save_evaluation(conn, task, req.model_name.strip(), req.model_version.strip(),
                                      req.code, ev, req.run_index, source="manual")
    for t in ev["tests"]:  # do not leak hidden test data back to the caller
        if t["hidden"]:
            t["args_repr"] = t["expected_repr"] = t["actual_repr"] = None
    return {"submission_id": sid, **ev}


@app.get("/api/summary")
def get_summary(include_demo: bool = False):
    with db() as c:
        return storage.summary(c, len(TASKS), include_demo)


@app.get("/api/models")
def get_models(include_demo: bool = False):
    with db() as c:
        return storage.model_comparison(c, include_demo)


@app.get("/api/task-performance")
def get_task_perf(include_demo: bool = False):
    with db() as c:
        return storage.task_performance(c, TASKS, include_demo)


@app.get("/api/difficulty")
def get_difficulty(include_demo: bool = False):
    with db() as c:
        return storage.difficulty_performance(c, include_demo)


@app.get("/api/failures")
def get_failures(include_demo: bool = False, task_id: Optional[str] = None, model_name: Optional[str] = None):
    with db() as c:
        return report.failure_analysis(c, TASKS, include_demo, task_id=task_id, model_name=model_name)


@app.get("/api/submissions")
def get_submissions(include_demo: bool = False, limit: int = 100):
    with db() as c:
        return storage.list_submissions(c, include_demo, limit=limit)


def _page(name: str):
    f = FRONTEND_DIR / name
    if not f.exists():
        raise HTTPException(404, f"{name} not found in public/")
    return FileResponse(f)


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
def serve_root():
    return _page("index.html")


@app.get("/failures", include_in_schema=False)
@app.get("/failures.html", include_in_schema=False)
def serve_failures():
    return _page("failures.html")


@app.get("/submit", include_in_schema=False)
@app.get("/submit.html", include_in_schema=False)
def serve_submit():
    return _page("submit.html")


# Static assets (app.js, style.css). Mounted last so the routes above win.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")