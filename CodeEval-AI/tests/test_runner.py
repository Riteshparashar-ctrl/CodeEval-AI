import pytest

from evaluator.dataset import load_tasks, reference_source
from evaluator.runner import evaluate_code

IDS = [t["id"] for t in load_tasks()]


@pytest.mark.parametrize("tid", IDS)
def test_reference_solution_scores_100(task_by_id, tid):
    ev = evaluate_code(task_by_id[tid], reference_source(tid))
    assert ev["score"] == 100 and ev["tests_failed"] == 0, [t for t in ev["tests"] if not t["passed"]]


def test_syntax_error_is_incomplete_implementation(task_by_id):
    ev = evaluate_code(task_by_id["CE-E01"], "def second_largest(nums:\n  pass")
    assert ev["score"] == 0
    assert {t["category"] for t in ev["tests"]} == {"incomplete_implementation"}


def test_missing_function(task_by_id):
    ev = evaluate_code(task_by_id["CE-E01"], "x = 1")
    assert ev["tests"][0]["actual_repr"].startswith("MissingFunction")


def test_infinite_loop_times_out(task_by_id):
    code = "def second_largest(nums):\n    while True:\n        pass\n"
    ev = evaluate_code(task_by_id["CE-E01"], code, timeout=0.5, perf_timeout=0.5)
    assert ev["score"] == 0
    assert any(t["category"] == "inefficient_algorithm" for t in ev["tests"])


def test_prints_do_not_break_harness(task_by_id):
    code = "def is_palindrome(s):\n    print('debug')\n    t=[c.lower() for c in s if c.isalnum()]\n    return t==t[::-1]\n"
    ev = evaluate_code(task_by_id["CE-E02"], code)
    assert ev["tests"][0]["passed"]
