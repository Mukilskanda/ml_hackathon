# Team viva guide

This is an implementation guide to study and verify, not a substitute for understanding your own results.

**Explain the full pipeline in one minute:** A trip supplies noisy GPS points and its directed road graph. We index densified road segments, propose eight candidate directed arcs for each observation, and compute geometry, motion and topology features. A supervised binary classifier scores whether each candidate matches a reference-derived label. We choose the model using cross-validation grouped by trip and tune the selected family with Bayesian TPE. An HMM combines learned emissions with directed shortest-path transitions; Viterbi finds a coherent sequence while handling gaps and jitter. FastAPI runs inference on Laptop 1, then a separate scorer optionally reads its internal reference. Laptop 2 sends a trip ID and shows predictions and aggregate metrics.

## Questions everyone should answer

1. **Why not classify directly into arc IDs?** Arc IDs are local row indexes and mean different roads across trips. Candidate scoring uses transferable geometric and motion features.
2. **What is the target label?** A binary label for each candidate, derived by monotonically aligning GPS samples to the supplied reference arc sequence. The route file is not one label per GPS observation.
3. **How do you avoid leakage?** Split by complete trip. Fit scalers only within training folds. Keep reference membership out of features. Use no reserved evaluator data. Load reference files only after inference on the server.
4. **What does Macro F1 mean here?** The average F1 for candidate negative/positive classes, threshold 0.5. It is distinct from observation Top-1 road-selection accuracy.
5. **Why report candidate miss rate?** If the reference road is not proposed, no classifier or decoder can select it; this limits achievable pointwise accuracy.
6. **Why five or more models?** To justify model selection experimentally across linear, probabilistic, tree, ensemble, boosting and neural approaches. Open the actual comparison CSV and explain its tradeoffs.
7. **What is Bayesian tuning doing?** Optuna TPE uses prior trial outcomes to propose promising hyperparameters. Sixteen trials are recorded; optimization uses grouped CV, not evaluator outcomes.
8. **What is the HMM state?** One candidate directed road arc at each observation, retaining its identity even when candidate indexes differ over time.
9. **How are emissions formed?** Normalize learned binary candidate probabilities; mix log scores with geometric evidence in the adaptive variant, weighted by candidate uncertainty.
10. **What is a transition?** Same-road projected progress, or remaining current road distance plus a directed shortest-path connector plus the next road offset. Reject physically implausible distances and account for elapsed time.
11. **What is Viterbi?** A dynamic program that maximizes total log emission and transition score. Backpointers recover the globally best sequence within each gap-separated chunk.
12. **Why tolerate backward projected motion?** GPS jitter can move the measured projection backward while the vehicle continues forward. The selected tolerance is a noise assumption, not permission for reverse travel on a one-way road.
13. **What happens at a big gap or disconnected candidate sets?** Restart the sequence chunk and expose the reset. Never fabricate a road connection in the map.
14. **Is confidence a calibrated probability?** The deployed model's normalized candidate score is a relative diagnostic. A sigmoid calibration experiment is retained separately; read its measured CV/log-loss outcome and caveat.
15. **What is novel?** The tested combination and engineering decisions within this project: directional candidates, uncertainty-aware hybrid emissions, gap handling and jitter tolerance. Do not claim new research priority.
16. **What are your limitations?** Derived-label circularity, anomalous references, candidate truncation, bounded shortest paths, severe-noise degradation, sampled training observations, development-selected decoder scores, and no measured reserved-evaluator performance.
17. **What has actually been tested?** Read `results/test_results.txt`, `results/api_verification.json`, `results/browser_qa.json`, and the final audit. Two physical laptops still require rehearsal.

## Suggested four-person review

Person 1 demonstrates file parsing, projection, candidates and the reference-alignment limitation. Person 2 explains all model comparisons, grouping, tuning and calibration. Person 3 derives Viterbi and explains transition/jitter failure cases. Person 4 demonstrates API requests, reference isolation, UI settings and separate deployment. Then each person should explain another member's component.

Use the generated report and actual CSVs for numeric answers. Do not memorize stale scores from chat; `artifacts/manifest.json` identifies the final selected implementation.

## Mathematical reasoning to be able to derive

### Coordinates and projection onto a road

For mean trip latitude phi0, the local coordinates are x = 111195.08*cos(phi0)*(lon-lon0) and y = 111195.08*(lat-lat0), in metres. This is a local approximation, not a global or high-precision survey projection.

For road endpoints a,b and GPS point z, let v=b-a. The projected fraction is f=clip(((z-a) dot v)/(v dot v),0,1). The foot is a+f*v and distance is ||z-foot||. The clamp prevents snapping beyond a finite road segment. Degenerate segments have a small denominator guard.

### Reference alignment is a separate weak-label procedure

Let j index positions in the supplied chronological reference route and L[j] its cumulative distance. The local cost combines capped GPS-to-road distance and directed heading disagreement. The recurrence is:

`D[t,j] = local[t,j] + min_(i<=j)(D[t-1,i] - lambda*L[i]) + lambda*L[j]`.

The initial prior is proportional to cumulative progress. Prefix minima reduce the naive quadratic reference-state transition step to linear time in route length. Backtracking returns a nondecreasing reference-position sequence. It can stay on or skip segments; it does not require visiting every reference segment or ending at the final reference arc. This is an assumption, not a supplied point label. An independently coded history/argmin traceback reproduced all ten development-trip label arrays.

### Supervised learning and classification metrics

For candidate j at observation t, y[t,j]=1 exactly when its arc ID equals the derived reference arc. Classifiers fit candidate feature vectors to binary targets. Logistic/boosted/neural models minimize versions of binary log loss `-y*log(p)-(1-y)*log(1-p)` plus their algorithm-specific regularization. Trees use impurity-based splits. Gaussian NB estimates class-conditioned feature distributions with an independence assumption.

Precision=TP/(TP+FP); recall=TP/(TP+FN); F1=2PR/(P+R). Candidate Macro F1 averages F1 for candidate-positive and candidate-negative classes. Observation Top-1 instead checks whether the highest-scoring candidate is the reference road. Candidate miss rate is the fraction whose reference road is absent; these cases are not silently removed.

If the positive candidate is missing, all candidates are negative. Candidate raw accuracy can still be high because negatives dominate. This is why it cannot replace observation Top-1 and miss rate.

### Emissions and transition compatibility

Normalize the binary affinities over the candidate set: q[t,j]=p[t,j]/sum_j p[t,j]. Normalized entropy is `H[t]=-sum_j q[t,j]*log(q[t,j])/log(K)` and is defined as zero for K=1.

The adaptive emission mixes `log(q)` with a geometric score based on projected distance and heading, using a larger geometric contribution for high candidate entropy. Emission strength 0.4 controls the overall weight of local evidence against transitions. q is a relative affinity, not a guaranteed calibrated multiway correctness probability.

For different roads, network distance is remaining current-road length plus directed shortest-path length plus next-road offset. For the same road, projected progress can be slightly negative because measurements jitter. Reject moves outside the selected jitter/travel caps. A valid transition score is proportional to `-|max(network_distance,0)-GPS_displacement|/(beta+2*sqrt(dt))`.

The retained soft U-turn prior subtracts log(2) for immediately reversed directed node pairs. It halves their compatibility, but permits genuine reversals if the rest of the sequence supports them. This is not a traffic-law database or a hard U-turn prohibition.

Production uses **unnormalized transition potentials**, so describe it precisely as HMM-style Viterbi/MAP sequence scoring. Do not call the rows a calibrated stochastic transition matrix. A row-normalized stochastic-HMM alternative was implemented, tested on training-only holdout data, and rejected because its measured accuracy and latency were worse.

### Viterbi and complexity

`V[t,j] = emission[t,j] + max_i(V[t-1,i] + transition[t,i,j])`.

Keep a backpointer to the maximizing predecessor. At the end, backtrack the best final state. Gaps/infeasible steps separate chunks; backtrack each chunk from its own best endpoint. Viterbi is O(T*K^2) once transition distances are available, with O(T*K) backpointer storage. K is normally eight.

Directed Dijkstra is the expensive graph stage. Pruning to the maximum physically feasible outgoing distance for each source cannot remove a feasible middle connector: remaining-road and next-road offsets are nonnegative. The optimization was checked against unpruned feasible matrices and predictions on every student-test trip.

## Experimental conclusions and difficult questions

**What exactly was independently audited?** The original 95.25% result is 95.2489% as an equal-trip mean, but 94.0971% when observations are pooled (18,029/19,160). Raw candidates, features, labels and model probabilities were regenerated. All three CV folds cover disjoint whole trips, and all seven algorithms plus tuned/directional variants reproduced their stored metrics on replay. No identical track files or matching moving ten-point windows were found across train/student-test partitions; that check cannot prove absence of all semantic overlap.

**Does this establish 95% true-road generalization?** No. The references are derived, some reference routes disagree with GPS, decoder settings were developed on student-test trips, and the final evaluator partition is unavailable. Leave-one-trip-out decoder reselection is a sensitivity diagnostic, not a completely nested unbiased pipeline test.

**Why keep the new U-turn prior?** A classifier trained on 68 trips scored a fixed seeded 12-trip training holdout. The prior improved mean point agreement by about 0.315 percentage points. Eighteen noise/dropout cases on three of those held-out training trips passed the robustness gate; repeated decode cost stayed essentially unchanged. The prior was selected before examining its student-test results. Its student-test aggregate gain is negligible and one trip regresses; explain that honestly.

**Why is trip 00000077 difficult?** It contributes the most errors in the original pipeline; many are the reverse directed road, rather than candidate misses. Direction becomes ambiguous under slow/noisy motion. The prior addresses a general failure mechanism, not a hardcoded trip-specific repair.

**Why not normalize transitions just to have a more complex HMM?** It changes the path objective by source-dependent row normalizers. The measured training-holdout result deteriorated substantially, so it was not selected. Mathematical description must match the actual score potentials.

**Why is calibration not deployed?** The earlier tuned nearest-candidate model's sigmoid produced only a tiny student-test log-loss improvement and unchanged Top-1. Nested calibrated CV did not demonstrate a compelling advantage, and fitting/calibration splits reduced base-fit data. The experiment remains documented and independently replayed; it is not silently applied to the later directional candidate model.

**Are the experiments all directly comparable?** Same-fold tuned/untuned and feature ablations are controlled comparisons. Candidate variants change candidate identities and class prevalence; calibration uses fewer fitting trips per outer fold; decoder settings use permitted development data. State those differences instead of treating every row as an untouched test.

**What is fixed and what is configurable?** Model/feature order/candidate strategy must match saved artifacts. Server address, ports, data root and CPU thread budget are configurable. Model architecture and inference parameters are fixed during a request. A new browser URL does not retrain the model.

**What happens when scoring breaks?** The predictor still returns its route. A malformed/missing reference yields null metrics and an explicit warning; labels remain server-side. Missing input GPS/graph files instead produce a validation error. These are distinct failures.

**What do direct continuity and network feasibility mean?** Direct continuity requires collapsed adjacent predicted arcs to share a node. Network feasibility also allows intermediate graph paths and tolerated same-road jitter. Neither proves correctness. Arc-set F1 measures coverage; it ignores ordering. Exact collapsed-sequence equality is separately recorded.

**What is the main robustness failure?** Severe added independent coordinate noise can destroy heading and candidate coverage. The code does not claim to solve arbitrary GPS noise. Expanded-query adaptive reranking changed two noisy-case scores and 3,354 training candidate rows. A training-matched refit lowered the declared grouped-CV objective, so that proposal was rejected. Production explicitly retains the historical_v1 candidate profile matching its trained artifacts; both profiles and outputs remain available for reproducibility.

**What is original?** The team's tested integration and engineering choices, controlled experiments, reliability fixes and transparent reference isolation. The algorithms themselves are established. No global research priority or independence from AI assistance should be claimed.

## Four-person cross-examination rehearsal

Each member should run a complete request and open its matching server request ID, explain the 15-feature schema, derive the two dynamic programs, identify the selected artifact, and locate one actual failed experiment. Rotate questions so the API owner explains grouping and the model owner explains a missing-reference API response. Replace the placeholder contribution list with actual work before submission.

Read `FINAL_READINESS_AUDIT.md` at the repository root and `docs/DEMO_SCRIPT.md` immediately before the demonstration. The current score is in `results/critical_audit/final_accuracy.json`; do not quote an old chat figure without its averaging and reference-label qualification.
