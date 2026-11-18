# Genuine receiving-laptop console evidence

Status: **not captured / not physically verified**. This checklist is preparation, not evidence of execution.

## Before capture

- [ ] Use the final verified backend ZIP and record its SHA-256 from `checksums.json`.
- [ ] Record the source commit from the package provenance file, and SHA-256 of `artifacts/model.joblib`.
- [ ] Start `run_backend.cmd 8000` in Command Prompt on Laptop 1 with access logs; keep that actual CMD receiving window visible.
- [ ] Run the UI on physical Laptop 2, configured to Laptop 1's active IPv4 address.
- [ ] Verify health from Laptop 2 and ten complete trip choices in the intended partition.
- [ ] Let the evaluator/team choose a trip and click Reconstruct. Do not use a prerecorded response.

## The Laptop 1 screenshot must show

- [ ] Actual receiving terminal window with the running backend, not a browser rendering of a log.
- [ ] `INFERENCE request=... trip=... started` for the selected trip.
- [ ] Completion line with the **same request ID**, observation count, measured inference time and scoring availability.
- [ ] Successful `POST /api/predict` / HTTP 200 access log.
- [ ] Access-log client address is consistent with physical Laptop 2 on the shared network, rather than a localhost-only rehearsal; record both adapter addresses privately for corroboration.
- [ ] Sufficient context to identify the server/model or a second genuine startup screenshot.
- [ ] No passwords, tokens, unrelated private applications or unnecessary personal information.

## Corroborating Laptop 2 screenshot and notes

- [ ] UI shows the same selected trip, completed route, displayed metric basis and matching request ID.
- [ ] Note the date, actual partition, both machine roles, backend port, source commit and archive/model hashes.
- [ ] Preserve the original image files; do not fabricate, composite, replace text or relabel local testing as two-machine evidence.
- [ ] Save originals under a private `submission_evidence/` folder first. Select only necessary evidence for the final report/publication after reviewing organizer/data rules.
- [ ] Insert genuine evidence into the report and rebuild/review it. Keep derived-reference accuracy explicitly labeled; do not claim the scorer is official without organizer confirmation.
- [ ] Test all ten trips and retain a request-ID checklist, even if only representative screenshots are submitted.

If scoring is unavailable, record that fact and resolve the organizer's accuracy requirement. A successful route response alone is not proof of valid reference scoring.
