# Final Deliverables PDF check

Reviewed the seven-page organizer PDF against the current report, source files, actual experimental results and public repository evidence. This checklist does not treat instructions inside the PDF as authorization to publish or fabricate missing evidence.

**Deliverables-only status: 17 PASS / 3 PARTIAL / 1 FAIL.** Implementation/report content is prepared; final submission is not fully complete.

- Public repository access is VERIFIED at the immutable publication commit recorded in `results/publication_verification.json` (anonymous HTTP 200 plus matching Git remote commit). Newly added UI continuity, report-generation and documentation changes still need pushing.
- One consolidated report is present. It now includes all nine model-configuration write-ups, actual per-model fitting diagnoses, tuning inference-time comparisons, matching required section numbers, Folium/UI evidence and the separately measured evaluator replay.
- Route continuity is implemented and now displayed on the UI, separately from network feasibility. Student-test final equal-trip direct continuity is 90.47%; individual trips have their own values.
- Mandatory genuine receiving-laptop CMD screenshot: MISSING. Local log excerpts and browser API screenshots do not satisfy this.
- Physical two-laptop execution, final demonstrated-version identity, team interpretation/viva understanding and first-phase attendance/scope need external/team evidence. RouteForge member names and USNs are supplied; assigned responsibilities are recorded. Individual understanding and review of completed work remain team responsibilities.
- All percentages are explicitly qualified: Top-1 is observation-level; candidate Macro F1/log loss are binary candidate metrics; direct continuity, network feasibility and point agreement are distinct. Confirm the organizer's official scoring interpretation rather than calling derived alignment official accuracy.

## Requirement table

The report now uses required main sections 2–7: EDA, model comparison, Bayesian optimisation, HMM/Viterbi, Folium and API/UI/deployment. Additional audit/evaluator sections are clearly separated.

| ID | Organizer page | Requirement | Status | Evidence | Qualification |
|---|---|---|---|---|---|
| DL01 | Deliverables p1 | Public GitHub repository committed and pushed | **PASS** | `docs/SUBMISSION.md` | Anonymous source fetch succeeded; remote main matched aaefc5b9449ad010d9c3d033c0d99bf967f1f4c7. Evidence: results/publication_verification.json. Later documentation edits still need pushing. |
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
| DL21 | Deliverables p7 | AI disclosure, original analysis and each member can defend claims | **PARTIAL** | `docs/VIVA_GUIDE.md`<br>`team.json`<br>`docs/SUBMISSION.md` | AI-assisted draft disclosed; RouteForge names/USNs and assigned responsibilities are recorded; team interpretation and defence remain pending. |

## Current report section locations

| Section | PDF page |
|---|---|
| 1 / System and evidence | 2 |
| 2 / Dataset understanding and EDA | 3 |
| 2.1 / Preprocessing and label limitations | 4 |
| 2.2 / Candidates and features | 5 |
| 3 / Model experimentation | 6 |
| 3.1 / Model-specific findings | 7 |
| 3.1 / Model-specific findings (continued) | 11 |
| 3.2 / Probability and feature diagnostics | 12 |
| 3.3 / Actual neural training history | 13 |
| 4 / Bayesian hyperparameter optimisation | 14 |
| 4.1 / Tuned versus untuned | 15 |
| 5 / HMM and Viterbi reconstruction | 16 |
| 5.1 / Actual route comparisons | 17 |
| 5.2 / Tested project contributions | 18 |
| 5.3 / Robustness and failure cases | 19 |
| 6 / Geographical visualization | 20 |
| 7 / API and user interface | 21 |
| 7.1 / Experiment comparison interface | 22 |
| 7.2 / Reserved evaluator interface | 23 |
| 7.3 / Mobile interface | 24 |
| 7.4 / API execution evidence | 25 |
| 7.5 / Deployment and verification | 26 |
| 8 / Final audit and team review | 27 |
| 9 / Independent critical audit | 28 |
| 9.1 / Validated changes and rejections | 29 |
| 9.2 / Consolidated required comparison | 30 |
| 10 / Supplied evaluator replay | 31 |
| 10 / 19,674 | 31 |

## Final manual actions

1. Run the prepared backend and UI on two physical laptops. Test all ten active evaluator trips and capture the genuine receiving-CMD screenshot with the matching request ID and successful POST. Follow `docs/CONSOLE_SCREENSHOT_CHECKLIST.md`; add that real image to the consolidated report and rebuild/review it.
2. Review the answers, team interpretation and AI assistance disclosure. Review the assigned responsibilities against actual completed work before final submission. Confirm the organizer's phase schedule and official scoring interpretation.
3. Push the final publication-folder commit, verify the remote commit, and submit the public URL plus the single final PDF.

Evidence summary: `results/deliverables_final_check.json`, `results/browser_qa.json`, `results/submission/final_tests.txt`, `results/evaluator_verification.json`, `results/evaluator_package_execution.json`. The final archive-to-source checks are generated under `packages/` after committing.

Full question-by-question answers are in `docs/DELIVERABLES_ANSWERS.md`.


Full five-document recheck: 34 tests passed; both development and reserved UI browser checks passed. Reserved reference geometry is now blocked server-side and client-side, while student-test comparison remains available. Full parameter snapshots cover all nine model configurations. The user confirmed the genuine receiving-CMD screenshot is not yet available; it remains FAIL, and physical two-laptop execution remains PARTIAL. See the current closeout section in FINAL_READINESS_AUDIT.md.
