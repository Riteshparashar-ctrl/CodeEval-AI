"""Failure analysis computed from stored evaluation results (never from invented data)."""
import json
from pathlib import Path

from .dataset import ROOT
from .runner import ROOT_CAUSE
from .storage import _f, _rows, difficulty_performance, summary, task_performance

REPORT_DIR = ROOT / "reports"


def failure_analysis(conn, tasks, include_demo=False):
    f = _f(include_demo)
    base = "FROM test_results r JOIN submissions s ON s.id=r.submission_id WHERE r.passed=0" + f
    by_cat = {r["category"]: r["c"] for r in _rows(conn, f"SELECT r.category, COUNT(*) c {base} GROUP BY r.category ORDER BY c DESC")}
    by_kind = {r["kind"]: r["c"] for r in _rows(conn, f"SELECT r.kind, COUNT(*) c {base} GROUP BY r.kind ORDER BY c DESC")}
    root = {}
    for cat, c in by_cat.items():
        root[ROOT_CAUSE.get(cat, cat)] = root.get(ROOT_CAUSE.get(cat, cat), 0) + c
    tasks_ranked = []
    for t in task_performance(conn, tasks, include_demo):
        if t["attempts"]:
            subs = _rows(conn, f"SELECT COUNT(*) c FROM submissions s WHERE s.task_id=? AND s.tests_failed>0{f}", (t["task_id"],))[0]["c"]
            tasks_ranked.append({**t, "submissions_with_failures": subs, "failure_rate_pct": round(100 * subs / t["attempts"], 2)})
    tasks_ranked.sort(key=lambda x: (-x["failure_rate_pct"], -x["tests_failed"]))
    edge_cases = _rows(conn, "SELECT r.test_id, r.kind, r.note, COUNT(*) failures " + base +
                       " AND r.kind!='basic' GROUP BY r.test_id ORDER BY failures DESC, r.test_id LIMIT 15")
    examples = _rows(conn, "SELECT s.model_name, s.is_demo, s.task_id, r.test_id, r.kind, r.category, r.args, r.expected, r.actual " +
                     base + " GROUP BY r.test_id, r.category ORDER BY MAX(s.id) DESC LIMIT 10")
    for e in examples:
        e["is_demo"] = bool(e["is_demo"])
    diff = difficulty_performance(conn, include_demo)
    worst = max(diff, key=lambda d: d["failure_rate_pct"]) if any(d["attempts"] for d in diff) else None
    return {"summary": summary(conn, len(tasks), include_demo), "include_demo": include_demo, "by_category": by_cat,
            "by_kind": by_kind, "root_cause": root, "tasks_ranked": tasks_ranked, "edge_cases": edge_cases,
            "difficulty": diff, "hardest_difficulty": worst["difficulty"] if worst else None, "examples": examples}


def render_markdown(rep):
    s = rep["summary"]
    label = "INCLUDES DEMO DATA (synthetic, not model results)" if rep["include_demo"] else "measured results only (demo data excluded)"
    lines = ["# CodeEval AI - Failure Report", "", f"Scope: {label}. Submissions analysed: {s['evaluated_responses']}.", ""]
    if not s["evaluated_responses"]:
        return "\n".join(lines + ["No evaluations stored yet. Run `python run.py benchmark` or `python run.py submit ...` first."]) + "\n"
    lines += [f"- Average score: {s['average_score']} / 100", f"- Fully-correct responses: {s['overall_accuracy_pct']}%",
              f"- Test cases passed / failed: {s['tests_passed']} / {s['tests_failed']}",
              f"- Difficulty with the highest test failure rate: {rep['hardest_difficulty']}", "",
              "## Root cause split (failed tests)", ""]
    lines += [f"- {k}: {v}" for k, v in rep["root_cause"].items()] or ["- none"]
    lines += ["", "## Failures by category", ""] + ([f"- {k}: {v}" for k, v in rep["by_category"].items()] or ["- none"])
    lines += ["", "## Tasks ranked by failure rate", "", "| Task | Difficulty | Attempts | Responses with failures | Rate % |", "|---|---|---|---|---|"]
    lines += [f"| {t['task_id']} {t['title']} | {t['difficulty']} | {t['attempts']} | {t['submissions_with_failures']} | {t['failure_rate_pct']} |" for t in rep["tasks_ranked"]]
    lines += ["", "## Most frequently failed hidden cases", "", "| Test | Kind | What it checks | Failures |", "|---|---|---|---|"]
    lines += [f"| {e['test_id']} | {e['kind']} | {e['note']} | {e['failures']} |" for e in rep["edge_cases"]]
    lines += ["", "## Examples (incorrect vs correct output)", "", "| Model | Test | Input | Expected (correct) | Actual (incorrect) | Category |", "|---|---|---|---|---|---|"]
    esc = lambda x: str(x).replace("|", "\\|").replace("\n", " ")
    lines += [f"| {esc(e['model_name'])}{' (DEMO)' if e['is_demo'] else ''} | {e['test_id']} | `{esc(e['args'])}` | `{esc(e['expected'])}` | `{esc(e['actual'])}` | {e['category']} |" for e in rep["examples"]]
    return "\n".join(lines) + "\n"


def write_reports(conn, tasks, include_demo=False, out_dir=REPORT_DIR):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rep = failure_analysis(conn, tasks, include_demo)
    (out / "failure_report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    (out / "failure_report.md").write_text(render_markdown(rep), encoding="utf-8")
    return rep
