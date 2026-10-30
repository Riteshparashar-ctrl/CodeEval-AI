import json

import pytest

from evaluator.dataset import KINDS, DatasetError, load_tasks, public_view, reference_source, resolve_tests


def test_counts_and_difficulty_mix(tasks):
    assert len(tasks) == 10
    mix = [t["difficulty"] for t in tasks]
    assert (mix.count("Easy"), mix.count("Medium"), mix.count("Hard")) == (3, 4, 3)


def test_unique_ids_and_all_kinds_present(tasks):
    assert len({t["id"] for t in tasks}) == len(tasks)
    for t in tasks:
        assert {x["kind"] for x in t["tests"]} == set(KINDS)
        assert reference_source(t["id"]).strip()


def test_resolve_tests_ids_and_hidden_flags(tasks):
    for t in tasks:
        tests = resolve_tests(t)
        assert len({x["id"] for x in tests}) == len(tests)
        assert all(x["hidden"] == (x["kind"] != "basic") for x in tests)


def test_public_view_hides_hidden_tests(tasks):
    v = public_view(tasks[0])
    assert "tests" not in v and len(v["examples"]) == 2


def test_duplicate_ids_rejected(tmp_path, tasks):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"tasks": [tasks[0], tasks[0]]}))
    with pytest.raises(DatasetError):
        load_tasks(p)


def test_missing_file_and_bad_task(tmp_path, tasks):
    with pytest.raises(DatasetError):
        load_tasks(tmp_path / "nope.json")
    bad = dict(tasks[0]); bad.pop("description")
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"tasks": [bad]}))
    with pytest.raises(DatasetError):
        load_tasks(p)
