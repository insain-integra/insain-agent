@echo off
REM Запуск API + бота (аналог: make up)
cd /d "%~dp0"
python scripts\dev.py start all
if errorlevel 1 pause
