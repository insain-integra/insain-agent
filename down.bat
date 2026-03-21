@echo off
REM Остановка API и бота (аналог: make down)
cd /d "%~dp0"
python scripts\dev.py stop all
if errorlevel 1 pause
