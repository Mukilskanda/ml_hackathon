@echo off
cd /d "%~dp0"
set "PATHSNAP_UI_PORT=%~1"
if "%PATHSNAP_UI_PORT%"=="" set "PATHSNAP_UI_PORT=8080"
echo Open http://localhost:%PATHSNAP_UI_PORT% in a browser. Configure Laptop 1's server URL using Settings.
python -m http.server %PATHSNAP_UI_PORT% --bind 0.0.0.0 --directory ui
pause
