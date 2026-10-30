"""Automated test runner. Each test runs in its own subprocess with a timeout.

NOTE: this isolates crashes and infinite loops, it is NOT a security sandbox.
Only evaluate code you are willing to run on your own machine.
"""
import json
import subprocess
import sys
from pathlib import Path

from .dataset import reference_source, resolve_tests
from .scoring import compute_score

HARNESS = Path(__file__).with_name("harness.py")
TIMEOUT, PERF_TIMEOUT, REFERENCE_TIMEOUT = 5.0, 10.0, 60.0
INCOMPLETE_ERRORS = {"SyntaxError", "IndentationError", "TabError", "MissingFunction", "NotImplementedError"}
ROOT_CAUSE = {"incomplete_implementation": "incomplete_implementation", "runtime_error": "incomplete_implementation",
              "missing_input_validation": "incomplete_implementation", "incorrect_logic": "incorrect_logic",
              "edge_case_failure": "incorrect_logic", "incorrect_assumption": "incorrect_logic",
              "inefficient_algorithm": "performance"}
_ref_cache = {}


def run_call(code, function, args, repeat=1, timeout=TIMEOUT):
    payload = json.dumps({"code": code, "function": function, "args": args, "repeat": repeat})
    try:
        p = subprocess.run([sys.executable, str(HARNESS)], input=payload, capture_output=True,
                           text=True, encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    lines = p.stdout.strip().splitlines()
    try:
        return json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        return {"status": "error", "error_type": "HarnessError", "message": (p.stderr or "no output")[-300:]}


def _same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _short(v, n=200):
    s = v if isinstance(v, str) else json.dumps(v)
    return s if len(s) <= n else s[:n] + "..."


def _expected(task, test):
    if not test["perf"]:
        return test["expect"]
    key = (task["id"], test["id"])
    if key not in _ref_cache:
        res = run_call(reference_source(task["id"]), task["function"], test["args"], test["repeat"], REFERENCE_TIMEOUT)
        if res["status"] != "ok":
            raise RuntimeError(f"reference solution failed on {test['id']}: {res}")
        _ref_cache[key] = res["result"]
    return _ref_cache[key]


def classify(kind, res, passed):
    if passed:
        return None
    st, et = res["status"], res.get("error_type")
    if st == "error" and et in INCOMPLETE_ERRORS:
        return "incomplete_implementation"
    if kind == "validation":
        return "missing_input_validation"
    if kind == "perf":
        return "inefficient_algorithm" if st != "ok" else "incorrect_logic"
    if st == "timeout":
        return "inefficient_algorithm"
    if st == "error":
        return "runtime_error"
    return {"edge": "edge_case_failure", "logic": "incorrect_assumption"}.get(kind, "incorrect_logic")


def judge(test, res, expected, timeout):
    st = res["status"]
    if test["raises"]:
        passed = st == "error" and res.get("error_type") == test["raises"]
        exp_repr = f"raises {test['raises']}"
    else:
        passed = st == "ok" and _same(res["result"], expected)
        exp_repr = _short(expected)
    if st == "ok":
        actual = _short(res["result"])
    elif st == "timeout":
        actual = f"timeout after {timeout}s"
    else:
        actual = f"{res.get('error_type')}: {res.get('message', '')}"[:200]
    return {"test_id": test["id"], "kind": test["kind"], "hidden": test["hidden"], "passed": passed,
            "category": classify(test["kind"], res, passed), "status": st, "note": test["note"],
            "args_repr": "(generated large input)" if test["perf"] else _short(test["args"]),
            "expected_repr": exp_repr, "actual_repr": actual}


def evaluate_code(task, code, manual_review=None, timeout=TIMEOUT, perf_timeout=PERF_TIMEOUT):
    results = []
    for test in resolve_tests(task):
        limit = perf_timeout if test["perf"] else timeout
        expected = _expected(task, test)
        res = run_call(code, task["function"], test["args"], test["repeat"], limit)
        results.append(judge(test, res, expected, limit))
    score, breakdown = compute_score(results, manual_review)
    passed = sum(1 for r in results if r["passed"])
    return {"task_id": task["id"], "score": score, "breakdown": breakdown, "tests_passed": passed,
            "tests_failed": len(results) - passed, "tests": results, "manual_review": manual_review or {}}
