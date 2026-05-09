@echo off
echo Clearing Course Manager backend data...
cd /d "%~dp0backend"
call venv\Scripts\activate
python clear_data.py %*
pause
