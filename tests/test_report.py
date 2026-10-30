import json

from evaluator import report, storage
from evaluator.demo import build_code
from evaluator.runner import evaluate_code


def test_empty_report_is_honest(conn, tasks, tmp_path):
    rep = report.write_reports(conn, tasks, out_dir=tmp_path)
    assert rep["summary"]["evaluated_responses"] == 0
    assert "No evaluations stored yet" in (tmp_path / "failure_report.md").read_text(encoding="utf-8")


def test_report_from_real_results(conn, tasks, task_by_id, tmp_path):
    t = task_by_id["CE-H01"]
    code = build_code("CE-H01", [("bisect_left", "bisect_right")], None)
    storage.save_evaluation(conn, t, "m", "1", code, evaluate_code(t, code))
    rep = report.write_reports(conn, tasks, out_dir=tmp_path)
    assert rep["root_cause"] == {"incorrect_logic": 1}
    assert rep["by_category"] == {"incorrect_assumption": 1}
    assert rep["hardest_difficulty"] == "Hard"
    assert rep["examples"][0]["expected"] == "1" and rep["examples"][0]["actual"] == "4"
    md = (tmp_path / "failure_report.md").read_text(encoding="utf-8")
    assert "demo data excluded" in md and "CE-H01-logic-1" in md
    assert json.loads((tmp_path / "failure_report.json").read_text())["summary"]["evaluated_responses"] == 1


def test_demo_rows_excluded_unless_requested(conn, tasks, task_by_id):
    t = task_by_id["CE-H01"]
    code = build_code("CE-H01", [("bisect_left", "bisect_right")], None)
    storage.save_evaluation(conn, t, "DEMO", "d", code, evaluate_code(t, code), is_demo=True)
    assert report.failure_analysis(conn, tasks)["summary"]["evaluated_responses"] == 0
    assert report.failure_analysis(conn, tasks, True)["examples"][0]["is_demo"] is True
