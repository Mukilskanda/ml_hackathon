# Methodology and limitations

## File semantics

All files are whitespace-separated and headerless. `.track`: longitude, latitude, seconds. `.nodes`: longitude and latitude; zero-based row index is node ID. `.arcs`: directed source and target node IDs; zero-based row index is arc ID. `.route`: chronological traversed arc IDs. Each trip has its own graph and ID namespace. A global multiclass classifier over raw arc IDs would therefore be inappropriate.

Longitude/latitude are converted to local metric coordinates using 111195.08 m per degree latitude and the cosine of the trip's mean latitude for longitude. This local equirectangular approximation is adequate for small trip extents; it is not a general global projection. Coordinates are converted to latitude/longitude only for Folium. UI canvas preserves geographic aspect ratio.

## Reference alignment: an explicit weak-label assumption

The supplied reference route is not observation-indexed. We align GPS samples monotonically to the reference segment sequence using dynamic programming. Local cost is capped point-to-segment distance plus a smoothed-motion directed-heading cost. Moving forward adds 0.015 times reference cumulative road length; staying is allowed. The start prior is 0.002 times cumulative route progress. This produces one derived arc label for each GPS observation.

These labels are useful supervised targets and a consistent development reference, but are not independent truth. They partly reflect the same geometry/motion assumptions used by the predictor; reported pointwise accuracy can consequently be optimistic. Route loops, incomplete routes and bad reference geometry can misalign observations. All reference-distance anomalies and candidate misses remain in the measured results; we do not silently drop difficult test points. No `.route` content is used to compute inference candidates or features. A test guards every inference file read to prove it does not open `.route`.

Before final evaluation, ask organizers whether they provide observation-level labels, expect a particular alignment, or use a route-sequence metric. Keep their official metric distinct from the development scorer. The current API reports its metric basis explicitly.

## Candidate construction and features

Each directed segment is densified with anchor spacing at most 25 m. A cKDTree retrieves up to 96 nearest anchors; unique owner segments are exactly reprojected to GPS points. A 512-anchor fallback expands retrieval if needed. The baseline retains eight nearest distinct arc IDs; a smaller graph retains its available count. Long roads are not represented by a single midpoint. This is an approximate candidate search, not a mathematical guarantee of the globally nearest eight segments.

The adaptive experiment ranks proposals by `distance + 18 * motion_reliability * (1 - heading_cosine)`, retains eight, and sorts the retained set by distance. It increases directional diversity in dense/parallel-road settings. Its training-matched comparison holds folds, observation samples and model hyperparameters fixed. Adoption is recorded in the manifest and experiment JSON.

The historical training generator used distance-only ranking after expanding an insufficient initial anchor query. This behavior is versioned as `historical_v1` for reproducibility. A `current_v2` proposal preserves adaptive ranking in the expanded pool. It changes 3,354 training candidate rows, so it was tested with a matching refit rather than silently mixed with the old trained model. Its grouped-CV objective decreased from 0.905956 to 0.905639. The proposal was rejected and serving explicitly selects `historical_v1`, consistent with its model artifact. Both profiles remain available for audited replay; rejected-profile stress-test differences are recorded.

Fifteen features describe distance, direction cosine and absolute sine, log segment length, projected fraction, distances from previous/next GPS points, observed speed, time gap, distance rank and margin, smoothed-heading reliability, source/target degree, and nearest endpoint distance. The five-point motion smoother uses both past and future observations; this is batch reconstruction, not a causal streaming system. Numeric node/arc IDs and reference-route membership are not features.

## Experimental protocol

All 80 training trips participate. Up to 450 seeded, uniformly selected observations per trip bound computation without dropping entire trips; all candidate rows are retained for each sampled observation. Three-fold GroupKFold prevents observations from one trip entering both fit and validation sets. Learned scalers are fitted inside each fold. No evaluator data is used.

Candidate binary labels indicate whether a candidate matches the derived reference arc. If the reference is absent from the candidate set, every candidate is negative and the observation contributes to miss rate and Top-1 failure. Candidate Macro F1 is the mean of positive/negative F1 at probability threshold 0.5; it is not macro F1 across thousands of trip-specific road IDs. Observation Top-1 selects the highest-scoring candidate. Both definitions are necessary to interpret the tables correctly.

Model selection uses the mean of grouped-CV candidate Macro F1 and observation Top-1. Student-test results are reported for model comparison. The shortlisted tree family is tuned with 16 seeded Optuna TPE trials, five startup trials and the same three trip-grouped folds. Hyperparameter selection creates ordinary CV selection optimism; no nested outer evaluation is claimed. Student-test data is also used for decoder development, so decoder development scores are not an untouched generalization estimate.

The calibration experiment uses disjoint training/calibration/validation trip groups within each outer fold. A final sigmoid is fitted on out-of-fold scores. The nested calibrated models train on fewer fitting trips than the uncalibrated CV baselines; report this limitation. Confidence displayed in the production UI remains an uncalibrated relative score unless the manifest explicitly selects calibration.

## Directed HMM and Viterbi

Hidden states are candidate directed arcs per observation. Binary classifier probabilities are clipped and normalized across each candidate set. Fixed HMM uses log normalized probabilities. Adaptive HMM mixes those logs with distance/heading geometry; mixture weight rises with normalized candidate entropy. The distance scale adapts to local candidate distances. An explicit emission-strength parameter controls overconfidence.

Transitions use projected progress on the same arc or remaining current-arc length, a bounded directed shortest path, and the next-arc offset. Directed Dijkstra is limited to 2000 m; absence within that bound is not proof of global disconnection. Physically implausible moves above `65 * dt + 70` m are rejected. Same-arc backward projected movement up to a selected jitter tolerance is treated as GPS jitter, not reverse driving. The transition penalty is absolute network/observed displacement mismatch divided by `beta + 2 * sqrt(dt)`.

Viterbi runs in log space: `V[t,j] = emission[t,j] + max_i(V[t-1,i] + transition[t,i,j])`. Backpointers recover the full sequence. A gap above 60 s or complete infeasibility restarts a chunk; it is counted and exposed. Missing reference candidates cannot be recovered by the classifier or HMM; prediction still returns the best available candidate, and candidate miss rate records that limitation. Networks without usable arcs fail with a clear validation error.

The audit retained a soft log(2) immediate-reversal cost after fixed training-only holdout and robustness/timing gates. It is not a hard prohibition of real U-turns. Production transition values are unnormalized compatibility potentials used for MAP/Viterbi scoring; they are not a stochastic transition matrix or calibrated behavior probabilities. An explicitly row-normalized HMM alternative was evaluated and rejected after it reduced training-holdout accuracy and increased time. Physically bounded Dijkstra pruning preserves the original feasible transition set while reducing computation.

For display, shortest-path connectors are reconstructed between selected segments. Disconnected joins remain separate polylines rather than fabricated straight connections. Reference labels stay server-side. Direct arc continuity measures collapsed consecutive predictions sharing a node; network feasibility additionally permits valid multi-arc paths and tolerated same-arc GPS jitter. These are different metrics. Route arc-set F1 measures coverage, not sequence order; exact collapsed-sequence equality is reported separately.

Drawing also breaks at decoder resets even if a geometric connector could be found. That prevents the visualization from silently implying a continuous reconstruction across a sequence restart. Reference scoring is a separate failure boundary; malformed references do not invalidate successful inference.

## Contributions and known limits

Project-level contributions: long-segment-safe spatial indexing, a training-matched directional candidate experiment, entropy/geometry hybrid emissions, directed time-gap-aware transitions, explicit GPS-jitter tolerance, reference isolation, and offline interactive prediction visualization. None is claimed as a new research algorithm.

Noise/dropout stress tests retain the original derived labels and perturb GPS coordinates using a fixed seed. Three clearly identified development trips are tested; the results are not a full distributional robustness guarantee. Severe added noise can remove the reference from the candidate set and cause performance collapse. Training diagnostics and failure cases are retained rather than hidden.
