@echo off
setlocal
title Engine Health Monitor - website
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.10+ and tick "Add to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment ...
    python -m venv .venv || (echo [ERROR] Could not create .venv & pause & exit /b 1)
)
call ".venv\Scripts\activate.bat"

python -c "import streamlit, torch" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies. First run takes a few minutes ...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt || (echo [ERROR] Install failed & pause & exit /b 1)
)

echo.
echo Starting the website. It opens in your browser at http://localhost:8501
echo Keep this window open while you use the site. Close it to stop the site.
echo.
python -m streamlit run code\app.py --server.port 8501 --browser.gatherUsageStats false
pause
