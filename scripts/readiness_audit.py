"""Generate a traceable PASS/PARTIAL/FAIL audit against all five supplied PDFs."""
import sys,json,re,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from pathsnap.core import ROOT

def main():
    records=[]
    def add(id,source,requirement,status,evidence,note=''):
        for e in evidence:
            assert (ROOT/e.split('::')[0]).exists(),e
        records.append(dict(id=id,source=source,requirement=requirement,status=status,evidence=evidence,note=note))
    P='PASS';Q='PARTIAL';F='FAIL'
    add('MG01','Main Guidelines p1-2','End-to-end noisy GPS to road reconstruction',P,['pathsnap/core.py','pathsnap/service.py','results/api_verification.json'])
    add('MG02','Main Guidelines p2','Read/understand the five supplied documents',P,['docs/REQUIREMENTS_CHECKLIST.md','FINAL_READINESS_AUDIT.md'] if (ROOT/'FINAL_READINESS_AUDIT.md').exists() else ['docs/REQUIREMENTS_CHECKLIST.md'])
    add('MG03','Main Guidelines p2','Independent processing, feature engineering and model comparison',P,['scripts/prepare.py','scripts/train.py','results/critical_audit/model_replay.json'])
    add('MG04','Main Guidelines p2','Bayesian optimisation and saved artifacts',P,['results/bayesian_trials.csv','results/critical_audit/bayesian_log_verification.json','artifacts/model.joblib'])
    add('MG05','Main Guidelines p2','HMM/Viterbi and candidate/road correspondence',P,['pathsnap/decoder.py','tests/test_critical_audit.py::test_viterbi_matches_exhaustive_path_enumeration'],'Uses explicitly disclosed proportional transition potentials; stochastic row-normalized alternative tested and rejected.')
    add('MG06','Main Guidelines p2','Laptop 1 model/API/graph/server scoring',P,['backend/app.py','docs/LAPTOP1_SETUP.md','results/api_verification.json'],'Verified as isolated-environment process on this machine.')
    add('MG07','Main Guidelines p2','Laptop 2 UI reaches actual Laptop 1',Q,['results/browser_qa.json','docs/DEPLOYMENT.md'],'Separate origins tested locally; physical machines/network not available.')
    add('MG08','Main Guidelines p2','Integration and final report',P,['results/browser_qa.json','output/pdf/PathSnap_Technical_Report.pdf'])
    add('DE01','Dataset Exploration p1-3','Exactly 80 train and 10 student-test trips',P,['results/dataset_inventory.csv','results/dataset_integrity.json'])
    add('DE02','Dataset Exploration p1-2','Column meanings, zero-based node/arc IDs, directed connections',P,['pathsnap/core.py','docs/METHODOLOGY.md','tests/test_critical_audit.py::test_index_files_reject_nonintegers_and_invalid_values'])
    add('DE03','Dataset Exploration p2','Do not equate route rows with GPS rows',P,['pathsnap/core.py::reference_labels','scripts/critical_accuracy_audit.py','results/critical_audit/accuracy_audit.json'])
    add('DE04','Dataset Exploration p2','File availability, counts, types, GPS/graph/reference sizes',P,['results/dataset_inventory.csv','results/dataset_integrity.json'])
    add('DE05','Dataset Exploration p2','Missing/invalid points, timestamp order and gaps',P,['pathsnap/core.py','results/dataset_inventory.csv','tests/test_pipeline.py::test_invalid_timestamp_rejected'])
    add('DE06','Dataset Exploration p2','Geographic extent, coordinate order and plausible ranges',P,['results/dataset_inventory.csv','tests/test_pipeline.py::test_invalid_coordinate_rejected','scripts/figures.py'])
    add('DE07','Dataset Exploration p2','Connectivity, components and isolated nodes',P,['pathsnap/core.py::inventory','results/dataset_inventory.csv'])
    add('DE08','Dataset Exploration p2','Investigate unusual trips and large GPS gaps',P,['results/dataset_inventory.csv','docs/METHODOLOGY.md','results/critical_audit/accuracy_audit.json'])
    add('DE09','Dataset Exploration p2-3','Physically meaningful geographic distances',P,['pathsnap/core.py','docs/METHODOLOGY.md'],'Local equirectangular approximation; not a global survey projection.')
    add('DE10','Dataset Exploration p3','Reference limitations and assumptions disclosed',P,['docs/METHODOLOGY.md','results/critical_audit/accuracy_audit.json'])
    add('DE11','Dataset Exploration p3','Whole-trip partitions and training-only preprocessing fit',P,['scripts/train.py::cv_run','results/training_split_manifest.json','results/critical_audit/model_replay.json'])
    add('DE12','Dataset Exploration p3','No evaluator data used for model/features/tuning',P,['scripts/train.py','scripts/decoder_improvement_audit.py'],'Experiment inputs explicitly target supplied train/student-test only; no evaluator files supplied.')
    add('DE13','Dataset Exploration p3','No reference input to prediction or UI',P,['tests/test_pipeline.py::test_inference_never_reads_reference','tests/test_critical_audit.py::test_reference_failure_does_not_destroy_prediction','backend/app.py'])
    add('DE14','Dataset Exploration p3-4','Retain inventory, statistics, GPS/maps and quality decisions',P,['results/figures/dataset_overview.png','results/maps/development_trip_00000007.html','docs/METHODOLOGY.md'])
    add('MT01','Models and Training p1-3','At least five distinct algorithms across families',P,['results/model_comparison.csv','results/critical_audit/model_replay.json'],'Seven algorithms plus tuned and candidate variants.')
    add('MT02','Models and Training p2','Configurations, seeds, experiment logs and results',P,['results/configurations/HistGradientBoosting.json','artifacts/manifest.json','results/cv_folds.json'])
    add('MT03','Models and Training p2','Use all 80 training trips for fit/CV; ten student trips for comparison',P,['artifacts/manifest.json','results/training_split_manifest.json','results/api_verification.json'],'Training samples up to 450 observations per trip; all student observations scored.')
    add('MT04','Models and Training p2-4','Consistent preprocessing and evidence-based selection',P,['scripts/train.py','results/critical_audit/model_replay.json','artifacts/manifest.json'])
    add('MT05','Models and Training p3','Accuracy, precision, recall, F1 and confusion matrices',P,['results/model_comparison.csv','results/model_per_trip.json','results/adaptive_model_per_trip.json'])
    add('MT06','Models and Training p3','Log loss, Top-1 and candidate miss rate',P,['pathsnap/metrics.py','results/model_comparison.csv'])
    add('MT07','Models and Training p3-4','Route continuity, sequence performance and timing',P,['results/model_route_metrics.csv','results/route_comparison.csv','results/training_diagnostics.json'])
    add('MT08','Models and Training p3-4','Primary metric and probability/speed/complexity justification',P,['artifacts/manifest.json','docs/METHODOLOGY.md','output/pdf/PathSnap_Technical_Report.pdf'])
    add('MT09','Models and Training p4','Bayesian space, objective, grouped CV, trial record, best config, refit and cost',P,['scripts/train.py','results/bayesian_trials.csv','results/critical_audit/bayesian_log_verification.json'])
    add('MT10','Models and Training p4','Untuned/tuned comparison on identical protocols',P,['results/model_comparison.csv','results/critical_audit/model_replay.json'])
    add('MT11','Models and Training p4-5','States, emissions, transitions and Viterbi recurrence explained',P,['docs/METHODOLOGY.md','docs/VIVA_GUIDE.md','pathsnap/decoder.py'],'No claim that production transition rows are stochastic probabilities.')
    add('MT12','Models and Training p5','Missing candidates, invalid transitions and GPS gap handling',P,['pathsnap/decoder.py','tests/test_pipeline.py::test_gap_reset_is_explicit','results/critical_audit/clean_environment_tests.txt'])
    add('MT13','Models and Training p5','One predicted road per relevant observation',P,['scripts/verify_api.py','results/api_verification.json'])
    add('MT14','Models and Training p5','Classifier-only versus sequence decoding and continuity analysis',P,['results/route_comparison.csv','results/figures/route_comparison.png'])
    add('MT15','Models and Training p5','Decoder tuning on permitted data only',P,['scripts/evaluate_routes.py','results/critical_audit/improvement_protocol.json'],'Original decoder uses student-test development tuning; new prior uses training-only replay gates.')
    add('MT16','Models and Training p5-6','All ten actual reserved evaluator trips work',Q,['backend/app.py','docs/DEPLOYMENT.md'],'Loader and synthetic partition handling tested; real reserved files not supplied.')
    add('MT17','Models and Training p6','Server computes accuracy with internal references',Q,['backend/app.py','results/api_verification.json'],'Derived-alignment scorer verified; official pointwise reference/scorer convention unresolved.')
    add('MT18','Models and Training p6','Live API calls/logs; no hardcoded outputs or bypass',P,['backend/app.py','results/server_log_excerpt.txt','results/api_verification.json'])
    add('MT19','Models and Training p6','Independent implementation and artifact explanation',Q,['docs/VIVA_GUIDE.md','docs/SUBMISSION.md'],'Experiments executed here; actual four-person understanding/ownership still requires team review.')
    add('DL01','Deliverables p1','Public GitHub repository committed and pushed',F,['docs/SUBMISSION.md'],'Local Git repository exists; no public remote has been created/verified.')
    add('DL02','Deliverables p1-2','Complete data/feature/training/evaluation/tuning/decoder/API/UI source',P,['pathsnap/core.py','scripts/train.py','backend/app.py','ui/app.js'])
    add('DL03','Deliverables p1-2','Artifacts, configs, logs, CSVs, maps and deployment files',P,['artifacts/model.joblib','results/bayesian_trials.csv','scripts/figures.py','requirements.lock.txt'])
    add('DL04','Deliverables p2','README, installation/execution/deployment and organized folders',P,['README.md','docs/LAPTOP1_SETUP.md','docs/LAPTOP2_SETUP.md'])
    add('DL05','Deliverables p2','No committed secrets or private credentials',P,['scripts/audit.py','.gitignore'],'Heuristic token/path scan, not a general security certification.')
    add('DL06','Deliverables p2','One consolidated PDF with prescribed sections and genuine results',P,['output/pdf/PathSnap_Technical_Report.pdf','scripts/report.py'])
    add('DL07','Deliverables p2','EDA, preprocessing, features, missing values, GPS and road maps',P,['results/dataset_inventory.csv','results/figures/dataset_overview.png','results/maps/development_trip_00000007.html'])
    add('DL08','Deliverables p3','Overall table with model/family/config/CV F1/Top-1/continuity/test F1/log loss/time',P,['output/pdf/PathSnap_Technical_Report.pdf','results/model_comparison.csv','results/model_route_metrics.csv'],'Consolidated required-field table added in audit appendix.')
    add('DL09','Deliverables p3-4','Every trained model: suitability, strengths/limits, hyperparameters, objective and actual test results',P,['scripts/report.py','results/configurations/MLP.json','results/model_comparison.csv'])
    add('DL10','Deliverables p4','Over/underfitting evidence connected to actual experiments',P,['results/training_diagnostics.json','results/cv_folds.json','output/pdf/PathSnap_Technical_Report.pdf'])
    add('DL11','Deliverables p4','Real CV/test F1, Top-1 and log-loss comparison plots',P,['results/figures/model_comparison.png','results/figures/log_loss.png'])
    add('DL12','Deliverables p4','No artificial training/validation curves',P,['results/figures/mlp_loss.png','scripts/figures.py'],'Only actual MLP training history plotted; no validation-loss history claimed.')
    add('DL13','Deliverables p5','Bayesian questions and tuned/untuned metrics',P,['results/bayesian_trials.csv','artifacts/manifest.json','output/pdf/PathSnap_Technical_Report.pdf'])
    add('DL14','Deliverables p5-6','HMM design questions, comparisons, improvement/failure discussion',P,['docs/VIVA_GUIDE.md','results/route_comparison.csv','results/critical_audit/training_holdout_decoder.csv'])
    add('DL15','Deliverables p6','Mandatory actual Folium GPS/network/reference/predicted layers, colors, legend, extent and controls',P,['results/maps/development_trip_00000007.html','scripts/figures.py','results/screenshots/folium_development_map.png'])
    add('DL16','Deliverables p6','Interactive map/code retained and representative screenshot in report',P,['results/maps/development_trip_00000007.html','output/pdf/PathSnap_Technical_Report.pdf'])
    add('DL17','Deliverables p6','Actual working UI screenshot',P,['results/screenshots/ui_desktop.png','results/screenshots/ui_mobile.png','results/browser_qa.json'])
    add('DL18','Deliverables p6','Genuine successful receiving-laptop CMD screenshot',F,['docs/DEPLOYMENT.md','results/server_log_excerpt.txt'],'Real local logs exist; no CMD screenshot of the physical receiving laptop has been captured.')
    add('DL19','Deliverables p7','Submitted source matches final demonstrated system',Q,['scripts/package.py','docs/SUBMISSION.md'],'Local artifact/package consistency verified; team must use final commit at external demo.')
    add('DL20','Deliverables p1','First-phase evaluation before lunch',Q,['docs/DEMO_SCRIPT.md'],'Organizer schedule and phase scope are external; not invented.')
    add('DL21','Deliverables p7','AI disclosure, original analysis and each member can defend claims',Q,['docs/VIVA_GUIDE.md','team.json','docs/SUBMISSION.md'],'AI-assisted draft disclosed; team interpretation and names remain placeholders by request.')
    add('AP01','Assessment p1','Meaningful >=5-model experimentation, tuning and retained records',P,['results/critical_audit/model_replay.json','results/critical_audit/bayesian_log_verification.json'])
    add('AP02','Assessment p1','Correctness, reproducibility, evidence beyond one high score',P,['results/critical_audit/accuracy_audit.json','results/critical_audit/clean_environment_tests.txt','docs/METHODOLOGY.md'])
    add('AP03','Assessment p2','No fabricated experiments, graphs, claims or implementation details',P,['scripts/verify_experiments.py','results/critical_audit/experiment_replay_checks.json','scripts/report.py'],'Claims are bounded to retained execution evidence; no universal originality certification.')
    add('AP04','Assessment p2','No sharing another team code/weights/results',Q,['docs/SUBMISSION.md'],'No other-team material used in this session; interteam behavior outside this environment cannot be audited.')
    add('AP05','Assessment p2-3','Every member explains/reproduces work in viva',Q,['docs/VIVA_GUIDE.md','docs/DEMO_SCRIPT.md'],'Guide and cross-examination plan supplied; human understanding cannot be certified here.')
    add('AP06','Assessment p3','No evaluator leakage or hardcoded predictions',P,['tests/test_pipeline.py::test_inference_never_reads_reference','backend/app.py','results/critical_audit/partition_overlap.json'])
    add('AP07','Assessment p3','Source/history/artifacts/results available for investigation',P,['results/artifact_checksums.json','results/dataset_integrity.json','docs/SUBMISSION.md'],'Local repository and packages prepared; public publication remains DL01 FAIL.')
    # User-specific final-audit items supplement, rather than replace, PDF rules.
    add('U01','User audit request','Fresh isolated install, dependency check and actual execution',P,['results/critical_audit/clean_environment_install.json','results/critical_audit/clean_environment_tests.txt','results/api_verification.json'])
    add('U02','User audit request','Exact two-laptop packages, launch commands and troubleshooting',P,['scripts/package.py','docs/LAPTOP1_SETUP.md','docs/LAPTOP2_SETUP.md','docs/DEPLOYMENT.md']+(['results/critical_audit/package_execution.json'] if (ROOT/'results'/'critical_audit'/'package_execution.json').exists() else []))
    add('U03','User audit request','Comprehensive viva and short demonstration script',P,['docs/VIVA_GUIDE.md','docs/DEMO_SCRIPT.md'])
    audit=json.loads((ROOT/'results'/'critical_audit'/'accuracy_audit.json').read_text());final=json.loads((ROOT/'results'/'critical_audit'/'final_accuracy.json').read_text())
    benchmark=pd.read_csv(ROOT/'results'/'critical_audit'/'decoder_pruning_benchmark.csv')
    tests=(ROOT/'results'/'critical_audit'/'clean_environment_tests.txt').read_text();count=re.search(r'(\d+) passed',tests).group(1)
    statuses={s:sum(r['status']==s for r in records) for s in [P,Q,F]}
    out=ROOT/'results'/'critical_audit';(out/'requirements_status.json').write_text(json.dumps({'counts':statuses,'records':records},indent=2))
    lines=['# FINAL_READINESS_AUDIT','',
      'Final critical audit, 18 November 2026. This supersedes the initial build audit. PASS means local evidence supports the stated scope; PARTIAL means external/human verification or an explicitly limited interpretation remains; FAIL means a mandatory external deliverable is currently absent, not that local inference is broken.','',
      f'**Status counts: {statuses[P]} PASS / {statuses[Q]} PARTIAL / {statuses[F]} FAIL.**','',
      '## Main findings','',
      f'- Independently reproduced original score: {100*audit["macro_trip_accuracy"]:.4f}% equal-trip mean; {100*audit["observation_weighted_accuracy"]:.4f}% observation-weighted ({audit["total_correct"]:,}/{audit["total_observations"]:,}).',
      '- Separate reference-DP implementation reproduced all ten label arrays. Raw inputs, candidates, features, stored probabilities and split disjointness were checked. No identical tracks or matching moving ten-point windows were found across train/student-test partitions.',
      '- These remain derived-reference development scores. Shared geometry/heading assumptions, reference anomalies and repeated development selection prevent an independent ground-truth or unbiased generalisation claim.',
      '- Refit/replayed all seven baseline algorithms plus tuned/directional variants. Stored CV/test metrics agree within 1e-7. All sixteen Bayesian objectives and database/CSV trial records agree. Feature ablation and calibration metrics replay exactly.',
      '- Robustness cases were rerun. Expanded-query adaptive reranking was evaluated, including a training-matched refit. Its grouped-CV objective decreased, so it was rejected. The deployed historical_v1 candidate profile matches the original training artifacts; both experiment profiles and changed rows are retained.',
      f'- Retained exact physical-bound pruning: all feasible matrices and ten original predictions unchanged; transition-building total {benchmark.unpruned_s.sum():.2f}s -> {benchmark.pruned_s.sum():.2f}s ({benchmark.unpruned_s.sum()/benchmark.pruned_s.sum():.2f}x in this benchmark).',
      '- Retained log(2) soft immediate-reversal cost only after training-only twelve-trip holdout, repeated timing and eighteen-case robustness gates. The stochastic row-normalized HMM alternative was rejected.',
      f'- Final descriptive student-test result: {100*final["mean_trip_accuracy"]:.4f}% equal-trip mean; {100*final["observation_weighted_accuracy"]:.4f}% observation-weighted. Aggregate gain over the original is negligible; one trip regresses. No claim of statistically significant or universal accuracy improvement.',
      f'- Fresh virtual environment installed the fully locked dependencies, passed pip check, passed {count} tests, reloaded the artifacts and served all ten real API requests. One Starlette/httpx deprecation warning is recorded; functionality passes.',
      '- Mathematical tests include exhaustive enumeration of Viterbi paths and SciPy cross-checks of directed shortest paths. UI/browser and package evidence are linked below.','',
      '## Unsupported claims to avoid','',
      '- Do not call the score official evaluator accuracy or independent true-road accuracy.',
      '- Do not claim research priority, guaranteed GPS-noise robustness, or that every trip improved.',
      '- Do not call unnormalized transition compatibilities a calibrated stochastic transition matrix. The chosen procedure is explicit HMM-style Viterbi/MAP scoring.',
      '- Do not claim two physical laptops, genuine receiving-console screenshots, public GitHub accessibility or four-member viva readiness were verified here.',
      '- The sampled training protocol uses every training trip, not every training observation. Calibration was a prior nearest-candidate experiment and is not deployed.','',
      '## Outstanding external and team work','',
      '1. Publish the local repository through the team account and verify its public URL.',
      '2. Run the complete deployment on two physical laptops and capture the actual receiving CMD console.',
      '3. Obtain reserved evaluator trips and confirm the organizer\'s reference-alignment/official scoring convention.',
      '4. Replace requested placeholders, review interpretation/actual contributions/AI disclosure, and rehearse the viva.',
      '5. Confirm the organizer\'s first-phase evaluation schedule and scope.','',
      '## Final submission closeout','',
      'All nine PARTIAL requirements were reviewed individually in `docs/PARTIAL_REQUIREMENTS_CLOSEOUT.md`. Exact physical setup, owner/admin firewall decisions, genuine receiving-console capture and publication steps are in `FINAL_HANDOFF.md`. No model/decoder tuning is part of this closeout.',
      'No dataset license/redistribution terms were found in the supplied ZIPs. A curated publication snapshot omits raw/bulk point data and private Git history; dependency metadata is recorded in `THIRD_PARTY_NOTICES.md`. Source-license selection and dataset-derived publication permission remain team/organizer decisions. Public publication remains unverified.',
      'Submission checks in `results/submission/submission_checks.json` verify that runtime/model files remain frozen, check recognizable secrets/history and file sizes, and compare deployment members. Deployment provenance and full ZIP-to-commit checks are generated under `packages/` after the final source commit.','',
      '## Requirement-by-requirement evidence','',
      '| ID | Source | Requirement | Status | Evidence | Boundary / qualification |',
      '|---|---|---|---|---|---|']
    for r in records:
        evidence='<br>'.join(f'`{e}`' for e in r['evidence'])
        lines.append(f'| {r["id"]} | {r["source"]} | {r["requirement"]} | **{r["status"]}** | {evidence} | {r["note"]} |')
    lines+=['','## Transfer and execution','',
      '- Laptop 1: `packages/PathSnap_Laptop1_Backend.zip`; see `docs/LAPTOP1_SETUP.md`.',
      '- Laptop 2: `packages/PathSnap_Laptop2_UI.zip` only; no dataset, model or reference labels. See `docs/LAPTOP2_SETUP.md`.',
      '- `packages/checksums.json` and `packages/transfer_manifest.json` describe exact archive content and hashes.',
      '- Clean-environment and package smoke tests are local. Physical networking remains PARTIAL.',
      '- Final source commit and clean-tree status are reported after committing; verify with `git log -1 --oneline` and `git status --porcelain`. The PDF/source evidence cannot contain its own final commit hash without changing that commit.','']
    (ROOT/'FINAL_READINESS_AUDIT.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'docs'/'FINAL_AUDIT.md').write_text('# Final audit\n\nThe authoritative audit is [FINAL_READINESS_AUDIT.md](../FINAL_READINESS_AUDIT.md), including PASS/PARTIAL/FAIL evidence and the final measured pipeline.\n',encoding='utf-8')
    print(json.dumps(statuses),flush=True)

if __name__=='__main__':main()
