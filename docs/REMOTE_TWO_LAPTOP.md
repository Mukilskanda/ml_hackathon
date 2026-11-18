# Genuine two-laptop demonstration from different locations

The two laptops can communicate over a private ZeroTier or Tailscale VPN; they do not have to share Wi-Fi or be in the same location. This is still a real two-device run if the frontend actually runs on Laptop 2 and sends requests to the backend on Laptop 1. It is not marked verified until that run and its evidence exist.

## ZeroTier option

1. Sign in at https://central.zerotier.com and create a private network. Copy its Network ID.
2. Both users install ZeroTier from https://www.zerotier.com/download/.
3. On each laptop, open the tray icon, select Join New Network, and enter the same Network ID.
4. In Central, authorize both devices under Member Devices/Members. Match the device identities rather than authorizing unknown requests.
5. Copy Laptop 1's Managed IP address from the member list. The Network ID joins the network; the Managed IP addresses the backend.
6. In Laptop 2's PathSnap settings, use http://LAPTOP1-MANAGED-IP:8000. Run the health/TCP checks below using that IP.
7. If blocked, check authorization, assigned Managed IPs, ZeroTier network rules and Laptop 1's firewall permission for TCP 8000 from Laptop 2's actual Managed IP.

Official creation/join/authorization guide: https://docs.zerotier.com/quickstart/.

## Tailscale option

1. Both users install Tailscale for Windows: https://tailscale.com/docs/install/windows.
2. Laptop 1's owner signs up/signs in, creating a private network (tailnet), and signs the local app into that network.
3. In the admin console, open Users, select Invite external users, and copy an invitation link or invite the teammate's email. The teammate accepts using her own account and connects her app to the invited network. Do not share account passwords.
4. Confirm both machines are online in the admin console. Copy Laptop 1's Tailscale IPv4 address (normally 100.x.x.x).

Official setup/invitation instructions: https://tailscale.com/docs/how-to/quickstart. Service connection and troubleshooting: https://tailscale.com/docs/how-to/connect-to-devices.

## Laptop 1: backend

Stop an older backend in its own terminal with Ctrl+C, then start the final code once. For the genuine receiving-CMD screenshot, use Command Prompt in the original project folder:

```cmd
tmp\clean_env\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --access-log
```

In an extracted backend package after setup, use `.venv\Scripts\python.exe` instead. Keep this CMD window open. Reserved evaluator references stay server-side; the UI gets predictions and aggregate scoring only. Student-test comparison maps can show their supplied reference.

## Laptop 2: UI and connection check

Extract PathSnap_Laptop2_UI.zip. In its folder, run:

```powershell
python -m http.server 8080 --bind 127.0.0.1 --directory ui
```

Open http://localhost:8080. In PathSnap's settings, enter `http://LAPTOP1-TAILSCALE-IP:8000`, replacing the placeholder with Laptop 1's actual VPN address: its ZeroTier Managed IP or its Tailscale 100.x.x.x address.

In another PowerShell window, replace the example address and run:

```powershell
$backendIp = '100.101.102.103'
Test-NetConnection -ComputerName $backendIp -Port 8000
Invoke-RestMethod "http://${backendIp}:8000/api/health"
```

Expected: TcpTestSucceeded is True; health reports status ok, evaluator mode and ten complete trips. The example IP is not a project setting. Both devices need the selected VPN connected, permission to reach the service and working internet connections.

If the port is blocked, check that the backend listens on 0.0.0.0, both machines are authorized on the intended VPN network, and its rules permit Laptop 2 to reach Laptop 1 TCP 8000. Laptop 1's owner may also need a Windows Firewall inbound rule. A narrow optional rule, run as administrator on Laptop 1 after replacing the peer address, is:

```powershell
$peerIp = '100.101.102.104'
New-NetFirewallRule -DisplayName 'PathSnap private VPN TCP 8000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress $peerIp -Profile Any
```

The peer address must be Laptop 2's actual VPN IP, either its ZeroTier Managed IP or its Tailscale IP. No firewall changes are automated and no public port forwarding is required.

## Capture genuine evidence

1. Laptop 2 selects and reconstructs a real evaluator trip; test all ten.
2. Laptop 1 captures its actual CMD window showing INFERENCE start/completion with a matching request ID and POST /api/predict HTTP 200. Keep the client address visible for corroboration.
3. Laptop 2 captures the corresponding UI trip, route and request ID.
4. Record both machine roles, network method (ZeroTier or Tailscale VPN), trip, date, source commit and model/package hashes. Preserve originals under submission_evidence/ and add the genuine receiving-CMD image to the report.

Two processes on one laptop are a local rehearsal. Label them as such; they do not prove physical two-laptop operation. Confirm any alternative demonstration arrangement with the organizer.
