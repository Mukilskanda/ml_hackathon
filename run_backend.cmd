@echo off
cd /d "%~dp0"
set "PATHSNAP_PORT=%~1"
if "%PATHSNAP_PORT%"=="" set "PATHSNAP_PORT=8000"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port %PATHSNAP_PORT% --access-log
) else (
  python -m uvicorn backend.app:app --host 0.0.0.0 --port %PATHSNAP_PORT% --access-log
)
pause
