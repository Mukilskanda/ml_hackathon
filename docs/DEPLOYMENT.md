# Deployment and physical verification

## Laptop 1: model server

1. Extract the complete project/archive. Use Python 3.13 if available.
2. Run `setup_backend.cmd` once, or create a virtual environment and install `requirements.lock.txt` manually.
3. Confirm `artifacts/model.joblib`, `artifacts/manifest.json`, `artifacts/decoder.json` exist. Keep `data/Student folder/student_test/` for rehearsal. Training is unnecessary for serving.
4. Run `run_backend.cmd 8000`. Keep the receiving console visible during evaluation.
5. Open `http://localhost:8000/api/health` and `http://localhost:8000/docs`.
6. Use `ipconfig` to find this laptop's IPv4 address on the shared network. Port 8000 is a default, not a requirement; pass another port to the launcher if needed.

## Laptop 2: user interface

1. Transfer `PathSnap_Laptop2_UI.zip`; no dataset, model or reference files are needed.
2. Extract it. Python is used only to serve static files; no pip packages are required.
3. Run `run_ui.cmd 8080` and open `http://localhost:8080`.
4. Click the settings gear. Enter `http://<Laptop1 IPv4>:<backend port>` and save. The URL is stored locally in this browser. There is no hardcoded LAN IP.
5. Check that the connection status is online and the trip menu contains the correct ten options.

## Network troubleshooting

- Both laptops must be reachable on the same network; guest Wi-Fi can isolate clients. A personal hotspot can also have client isolation depending on the device.
- The backend must bind to `0.0.0.0`, not just `127.0.0.1`.
- Check the configured port and Laptop 1's current IPv4 address. `localhost` on Laptop 2 means Laptop 2, not Laptop 1.
- If Windows asks about Python networking, the laptop owner must decide the appropriate private-network access. This project does not alter firewall/security settings.
- The UI's geographic canvas and system-font fallback work offline. Optional Folium HTML uses external Leaflet resources and OpenStreetMap tiles, which require network access.

## Reserved evaluator data

The supplied ZIP contains no evaluator partition. Add actual reserved trip folders under `data/evaluator_test/<eight-digit-id>/`. Actual eight-digit trip directories activate evaluator mode; a stray README does not. Only complete `.track`/`.nodes`/`.arcs` trip folders enter the menu. Health/trip endpoints report missing files and counts other than ten. `.route`, if legitimately supplied, is read only by the server-side scorer after inference. A malformed reference produces a scoring warning and null metrics while preserving the prediction. Official pointwise scoring may require an organizer-provided scorer; the current alignment-derived metric is clearly labeled.

`PATHSNAP_DATA_ROOT` can point to another data directory; `PATHSNAP_THREADS` sets the default OpenMP/BLAS thread budget. The backend validates model/feature/candidate-profile compatibility on startup. The UI defaults to its own HTTP origin, supports `?api=...`, and stores a configured address; hosting the backend UI on a custom port works without assuming port 8000.

Read-only network diagnostics from Laptop 2:

```powershell
Test-NetConnection -ComputerName <Laptop1-IPv4> -Port 8000
Invoke-RestMethod http://<Laptop1-IPv4>:8000/api/health
```

Replace angle-bracket placeholders before running. A successful local health check on Laptop 1 does not establish reachability from Laptop 2. If the UI says server unavailable, check URL scheme/port, IP changes, guest-network isolation, and the owner's private-network firewall permission. Never enter the wildcard bind address `0.0.0.0` as a client URL. No firewall changes are automated.

## Physical verification checklist (NOT yet performed)

- [ ] Start backend on Laptop 1 and static UI on Laptop 2.
- [ ] Reach health endpoint from Laptop 2 using Laptop 1's network address.
- [ ] Confirm ten actual evaluator trips when supplied, otherwise ten student-test rehearsal trips.
- [ ] Select and reconstruct every active trip across the network.
- [ ] Confirm unique live request IDs and HTTP responses in Laptop 1's console.
- [ ] Confirm route and metrics update in Laptop 2's UI.
- [ ] Test incorrect server URL and recover through settings.
- [ ] Test a fresh browser or clear browser storage and reconnect.
- [ ] Capture genuine UI and receiving-console screenshots during the two-laptop rehearsal.
- [ ] Keep the reference files server-side and confirm they are absent from the UI transfer ZIP.
- [ ] Replace placeholders, review the PDF and publish/verify the GitHub repository.

Local separate-origin browser and API tests are recorded in `results/browser_qa.json` and `results/api_verification.json`. They are not evidence that two physical laptops were tested.
