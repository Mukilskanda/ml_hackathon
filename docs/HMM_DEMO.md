# Live HMM/Viterbi review logs

Run these in PowerShell from the project folder. The commands load the selected saved model and decoder settings, then execute real candidate generation, classifier scoring, directed graph transitions and Viterbi decoding. They do not fit models, search parameters, write caches or replace artifacts.

In the extracted Laptop 1 backend package, use `.\.venv\Scripts\python.exe` instead of `.\tmp\clean_env\Scripts\python.exe` after running backend setup. The demo script and this guide are included in that package.

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null
.\tmp\clean_env\Scripts\python.exe -u scripts/demo_hmm.py --partition student --trip 00000052 --steps 5 2>&1 | Tee-Object -FilePath tmp/hmm_trip_00000052.log
```

For all ten development trips and an equal-trip summary:

```powershell
.\tmp\clean_env\Scripts\python.exe -u scripts/demo_hmm.py --partition student --all-trips --steps 2 2>&1 | Tee-Object -FilePath tmp/hmm_all_student_trips.log
```

For the separately supplied evaluator partition, without tuning:

```powershell
.\tmp\clean_env\Scripts\python.exe -u scripts/demo_hmm.py --partition evaluator --all-trips --steps 2 2>&1 | Tee-Object -FilePath tmp/hmm_all_evaluator_trips.log
```

Use the installed environment's Python path on other laptops. These commands use this workspace's verified environment.

Explain the log stages:

| Stage | Meaning |
|---|---|
| OBSERVATIONS | The actual GPS measurements and directed road graph loaded. |
| HIDDEN STATES | Candidate directed road IDs that the vehicle could occupy at each observation. |
| EMISSION INPUT | Normalized classifier candidate scores entering adaptive emission scoring. These are relative scores, not calibrated correctness probabilities. |
| TRANSITIONS | The real network-distance tensor between consecutive candidate sets, before transition penalties. Infinite entries mean not found under the bounded/pruned search; do not claim global disconnection. |
| VITERBI | Actual forward dynamic programming and backtracking with the frozen configuration. |
| PATH | A sample of selected states after backtracking, rather than a live per-iteration trace. |
| CHANGED | Examples where the full-sequence decoder chose a different road from independent classifier Top-1. A locally smaller classifier score can win once transitions and geometry are considered. |
| CONTINUITY | Direct connected road changes after consecutive duplicates are collapsed; no reference is needed. |
| FEASIBILITY | Physically feasible transitions, allowing intermediate connecting roads and tolerated GPS jitter. |
| RESETS | Sequence restart locations for large gaps or wholly infeasible transitions. |
| SCORING / AGREEMENT | The reference is loaded only after prediction. Agreement uses derived point alignment and is not official evaluator accuracy. |
| INTEGRITY | Checks that saved model/configuration hashes did not change during this run. |

The all-student run reproduces the report's development averages. Individual-trip values differ from those averages. The evaluator partition has different trips and is not used to select parameters.

The ordinary backend console separately shows HTTP request/completion IDs when the UI reconstructs a route. The command-line logs above explain decoding internals; they do not replace the genuine receiving-laptop CMD screenshot required for two-laptop deployment evidence.

`scripts/evaluate_routes.py` is a development search that rewrites decoder settings. Use the read-only `scripts/demo_hmm.py` command for the final review.
