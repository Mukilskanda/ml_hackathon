@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if errorlevel 1 exit /b 1
echo Setup complete. Run run_backend.cmd on Laptop 1.
pause
