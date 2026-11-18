# Answers to the Deliverables PDF

These answers describe executed PathSnap work. Use them as a study draft and add the team's own interpretation. Names remain placeholders at the user's request. The supplied Deliverables PDF matches the seven-page organizer document in materials/Deliverables.pdf.

## 1. What are we submitting?

Exactly two official deliverables: the public GitHub repository and one consolidated technical-report PDF. The repository contains processing/features/training/evaluation/Bayesian search/HMM/API/UI/map-generation source, saved artifacts, configurations, aggregate results, dependency pins and deployment instructions. The report includes actual plots, measured tables, Folium/UI screenshots and limitations. A genuine receiving-laptop CMD screenshot is still required; local logs and Swagger screenshots do not replace it.

Public repository: https://github.com/Mukilskanda/ml_hackathon. Public access was checked in results/publication_verification.json. Later local changes must be pushed before submission.

## 2. Dataset understanding and EDA

### How did we preprocess the data?

We parse .track as longitude/latitude/timestamp, .nodes as road coordinates, .arcs as zero-based directed node pairs and .route as a traversed arc sequence. We validate shapes, finite coordinates, index bounds, geographic ranges and strictly increasing timestamps. Invalid input is rejected rather than silently repaired. There were no missing GPS values in the measured supplied train/student-test inventory, so no missing-value imputation was needed.

We project each local network to metres using 111195.08 metres per latitude degree and a cosine-latitude longitude scale. Directed parallel edges are represented using minimum edge length, not sparse-matrix summation. A five-point smoothed motion estimate supplies heading; we compute time gaps and speed. This is complete-trip offline map matching and can use neighboring observations; we do not claim causal streaming inference.

The reference .route is NOT one label per GPS observation. A separate monotone dynamic program aligns observations to its ordered road segments, using distance, heading and a progress penalty. These labels are derived references with limitations, not independently verified physical ground truth. Prediction features and inference never read reference membership.

### What patterns did we observe?

The train/student-test inventory has 227,577 GPS observations across 90 trips. Trip sizes range from 262 to 19,313; the largest timestamp gap is 153064 seconds. Missing GPS values: 0. Trip lengths and timestamp gaps vary, and noisy GPS can lie away from roads. Some supplied references, particularly trips 00000033 and 00000054, disagree substantially with observations. We retain and document them rather than deleting difficult trips.

Partitions: 80 training trips for fitting/grouped CV/tuning; 10 student-test trips for development comparison and decoder development; 10 later-supplied evaluator trips for a frozen-model replay only. No evaluator result selected a model, feature or hyperparameter. All 80 training trips are represented; fitting samples at most 450 seeded observations per trip. Student-test and evaluator scoring use all observations. Scaling is fitted inside each training fold, and complete trips are kept together in GroupKFold.

### What features did we extract, and why?

| Feature | Meaning and reason |
|---|---|
| distance_m | Projected GPS-to-segment distance; measures geometric proximity. |
| heading_cos | Agreement between motion and directed road heading; distinguishes opposite directions. |
| heading_abs_sin | Magnitude of angular mismatch; captures sideways misalignment. |
| log_length | log(1 + segment length); captures road scale without extreme length domination. |
| fraction | Clamped position along the segment; informs progress and junction behavior. |
| prev_distance_m | Previous GPS observation's distance to this segment; supplies local trajectory context. |
| next_distance_m | Next GPS observation's distance to this segment; supplies offline trajectory context. |
| speed_mps | Motion magnitude divided by elapsed time; describes movement conditions. |
| gap_s | Timestamp gap; distinguishes regular motion from large gaps. |
| distance_rank | Candidate proximity rank; helps compare hypotheses within an observation. |
| distance_margin_m | Candidate distance minus the nearest candidate distance; measures relative ambiguity. |
| heading_reliability | Strength of smoothed displacement; downweights unreliable stationary/noisy headings. |
| source_degree | Graph degree at the candidate source endpoint; describes junction complexity. |
| target_degree | Graph degree at the target endpoint; adds endpoint topology context. |
| endpoint_distance_m | Distance along the road to its nearer endpoint; describes junction proximity. |

The densified spatial index proposes nearby segments, then exact segment projection ranks the retrieved candidates. Eight distinct candidates are retained. The final historical_v1 directional candidate profile matches the saved training artifact. Retrieval is approximate, so we measure candidate miss rate instead of assuming perfect coverage. Controlled feature ablation shows that geometry plus motion/topology outperforms distance alone.

EDA evidence: results/dataset_inventory.csv, results/figures/dataset_overview.png, results/figures/geographic_comparison.png and the Folium generator in scripts/figures.py. Every plot identifies its partition.

## 3. Model experimentation and comparison

Seven distinct baseline algorithms and two tuned/candidate configurations were evaluated. The binary task asks whether a proposed road is the reference-aligned road; Top-1 chooses the highest-scoring candidate for each GPS observation. Arc IDs are local to each trip, so a single global road-ID classifier would be inappropriate.

**Metric definitions:** Top-1 is observation-level and the model table pools all student-test observations. Macro F1 below is positive/negative candidate-binary Macro F1 at threshold 0.5; log loss is candidate-binary log loss. These are explicitly NOT road-class Macro F1 or an official evaluator scoring convention. Route summaries elsewhere use an equal-trip mean. Confirm the organizer's scoring interpretation instead of silently relabelling these metrics.

| Configuration | CV candidate Macro F1 | Student Top-1 | Student candidate Macro F1 | Binary log loss | Classifier inference |
|---|---:|---:|---:|---:|---:|
| LogisticRegression | 91.09% | 86.53% | 91.12% | 0.1146 | 0.086 s |
| GaussianNB | 79.42% | 85.55% | 78.56% | 0.7325 | 0.134 s |
| DecisionTree | 92.85% | 88.27% | 92.61% | 0.1031 | 0.070 s |
| RandomForest | 93.48% | 87.83% | 93.02% | 0.0733 | 0.654 s |
| ExtraTrees | 92.82% | 87.22% | 92.30% | 0.0846 | 0.714 s |
| HistGradientBoosting | 93.48% | 88.98% | 93.36% | 0.0699 | 0.837 s |
| MLP | 92.66% | 87.69% | 92.80% | 0.0765 | 0.110 s |
| HistGradientBoosting_tuned | 93.64% | 89.26% | 93.46% | 0.0698 | 0.538 s |
| HistGradientBoosting_tuned_adaptive_candidates | 93.58% | 88.50% | 93.30% | 0.0708 | 0.538 s |

Inference here is summed classifier prediction time across the ten student-test trips, excluding feature extraction, HMM, geometry, reference scoring and HTTP overhead. Full configurations are in results/configurations/.

### LogisticRegression

**A. Why suitable; strengths and limitations:** A fast linear baseline for distance and direction features. It is interpretable but cannot represent all nonlinear geometry/topology interactions. Family: Linear / probabilistic.

**B. Training/configuration and loss:** Log loss with L2 regularisation; C=1, max_iter=300, standardized features. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 86.53%; candidate Macro F1 91.12%; candidate precision 84.50%; candidate recall 84.41%; binary log loss 0.1146. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 91.21% versus grouped-CV 91.09%, a 0.11 percentage-point gap. CV fold Top-1 standard deviation is 0.0304. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### GaussianNB

**A. Why suitable; strengths and limitations:** A low-cost probabilistic baseline. Correlated distance, heading and neighborhood features conflict with its conditional-independence assumption; its measured log loss is a direct probability-quality diagnostic. Family: Probabilistic.

**B. Training/configuration and loss:** Gaussian class likelihood; variance smoothing 1e-7; standardized features. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 85.55%; candidate Macro F1 78.56%; candidate precision 49.62%; candidate recall 93.43%; binary log loss 0.7325. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 79.52% versus grouped-CV 79.42%, a 0.09 percentage-point gap. CV fold Top-1 standard deviation is 0.0314. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### DecisionTree

**A. Why suitable; strengths and limitations:** Captures nonlinear distance/heading rules and is easy to inspect. A single tree is sensitive to sample variation and can produce coarse probabilities. Family: Tree.

**B. Training/configuration and loss:** Gini impurity; max_depth=12, min_samples_leaf=25. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 88.27%; candidate Macro F1 92.61%; candidate precision 87.28%; candidate recall 86.83%; binary log loss 0.1031. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 94.65% versus grouped-CV 92.85%, a 1.80 percentage-point gap. CV fold Top-1 standard deviation is 0.0284. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### RandomForest

**A. Why suitable; strengths and limitations:** Averages nonlinear rules for stability. More trees cost time and memory; uncalibrated leaf probabilities can remain imperfect. Family: Bagged ensemble.

**B. Training/configuration and loss:** 100 Gini trees; max_depth=18, min_samples_leaf=10, four workers. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 87.83%; candidate Macro F1 93.02%; candidate precision 89.77%; candidate recall 85.81%; binary log loss 0.0733. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 95.42% versus grouped-CV 93.48%, a 1.94 percentage-point gap. CV fold Top-1 standard deviation is 0.0311. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### ExtraTrees

**A. Why suitable; strengths and limitations:** Tests whether stronger split randomisation improves generalisation and efficiency. Random thresholds can underfit useful distance boundaries. Family: Randomized ensemble.

**B. Training/configuration and loss:** 100 randomized Gini trees; max_depth=20, min_samples_leaf=8, four workers. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 87.22%; candidate Macro F1 92.30%; candidate precision 90.53%; candidate recall 82.71%; binary log loss 0.0846. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 93.68% versus grouped-CV 92.82%, a 0.86 percentage-point gap. CV fold Top-1 standard deviation is 0.0306. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### HistGradientBoosting

**A. Why suitable; strengths and limitations:** Efficient nonlinear boosting for structured candidate features. Its strong grouped-CV result made it the promising Bayesian-search family. Family: Boosting.

**B. Training/configuration and loss:** Binary log loss; 130 iterations, 23 leaves, learning_rate=0.09, L2=2; early stopping disabled. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 88.98%; candidate Macro F1 93.36%; candidate precision 89.01%; candidate recall 87.71%; binary log loss 0.0699. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 94.72% versus grouped-CV 93.48%, a 1.24 percentage-point gap. CV fold Top-1 standard deviation is 0.0302. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### MLP

**A. Why suitable; strengths and limitations:** Tests learned nonlinear feature interactions. Scaling and optimization matter; the recorded fit hit its epoch cap, so convergence is not established. Family: Neural network.

**B. Training/configuration and loss:** Binary log loss with L2 regularisation; standardized inputs, hidden=(32,16), Adam, batch_size=1024, 45 epochs. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 87.69%; candidate Macro F1 92.80%; candidate precision 90.11%; candidate recall 84.72%; binary log loss 0.0765. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 93.57% versus grouped-CV 92.66%, a 0.91 percentage-point gap. CV fold Top-1 standard deviation is 0.0283. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### HistGradientBoosting_tuned

**A. Why suitable; strengths and limitations:** Considered to improve the promising boosting family using the declared grouped-CV objective. It retains efficient nonlinear tabular learning. The search introduces selection optimism; gains over untuned boosting are small. Family: Boosting / tuned nearest candidates.

**B. Training/configuration and loss:** Binary log loss; 71 iterations, 32 leaves, learning_rate=0.08695286005074185, min_samples_leaf=75, L2=3.685855708246808; early stopping disabled. Starts from the untuned family configuration reported above. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 89.26%; candidate Macro F1 93.46%; candidate precision 88.99%; candidate recall 88.10%; binary log loss 0.0698. Candidate miss rate: 0.38%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 94.50% versus grouped-CV 93.64%, a 0.87 percentage-point gap. CV fold Top-1 standard deviation is 0.0301. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### HistGradientBoosting_tuned_adaptive_candidates

**A. Why suitable; strengths and limitations:** Tests geometry/motion-aware retrieval with a matching refit on the same training observations. The combined grouped-CV objective improves slightly, but student-test classifier Top-1 decreases. This is a separate candidate-profile experiment, not a universal improvement. Family: Boosting / tuned directional candidates.

**B. Training/configuration and loss:** Same tuned boosting parameters as the preceding model; eight directional candidates using the historical_v1 profile and binary log loss. The common protocol uses seed 42, all 80 training trip groups, at most 450 observations per trip and three-fold trip-grouped CV. Full estimator defaults and initial parameters are retained in the model configuration JSON.

**C. Actual student-test results:** observation Top-1 88.50%; candidate Macro F1 93.30%; candidate precision 89.15%; candidate recall 87.38%; binary log loss 0.0708. Candidate miss rate: 0.33%.

**D. Overfitting/underfitting evidence:** sampled-training candidate Macro F1 94.49% versus grouped-CV 93.58%, a 0.91 percentage-point gap. CV fold Top-1 standard deviation is 0.0307. This measures fitting optimism, not proof of a unique cause. The MLP reached its 45-epoch cap, so convergence is not established. For other algorithms, do not invent epoch-wise validation histories. Training/CV differences also reflect trip difficulty and reference quality.

### Which visualisations support comparison?

The report includes CV candidate Macro F1 and student-test candidate Macro F1/observation Top-1 comparisons for all nine configurations, a binary log-loss comparison, feature-ablation results, per-trip route comparisons, and the actual MLP training loss curve. No validation-loss history was collected; we state that limitation. Trees and naive Bayes do not have epoch-wise training histories, so we do not fabricate curves. Confusion matrices are retained as optional candidate-binary diagnostics.

## 4. Bayesian hyperparameter optimisation

**Which model and why?** Histogram gradient boosting was the most promising eligible family on the declared grouped-CV objective, rather than on training accuracy alone.

**Search space:** max_iter 70–210; max_leaf_nodes 10–45; min_samples_leaf 15–100; learning_rate 0.025–0.2 log-uniform; l2_regularization 0.1–20 log-uniform. Optuna's TPE sampler uses seed 42 and five startup trials.

**Objective:** maximise 0.5 * (grouped-CV candidate Macro F1 + grouped-CV observation Top-1). All three CV folds group by complete trip; evaluator outcomes never enter this objective.

**Number of trials:** 16 executed trials, recorded in results/bayesian_trials.csv; full fold/trial records and search source are retained.

**Best values:**

```json
{
  "max_iter": 71,
  "learning_rate": 0.08695286005074185,
  "max_leaf_nodes": 32,
  "min_samples_leaf": 75,
  "l2_regularization": 3.685855708246808
}
```

**Did tuning improve it?** On the matched nearest-candidate experiment, CV candidate Macro F1 changed from 93.48% to 93.64%; student-test Top-1 88.98% to 89.26%; student-test candidate Macro F1 93.36% to 93.46%; binary log loss 0.06990 to 0.06985; classifier inference 0.837 s to 0.538 s. These are small gains, not a dramatic improvement. The tuned directional-candidate refit improved the combined grouped-CV objective slightly but reduced student-test classifier Top-1; we report that trade-off honestly.

**Why this final model?** The final artifact is HistGradientBoosting_tuned_adaptive_candidates with its matching historical_v1 candidate profile and saved decoder settings. Selection followed the declared grouped-CV criterion plus separately documented training-only decoder/robustness gates. We did not choose the most complex algorithm or the highest training score. Saved artifacts were reloaded and tested through the API. No new tuning used the supplied evaluator trips.

## 5. HMM and Viterbi route reconstruction

**Hidden states:** the eight candidate directed road arcs at each GPS observation; numeric arc identities are trip-local.

**Emissions:** the classifier's binary scores are clipped and normalized across candidates. Adaptive HMM-style scoring combines log classifier scores with distance/heading geometry; uncertainty controls the mixture. These are scoring potentials and relative confidence, not independently calibrated multiway probabilities.

**Transitions:** use progress on the current road, bounded directed shortest-path distance and progress along the next road. Compare network travel with GPS displacement; score mismatch using beta + 2*sqrt(dt). Reject physically implausible travel above 65*dt + 70 metres. The saved configuration has beta=8, geometry_weight=0.6, jitter_m=30, emission_strength=0.4 and an immediate-reversal cost log(2). Directed search is bounded at 2000 metres. Production transition rows are not normalized as a stochastic transition matrix.

**Viterbi:** V[t,j] = emission[t,j] + max_i(V[t-1,i] + transition[t,i,j]). Log-space scores avoid underflow; backpointers recover the best sequence.

**Missing candidates:** if the correct road is not proposed, the classifier/HMM cannot recover it. We return the best available candidate and report miss rate. Spatial lookup has a fallback expansion; a network with no usable arcs fails clearly.

**Large gaps/disconnections:** gaps above 60 seconds or wholly infeasible transitions restart a sequence chunk. Unreachable/reset joins remain separate display polylines. We never invent a straight connector or repair a prediction using the known reference.

**Did decoding help?** The following use equal-trip means on the same ten student-test trips, unlike the pooled classifier table above.

| Method | Derived point agreement | Direct route continuity |
|---|---:|---:|
| nearest_road | 55.43% | 42.35% |
| classifier_only | 90.21% | 76.63% |
| fixed_hmm | 95.01% | 91.51% |
| adaptive_hmm | 95.25% | 91.11% |
| audited_hmm | 95.26% | 90.47% |

**Continuity definition:** remove consecutive duplicate road IDs. Count distinct successive roads whose directed target/source nodes match, divided by the number of such road changes. A sequence with no road changes has continuity 1 by convention. This needs no reference labels. It is stricter than network feasibility, which allows intermediate connecting roads and tolerated same-road jitter. In the UI, Route continuity refers to the selected trip; the Experiment bench shows equal-trip benchmark continuity.

HMM decoding improves agreement and continuity over classifier-only predictions, but does not help every trip or maximise every metric. The fixed HMM has slightly higher direct continuity than the final audited decoder. The final soft reversal prior gives negligible aggregate student-test accuracy gain and one trip regresses. Severe GPS noise can destroy heading/candidate coverage, and inconsistent supplied references limit interpretation.

## 6. Folium geographical visualisation

We generate an actual interactive Folium map using scripts/figures.py. It overlays original GPS observations, relevant directed road geometry, the supplied reference where available and the predicted route. Layers have distinguishable colours, a legend, appropriate fit bounds and toggle controls. The report embeds a representative screenshot of student-test trip 00000007. The code is public, so a generated HTML map can be regenerated from the legitimately supplied local data. Raw/location-bearing files are kept out of the curated public snapshot.

The separate evaluator UI has an offline canvas: blue is the actual path from the supplied .route reference, green is the model prediction and orange dots are GPS. The reference is fetched separately AFTER prediction; it never affects classifier/decoder output. Actual means supplied reference, not independently verified physical truth. No reference means an unavailable layer, not a guessed actual path.

## 7. API, UI and deployment

Laptop 1 loads the saved model and runs FastAPI/inference. Laptop 2 runs the static website, chooses a trip and sends HTTP requests to Laptop 1's IPv4 address. Neither laptop trains a model during inference. The backend returns predicted route geometry, observation counts, reference-free direct continuity, network feasibility, timings, relative confidence and a request ID. Optional server-side reference scoring is computed only after prediction. A separate GET endpoint serves reference comparison geometry.

Working UI screenshots, actual HTTP responses, 33 passing automated tests, isolated-environment installation and extracted-package execution have local evidence. The UI is checked at desktop and mobile sizes, with connection recovery and error handling. Final source/package hashes tie the demonstrated implementation to saved source. A physical two-laptop run and genuine receiving-CMD screenshot must still be captured; a browser API screenshot or copied console text does not satisfy that requirement.

Demonstration: on Laptop 2 reconstruct trip 00000023; show blue reference versus green prediction; show route continuity separately from network feasibility; show playback; open Experiment bench. On Laptop 1 show the matching request ID and successful POST in the real CMD receiving window. Test all ten evaluator trips, not only the short example.

## 8. Integrity, originality and limitations

Our novelty consists of documented engineering contributions and measured comparisons, not a claim to invent HMMs, Viterbi, boosting or spatial indexes. All experiments/results are real saved outputs. Candidate/feature alignment, physical-bound graph pruning, uncertainty-aware emissions, explicit resets, relative-confidence diagnostics and the separate deployment form the project contribution. Rejected alternatives are retained and explained.

The final student-test derived-reference agreement is 95.2559% equal-trip / 94.1284% pooled. The later frozen evaluator replay is 95.4855% equal-trip / 95.1510% pooled across 10 trips and 19,674 observations. These are not official evaluator accuracy, independent physical road truth or guaranteed generalisation. The official scoring convention still requires confirmation.

AI assistance was used for code/documentation and is disclosed in the draft. Every member must independently review, interpret and be able to defend the work. Do not present this document as proof that all members understand it. Placeholders and suggested ownership are not verified personal contributions.

## What is still needed before final submission?

1. Genuine physical two-laptop rehearsal and receiving-CMD screenshot added to the consolidated report.
2. Push the final UI continuity/report-generation/documentation changes; verify the final remote version.
3. Team review, actual interpretation and policy-compliant AI disclosure; confirm first-phase schedule and official scoring interpretation.
4. Submit the repository URL and the single final technical-report PDF through the organizer's requested channel.
