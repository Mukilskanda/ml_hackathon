# Three-minute demonstration script

## Before the evaluator arrives

- Laptop 1: `run_backend.cmd 8000`, with receiving console visible.
- Laptop 2: `run_ui.cmd 8080`, open `http://localhost:8080`, configure Laptop 1's IPv4 URL in Settings.
- Verify ten complete actual active trips. DEVELOPMENT is correct for supplied rehearsal data; do not label it reserved evaluation data.
- Check `http://<Laptop1-IP>:8000/api/health`. Keep the final commit and manifest available.

## 0:00-0:30 — Problem and boundary

"We reconstruct a road sequence from noisy GPS observations and a directed road network. Road IDs differ between trips, so our model scores candidate roads rather than predicting a global road-ID class. The UI runs on this laptop; the saved model, graph decoder and reference scorer run on the other laptop."

## 0:30-1:10 — Run a live request

Let the evaluator select any of the ten available trips. Click Reconstruct. Point to the new request ID in Laptop 1's console and its matching completion in Laptop 2. Explain that this executes candidate generation, model prediction and Viterbi without training or a prediction lookup.

Toggle GPS, classifier-only, decoded route and uncertainty layers. Zoom/pan and move the playback slider. Read latency as inference time, not total network delay. Explain any reset or disconnected join rather than hiding it.

## 1:10-1:50 — Explain the mathematics

"We project GPS onto nearby directed segments and use geometry, motion and topology features. The selected boosted tree produces candidate affinities. Our sequence score combines learned and geometric emission information with directed shortest-path compatibility. Viterbi chooses the best complete sequence. A small soft prior discourages immediate reversals caused by jitter, while elapsed-time limits and explicit gap resets handle missing observations."

"The transition scores are unnormalized compatibility potentials, not calibrated probabilities of driver behavior. We tested a row-normalized HMM alternative; it was worse on the training-only holdout."

## 1:50-2:30 — Show evidence

Open Experiment bench. Identify seven baseline algorithms, the grouped-CV selection objective, 16 Bayesian trials, and classifier-only versus sequence results. Explain the final model choice and one rejected approach. Open the report's audit appendix for the latency-preserving optimization and training-only prior validation.

"Our original 95.25% is an equal-trip mean agreement with derived reference labels, not an official independent ground-truth score. Observation weighting gives a different result. Current figures are recorded in the audit; the final change has a negligible student-test aggregate gain and can regress on an individual trip."

## 2:30-3:00 — Integrity and limitations

"The supplied .route is a sequence of traversed segments, so we document a separate monotone reference alignment. Reference labels never enter inference. A separate request can display the student-test reference in blue after prediction. Reserved evaluator references never enter the UI. We group CV by complete trip and keep evaluator data untouched during development. Severe added GPS noise remains a failure case. Official scoring and physical deployment evidence are reported only when actually verified."

Offer the source, report, manifest, trial history and actual logs. Each member should answer questions across all components; use `VIVA_GUIDE.md` for preparation.

## If something fails

- Connection error: check Settings, Laptop 1 address/port and `/api/health`; no need to retrain.
- No/too few trip options: inspect health/data warnings and complete input files.
- Null accuracy: predictions still work; inspect server-side reference scoring and its warning.
- Slow first request: distinguish cold start, inference, route geometry and scoring timings.
- A wrong route: show the raw points, classifier layer and uncertainty; identify the failure honestly.
- Capture genuine UI and receiving-console screenshots during the physical rehearsal. Do not substitute a browser screenshot for a CMD screenshot.
