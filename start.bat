@echo off
setlocal
title EnginePulse - C-MAPSS RUL

REM Always run from the folder this file lives in (the repo root)
cd /d "%~dp0"

REM ---- Check Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo Install Python 3.10+ from https://www.python.org and tick "Add to PATH".
    pause
    exit /b 1
)

REM ---- Check dataset ----
if not exist "data\CMAPSS\train_FD001.txt" (
    echo [ERROR] data\CMAPSS\train_FD001.txt is missing.
    echo Put the C-MAPSS FD001 and FD003 files in data\CMAPSS\ and try again.
    pause
    exit /b 1
)

REM ---- Create virtual environment on first run ----
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
    call ".venv\Scripts\activate.bat"
    echo Installing dependencies. This takes a few minutes the first time ...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency install failed.
        pause
        exit /b 1
    )
) else (
    call ".venv\Scripts\activate.bat"
)

:menu
echo.
echo ==============================================
echo   C-MAPSS Remaining Useful Life prediction
echo ==============================================
echo   1. Run all experiments   (about 75 min on CPU)
echo   2. Rebuild figures only  (about 1 min)
echo   3. Build the Word report (needs Node.js)
echo   4. Reinstall dependencies
echo   5. Exit
echo.
set "choice="
set /p choice=Pick an option [1-5]:

if "%choice%"=="1" goto run_all
if "%choice%"=="2" goto figures
if "%choice%"=="3" goto report
if "%choice%"=="4" goto reinstall
if "%choice%"=="5" goto end
echo Not a valid option.
goto menu

:run_all
echo Running all experiments. Output goes to results\results.json
python code\run_experiments.py
if errorlevel 1 echo [ERROR] The experiment run stopped with an error.
goto menu

:figures
python code\make_figures.py
if errorlevel 1 echo [ERROR] Figure generation stopped with an error.
goto menu

:report
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js was not found. Install it from https://nodejs.org
    goto menu
)
pushd report
if not exist "node_modules\docx" call npm install docx
node build_report.js
popd
goto menu

:reinstall
python -m pip install --upgrade -r requirements.txt
goto menu

:end
endlocal
