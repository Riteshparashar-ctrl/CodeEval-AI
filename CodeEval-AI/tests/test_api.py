import pytest
from fastapi.testclient import TestClient

from evaluator.dataset import reference_source


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEEVAL_DB", str(tmp_path / "api.db"))
    from backend.app import app
    return TestClient(app)


def test_tasks_endpoint_hides_hidden_tests(client):
    r = client.get("/api/tasks").json()
    assert len(r) == 10 and all("tests" not in t for t in r)


def test_evaluate_stores_and_summarises(client):
    body = {"model_name": "m", "model_version": "1", "task_id": "CE-E02", "code": reference_source("CE-E02")}
    r = client.post("/api/evaluate", json=body).json()
    assert r["score"] == 100
    assert all(t["expected_repr"] is None for t in r["tests"] if t["hidden"])
    s = client.get("/api/summary").json()
    assert s["evaluated_responses"] == 1 and s["overall_accuracy_pct"] == 100
    assert client.get("/api/models").json()[0]["model_name"] == "m"
    assert client.get("/api/failures").json()["summary"]["evaluated_responses"] == 1


def test_validation_errors(client):
    assert client.post("/api/evaluate", json={"model_name": "m", "task_id": "nope", "code": "x"}).status_code == 404
    assert client.post("/api/evaluate", json={"model_name": "m", "task_id": "CE-E02", "code": ""}).status_code == 422
    bad = {"model_name": "m", "task_id": "CE-E02", "code": "x=1", "manual_review": {"complexity": 99}}
    assert client.post("/api/evaluate", json=bad).status_code == 422


def test_static_dashboard_served(client):
    assert "CodeEval" in client.get("/").text
