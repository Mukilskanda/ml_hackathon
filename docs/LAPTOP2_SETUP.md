# Laptop 2: exact UI transfer

Transfer only `packages/PathSnap_Laptop2_UI.zip` to the UI laptop. The archive contains static UI files, a launcher and deployment/demo guides; it contains no model, GPS dataset or reference labels.

1. Extract the ZIP. Use Python 3 to serve it; no pip installation is needed.
2. Run `run_ui.cmd 8080`, or `python -m http.server 8080 --directory ui`.
3. Open `http://localhost:8080`.
4. Click Settings and enter `http://<Laptop1-IPv4>:<backend-port>`.
5. Verify the status, active partition and ten options. Run every trip and confirm matching request IDs on Laptop 1.

The address can also be supplied as `http://localhost:8080/?api=http://<Laptop1-IPv4>:8000`. A stored setting is local to this browser. Never enter `localhost` as the backend address unless the backend is actually on this laptop. See DEPLOYMENT.md for troubleshooting.

Use the same reachable network or a tested hotspot. Network isolation, firewall prompts and the genuine receiving-console screenshot must be verified on the physical machines. This project does not alter firewall settings.
