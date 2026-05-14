@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%lib\vnpy;%ROOT%lib\vnpy_ctp;%ROOT%lib\vnpy_ctptest;%ROOT%"
echo Starting CTP Penetration Test Web Console...

REM Start Web server in background
start /b "" "%ROOT%.venv\Scripts\python.exe" "%ROOT%src\app\web\main.py"

REM Wait for server startup
timeout /t 3 /nobreak >nul

REM Open browser
echo Opening browser...
start http://127.0.0.1:5006

REM Keep window open
echo Web console is running. Close this window to stop.
pause
