from evaluator import storage
from evaluator.demo import build_code
from evaluator.runner import evaluate_code


def store(conn, task, name, code, demo=False, version="v1", run=1):
    ev = evaluate_code(task, code)
    return storage.save_evaluation(conn, task, name, version, code, ev, run, "manual", demo), ev


def test_save_and_summary(conn, task_by_id):
    t = task_by_id["CE-E01"]
    store(conn, t, "m1", build_code("CE-E01", None, None))
    store(conn, t, "m1", build_code("CE-E01", [("if second is None:", "if False:")], None), run=2)
    s = storage.summary(conn, 10)
    assert s["evaluated_responses"] == 2 and s["overall_accuracy_pct"] == 50 and s["average_score"] == 97.5
    assert s["tests_failed"] == 1


def test_demo_excluded_by_default_and_deletable(conn, task_by_id):
    t = task_by_id["CE-E01"]
    store(conn, t, "real", build_code("CE-E01", None, None))
    store(conn, t, "DEMO-x", build_code("CE-E01", None, None), demo=True)
    assert storage.summary(conn, 10)["evaluated_responses"] == 1
    assert storage.summary(conn, 10, include_demo=True)["evaluated_responses"] == 2
    assert [m["model_name"] for m in storage.model_comparison(conn)] == ["real"]
    storage.delete_demo(conn)
    assert storage.summary(conn, 10, True)["evaluated_responses"] == 1
    assert conn.execute("SELECT COUNT(*) FROM test_results").fetchone()[0] == 8  # cascade removed demo rows


def test_model_comparison_and_difficulty(conn, task_by_id, tasks):
    t = task_by_id["CE-E01"]
    store(conn, t, "m1", build_code("CE-E01", [("if second is None:", "if False:")], None), version="2.0")
    m = storage.model_comparison(conn)[0]
    assert (m["model_name"], m["model_version"], m["tasks_attempted"]) == ("m1", "2.0", 1)
    assert m["common_failures"][0]["category"] == "missing_input_validation"
    assert storage.difficulty_performance(conn)[0]["attempts"] == 1
    assert storage.task_performance(conn, tasks)[0]["attempts"] == 1
