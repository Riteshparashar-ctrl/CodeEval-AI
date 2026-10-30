"""Dataset loading, validation and test materialisation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "dataset" / "tasks.json"
REF_DIR = ROOT / "reference_solutions"
KINDS = ("basic", "edge", "logic", "validation", "perf")
DIFFICULTIES = ("Easy", "Medium", "Hard")
REQUIRED_FIELDS = ("id", "title", "difficulty", "topic", "function", "description",
                   "input_format", "expected_output", "evaluation_criteria", "tests")
_SAFE_BUILTINS = {"range": range, "str": str, "list": list, "sorted": sorted, "len": len}


class DatasetError(ValueError):
    pass


def _validate_task(t):
    missing = [f for f in REQUIRED_FIELDS if f not in t]
    if missing:
        raise DatasetError(f"task {t.get('id', '?')} is missing fields: {missing}")
    if t["difficulty"] not in DIFFICULTIES:
        raise DatasetError(f"{t['id']}: bad difficulty {t['difficulty']!r}")
    kinds = set()
    for i, test in enumerate(t["tests"]):
        k = test.get("kind")
        if k not in KINDS:
            raise DatasetError(f"{t['id']} test {i}: bad kind {k!r}")
        kinds.add(k)
        if k == "perf":
            if "args_expr" not in test:
                raise DatasetError(f"{t['id']} perf test needs args_expr")
        elif "args" not in test or ("expected" not in test and "raises" not in test):
            raise DatasetError(f"{t['id']} test {i}: needs args and expected/raises")
    if kinds != set(KINDS):
        raise DatasetError(f"{t['id']}: every kind is required, missing {set(KINDS) - kinds}")
    if not (REF_DIR / f"{t['id']}.py").exists():
        raise DatasetError(f"{t['id']}: reference solution file missing")


def load_tasks(path=DATASET_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise DatasetError(f"cannot read dataset: {e}") from e
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise DatasetError("dataset has no tasks")
    seen = set()
    for t in tasks:
        _validate_task(t)
        if t["id"] in seen:
            raise DatasetError(f"duplicate task id {t['id']}")
        seen.add(t["id"])
    return tasks


def reference_source(task_id):
    return (REF_DIR / f"{task_id}.py").read_text(encoding="utf-8")


def resolve_tests(task):
    """Return runnable tests with stable ids. Perf inputs are generated from args_expr."""
    out, counters = [], {}
    for t in task["tests"]:
        k = t["kind"]
        counters[k] = counters.get(k, 0) + 1
        perf = k == "perf"
        args = eval(t["args_expr"], {"__builtins__": _SAFE_BUILTINS}) if perf else t["args"]
        out.append({"id": f"{task['id']}-{k}-{counters[k]}", "kind": k, "args": args,
                    "expect": t.get("expected"), "raises": t.get("raises"),
                    "repeat": t.get("repeat", 1), "note": t.get("note", ""),
                    "hidden": k != "basic", "perf": perf})
    return out


def public_view(task):
    """Task data that is safe to show to a model: no hidden tests."""
    counts = {k: sum(1 for t in task["tests"] if t["kind"] == k) for k in KINDS}
    keys = ("id", "title", "difficulty", "topic", "function", "description", "input_format",
            "expected_output", "evaluation_criteria", "reference_complexity")
    view = {k: task.get(k) for k in keys}
    view["examples"] = [{"args": t["args"], "expected": t["expected"]}
                        for t in task["tests"] if t["kind"] == "basic"]
    view["test_counts"] = counts
    return view
