# PathSnap

An end-to-end candidate classifier and directed-road HMM for noisy GPS map matching. This repository contains executed experiments, trained artifacts, a FastAPI inference server, a separate browser UI, Folium maps, tests, and a generated technical report.

**For final deployment and submission, start with [FINAL_HANDOFF.md](FINAL_HANDOFF.md).** No further model tuning is required. It contains exact laptop commands, network/firewall prerequisites, expected logs, screenshot evidence and manual actions. All nine PARTIAL items have a local-preparation closeout in [docs/PARTIAL_REQUIREMENTS_CLOSEOUT.md](docs/PARTIAL_REQUIREMENTS_CLOSEOUT.md); external outcomes remain unverified.

The refreshed interface includes a larger route canvas, trip diagnostics, readable model names, the selected-model badge, ordered decoder comparisons, and connection settings on mobile. Loading and failed-request states identify what is currently displayed; JSON export contains the actual server response. Browser checks cover live inference, export, connection recovery and 320â€“1024 px layouts. This interface update changes no model, prediction logic, decoder settings or development experimental results. A separate comparison endpoint now serves supplied reference geometry after prediction. Reload with Ctrl+F5 after replacing the UI files.

**Publication boundary:** use the curated `packages/PathSnap_Publication_Source/` snapshot or its ZIP, following [docs/PUBLICATION.md](docs/PUBLICATION.md). Do not directly push private development history or upload deployment/full-local ZIPs. The curated snapshot omits raw/bulk per-point data and location-bearing generated outputs; the final PDF is a separate event deliverable. Omitted evidence can be regenerated with legitimately supplied data. See [dataset/source permissions](docs/LICENSING_AND_DATA.md) and [dependency notices](THIRD_PARTY_NOTICES.md).

**Read [FINAL_READINESS_AUDIT.md](FINAL_READINESS_AUDIT.md) before claiming evaluation readiness.** It contains the PASS/PARTIAL/FAIL table against all five PDFs. Local tests cannot establish physical two-laptop connectivity or official evaluator accuracy. All pointwise development scores use a documented alignment derived from supplied reference routes, not independent point labels.

## Quick demonstration on this laptop

Python 3.13 was used for the recorded experiments. Python 3.11-3.13 with the pinned dependencies is recommended; use scikit-learn **1.7.2** when loading the supplied pickle artifacts.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --access-log
```

Open <http://localhost:8000>. The UI is also served by the backend for convenient local testing. For the required separate UI process:

```powershell
python -m http.server 8080 --directory ui
```

Open <http://localhost:8080>, click the connection settings gear, and configure the API server URL. Run `run_backend.cmd [port]` on Laptop 1 and `run_ui.cmd [port]` on Laptop 2; both ports are configurable. `setup_backend.cmd` performs the initial backend virtual-environment setup.

## Two-laptop deployment

1. Keep the backend, artifacts, results and raw data on Laptop 1. Run the backend bound to `0.0.0.0`.
2. Transfer **only `packages/PathSnap_Laptop2_UI.zip`** to Laptop 2 and extract it. It contains `ui/`, `run_ui.cmd`, and its setup guide. It contains no model, reference labels, or raw dataset.
3. Put both laptops on the same reachable network. Find Laptop 1's IPv4 address using `ipconfig` on that laptop. No particular LAN address is embedded in the project.
4. Run the UI launcher on Laptop 2 and open its localhost URL. Configure `http://<Laptop1-IPv4>:<backend-port>` in the gear menu.
5. Verify the health check and reconstruct **all ten** active trips. Confirm incoming request IDs in the console on Laptop 1. Follow `docs/DEPLOYMENT.md`.
6. The supplied evaluator ZIP is now imported locally: the app lists **ten evaluator trips** and says EVALUATOR MODE. Without that private folder, it falls back to the ten student-test development trips.
7. When organizers supply the reserved data, place trip folders at `data/evaluator_test/000000XX/000000XX.track`, `.nodes`, `.arcs`, and optionally `.route`. If that directory contains trips, it becomes the active partition. The backend reads only the three inference files until prediction finishes; `.route` is read by the separate scorer and comparison endpoint. Reference files remain on Laptop 1; the browser can display their geometry after prediction.

The official evaluator's pointwise reference/scoring convention must be confirmed with organizers. The supplied `.route` files describe traversed arc sequences, not one label per GPS sample. Our derived alignment is explicitly described in `docs/METHODOLOGY.md`.

## Reproduce the experiments

Extract the original Student folder ZIP into `data/`, retaining `data/Student folder/train/<trip>/` and `data/Student folder/student_test/<trip>/`. Do not include reserved evaluator data in development commands.

```powershell
python scripts/prepare.py
python scripts/train.py
python scripts/ablate.py
python scripts/calibrate.py
python scripts/evaluate_routes.py
python scripts/adaptive_candidates.py
python scripts/train_adaptive.py
python scripts/evaluate_routes.py
python scripts/robustness.py
python scripts/diagnostics.py
python scripts/figures.py
python -m pytest -q
```

`train.py` fits seven baselines and performs 16 Optuna TPE trials on the shortlisted tree family. `train_adaptive.py` is a controlled candidate-selection experiment using the same sampled GPS observations, folds and tuned parameters; it adopts the adaptive variant only if its declared CV objective improves. The second route evaluation tunes the decoder for the selected model. `calibrate.py` is a separate group-aware probability diagnostic; it is not silently substituted for the selected model.

**Cache and resume:** `prepare.py` reuses per-trip candidate caches. Delete only the relevant cache files if changing preprocessing or features. `train.py` resumes the named Optuna study in `results/optuna.db`; for a fully fresh independent run, archive that database first. Do not run the selection scripts repeatedly against already-selected artifacts: start with `train.py`, then follow the sequence above. Training uses a deterministic maximum of 450 observations per training trip for bounded runtime and balanced trip representation, all eight candidates per selected observation, and all 80 training trips. Student-test evaluation uses every observation. Raw trip EDA and candidate coverage use every supplied observation.

`python scripts/verify_api.py` runs all active trips through a live local API. `python scripts/browser_qa.py` uses Playwright to test and screenshot the browser UI; install Playwright and Chromium only if rerunning that optional tool. `python scripts/report.py` rebuilds the report from saved measurements and screenshots. `python scripts/package.py` builds the handoff ZIPs and checksums. No training occurs during an API request.

## Final critical audit and retained changes

The independent audit reproduced the original equal-trip mean as **95.2489%**, versus **94.0971% observation-weighted (18,029/19,160)**. These are derived-reference development agreements. The final soft U-turn prior gives **95.2559% equal-trip mean / 94.1284% observation-weighted**; the development aggregate gain is negligible and an individual trip regresses. Its retention is supported by a fixed training-only holdout and robustness/timing gates, not a search over student-test results.

Physical-bound Dijkstra pruning preserves every feasible transition and all ten original predicted sequences; measured transition-building time fell about threefold. Single-candidate entropy, index validation, reference-scoring isolation, incomplete partition handling, schema validation, reset-aware drawing and UI connection/keyboard behavior were hardened. A row-normalized HMM alternative and a training-matched corrected candidate-fallback refit were rejected based on training-only evidence. The deployed `historical_v1` candidate profile preserves consistency with the saved classifier; `current_v2` is an explicitly retained experimental profile, not silently substituted into serving.

The full audit replay commands, after the historical training sequence above, are:

```powershell
python scripts/critical_accuracy_audit.py
python scripts/verify_experiments.py
python scripts/benchmark_decoder.py
python scripts/decoder_improvement_audit.py
python scripts/uturn_validation.py
python scripts/promote_validated_decoder.py
python scripts/corrected_candidate_refit.py
python scripts/robustness.py
```

`critical_accuracy_audit.py` uses a frozen original decoder and an independent alignment implementation to audit the original claim. `promote_validated_decoder.py` requires the training-only gate to pass. `corrected_candidate_refit.py` tests the expanded-candidate profile using the same observation sample and grouped-CV objective; it retains the original profile if the criterion falls. Do not run `evaluate_routes.py` after those final gates unless you intend to redo the audit/promotion sequence: it regenerates the original development decoder configuration. The stored original and final results are separate.

A real isolated Python 3.13 environment installed the now fully pinned dependency lock, passed `pip check`, reloaded the saved artifacts, passed the test suite and served the live API. See `results/critical_audit/clean_environment_install.json` and its test log. Install optional browser/PDF QA dependencies with `requirements-dev.txt`. The clean environment records a nonfatal Starlette/httpx deprecation warning; it is not hidden.

## Exact laptop packages

- `PathSnap_Laptop1_Backend.zip`: selected model/configuration, inference source, UI, ten student-test rehearsal trips, locked dependencies and setup guides. Use [Laptop 1 setup](docs/LAPTOP1_SETUP.md).
- `PathSnap_Laptop2_UI.zip`: only static UI, launcher and deployment/demo guides. No model, raw data or reference labels. Use [Laptop 2 setup](docs/LAPTOP2_SETUP.md).
- `PathSnap_Complete_Local.zip`: complete local source, evidence, report and supplied data backup; do not publish the dataset ZIP by default.
- `packages/transfer_manifest.json`: exact per-file membership/hashes for the two deployment packages. `packages/checksums.json` hashes each archive.

Read [the viva guide](docs/VIVA_GUIDE.md) and [three-minute demonstration script](docs/DEMO_SCRIPT.md). Team understanding, public GitHub publication, physical networking/console screenshots and the organizer's official scorer remain external checks.

## Project layout

| Folder | Contents |
|---|---|
| `pathsnap/` | Parsing, projected geometry, candidate features, directed-graph decoder, inference and scoring metrics |
| `backend/` | FastAPI endpoints, input validation, isolated post-prediction reference scoring |
| `ui/` | Responsive HTML/CSS/JavaScript interface; no frontend build needed |
| `scripts/` | Reproducible preparation, training, optimisation, ablation, robustness, figures, QA, reporting and packaging |
| `artifacts/` | Selected model, component models, manifest, decoder configuration |
| `results/` | Actual CSV/JSON results, configurations, trial history, figures, maps and screenshots |
| `docs/` | Methodology, compliance checklist, deployment instructions and viva guide |
| `output/pdf/` | Consolidated technical report |
| `packages/` | Separate UI transfer ZIP and complete local archive (generated, not committed) |
| `tests/` | Geometry, directed connectivity, candidate identity, decoding, leakage and API tests |

## API

- `GET /api/health`: selected model, decoder and active mode.
- `GET /api/trips`: actual trip options in the active partition.
- `POST /api/predict` with `{"trip_id":"00000052"}`: live predictions, geographic geometry, confidence diagnostics, timings and optional server-side metrics. Strict eight-digit ID validation prevents path traversal. Every request executes inference again and logs a unique request ID.
- `GET /api/experiments`: measured development experiment summaries.
- `GET /docs`: automatically generated OpenAPI documentation.

Predictions are never hardcoded. The server has no authentication because it is intended for a trusted local demonstration network. Do not expose it directly to the public internet. CORS permits a separate UI origin without credentials. Only load the trusted joblib artifacts produced by this project.

## Submission

Exactly two official deliverables are required: a **public GitHub repository** and **one consolidated PDF**. The local repository is prepared here, but creating/publishing a remote repository requires the team's authenticated GitHub account. Do not claim the repository is public until its URL has been verified. Follow `docs/SUBMISSION.md`.

The private workspace commit and deployed implementation are linked by `SOURCE_COMMIT.txt`/`PROVENANCE.json` in each ZIP. `scripts/submission_checks.py` verifies that runtime files and selected model/configuration still match the frozen audited implementation, scans source/history for recognizable secrets and checks publication file sizes. `scripts/prepare_publication.py` builds the separate data-minimized source snapshot without publishing it.

Replace placeholders in `team.json` and rerun `scripts/report.py`. The report is an AI-assisted technical draft grounded in execution outputs; each teammate must review the claims, add their own interpretation, accurately disclose assistance according to event rules, and be able to defend the implementation. Do not copy between teams or invent experimental evidence.

## Technical sources

- Supplied five organizer PDFs (read as task reference material).
- [scikit-learn GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html).
- [Optuna TPE sampler](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html).
- [SciPy shortest-path algorithms](https://docs.scipy.org/doc/scipy/reference/sparse.csgraph.html).
- [FastAPI documentation](https://fastapi.tiangolo.com/).
- [Folium documentation](https://python-visualization.github.io/folium/latest/).

Project contributions are engineering improvements tested within this dataset; no claim of new research priority is made.


## Supplied evaluator data and actual/predicted comparison

The later-supplied evaluator ZIP has been imported locally and tested with the frozen pipeline: 10 trips, 19,674 observations, 95.4855% equal-trip and 95.1510% pooled **derived-reference agreement**. This is not official evaluator accuracy. The model and decoder match the audited artifacts; no tuning or manual prediction correction used these results. See `results/evaluator_verification.json`.

In Route explorer, reconstruct a trip. **Blue is the actual path from the supplied `.route` reference; green is the predicted path; orange dots are raw GPS.** Use the independent layer checkboxes to inspect each. Where the routes overlap, the blue border remains visible around green. Actual means the supplied reference, not independently verified physical ground truth. The UI requests reference geometry separately after prediction; it never feeds the classifier or decoder. Missing or invalid references are shown as unavailable and do not block prediction. To disable comparison, set `PATHSNAP_REFERENCE_DISPLAY=0` before starting the server. Raw references remain on Laptop 1; Laptop 2 only receives comparison geometry at runtime.
