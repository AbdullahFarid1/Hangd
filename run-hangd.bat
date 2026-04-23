@echo off
REM ============================================================
REM  Hangd — launch worker + dev server
REM  Double-click from the project root.
REM ============================================================

set "ROOT=%~dp0"

REM ----- Sanity checks ----------------------------------------
echo.
echo === Hangd launcher ===
echo Root: %ROOT%
echo.

if not exist "%ROOT%.venv\Scripts\activate.bat" (
    echo ERROR: .venv not found at %ROOT%.venv
    echo Create it with:  python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "%ROOT%backend\.env" (
    echo ERROR: backend\.env missing. Copy backend\.env.example to backend\.env and add your Supabase keys.
    pause
    exit /b 1
)

if not exist "%ROOT%web\node_modules" (
    echo ERROR: web\node_modules missing. Run:  cd web ^&^& npm install
    pause
    exit /b 1
)

if not exist "%ROOT%web\.env.local" (
    echo ERROR: web\.env.local missing. Copy web\.env.example to web\.env.local and add your Supabase keys.
    pause
    exit /b 1
)

REM ----- Port conflict check ----------------------------------
netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo WARNING: Something is already listening on port 3000.
    echo If it's a leftover dev server, kill it before continuing.
    echo To find the PID:  netstat -ano ^| findstr :3000
    echo Then:             taskkill /F /PID ^<pid^>
    echo.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "%CONTINUE%"=="y" exit /b 0
)

REM ----- Prepare log file -------------------------------------
if not exist "%ROOT%data\logs" mkdir "%ROOT%data\logs"
REM Touch the log file so the tail window has something to read from startup.
type nul >> "%ROOT%data\logs\worker.log"

REM ----- Launch -----------------------------------------------
echo Starting worker, dev server, and log tail in three new windows...
echo (Leave them open. Close them with Ctrl+C inside each window when done.)
echo.

REM cmd /k keeps the window open even if the command crashes — you can read the error.
start "Hangd worker" cmd /k "cd /d "%ROOT%" && call .venv\Scripts\activate.bat && python -m backend.worker || echo. && echo --- WORKER EXITED. Read the error above and fix it. Press any key to close this window. --- && pause"

start "Hangd web (npm run dev)" cmd /k "cd /d "%ROOT%web" && npm run dev || echo. && echo --- DEV SERVER EXITED. Read the error above. Press any key to close this window. --- && pause"

REM PowerShell Get-Content -Wait acts like `tail -f` for a live log view.
start "Hangd logs (tail worker.log)" powershell -NoExit -Command "Get-Content -Path '%ROOT%data\logs\worker.log' -Wait -Tail 200"

echo Three windows opened. Visit http://localhost:3000 once the dev server prints "Ready".
echo Log file: %ROOT%data\logs\worker.log
echo.
pause
