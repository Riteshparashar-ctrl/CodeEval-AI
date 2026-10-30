"""Known-buggy submissions must lose points in exactly the expected dimension."""
from evaluator.demo import build_code
from evaluator.runner import evaluate_code


def run(task_by_id, tid, repl):
    return evaluate_code(task_by_id[tid], build_code(tid, repl, None))


def failed(ev):
    return {t["test_id"]: t["category"] for t in ev["tests"] if not t["passed"]}


def test_missing_validation_only_costs_validation_points(task_by_id):
    ev = run(task_by_id, "CE-E01", [("if second is None:", "if False:")])
    assert failed(ev) == {"CE-E01-validation-1": "missing_input_validation"}
    assert ev["score"] == 95


def test_naive_palindrome_fails_edge_and_logic(task_by_id):
    ev = run(task_by_id, "CE-E02", [("if c.isalnum()", "if c != ' '")])
    f = failed(ev)
    assert f["CE-E02-edge-2"] == "edge_case_failure" and f["CE-E02-logic-2"] == "incorrect_assumption"
    assert ev["breakdown"]["functional"] == 40 and ev["breakdown"]["edge_cases"] == 12.5


def test_non_strict_lis_fails_logic_trap(task_by_id):
    ev = run(task_by_id, "CE-H01", [("bisect_left", "bisect_right")])
    assert list(failed(ev)) == ["CE-H01-logic-1"] and ev["score"] == 90


def test_all_negative_array_edge_case(task_by_id):
    ev = run(task_by_id, "CE-M01", [("best = cur = nums[0]", "best = cur = 0")])
    assert {k for k, v in failed(ev).items() if v == "edge_case_failure"} == {"CE-M01-edge-1", "CE-M01-edge-2"}


def test_index_error_is_runtime_error(task_by_id):
    ev = run(task_by_id, "CE-M02", [("return lo if lo < len(nums) and nums[lo] == target else -1",
                                     "return lo if nums[lo] == target else -1")])
    assert "runtime_error" in set(failed(ev).values())


def test_quadratic_solution_fails_only_complexity(task_by_id):
    code = ("def longest_increasing_subsequence(nums):\n    if not isinstance(nums, list) or any(type(x) is not int for x in nums):\n"
            "        raise ValueError('bad')\n    dp = [1] * len(nums)\n    for i in range(len(nums)):\n        for j in range(i):\n"
            "            if nums[j] < nums[i]:\n                dp[i] = max(dp[i], dp[j] + 1)\n    return max(dp) if dp else 0\n")
    ev = evaluate_code(task_by_id["CE-H01"], code, perf_timeout=3)
    assert failed(ev) == {"CE-H01-perf-1": "inefficient_algorithm"} and ev["breakdown"]["complexity"] == 0
