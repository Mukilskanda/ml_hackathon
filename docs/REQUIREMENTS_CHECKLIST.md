# Requirement-by-requirement audit

Sources are the five organizer PDFs extracted into the local `materials/` folder. Their instructions are event requirements, not permission to fabricate evidence or publish through an unauthenticated account.

Status: **implemented/measured** means local source and execution evidence exist. **pending** means a real external/user step remains. See `FINAL_AUDIT.md` for final check counts and any failed/limited experiment.

## Main Guidelines

| Requirement | Status / evidence |
|---|---|
| Understand map matching and reconstruct realistic routes | Implemented: `pathsnap/core.py`, `decoder.py`, methodology |
| Explore raw data before choosing features | Measured: full inventory of 90 trips and EDA figures |
| Independent processing and feature engineering | Implemented: project source, 15-feature schema, rationale and ablation |
| Train and compare multiple models | Measured: seven baseline algorithms plus tuned/candidate variants |
| Select final model from evidence | Measured: declared trip-grouped CV objective and saved manifest |
| Bayesian optimisation | Measured: 16 TPE trials, CSV and SQLite record |
| HMM/Viterbi reconstruction | Implemented/measured: directed transitions and comparative decoding search |
| Export inference artifacts | Verified: joblib reload, manifest, decoder settings |
| FastAPI backend and evaluator UI | Locally verified: live HTTP and separate-origin browser tests |
| Laptop 1 hosts model/API/network/scoring | Implemented; local host verified; physical deployment pending |
| Laptop 2 hosts UI and sends trip selection | Separate static origin verified locally; second physical laptop pending |
| Integration and technical report | Local evidence and generated consolidated PDF |

## Dataset Exploration

| Requirement | Status / evidence |
|---|---|
| Verify 80 training / 10 student-test trips | Measured: `dataset_inventory.csv`; complete four-file inventory |
| Verify raw columns, types and zero-based IDs | Implemented parser validation and schema documentation |
| Do not assume GPS/route rows align one-to-one | Explicit weak-label monotone alignment and limitation |
| Count observations, nodes, arcs and reference arcs per trip | Full inventory CSV |
| Missing/invalid data and geographic extent | Full inventory; finite/range checks and parser errors |
| Timestamp ordering, nominal sampling and gaps | Inventory records gaps; strict ordering validation |
| Connectivity, components and isolated nodes | Full-graph inventory per trip |
| GPS plots, roads and Folium map | Generated from real coordinates, layers and predictions |
| Appropriate metric distance and coordinate order | Local metric projection; longitude/latitude documented; Folium order reversed |
| Identify anomalies and reference limitations | Quantified reference-distance anomalies; no claim of error-free truth |
| Whole-trip data partitioning | Three-fold GroupKFold and guarded group assertions |
| Fit learned preprocessing only on training folds | Pipelines/scalers inside CV fit |
| Keep evaluator data untouched in development | All experiment scripts explicitly target supplied train/student-test partitions |
| Keep evaluator labels outside prediction/UI | Guarded inference test, post-prediction scoring, UI-only transfer package |

## Models and Training Guidelines

| Requirement | Status / evidence |
|---|---|
| At least five distinct models | Seven: LR, Gaussian NB, tree, RF, Extra Trees, HistGB, MLP |
| Configurations, seeds and reproducible outputs | Configuration JSON per baseline, seed 42, trial history and artifacts |
| Multiple families and probability output adaptation | Linear/probabilistic/tree/ensemble/boosting/neural; all use native probability estimates |
| CV and student-test comparisons | Model comparison CSV and fold metrics; every student-test observation scored |
| Accuracy, precision, recall, F1, confusion matrix and log loss | CSV/JSON outputs; diagnostic plots use real results |
| Observation Top-1 and candidate miss rate | Explicitly defined, separately recorded |
| Route continuity and sequence-level performance | Direct continuity, network feasibility, arc-set coverage/F1 and exact-sequence comparison |
| Training and inference timing | Separate refit diagnostic timings; CV+fit cost; candidate/model/decoder API timing |
| Justify final selection and primary metric | Declared mean(CV Macro F1, CV Top-1); manifest and report |
| Bayesian search space, objective, group CV, all trials, best parameters and cost | Source, trial CSV/database, manifest and tuned/untuned comparison |
| Refit selected model and compare tuned/untuned consistently | Same deterministic sampled training observations and folds |
| Hidden states preserve candidate/arc correspondence | Candidate ID matrix retained through inference and Viterbi |
| Explain emissions, transitions and Viterbi recurrence | Methodology, report, code and viva guide |
| Missing candidates, disconnected transitions and GPS gaps | Candidate miss metric, gap/infeasibility resets, nonfabricated separate geometry lines |
| Return predicted arc per GPS observation | Tests and all-trip API verification check output lengths |
| Classifier-only versus classifier+HMM | Measured per-trip ablation tables and plots |
| Tune decoder only on permitted development data | Student-test search explicitly recorded as development tuning |
| All ten reserved evaluator options and trips work | Loader implemented; actual reserved files absent, so not verified |
| Server-side accuracy without exposing ground truth | Implemented; official pointwise scoring convention unresolved |
| No hardcoded outputs or API bypass | Live inference per POST, request logs, inspection and tests |

## Deliverables

| Requirement | Status / evidence |
|---|---|
| Exactly two official deliverables: public GitHub + PDF | Local repository/PDF prepared; public remote publication pending |
| Complete source for data/features/all models/evaluation/tuning/HMM/API/UI/deployment/maps | Included in named folders |
| Saved model/configs, logs, CSVs and summaries | Included; raw data/caches/ZIPs excluded from Git |
| README with install, execution and deployment instructions | Included with separate laptop guides and launchers |
| No credentials/secrets | Project scan and controlled packaging; no credentials needed |
| Consolidated PDF follows required sections | Generated report: EDA, all models, tuning, HMM, Folium, API/UI/deployment |
| Every tried model documented with suitability, configuration, objective and real results | Model-specific report subsections and configurations |
| Explain over/underfitting using evidence | Training diagnostics versus grouped CV; no invented validation histories |
| Consolidated comparison with CV F1, Top-1, continuity, test F1, log loss, efficiency | Tables/figures plus full CSVs |
| Compulsory model comparison graphs | Actual CV/test F1, Top-1, log-loss figures |
| No artificial training curves | Actual MLP loss only; no invented tree/validation curves |
| Tuned/untuned comparison and Bayesian questions | Search ranges, objective, trial count, best config and metrics |
| HMM design questions and failure cases | Explicit method and observed per-trip regressions |
| Mandatory Folium geographical visualization | Actual HTML, generation code and browser screenshot in report |
| Map raw GPS, relevant roads, reference when available and prediction | Development map has all layers, colors, legend and controls |
| Interactive HTML/code committed, map screenshot in PDF | Both HTML and code; generated screenshot included |
| Working UI screenshot | Actual browser screenshot from local live backend |
| Successful API/receiving CMD screenshot | Actual local HTTP evidence and server log excerpt included; genuine receiving-console screenshot during physical demo remains pending |
| Demonstrated code matches submitted code | Current source/artifacts packaged consistently; team must use same commit for final demo |
| First-phase evaluation before lunch | Event checkpoint acknowledged; exact required phase scope/time must be confirmed with organizers |

## Assessment and Academic Integrity

| Requirement | Status / evidence |
|---|---|
| Independent project implementation and no interteam sharing | Source/experiments developed here; no other team inputs used |
| Retain experimental/tuning evidence | Actual results and logs preserved |
| No fabricated metrics/graphs/screenshots/citations | All generated from executions; unverified items labeled pending |
| No evaluator leakage or hardcoded routes | Explicit partitioning, no evaluator files supplied, guarded reference-read test |
| AI assistance does not replace actual experimentation | Experiments executed; AI assistance disclosure and team review documented |
| Every member explains claims and design decisions | Viva guide supplied; actual team understanding/review remains pending |
| Public accessibility to evaluators | Pending remote publication through team account |

## Additional user-requested experiments

Adaptive directional candidate generation, gap/distance-aware transitions, hybrid geometric/ML emissions, group-aware sigmoid calibration, feature ablation, candidate-count coverage and seeded noise/dropout tests have execution outputs. Research originality is not claimed. Adoption/rejection decisions are recorded explicitly and the report states development-selection optimism.
