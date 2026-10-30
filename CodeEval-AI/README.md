# CodeEval AI - AI Coding Reliability Benchmark

A small, fully reproducible platform that measures where AI-generated code breaks: wrong logic, missed edge
cases, bad complexity, missing input validation. Built for the HackerRank AI Evaluation Challenge.

> **Honesty statement.** This repository ships **no benchmark results for any AI model**. Nothing in the code
> or docs claims a model was tested. All numbers appear only after *you* run an evaluation. Sample data
> (`python run.py demo`) is synthetic, flagged `is_demo=1`, and always labelled **DEMO DATA** in the UI and reports.

## 1. Project overview
Backend: Python 3 + FastAPI + SQLite + Pydantic. Frontend: HTML/CSS/JavaScript dashboard (Chart.js via CDN).
Evaluator: a subprocess-based Python test runner with JSON expected answers and deterministic scoring.

## 2. Problem statement
Code models often return confident, plausible code that fails on boundaries, hidden assumptions or large
inputs. Pass/fail on a few visible examples hides this. CodeEval AI scores each answer against visible tests,
hidden edge cases, wrong-assumption traps, a validation contract and a scalability test.

## 3. Domain and expertise
Software engineering evaluation: algorithms and data structures, test design, complexity analysis and
reliability measurement of LLM-generated code.

## 4. Research motivation
Public code benchmarks such as HumanEval (Chen et al., 2021) and MBPP (Austin et al., 2021) rely on limited
test suites; EvalPlus (Liu et al., 2023) showed that stronger tests expose failures that weaker suites miss.
SWE-bench (Jimenez et al., 2023) targets repository-level tasks. CodeEval AI is a compact, original benchmark
focused on *failure modes* (edge cases, assumptions, complexity, validation) rather than a single pass rate.
No data from those benchmarks is used.

## 5. What the benchmark measures
Logical errors, debugging-relevant failures, edge-case handling, algorithm correctness, time/space behaviour
(empirically, via large inputs), input validation, boundary conditions and incorrect assumptions.

## 6. Dataset description
`dataset/tasks.json`: **10 original tasks** (3 Easy, 4 Medium, 3 Hard) covering arrays, strings, searching,
sorting, recursion, math/DP and data structures. Each task has an ID, description, input format, expected output,
evaluation criteria, difficulty, a reference solution (`reference_solutions/<ID>.py`) and 8 tests:
2 `basic` (public), 2 `edge`, 2 `logic`, 1 `validation`, 1 `perf` (all hidden).

| ID | Task | Level | ID | Task | Level |
|---|---|---|---|---|---|
| CE-E01 | Second largest distinct value | Easy | CE-M03 | Group anagrams | Medium |
| CE-E02 | Alphanumeric palindrome | Easy | CE-M04 | Balanced brackets | Medium |
| CE-E03 | Merge two sorted lists | Easy | CE-H01 | Longest strictly increasing subsequence | Hard |
| CE-M01 | Maximum subarray sum | Medium | CE-H02 | Edit distance | Hard |
| CE-M02 | First-occurrence binary search | Medium | CE-H03 | Count N-Queens solutions | Hard |

## 7. Evaluation methodology
Each test runs in a fresh subprocess (`evaluator/harness.py`) with a 5 s limit (10 s for perf). Results are
compared by exact JSON equality (so `True != 1`). Validation tests pass only if `ValueError` is raised. Perf
tests use large generated inputs; the expected output is computed by running the reference solution.
Every failed test gets a category: `incomplete_implementation` (syntax error, missing function),
`runtime_error`, `missing_input_validation`, `incorrect_logic`, `edge_case_failure`, `incorrect_assumption`,
`inefficient_algorithm`. Root-cause groups: *incomplete implementation* (crash/missing validation),
*incorrect logic* (runs, wrong answer), *performance* (timeout). `runtime_error` on valid input is classified
heuristically as incomplete implementation.

## 8. Scoring methodology (100 points, fully deterministic)
| Dimension | Points | Source |
|---|---|---|
| Functional correctness | 40 | share of `basic` tests passed |
| Edge-case handling | 25 | share of `edge` tests passed |
| Logical correctness | 20 | share of `logic` tests passed (traps for wrong assumptions) |
| Complexity analysis | 10 | `perf` test (large input within time limit); optional manual override 0-10 |
| Input validation | 5 | share of `validation` tests passed |

"Logical correctness" and "complexity" are deterministic *proxies*: they do not read the model's prose
explanation. Rubric for manual review of complexity: 10 = optimal and justified, 5 = correct but suboptimal,
0 = wrong or exponential. Submit it with `--manual-complexity` or the Submit page. **Accuracy** = share of
responses that pass *every* test. No LLM is used for grading.

## 9. Architecture
```
CodeEval-AI/
  backend/app.py        FastAPI API + static hosting      evaluator/dataset.py  load + validate tasks
  frontend/             dashboard, failures, submit        evaluator/runner.py   subprocess test runner
  dataset/tasks.json    tasks, tests, expected answers     evaluator/scoring.py  100-point scoring
  reference_solutions/  one verified solution per task     evaluator/adapters.py model API adapters
  evaluator/storage.py  SQLite + aggregates                evaluator/report.py   failure analysis/reports
  tests/  results/(SQLite DB)  reports/  run.py (CLI)  models.example.json  .env.example
```

## 10. Installation (Windows 10/11, macOS, Linux; Python 3.9+)
```
python -m venv .venv
.venv\Scripts\activate          (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## 11. How to execute
```
python run.py validate          # checks dataset; all reference solutions must score 100
python run.py test              # unit tests
python run.py serve             # dashboard at http://127.0.0.1:8000
python run.py submit --model my-model --version v1 --task CE-E01 --file answer.py   # manual evaluation
python run.py benchmark --config models.json --runs 3   # single command: validate -> API eval -> report
python run.py report            # reports/failure_report.md + .json (measured data only)
python run.py demo              # optional DEMO DATA; python run.py reset-demo removes it
```
Manual evaluation also works in the browser (Submit page). Multiple runs: `--run N` / `--runs N`.

## 12. How to integrate AI models
Copy `models.example.json` to `models.json` and `.env.example` to `.env`; put real model IDs and keys in them
(never commit them). Built-in adapters: `openai_compatible` (any `/chat/completions` endpoint via `base_url`)
and `anthropic`. Add a new one by subclassing in `evaluator/adapters.py` and registering it in `ADAPTERS`.
Entries without credentials are skipped and failed API calls are not recorded: nothing is ever invented.
The model prompt contains the task text and only the public examples.

## 13. Results and failure analysis
**Actual experimental findings: none included.** After you run evaluations, `reports/failure_report.md` and the
Failure analysis page list the most-failed tasks, the hidden cases that cause the most errors, the logic vs
incomplete-implementation split, the failure rate per difficulty and expected-vs-actual examples, all computed
from stored results. Verified facts about this repo (not model results): the 10 reference solutions score
100/100 and the 43 unit tests pass. `python run.py demo` builds *illustrative* flawed submissions (mutated
reference solutions); they are not AI output.

## 14. Limitations
- Execution is **not a security sandbox**: only run code you trust on your own machine.
- 10 tasks and 8 tests each give limited coverage; scores are not statistically strong without many runs.
- Complexity is measured by a single large input, so it can miss constants and noisy timing across machines.
- Logic/complexity scores are proxies for reasoning quality; written explanations are not graded automatically.
- Python only; one function per task.

## 15. Future improvements
More tasks and languages, property-based test generation, memory profiling, container sandboxing,
confidence/calibration tracking per response, statistical confidence intervals over repeated runs.

## 16. Sources and references
- Chen et al. (2021), *Evaluating Large Language Models Trained on Code*, arXiv:2107.03374
- Austin et al. (2021), *Program Synthesis with Large Language Models*, arXiv:2108.07732
- Liu et al. (2023), *Is Your Code Generated by ChatGPT Really Correct?*, arXiv:2305.01210
- Jimenez et al. (2023), *SWE-bench*, arXiv:2310.06770
- Levenshtein (1966) edit distance; Kadane's maximum-subarray algorithm; FastAPI and Pydantic documentation.
Used for motivation only. All tasks, tests and solutions in this repo are original.
