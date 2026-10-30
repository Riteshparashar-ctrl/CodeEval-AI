"""SQLite persistence and aggregate queries."""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Ensure ROOT is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "results" / "codeeval.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT NOT NULL, model_version TEXT NOT NULL DEFAULT '',
  task_id TEXT NOT NULL, difficulty TEXT NOT NULL, run_index INTEGER NOT NULL DEFAULT 1,
  source TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0, code TEXT NOT NULL, score REAL NOT NULL,
  breakdown TEXT NOT NULL, tests_passed INTEGER NOT NULL, tests_failed INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS test_results(
  id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  test_id TEXT, kind TEXT, passed INTEGER, category TEXT, status TEXT, args TEXT, expected TEXT, actual TEXT, note TEXT);
"""


def resolve_db_path(path=None) -> Path:
    """Resolve database path, handling serverless read-only filesystems (Vercel, AWS Lambda)."""
    if path:
        return Path(path)
    if os.environ.get("CODEEVAL_DB"):
        return Path(os.environ["CODEEVAL_DB"])

    is_serverless = bool(
        os.environ.get("VERCEL")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("LAMBDA_TASK_ROOT")
    )

    if is_serverless:
        tmp_db = Path(tempfile.gettempdir()) / "codeeval.db"
        if not tmp_db.exists() and DB_PATH.exists() and DB_PATH.stat().st_size > 0:
            try:
                shutil.copy2(str(DB_PATH), str(tmp_db))
            except Exception:
                pass
        return tmp_db

    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_file = DB_PATH.parent / ".perm_check"
        test_file.touch()
        test_file.unlink()
        return DB_PATH
    except (OSError, PermissionError):
        tmp_db = Path(tempfile.gettempdir()) / "codeeval.db"
        if not tmp_db.exists() and DB_PATH.exists() and DB_PATH.stat().st_size > 0:
            try:
                shutil.copy2(str(DB_PATH), str(tmp_db))
            except Exception:
                pass
        return tmp_db


def connect(path=None):
    target = resolve_db_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(target))
    except (OSError, sqlite3.OperationalError):
        conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn


def save_evaluation(conn, task, model_name, model_version, code, evaluation, run_index=1, source="manual", is_demo=False):
    cur = conn.execute(
        "INSERT INTO submissions(model_name,model_version,task_id,difficulty,run_index,source,is_demo,code,score,"
        "breakdown,tests_passed,tests_failed,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (model_name, model_version, task["id"], task["difficulty"], run_index, source, int(is_demo), code,
         evaluation["score"], json.dumps(evaluation["breakdown"]), evaluation["tests_passed"],
         evaluation["tests_failed"], datetime.now(timezone.utc).isoformat(timespec="seconds")))
    sid = cur.lastrowid
    conn.executemany(
        "INSERT INTO test_results(submission_id,test_id,kind,passed,category,status,args,expected,actual,note) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        [(sid, t["test_id"], t["kind"], int(t["passed"]), t["category"], t["status"], t["args_repr"],
          t["expected_repr"], t["actual_repr"], t["note"]) for t in evaluation["tests"]])
    conn.commit()
    return sid


def delete_demo(conn):
    conn.execute("DELETE FROM submissions WHERE is_demo=1")
    conn.commit()


def _f(include_demo, alias="s"):
    return "" if include_demo else f" AND {alias}.is_demo=0"


def _rows(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _r(v, n=2):
    return round(v, n) if v is not None else 0


def summary(conn, total_tasks, include_demo=False):
    r = conn.execute(
        "SELECT COUNT(*) n, AVG(score) a, SUM(CASE WHEN tests_failed=0 THEN 1 ELSE 0 END) ok, SUM(tests_passed) tp, "
        f"SUM(tests_failed) tf, SUM(is_demo) d FROM submissions s WHERE 1=1{_f(include_demo)}").fetchone()
    n = r["n"] or 0
    return {"total_tasks": total_tasks, "evaluated_responses": n, "overall_accuracy_pct": _r(100 * (r["ok"] or 0) / n) if n else 0,
            "average_score": _r(r["a"]), "tests_passed": r["tp"] or 0, "tests_failed": r["tf"] or 0,
            "demo_responses": r["d"] or 0}


def model_comparison(conn, include_demo=False):
    rows = _rows(conn,
        "SELECT model_name, model_version, is_demo, COUNT(*) attempts, COUNT(DISTINCT task_id) tasks_attempted, "
        "SUM(tests_passed) tests_passed, SUM(tests_failed) tests_failed, AVG(score) avg_score, "
        "100.0*SUM(CASE WHEN tests_failed=0 THEN 1 ELSE 0 END)/COUNT(*) accuracy_pct FROM submissions s "
        f"WHERE 1=1{_f(include_demo)} GROUP BY model_name, model_version, is_demo ORDER BY avg_score DESC")
    for row in rows:
        cats = _rows(conn,
            "SELECT r.category, COUNT(*) c FROM test_results r JOIN submissions s ON s.id=r.submission_id "
            "WHERE r.passed=0 AND s.model_name=? AND s.model_version=? AND s.is_demo=? GROUP BY r.category "
            "ORDER BY c DESC LIMIT 3", (row["model_name"], row["model_version"], row["is_demo"]))
        row["common_failures"] = [{"category": c["category"], "count": c["c"]} for c in cats]
        row["avg_score"], row["accuracy_pct"] = _r(row["avg_score"]), _r(row["accuracy_pct"])
        row["is_demo"] = bool(row["is_demo"])
    return rows


def task_performance(conn, tasks, include_demo=False):
    got = {r["task_id"]: r for r in _rows(conn,
        "SELECT task_id, COUNT(*) attempts, AVG(score) avg_score, SUM(tests_failed) tests_failed, "
        "100.0*SUM(CASE WHEN tests_failed=0 THEN 1 ELSE 0 END)/COUNT(*) accuracy_pct FROM submissions s "
        f"WHERE 1=1{_f(include_demo)} GROUP BY task_id")}
    out = []
    for t in tasks:
        r = got.get(t["id"], {})
        out.append({"task_id": t["id"], "title": t["title"], "difficulty": t["difficulty"],
                    "attempts": r.get("attempts", 0), "avg_score": _r(r.get("avg_score")),
                    "accuracy_pct": _r(r.get("accuracy_pct")), "tests_failed": r.get("tests_failed", 0)})
    return out


def difficulty_performance(conn, include_demo=False):
    rows = _rows(conn,
        "SELECT difficulty, COUNT(*) attempts, AVG(score) avg_score, SUM(tests_passed) tp, SUM(tests_failed) tf, "
        "100.0*SUM(CASE WHEN tests_failed=0 THEN 1 ELSE 0 END)/COUNT(*) accuracy_pct FROM submissions s "
        f"WHERE 1=1{_f(include_demo)} GROUP BY difficulty")
    by = {r["difficulty"]: r for r in rows}
    out = []
    for d in ("Easy", "Medium", "Hard"):
        r = by.get(d)
        tot = (r["tp"] + r["tf"]) if r else 0
        out.append({"difficulty": d, "attempts": r["attempts"] if r else 0, "avg_score": _r(r["avg_score"]) if r else 0,
                    "accuracy_pct": _r(r["accuracy_pct"]) if r else 0,
                    "failure_rate_pct": _r(100 * r["tf"] / tot) if r and tot else 0})
    return out


def list_submissions(conn, include_demo=False, limit=100):
    rows = _rows(conn, "SELECT id, model_name, model_version, task_id, run_index, source, is_demo, score, tests_passed, "
                       f"tests_failed, created_at FROM submissions s WHERE 1=1{_f(include_demo)} ORDER BY id DESC LIMIT ?", (limit,))
    for r in rows:
        r["is_demo"] = bool(r["is_demo"])
    return rows
