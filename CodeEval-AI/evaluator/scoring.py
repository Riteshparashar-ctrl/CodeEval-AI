"""Deterministic scoring out of 100.

Every dimension is computed from automated test outcomes:
  functional (40)  <- public 'basic' tests
  edge_cases (25)  <- hidden 'edge' tests
  logic      (20)  <- hidden 'logic' tests (traps for wrong assumptions)
  complexity (10)  <- hidden 'perf' test (large input under a time limit)
  validation  (5)  <- hidden 'validation' tests (must raise ValueError)
A reviewer may manually override the complexity dimension (0-10) via manual_review.
"""
DIMENSIONS = (("basic", "functional", 40), ("edge", "edge_cases", 25), ("logic", "logic", 20),
              ("perf", "complexity", 10), ("validation", "validation", 5))
MAX_SCORE = sum(d[2] for d in DIMENSIONS)
MANUAL_DIMENSIONS = {"complexity"}


def compute_score(results, manual_review=None):
    manual_review = manual_review or {}
    bad = set(manual_review) - MANUAL_DIMENSIONS
    if bad:
        raise ValueError(f"manual review is only allowed for {sorted(MANUAL_DIMENSIONS)}, got {sorted(bad)}")
    breakdown = {}
    for kind, dim, weight in DIMENSIONS:
        rs = [r for r in results if r["kind"] == kind]
        earned = weight * sum(1 for r in rs if r["passed"]) / len(rs) if rs else 0.0
        if dim in manual_review:
            earned = float(manual_review[dim])
            if not 0 <= earned <= weight:
                raise ValueError(f"manual {dim} score must be between 0 and {weight}")
        breakdown[dim] = round(earned, 2)
    return round(sum(breakdown.values()), 2), breakdown
