"""Loads clearly-labelled DEMO DATA into the database."""
from .dataset import reference_source
from .demo_data import PROFILES
from .runner import evaluate_code
from .storage import delete_demo, save_evaluation


def build_code(task_id, replacements, code):
    if code is not None:
        return code
    src = reference_source(task_id)
    for old, new in replacements or []:
        if old not in src:
            raise ValueError(f"demo mutation target {old!r} not found in {task_id}")
        src = src.replace(old, new)
    return src


def load_demo(conn, tasks, log=print):
    by_id = {t["id"]: t for t in tasks}
    delete_demo(conn)
    n = 0
    for p in PROFILES:
        for task_id, repl, code in p["entries"]:
            src = build_code(task_id, repl, code)
            ev = evaluate_code(by_id[task_id], src)
            save_evaluation(conn, by_id[task_id], p["model_name"], p["model_version"], src, ev, source="demo", is_demo=True)
            n += 1
            log(f"  [DEMO] {p['model_name']} {task_id}: {ev['score']}")
    return n
