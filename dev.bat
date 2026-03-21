@echo off
REM Универсально: dev.bat status | dev.bat start calc
cd /d "%~dp0"
python scripts\dev.py %*
if errorlevel 1 pause
