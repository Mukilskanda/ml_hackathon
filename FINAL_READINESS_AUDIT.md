# FINAL_READINESS_AUDIT

Final critical audit, 18 November 2026. This supersedes the initial build audit. PASS means local evidence supports the stated scope; PARTIAL means external/human verification or an explicitly limited interpretation remains; FAIL means a mandatory external deliverable is currently absent, not that local inference is broken.

**Status counts: 62 PASS / 8 PARTIAL / 2 FAIL.**

## Main findings

- Independently reproduced original score: 95.2489% equal-trip mean; 94.0971% observation-weighted (18,029/19,160).
- Separate reference-DP implementation reproduced all ten label arrays. Raw inputs, candidates, features, stored probabilities and split disjointness were checked. No identical tracks or matching moving ten-point windows were found across train/student-test partitions.
- These remain derived-reference development scores. Shared geometry/heading assumptions, reference anomalies and repeated development selection prevent an independent ground-truth or unbiased generalisation claim.
- Refit/replayed all seven baseline algorithms plus tuned/directional variants. Stored CV/test metrics agree within 1e-7. All sixteen Bayesian objectives and database/CSV trial records agree. Feature ablation and calibration metrics replay exactly.
- Robustness cases were rerun. Expanded-query adaptive reranking was evaluated, including a training-matched refit. Its grouped-CV objective decreased, so it was rejected. The deployed historical_v1 candidate profile matches the original training artifacts; both experiment profiles and changed rows are retained.
- Retained exact physical-bound pruning: all feasible matrices and ten original predictions unchanged; transition-building total 11.63s -> 3.93s (2.96x in this benchmark).
- Retained log(2) soft immediate-reversal cost only after training-only twelve-trip holdout, repeated timing and eighteen-case robustness gates. The stochastic row-normalized HMM alternative was rejected.
- Final descriptive student-test result: 95.2559% equal-trip mean; 94.1284% observation-weighted. Aggregate gain over the original is negligible; one trip regresses. No claim of statistically significant or universal accuracy improvement.
- Fresh virtual environment installed the fully locked dependencies, passed pip check, passed 28 tests, reloaded the artifacts and served all ten real API requests. One Starlette/httpx deprecation warning is recorded; functionality passes.
- Mathematical tests include exhaustive enumeration of Viterbi paths and SciPy cross-checks of directed shortest paths. UI/browser and package evidence are linked below.

## Unsupported claims to avoid

- Do not call the score official evaluator accuracy or independent true-road accuracy.
- Do not claim research priority, guaranteed GPS-noise robustness, or that every trip improved.
- Do not call unnormalized transition compatibilities a calibrated stochastic transition matrix. The chosen procedure is explicit HMM-style Viterbi/MAP scoring.
- Do not claim two physical laptops, genuine receiving-console screenshots, public GitHub accessibility or four-member viva readiness were verified here.
- The sampled training protocol uses every training trip, not every training observation. Calibration was a prior nearest-candidate experiment and is not deployed.

## Outstanding external and team work

1. Publish the local repository through the team account and verify its public URL.
2. Run the complete deployment on two physical laptops and capture the actual receiving CMD console.
3. Confirm the organizer's reference-alignment/official scoring convention.
4. Replace requested placeholders, review interpretation/actual contributions/AI disclosure, and rehearse the viva.
5. Confirm the organizer's first-phase evaluation schedule and scope.

## Final submission closeout

All nine PARTIAL requirements were reviewed individually in `docs/PARTIAL_REQUIREMENTS_CLOSEOUT.md`. Exact physical setup, owner/admin firewall decisions, genuine receiving-console capture and publication steps are in `FINAL_HANDOFF.md`. No model/decoder tuning is part of this closeout.
No dataset license/redistribution terms were found in the supplied ZIPs. A curated publication snapshot omits raw/bulk point data and private Git history; dependency metadata is recorded in `THIRD_PARTY_NOTICES.md`. Source-license selection and dataset-derived publication permission remain team/organizer decisions. Public publication remains unverified.
Submission checks in `results/submission/submission_checks.json` verify that runtime/model files remain frozen, check recognizable secrets/history and file sizes, and compare deployment members. Deployment provenance and full ZIP-to-commit checks are generated under `packages/` after the final source commit.

## Requirement-by-requirement evidence

| ID | Source | Requirement | Status | Evidence | Boundary / qualification |
|---|---|---|---|---|---|
| MG01 | Main Guidelines p1-2 | End-to-end noisy GPS to road reconstruction | **PASS** | `pathsnap/core.py`<br>`pathsnap/service.py`<br>`results/api_verification.json` |  |
| MG02 | Main Guidelines p2 | Read/understand the five supplied documents | **PASS** | `docs/REQUIREMENTS_CHECKLIST.md`<br>`FINAL_READINESS_AUDIT.md` |  |
| MG03 | Main Guidelines p2 | Independent processing, feature engineering and model comparison | **PASS** | `scripts/prepare.py`<br>`scripts/train.py`<br>`results/critical_audit/model_replay.json` |  |
| MG04 | Main Guidelines p2 | Bayesian optimisation and saved artifacts | **PASS** | `results/bayesian_trials.csv`<br>`results/critical_audit/bayesian_log_verification.json`<br>`artifacts/model.joblib` |  |
| MG05 | Main Guidelines p2 | HMM/Viterbi and candidate/road correspondence | **PASS** | `pathsnap/decoder.py`<br>`tests/test_critical_audit.py::test_viterbi_matches_exhaustive_path_enumeration` | Uses explicitly disclosed proportional transition potentials; stochastic row-normalized alternative tested and rejected. |
| MG06 | Main Guidelines p2 | Laptop 1 model/API/graph/server scoring | **PASS** | `backend/app.py`<br>`docs/LAPTOP1_SETUP.md`<br>`results/api_verification.json` | Verified as isolated-environment process on this machine. |
| MG07 | Main Guidelines p2 | Laptop 2 UI reaches actual Laptop 1 | **PARTIAL** | `results/browser_qa.json`<br>`docs/DEPLOYMENT.md` | Separate origins tested locally; physical machines/network not available. |
| MG08 | Main Guidelines p2 | Integration and final report | **PASS** | `results/browser_qa.json`<br>`output/pdf/PathSnap_Technical_Report.pdf` |  |
| DE01 | Dataset Exploration p1-3 | Exactly 80 train and 10 student-test trips | **PASS** | `results/dataset_inventory.csv`<br>`results/dataset_integrity.json` |  |
| DE02 | Dataset Exploration p1-2 | Column meanings, zero-based node/arc IDs, directed connections | **PASS** | `pathsnap/core.py`<br>`docs/METHODOLOGY.md`<br>`tests/test_critical_audit.py::test_index_files_reject_nonintegers_and_invalid_values` |  |
| DE03 | Dataset Exploration p2 | Do not equate route rows with GPS rows | **PASS** | `pathsnap/core.py::reference_labels`<br>`scripts/critical_accuracy_audit.py`<br>`results/critical_audit/accuracy_audit.json` |  |
| DE04 | Dataset Exploration p2 | File availability, counts, types, GPS/graph/reference sizes | **PASS** | `results/dataset_inventory.csv`<br>`results/dataset_integrity.json` |  |
| DE05 | Dataset Exploration p2 | Missing/invalid points, timestamp order and gaps | **PASS** | `pathsnap/core.py`<br>`results/dataset_inventory.csv`<br>`tests/test_pipeline.py::test_invalid_timestamp_rejected` |  |
| DE06 | Dataset Exploration p2 | Geographic extent, coordinate order and plausible ranges | **PASS** | `results/dataset_inventory.csv`<br>`tests/test_pipeline.py::test_invalid_coordinate_rejected`<br>`scripts/figures.py` |  |
| DE07 | Dataset Exploration p2 | Connectivity, components and isolated nodes | **PASS** | `pathsnap/core.py::inventory`<br>`results/dataset_inventory.csv` |  |
| DE08 | Dataset Exploration p2 | Investigate unusual trips and large GPS gaps | **PASS** | `results/dataset_inventory.csv`<br>`docs/METHODOLOGY.md`<br>`results/critical_audit/accuracy_audit.json` |  |
| DE09 | Dataset Exploration p2-3 | Physically meaningful geographic distances | **PASS** | `pathsnap/core.py`<br>`docs/METHODOLOGY.md` | Local equirectangular approximation; not a global survey projection. |
| DE10 | Dataset Exploration p3 | Reference limitations and assumptions disclosed | **PASS** | `docs/METHODOLOGY.md`<br>`results/critical_audit/accuracy_audit.json` |  |
| DE11 | Dataset Exploration p3 | Whole-trip partitions and training-only preprocessing fit | **PASS** | `scripts/train.py::cv_run`<br>`results/training_split_manifest.json`<br>`results/critical_audit/model_replay.json` |  |
| DE12 | Dataset Exploration p3 | No evaluator data used for model/features/tuning | **PASS** | `scripts/train.py`<br>`scripts/decoder_improvement_audit.py` | Experiment inputs explicitly target supplied train/student-test only; no evaluator files supplied. |
| DE13 | Dataset Exploration p3 | Keep evaluator ground truth separate from prediction | **PASS** | `tests/test_pipeline.py::test_inference_never_reads_reference`<br>`tests/test_critical_audit.py::test_reference_failure_does_not_destroy_prediction`<br>`backend/app.py` |  |
| DE14 | Dataset Exploration p3-4 | Retain inventory, statistics, GPS/maps and quality decisions | **PASS** | `results/figures/dataset_overview.png`<br>`results/maps/development_trip_00000007.html`<br>`docs/METHODOLOGY.md` |  |
| MT01 | Models and Training p1-3 | At least five distinct algorithms across families | **PASS** | `results/model_comparison.csv`<br>`results/critical_audit/model_replay.json` | Seven algorithms plus tuned and candidate variants. |
| MT02 | Models and Training p2 | Configurations, seeds, experiment logs and results | **PASS** | `results/configurations/HistGradientBoosting.json`<br>`artifacts/manifest.json`<br>`results/cv_folds.json` |  |
| MT03 | Models and Training p2 | Use all 80 training trips for fit/CV; ten student trips for comparison | **PASS** | `artifacts/manifest.json`<br>`results/training_split_manifest.json`<br>`results/api_verification.json` | Training samples up to 450 observations per trip; all student observations scored. |
| MT04 | Models and Training p2-4 | Consistent preprocessing and evidence-based selection | **PASS** | `scripts/train.py`<br>`results/critical_audit/model_replay.json`<br>`artifacts/manifest.json` |  |
| MT05 | Models and Training p3 | Accuracy, precision, recall, F1 and confusion matrices | **PASS** | `results/model_comparison.csv`<br>`results/model_per_trip.json`<br>`results/adaptive_model_per_trip.json` |  |
| MT06 | Models and Training p3 | Log loss, Top-1 and candidate miss rate | **PASS** | `pathsnap/metrics.py`<br>`results/model_comparison.csv` |  |
| MT07 | Models and Training p3-4 | Route continuity, sequence performance and timing | **PASS** | `results/model_route_metrics.csv`<br>`results/route_comparison.csv`<br>`results/training_diagnostics.json` |  |
| MT08 | Models and Training p3-4 | Primary metric and probability/speed/complexity justification | **PASS** | `artifacts/manifest.json`<br>`docs/METHODOLOGY.md`<br>`output/pdf/PathSnap_Technical_Report.pdf` |  |
| MT09 | Models and Training p4 | Bayesian space, objective, grouped CV, trial record, best config, refit and cost | **PASS** | `scripts/train.py`<br>`results/bayesian_trials.csv`<br>`results/critical_audit/bayesian_log_verification.json` |  |
| MT10 | Models and Training p4 | Untuned/tuned comparison on identical protocols | **PASS** | `results/model_comparison.csv`<br>`results/critical_audit/model_replay.json` |  |
| MT11 | Models and Training p4-5 | States, emissions, transitions and Viterbi recurrence explained | **PASS** | `docs/METHODOLOGY.md`<br>`docs/VIVA_GUIDE.md`<br>`pathsnap/decoder.py` | No claim that production transition rows are stochastic probabilities. |
| MT12 | Models and Training p5 | Missing candidates, invalid transitions and GPS gap handling | **PASS** | `pathsnap/decoder.py`<br>`tests/test_pipeline.py::test_gap_reset_is_explicit`<br>`results/critical_audit/clean_environment_tests.txt` |  |
| MT13 | Models and Training p5 | One predicted road per relevant observation | **PASS** | `scripts/verify_api.py`<br>`results/api_verification.json` |  |
| MT14 | Models and Training p5 | Classifier-only versus sequence decoding and continuity analysis | **PASS** | `results/route_comparison.csv`<br>`results/figures/route_comparison.png` |  |
| MT15 | Models and Training p5 | Decoder tuning on permitted data only | **PASS** | `scripts/evaluate_routes.py`<br>`results/critical_audit/improvement_protocol.json` | Original decoder uses student-test development tuning; new prior uses training-only replay gates. |
| MT16 | Models and Training p5-6 | All ten actual reserved evaluator trips work | **PASS** | `backend/app.py`<br>`docs/DEPLOYMENT.md` | All ten newly supplied evaluator trips passed frozen-model inference and exact reference geometry checks: `results/evaluator_verification.json`; physical execution remains covered by MG07. |
| MT17 | Models and Training p6 | Server computes accuracy with internal references | **PARTIAL** | `backend/app.py`<br>`results/api_verification.json` | Derived-alignment scorer verified; official pointwise reference/scorer convention unresolved. |
| MT18 | Models and Training p6 | Live API calls/logs; no hardcoded outputs or bypass | **PASS** | `backend/app.py`<br>`results/server_log_excerpt.txt`<br>`results/api_verification.json` |  |
| MT19 | Models and Training p6 | Independent implementation and artifact explanation | **PARTIAL** | `docs/VIVA_GUIDE.md`<br>`docs/SUBMISSION.md` | Experiments executed here; actual four-person understanding/ownership still requires team review. |
| DL01 | Deliverables p1 | Public GitHub repository committed and pushed | **FAIL** | `docs/SUBMISSION.md` | Local Git repository exists; no public remote has been created/verified. |
| DL02 | Deliverables p1-2 | Complete data/feature/training/evaluation/tuning/decoder/API/UI source | **PASS** | `pathsnap/core.py`<br>`scripts/train.py`<br>`backend/app.py`<br>`ui/app.js` |  |
| DL03 | Deliverables p1-2 | Artifacts, configs, logs, CSVs, maps and deployment files | **PASS** | `artifacts/model.joblib`<br>`results/bayesian_trials.csv`<br>`scripts/figures.py`<br>`requirements.lock.txt` |  |
| DL04 | Deliverables p2 | README, installation/execution/deployment and organized folders | **PASS** | `README.md`<br>`docs/LAPTOP1_SETUP.md`<br>`docs/LAPTOP2_SETUP.md` |  |
| DL05 | Deliverables p2 | No committed secrets or private credentials | **PASS** | `scripts/audit.py`<br>`.gitignore` | Heuristic token/path scan, not a general security certification. |
| DL06 | Deliverables p2 | One consolidated PDF with prescribed sections and genuine results | **PASS** | `output/pdf/PathSnap_Technical_Report.pdf`<br>`scripts/report.py` |  |
| DL07 | Deliverables p2 | EDA, preprocessing, features, missing values, GPS and road maps | **PASS** | `results/dataset_inventory.csv`<br>`results/figures/dataset_overview.png`<br>`results/maps/development_trip_00000007.html` |  |
| DL08 | Deliverables p3 | Overall table with model/family/config/CV F1/Top-1/continuity/test F1/log loss/time | **PASS** | `output/pdf/PathSnap_Technical_Report.pdf`<br>`results/model_comparison.csv`<br>`results/model_route_metrics.csv` | Consolidated required-field table added in audit appendix. |
| DL09 | Deliverables p3-4 | Every trained model: suitability, strengths/limits, hyperparameters, objective and actual test results | **PASS** | `scripts/report.py`<br>`results/configurations/MLP.json`<br>`results/model_comparison.csv` |  |
| DL10 | Deliverables p4 | Over/underfitting evidence connected to actual experiments | **PASS** | `results/training_diagnostics.json`<br>`results/cv_folds.json`<br>`output/pdf/PathSnap_Technical_Report.pdf` |  |
| DL11 | Deliverables p4 | Real CV/test F1, Top-1 and log-loss comparison plots | **PASS** | `results/figures/model_comparison.png`<br>`results/figures/log_loss.png` |  |
| DL12 | Deliverables p4 | No artificial training/validation curves | **PASS** | `results/figures/mlp_loss.png`<br>`scripts/figures.py` | Only actual MLP training history plotted; no validation-loss history claimed. |
| DL13 | Deliverables p5 | Bayesian questions and tuned/untuned metrics | **PASS** | `results/bayesian_trials.csv`<br>`artifacts/manifest.json`<br>`output/pdf/PathSnap_Technical_Report.pdf` |  |
| DL14 | Deliverables p5-6 | HMM design questions, comparisons, improvement/failure discussion | **PASS** | `docs/VIVA_GUIDE.md`<br>`results/route_comparison.csv`<br>`results/critical_audit/training_holdout_decoder.csv` |  |
| DL15 | Deliverables p6 | Mandatory actual Folium GPS/network/reference/predicted layers, colors, legend, extent and controls | **PASS** | `results/maps/development_trip_00000007.html`<br>`scripts/figures.py`<br>`results/screenshots/folium_development_map.png` |  |
| DL16 | Deliverables p6 | Interactive map/code retained and representative screenshot in report | **PASS** | `results/maps/development_trip_00000007.html`<br>`output/pdf/PathSnap_Technical_Report.pdf` |  |
| DL17 | Deliverables p6 | Actual working UI screenshot | **PASS** | `results/screenshots/ui_desktop.png`<br>`results/screenshots/ui_mobile.png`<br>`results/browser_qa.json` |  |
| DL18 | Deliverables p6 | Genuine successful receiving-laptop CMD screenshot | **FAIL** | `docs/DEPLOYMENT.md`<br>`results/server_log_excerpt.txt` | Real local logs exist; no CMD screenshot of the physical receiving laptop has been captured. |
| DL19 | Deliverables p7 | Submitted source matches final demonstrated system | **PARTIAL** | `scripts/package.py`<br>`docs/SUBMISSION.md` | Local artifact/package consistency verified; team must use final commit at external demo. |
| DL20 | Deliverables p1 | First-phase evaluation before lunch | **PARTIAL** | `docs/DEMO_SCRIPT.md` | Organizer schedule and phase scope are external; not invented. |
| DL21 | Deliverables p7 | AI disclosure, original analysis and each member can defend claims | **PARTIAL** | `docs/VIVA_GUIDE.md`<br>`team.json`<br>`docs/SUBMISSION.md` | AI-assisted draft disclosed; team interpretation and names remain placeholders by request. |
| AP01 | Assessment p1 | Meaningful >=5-model experimentation, tuning and retained records | **PASS** | `results/critical_audit/model_replay.json`<br>`results/critical_audit/bayesian_log_verification.json` |  |
| AP02 | Assessment p1 | Correctness, reproducibility, evidence beyond one high score | **PASS** | `results/critical_audit/accuracy_audit.json`<br>`results/critical_audit/clean_environment_tests.txt`<br>`docs/METHODOLOGY.md` |  |
| AP03 | Assessment p2 | No fabricated experiments, graphs, claims or implementation details | **PASS** | `scripts/verify_experiments.py`<br>`results/critical_audit/experiment_replay_checks.json`<br>`scripts/report.py` | Claims are bounded to retained execution evidence; no universal originality certification. |
| AP04 | Assessment p2 | No sharing another team code/weights/results | **PARTIAL** | `docs/SUBMISSION.md` | No other-team material used in this session; interteam behavior outside this environment cannot be audited. |
| AP05 | Assessment p2-3 | Every member explains/reproduces work in viva | **PARTIAL** | `docs/VIVA_GUIDE.md`<br>`docs/DEMO_SCRIPT.md` | Guide and cross-examination plan supplied; human understanding cannot be certified here. |
| AP06 | Assessment p3 | No evaluator leakage or hardcoded predictions | **PASS** | `tests/test_pipeline.py::test_inference_never_reads_reference`<br>`backend/app.py`<br>`results/critical_audit/partition_overlap.json` |  |
| AP07 | Assessment p3 | Source/history/artifacts/results available for investigation | **PASS** | `results/artifact_checksums.json`<br>`results/dataset_integrity.json`<br>`docs/SUBMISSION.md` | Local repository and packages prepared; public publication remains DL01 FAIL. |
| U01 | User audit request | Fresh isolated install, dependency check and actual execution | **PASS** | `results/critical_audit/clean_environment_install.json`<br>`results/critical_audit/clean_environment_tests.txt`<br>`results/api_verification.json` |  |
| U02 | User audit request | Exact two-laptop packages, launch commands and troubleshooting | **PASS** | `scripts/package.py`<br>`docs/LAPTOP1_SETUP.md`<br>`docs/LAPTOP2_SETUP.md`<br>`docs/DEPLOYMENT.md`<br>`results/critical_audit/package_execution.json` |  |
| U03 | User audit request | Comprehensive viva and short demonstration script | **PASS** | `docs/VIVA_GUIDE.md`<br>`docs/DEMO_SCRIPT.md` |  |

## Transfer and execution

- Laptop 1: `packages/PathSnap_Laptop1_Backend.zip`; see `docs/LAPTOP1_SETUP.md`.
- Laptop 2: `packages/PathSnap_Laptop2_UI.zip` only; no dataset, model or reference labels. See `docs/LAPTOP2_SETUP.md`.
- `packages/checksums.json` and `packages/transfer_manifest.json` describe exact archive content and hashes.
- Clean-environment and package smoke tests are local. Physical networking remains PARTIAL.
- Final source commit and clean-tree status are reported after committing; verify with `git log -1 --oneline` and `git status --porcelain`. The PDF/source evidence cannot contain its own final commit hash without changing that commit.


## Supplied evaluator ZIP and comparison UI update

The later-supplied evaluator ZIP contains ten complete trips and 19,674 observations, including supplied `.route` references. It is imported under `data/evaluator_test/`; raw files remain excluded from Git/publication. All ten frozen-model requests and exact reference-geometry checks passed (`results/evaluator_verification.json`). No model, feature, decoder or hyperparameter was selected using these results. The original prediction functions remain unchanged; `GET /api/reference/{trip_id}` is a separate display-only endpoint, requested after prediction. Set `PATHSNAP_REFERENCE_DISPLAY=0` to disable display.

Untuned evaluator replay: **95.4855% equal-trip / 95.1510% pooled derived-reference agreement**, not official evaluator accuracy. The thirty-test suite and responsive browser checks passed; see `tests/test_reference_display.py` and `results/browser_qa.json`. MT16 is now locally PASS; physical two-laptop execution and official scoring remain unverified. The original nine-item closeout document is retained as a historical checklist; eight requirements remain PARTIAL.
