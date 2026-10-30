# CodeEval AI - Failure Report

Scope: INCLUDES DEMO DATA (synthetic, not model results). Submissions analysed: 14.

- Average score: 88.39 / 100
- Fully-correct responses: 28.57%
- Test cases passed / failed: 98 / 14
- Difficulty with the highest test failure rate: Medium

## Root cause split (failed tests)

- incorrect_logic: 7
- performance: 3
- incomplete_implementation: 4

## Failures by category

- edge_case_failure: 4
- inefficient_algorithm: 3
- runtime_error: 2
- missing_input_validation: 2
- incorrect_assumption: 2
- incorrect_logic: 1

## Tasks ranked by failure rate

| Task | Difficulty | Attempts | Responses with failures | Rate % |
|---|---|---|---|---|
| CE-M01 Maximum Subarray Sum | Medium | 2 | 2 | 100.0 |
| CE-E02 Alphanumeric Palindrome | Easy | 1 | 1 | 100.0 |
| CE-M02 First Occurrence Binary Search | Medium | 1 | 1 | 100.0 |
| CE-H01 Longest Strictly Increasing Subsequence | Hard | 2 | 2 | 100.0 |
| CE-E01 Second Largest Distinct Value | Easy | 1 | 1 | 100.0 |
| CE-M04 Balanced Brackets | Medium | 1 | 1 | 100.0 |
| CE-H03 Count N-Queens Solutions | Hard | 1 | 1 | 100.0 |
| CE-H02 Edit Distance | Hard | 2 | 1 | 50.0 |
| CE-E03 Merge Two Sorted Lists | Easy | 2 | 0 | 0.0 |
| CE-M03 Group Anagrams | Medium | 1 | 0 | 0.0 |

## Most frequently failed hidden cases

| Test | Kind | What it checks | Failures |
|---|---|---|---|
| CE-E01-validation-1 | validation | fewer than two distinct values | 1 |
| CE-E02-edge-2 | edge | punctuation, spaces, mixed case | 1 |
| CE-E02-logic-2 | logic | underscore is not alphanumeric | 1 |
| CE-H01-logic-1 | logic | equal values are not strictly increasing | 1 |
| CE-H01-perf-1 | perf | 200k elements (O(n^2) times out) | 1 |
| CE-H02-perf-1 | perf | 1500 x 1500 characters | 1 |
| CE-H03-validation-1 | validation | n below 1 | 1 |
| CE-M01-edge-1 | edge | single negative element | 1 |
| CE-M01-edge-2 | edge | all negative: empty subarray not allowed | 1 |
| CE-M01-perf-1 | perf | 500k elements | 1 |
| CE-M02-edge-1 | edge | empty list | 1 |
| CE-M04-edge-2 | edge | unclosed opening bracket | 1 |

## Examples (incorrect vs correct output)

| Model | Test | Input | Expected (correct) | Actual (incorrect) | Category |
|---|---|---|---|---|---|
| DEMO-B (naive algorithms) (DEMO) | CE-H02-perf-1 | `(generated large input)` | `2` | `RecursionError: maximum recursion depth exceeded` | inefficient_algorithm |
| DEMO-B (naive algorithms) (DEMO) | CE-H01-perf-1 | `(generated large input)` | `511` | `timeout after 10.0s` | inefficient_algorithm |
| DEMO-B (naive algorithms) (DEMO) | CE-M01-perf-1 | `(generated large input)` | `124` | `timeout after 10.0s` | inefficient_algorithm |
| DEMO-A (mutated reference) (DEMO) | CE-H03-validation-1 | `[0]` | `raises ValueError` | `1` | missing_input_validation |
| DEMO-A (mutated reference) (DEMO) | CE-H01-logic-1 | `[[7, 7, 7, 7]]` | `1` | `4` | incorrect_assumption |
| DEMO-A (mutated reference) (DEMO) | CE-M04-edge-2 | `["("]` | `false` | `true` | edge_case_failure |
| DEMO-A (mutated reference) (DEMO) | CE-M02-basic-2 | `[[1, 2, 3], 4]` | `-1` | `IndexError: list index out of range` | runtime_error |
| DEMO-A (mutated reference) (DEMO) | CE-M02-edge-1 | `[[], 1]` | `-1` | `IndexError: list index out of range` | runtime_error |
| DEMO-A (mutated reference) (DEMO) | CE-M01-basic-2 | `[[2, 3, -1]]` | `5` | `3` | incorrect_logic |
| DEMO-A (mutated reference) (DEMO) | CE-M01-edge-1 | `[[-3]]` | `-3` | `0` | edge_case_failure |
