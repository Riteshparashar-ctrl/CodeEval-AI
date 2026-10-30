import pytest

from evaluator.scoring import DIMENSIONS, MAX_SCORE, compute_score


def mk(passed_by_kind):
    out = []
    for kind, flags in passed_by_kind.items():
        out += [{"kind": kind, "passed": f} for f in flags]
    return out


ALL = {"basic": [True, True], "edge": [True, True], "logic": [True, True], "perf": [True], "validation": [True]}


def test_weights_sum_to_100():
    assert MAX_SCORE == 100 and [d[2] for d in DIMENSIONS] == [40, 25, 20, 10, 5]


def test_perfect_and_zero():
    assert compute_score(mk(ALL))[0] == 100
    assert compute_score(mk({k: [False] * len(v) for k, v in ALL.items()}))[0] == 0


def test_partial_credit_is_proportional():
    r = dict(ALL, basic=[True, False], edge=[True, False])
    score, b = compute_score(mk(r))
    assert b["functional"] == 20 and b["edge_cases"] == 12.5 and score == 67.5


def test_manual_complexity_override():
    r = dict(ALL, perf=[False])
    assert compute_score(mk(r))[1]["complexity"] == 0
    score, b = compute_score(mk(r), {"complexity": 7.5})
    assert b["complexity"] == 7.5 and score == 97.5


@pytest.mark.parametrize("bad", [{"complexity": 11}, {"complexity": -1}, {"functional": 5}])
def test_invalid_manual_review_rejected(bad):
    with pytest.raises(ValueError):
        compute_score(mk(ALL), bad)
