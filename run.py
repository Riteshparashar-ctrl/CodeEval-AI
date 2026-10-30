#!/usr/bin/env python3
"""CodeEval AI command line. Run `python run.py --help`."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from evaluator import report, storage  # noqa: E402
from evaluator.adapters import AdapterError, build_prompt, extract_code, make_adapter  # noqa: E402
from evaluator.dataset import DatasetError, load_tasks, reference_source  # noqa: E402
from evaluator.demo import load_demo  # noqa: E402
from evaluator.runner import evaluate_code  # noqa: E402


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def pick(tasks, ids):
    if not ids:
        return tasks
    by = {t["id"]: t for t in tasks}
    unknown = [i for i in ids if i not in by]
    if unknown:
        sys.exit(f"unknown task id(s): {unknown}")
    return [by[i] for i in ids]


def cmd_validate(a):
    tasks = load_tasks()
    counts = {d: sum(1 for t in tasks if t["difficulty"] == d) for d in ("Easy", "Medium", "Hard")}
    print(f"Dataset OK: {len(tasks)} tasks {counts}")
    bad = 0
    for t in tasks:
        ev = evaluate_code(t, reference_source(t["id"]))
        ok = ev["score"] == 100
        bad += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} reference {t['id']} -> {ev['score']}")
    if bad:
        sys.exit("reference solutions do not all score 100")


def cmd_serve(a):
    import uvicorn
    print(f"Dashboard: http://{a.host}:{a.port}")
    uvicorn.run("backend.app:app", host=a.host, port=a.port)


def cmd_submit(a):
    task = pick(load_tasks(), [a.task])[0]
    code = Path(a.file).read_text(encoding="utf-8")
    review = {"complexity": a.manual_complexity} if a.manual_complexity is not None else None
    ev = evaluate_code(task, code, review)
    conn = storage.connect()
    sid = storage.save_evaluation(conn, task, a.model, a.version, code, ev, a.run, source="manual")
    print(f"Saved submission #{sid}: score {ev['score']}/100 {ev['breakdown']}")
    for t in ev["tests"]:
        if not t["passed"]:
            print(f"  FAIL {t['test_id']} [{t['category']}] got: {t['actual_repr']}")


def cmd_eval(a):
    tasks = pick(load_tasks(), a.tasks)
    cfg_path = Path(a.config)
    if not cfg_path.exists():
        sys.exit(f"{cfg_path} not found. Copy models.example.json to models.json and edit it, or use `submit` for manual evaluation.")
    conn = storage.connect()
    done = 0
    for m in json.loads(cfg_path.read_text(encoding="utf-8"))["models"]:
        if not m.get("enabled", True):
            print(f"skip {m['name']}: disabled in config")
            continue
        try:
            adapter = make_adapter(m)
        except AdapterError as e:
            print(f"skip {m.get('name')}: {e}")
            continue
        if not adapter.available():
            print(f"skip {adapter.name}: env var {m.get('api_key_env')} not set (nothing evaluated, nothing invented)")
            continue
        for task in tasks:
            for run in range(1, a.runs + 1):
                try:
                    code = extract_code(adapter.generate(build_prompt(task)))
                except AdapterError as e:
                    print(f"  {adapter.name} {task['id']} run {run}: API failed ({e}); not recorded")
                    continue
                ev = evaluate_code(task, code)
                storage.save_evaluation(conn, task, adapter.name, adapter.version, code, ev, run, source="api")
                done += 1
                print(f"  {adapter.name} {task['id']} run {run}: {ev['score']}")
    print(f"Stored {done} real evaluation(s).")


def cmd_demo(a):
    conn = storage.connect()
    n = load_demo(conn, load_tasks())
    print(f"Loaded {n} DEMO DATA submissions (synthetic, flagged is_demo=1). Tick 'Include DEMO DATA' in the dashboard.")


def cmd_reset_demo(a):
    storage.delete_demo(storage.connect())
    print("Demo data removed.")


def cmd_report(a):
    rep = report.write_reports(storage.connect(), load_tasks(), include_demo=a.include_demo)
    print(f"Wrote reports/failure_report.md and .json ({rep['summary']['evaluated_responses']} submissions).")


def cmd_test(a):
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")]))


def cmd_benchmark(a):
    cmd_validate(a)
    cmd_eval(a)
    cmd_report(argparse.Namespace(include_demo=False))


def main():
    load_env()
    p = argparse.ArgumentParser(description="CodeEval AI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="validate dataset and reference solutions").set_defaults(fn=cmd_validate)
    s = sub.add_parser("serve", help="start dashboard + API")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=cmd_serve)
    s = sub.add_parser("submit", help="evaluate a manual response from a .py file")
    s.add_argument("--model", required=True)
    s.add_argument("--version", default="")
    s.add_argument("--task", required=True)
    s.add_argument("--file", required=True)
    s.add_argument("--run", type=int, default=1)
    s.add_argument("--manual-complexity", type=float, default=None, help="optional reviewer score 0-10")
    s.set_defaults(fn=cmd_submit)
    for name, fn, helptext in (("eval", cmd_eval, "evaluate API models from a config"),
                               ("benchmark", cmd_benchmark, "validate -> eval -> report (single command)")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("--config", default="models.json")
        s.add_argument("--runs", type=int, default=1)
        s.add_argument("--tasks", nargs="*")
        s.set_defaults(fn=fn)
    sub.add_parser("demo", help="load DEMO DATA").set_defaults(fn=cmd_demo)
    sub.add_parser("reset-demo", help="delete DEMO DATA").set_defaults(fn=cmd_reset_demo)
    s = sub.add_parser("report", help="write reports/failure_report.*")
    s.add_argument("--include-demo", action="store_true")
    s.set_defaults(fn=cmd_report)
    sub.add_parser("test", help="run unit tests").set_defaults(fn=cmd_test)
    a = p.parse_args()
    try:
        a.fn(a)
    except DatasetError as e:
        sys.exit(f"dataset error: {e}")


if __name__ == "__main__":
    main()
