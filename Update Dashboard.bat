@echo off
title USDA Rail Dashboard Updater
cd /d "%~dp0"

set NETLIFY=C:\Users\KoltenPostin\AppData\Roaming\npm\netlify.cmd
set PYTHON=C:\Users\KoltenPostin\AppData\Local\Programs\Python\Python312\python.exe
set PUBLISH=%~dp0publish

:: ── Step 1: Rebuild data and update HTML ──────────────────────────────────────
echo.
echo [1/2] Updating dashboard data...
"%PYTHON%" "%~dp0update_dashboard.py"

if %errorlevel% neq 0 (
    echo.
    echo Something went wrong with the data update. See above for details.
    pause
    exit /b 1
)

:: ── Step 2: Deploy to Netlify ─────────────────────────────────────────────────
echo.
echo [2/2] Deploying to Netlify...

if not exist "%NETLIFY%" (
    echo  Netlify CLI not found at %NETLIFY%
    pause
    exit /b 1
)

"%NETLIFY%" deploy --prod --dir "%PUBLISH%"

if %errorlevel% neq 0 (
    echo.
    echo  Netlify deploy failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo  Done! Dashboard is live and updated.
echo.
pause
