# Laptop 1: exact backend deployment

Use `packages/PathSnap_Laptop1_Backend.zip` when deploying to a fresh model-server laptop. The complete local ZIP is an optional source/data backup, not the UI transfer archive.

## Installation

1. Install/use 64-bit Python 3.13 (the verified version family). Extract the ZIP into a writable folder.
2. In that folder run:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --access-log
```

Alternatively use `setup_backend.cmd` then `run_backend.cmd 8000`. The archive contains the selected inference artifacts, required source/UI, experiment summaries and all ten student-test rehearsal trip folders. It contains no training cache or unselected model files.

## Data and configuration

The default data root is `data/`. Rehearsal inputs are under `data/Student folder/student_test/<id>/`. When supplied by organizers, put reserved trips under `data/evaluator_test/<id>/`; that partition is activated when actual trip directories exist. The health endpoint lists complete-trip counts and missing-file warnings. Keep `.route` files here only; inference does not read them.

Optional PowerShell configuration:

```powershell
$env:PATHSNAP_DATA_ROOT = 'D:\PathSnapData'
$env:PATHSNAP_THREADS = '4'
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 9000 --access-log
```

The example data-root value is a placeholder, not an embedded project path. Set it to your actual data directory. `0.0.0.0` is a bind address, not the URL to enter on Laptop 2. Use Laptop 1's IPv4 address and actual backend port. Keep the server console visible for request evidence.

Before evaluation, check `/api/health`, `/api/trips`, all ten live predictions and the model/decoder manifest. No training is required. Test under the same locked packages used by the verified clean installation.
