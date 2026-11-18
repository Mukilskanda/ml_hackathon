# Final submission and deployment handoff

The model, features and selected decoder are frozen. Do not run training, Bayesian search or decoder-selection scripts for the demonstration. The only remaining work is publication, physical deployment, organizer confirmation and team sign-off.

## What to copy

| Destination | Copy exactly | Install | Keep private |
|---|---|---|---|
| Laptop 1: backend/model | `packages/PathSnap_Laptop1_Backend.zip`, plus `packages/checksums.json` | 64-bit Python 3.13; locked Python packages in a virtual environment | Raw trip files and reference `.route` files stay here |
| Laptop 2: frontend | `packages/PathSnap_Laptop2_UI.zip`, plus `packages/checksums.json` | Python 3 for the standard-library static server; modern browser; no pip packages | No model, GPS dataset or reference files are needed |
| Public GitHub | Prepared folder `packages/PathSnap_Publication_Source/`, or `PathSnap_Publication_Source.zip` | Git and the team's GitHub authentication | Never upload backend/full-local ZIPs or push the private development repository's history |
| Report submission | `output/pdf/PathSnap_Technical_Report.pdf` | PDF reader | Submit through the organizer's required channel; confirm any public redistribution permission |
| Private backup only | `packages/PathSnap_Complete_Local.zip` | None | Contains supplied data and detailed experiment evidence; not a public release asset |

The publication snapshot omits raw data, per-point arrays, coordinate-bearing generated maps/screenshots and the PDF. It retains source, required model artifacts, aggregate experiments, dependency notices and map/report generation code. The PDF remains the separate official deliverable. Public inclusion of location-bearing outputs can be decided after organizer permission; no permission was inferred from the absence of a license file.

## 1. Check archive integrity before copying

Run in PowerShell from the folder containing the ZIPs and `checksums.json`:

```powershell
$expected = Get-Content .\checksums.json -Raw | ConvertFrom-Json
$actual = (Get-FileHash .\PathSnap_Laptop1_Backend.zip -Algorithm SHA256).Hash.ToLowerInvariant()
$actual -eq $expected.'PathSnap_Laptop1_Backend.zip'.sha256
```

Expect `True`. Repeat with `PathSnap_Laptop2_UI.zip` for Laptop 2. Use the newly generated checksums, not hashes copied from an old chat. `transfer_manifest.json` lists every deployment member and its SHA-256.

## 2. Laptop 1: install and start the model server

1. Extract the backend ZIP into a writable folder. Open PowerShell in that extracted folder.
2. Check the interpreter and create an isolated environment:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Use Python 3.13, the verified version family. Installation needs internet access unless the dependencies are already available from an approved local package cache. `pip check` must print `No broken requirements found.` No model training is needed.

3. Start the server and keep this console open:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --access-log
```

Alternatively double-click `run_backend.cmd`, or run `run_backend.cmd 8000` from CMD after `setup_backend.cmd`. Expected log content includes:

```text
PathSnap model=HistGradientBoosting_tuned_adaptive_candidates decoder=adaptive; inference does not read .route files
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

Process IDs and exact log prefixes can differ. Stop with Ctrl+C. Do not close the server before the demonstration ends.

For the specifically requested receiving-**CMD** screenshot, open Command Prompt in this backend folder and run `run_backend.cmd 8000`; use that real receiving window for capture. PowerShell installation steps above do not substitute for the requested CMD evidence.

4. In a second PowerShell window on Laptop 1:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
ipconfig
```

Expect `status: ok`, `complete_trip_count: 10`, `data_ready: True`, and no data warnings for a complete supplied partition. Initially `mode` is `development`. Write down the **IPv4 address of the active shared Wi-Fi/Ethernet adapter**; ignore disconnected, VPN and virtual adapters. Do not use `0.0.0.0` or `127.0.0.1` as Laptop 2's server address.

## 3. Network and firewall prerequisites

- Put both machines on the same reachable, trusted network. Guest Wi-Fi and some hotspots isolate clients.
- Laptop 1 must accept inbound TCP on the selected backend port, normally 8000, from Laptop 2. Bind to `0.0.0.0`, as above.
- If Windows asks about Python, the owner should allow the intended Python interpreter on the appropriate **Private** network. If necessary, the owner/admin can add a narrow inbound TCP 8000 rule scoped to Private/local subnet. Follow campus IT rules. Do not disable the firewall, expose the server publicly or enable unrelated ports.
- Laptop 2 serves its UI locally; this workflow does not require exposing its port 8080 to Laptop 1.
- This project does not automatically change network profiles or firewall settings. Those decisions require the machine owner or administrator.

## 4. Laptop 2: start and connect the UI

1. Extract the UI ZIP. Open PowerShell in that folder:

```powershell
python --version
python -m http.server 8080 --bind 127.0.0.1 --directory ui
```

Alternatively run `run_ui.cmd 8080`. The launcher binds more broadly; the explicit command above serves only this laptop. Expected console output resembles `Serving HTTP on 127.0.0.1 port 8080`.

2. Open `http://localhost:8080` in the browser.
3. Click the Settings gear. Enter `http://LAPTOP1_IPV4:8000`, replacing `LAPTOP1_IPV4` with the actual address from `ipconfig`, and save. Do not enter that placeholder literally.
4. From another PowerShell window on Laptop 2, test the real address. Replace the example first:

```powershell
$serverIp = '192.168.1.25'
Test-NetConnection -ComputerName $serverIp -Port 8000
Invoke-RestMethod "http://${serverIp}:8000/api/health"
```

`192.168.1.25` is an example only, not a project setting. Expect `TcpTestSucceeded: True` and the backend health response. A successful Laptop 1 localhost check alone does not prove this cross-machine connection.

5. Confirm the UI says **Model server online**, lists ten actual active trips, and shows the correct partition label. Select and reconstruct **all ten** trips, not just the short example.

## 5. Verify a genuine inference request

For each selected trip, Laptop 1 should print actual messages of this form:

```text
INFERENCE request=<new-id> trip=<selected-trip-id> started
INFERENCE request=<same-id> trip=<selected-trip-id> observations=<count> inference_s=<measured> scored=True completed
"POST /api/predict HTTP/1.1" 200 OK
```

The UI completion message contains the same request ID. Values are generated during execution; never edit or prewrite logs. `scored=False` or null metrics means reference scoring is unavailable; a route prediction can still succeed. If the evaluator requires accuracy, resolve that missing reference/scorer before evaluation.

## 6. Reserved evaluation data

Obtain the ten reserved trip folders from the organizer. Keep them **only on Laptop 1**, under `data/evaluator_test/<eight-digit-trip-id>/` with matching `.track`, `.nodes` and `.arcs` names. `.route` is optional for inference and used only server-side for scoring if legitimately provided. Actual trip directories activate evaluator mode; health/menu warnings identify incomplete folders. Refresh the UI and verify ten complete evaluator options.

Do not train, tune or manually repair predictions using reserved references. Confirm whether the organizer supplies point labels or a specific official route scorer. The current scorer uses a documented derived monotone alignment; its displayed percentage must not be presented as official evaluator accuracy.

## 7. Genuine console screenshot checklist

Follow `docs/CONSOLE_SCREENSHOT_CHECKLIST.md`. Capture the actual receiving CMD/PowerShell window on Laptop 1 after a live request from Laptop 2, with matching request ID/trip ID and successful POST/completion visible. Capture Laptop 2's corresponding UI separately. Save the original screenshots and a short text record of the commit, model hash, date, partition and trip. No screenshots proving this physical setup have been created here.

## 8. Troubleshooting

| Symptom | Check / action |
|---|---|
| `python` not found or opens Store | Install/use 64-bit Python 3.13 and reopen the terminal; verify `python --version` |
| Port already in use | Close the prior server or choose another port, e.g. 9000; update the UI URL and firewall scope consistently |
| Laptop 1 health works; Laptop 2 TCP fails | Correct adapter IPv4, same network, bind address, client isolation, owner/admin's inbound firewall permission |
| TCP works but UI fails | Include `http://` and the backend port; check stored Settings; use the actual Laptop 1 address, not Laptop 2 localhost |
| No/too few trip options | Read health `data_warnings`; check matching filenames and complete `.track/.nodes/.arcs` trip folders |
| Wrong partition | Check for reserved trip directories and any `PATHSNAP_DATA_ROOT` override; development is expected before reserved data is supplied |
| Startup schema/profile mismatch | Restore the model, manifest and decoder from the same verified backend ZIP; do not mix artifact versions |
| Route returned but accuracy absent | Inspect receiving logs/reference data; malformed references do not invalidate inference; confirm official scorer |
| Slow first request | Distinguish cold startup, inference, geometry/scoring and network time; retain the locked environment; do not retrain |
| No online basemap | Main UI geographic canvas works offline. Optional Folium HTML needs Leaflet CDN resources; online tiles are optional |
| Incorrect route | Report the actual failure, uncertainty and resets; do not alter predictions or hide the trip |

## 9. Public repository and final submission

Use `docs/PUBLICATION.md` and `docs/LICENSING_AND_DATA.md`. The local development history contains detailed derived records; do not directly push that history by accident. A curated, clean publication snapshot is prepared separately. Its runtime/model files must match the final source commit, as checked by `scripts/submission_checks.py`.

Before submission, replace team placeholders, review actual contributions and AI assistance disclosure, and rehearse `docs/DEMO_SCRIPT.md` using `docs/VIVA_GUIDE.md`. Submit the public repository URL and the single consolidated PDF through the organizer's required channel. Verify the URL while logged out. Publication and physical execution remain incomplete until observed and recorded.

## Manual actions that cannot be completed here

1. Provide team names/USNs, confirm actual contributions/originality/AI disclosure, review the report and rehearse the viva.
2. Ask organizers for reserved trips, the official scoring convention, first-phase schedule/scope and redistribution rules for dataset-derived outputs.
3. Perform the two-laptop network/firewall setup, run every trip, and capture genuine console/UI evidence.
4. Publish the prepared clean repository through the team's account, verify public access, and submit its URL plus the final PDF.
